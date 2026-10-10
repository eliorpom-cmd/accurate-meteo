// Two jobs on Cloudflare:
// 1. Reliable clock: GitHub delays or drops scheduled workflows when busy, Cloudflare cron triggers fire on time.
//    Every 15 minutes, start the forecast workflow unless a run is already queued or running.
//    Secret: GITHUB_TOKEN (fine-grained, this repository only, Actions: read and write).
// 2. Public API (https://meteo-api.byelior.com/v1/prevision): the latest prevision.json, open to everyone, no key,
//    cached 60 s at Cloudflare's edge so traffic never reaches GitHub more than once a minute per location.
// 3. History (/v1/historique): the public forecast as served at each hour, kept by the workflow on the `journal` branch
//    (historique/<YYYY-MM-DDTHHZ>.json, first run of each hour, never rewritten).
const REPO = 'eliorpom-cmd/accurate-meteo';

const gh = (env, path, init = {}) =>
  fetch(`https://api.github.com/repos/${REPO}${path}`, {
    ...init,
    headers: {
      Authorization: `Bearer ${env.GITHUB_TOKEN}`,
      Accept: 'application/vnd.github+json',
      'User-Agent': 'accurate-meteo-horloge',
      ...(init.headers || {}),
    },
  });

async function tick(env) {
  for (const status of ['queued', 'in_progress']) {
    const runs = await (await gh(env, `/actions/workflows/prevision.yml/runs?status=${status}&per_page=1`)).json();
    if (runs.total_count > 0) return `déjà ${status}`;
  }
  const r = await gh(env, '/actions/workflows/prevision.yml/dispatches', {
    method: 'POST',
    body: JSON.stringify({ ref: 'main' }),
  });
  if (r.status !== 204) throw new Error(`GitHub ${r.status} ${await r.text()}`);
  return 'lancé';
}

const SOURCE = `https://raw.githubusercontent.com/${REPO}/prevision/prevision.json`;
const RAW = `https://raw.githubusercontent.com/${REPO}/journal/historique`;
const ENDPOINTS = { prevision: '/v1/prevision', historique: '/v1/historique', heure: '/v1/historique/2026-10-10T12Z', avant: '/v1/historique?le=2026-10-09T18:30Z' };
const CORS = { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'GET, OPTIONS' };
const META = {
  modele: 'GRESIL',
  api_version: 1,
  doc: `https://github.com/${REPO}#public-api`,
  lieu: { nom: 'Grenoble', latitude: 45.2115, longitude: 5.6828, altitude_m: 213 },
  attribution: 'GRESIL, Accurate Meteo (MIT). Données : Open-Meteo (CC BY 4.0), Météo-France (Licence Ouverte 2.0), EUMETSAT.',
  usage: 'Libre et sans clé, usage non commercial (condition de l\'offre gratuite Open-Meteo). Citez la source.',
};

function json(body, status = 200, extra = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json; charset=utf-8', ...CORS, ...extra },
  });
}

// Hours recorded, oldest first ("2026-10-10T12Z"), from the git tree of the journal branch.
// Authenticated call (5 000/h instead of 60/h per shared Cloudflare IP), cached 5 min at the edge.
async function heures(env, ctx) {
  const cle = new Request('https://cache.local/historique-liste');
  const enCache = await caches.default.match(cle);
  if (enCache) return enCache.json();
  let r = await gh(env, '/git/trees/journal:historique');
  // the token is scoped to Actions: if GitHub refuses it for contents, fall back to an anonymous call (public repo)
  if (r.status === 401 || r.status === 403) r = await fetch(`https://api.github.com/repos/${REPO}/git/trees/journal:historique`,
    { headers: { Accept: 'application/vnd.github+json', 'User-Agent': 'accurate-meteo-horloge' } });
  if (r.status === 404) return [];
  if (!r.ok) throw new Error(`GitHub ${r.status}`);
  const liste = (await r.json()).tree.map(f => f.path.replace(/\.json$/, '')).filter(h => /^\d{4}-\d\d-\d\dT\d\dZ$/.test(h)).sort();
  ctx.waitUntil(caches.default.put(cle, new Response(JSON.stringify(liste), { headers: { 'Cache-Control': 'max-age=300' } })));
  return liste;
}

// "2026-10-09T18:30Z", "2026-10-09T20:30+02:00", "2026-10-09" (end of that day in Grenoble) → hour key in UTC ("2026-10-09T18Z")
function cleHeure(texte) {
  texte = texte.replace(' ', '+');   // an unencoded "+02:00" arrives as a space
  let t;
  if (/^\d{4}-\d\d-\d\d$/.test(texte)) {
    const midi = Date.parse(texte + 'T12:00Z');
    const decalage = Date.parse(new Date(midi).toLocaleString('sv-SE', { timeZone: 'Europe/Paris' }).replace(' ', 'T') + 'Z') - midi;
    t = Date.parse(texte + 'T23:59Z') - decalage;
  } else t = Date.parse(texte);
  return Number.isNaN(t) ? null : new Date(t).toISOString().slice(0, 13) + 'Z';
}

async function historique(url, env, ctx) {
  const exacte = url.pathname.match(/^\/v1\/historique\/(\d{4}-\d\d-\d\dT\d\dZ)$/);
  if (!exacte && url.pathname !== '/v1/historique') return json({ erreur: 'Introuvable', endpoints: ENDPOINTS }, 404);
  const liste = exacte ? null : await heures(env, ctx);
  let heure = exacte && exacte[1];
  if (!exacte) {
    const le = url.searchParams.get('le');
    if (!le) return json({ ...META, heures: liste, endpoints: ENDPOINTS }, 200, { 'Cache-Control': 'public, max-age=300' });
    const cible = cleHeure(le);
    if (!cible) return json({ erreur: `Date illisible : ${le}. Exemple : 2026-10-09T18:30Z` }, 400);
    heure = liste.filter(h => h <= cible).pop();
    if (!heure) return json({ erreur: `Rien d'enregistré avant ${le}.`, premiere_heure: liste[0] || null }, 404);
  }
  // a recorded hour never changes: cache it a day
  const r = await fetch(`${RAW}/${heure}.json`, { cf: { cacheTtl: 86400, cacheEverything: true } });
  if (r.status === 404) return json({ erreur: `Aucune prévision enregistrée pour ${heure}.`, liste: '/v1/historique' }, 404);
  if (!r.ok) return json({ erreur: `Source indisponible (${r.status})` }, 502);
  return json({ ...(await r.json()), ...META, enregistree: heure }, 200, { 'Cache-Control': `public, max-age=${exacte ? 86400 : 300}` });
}

async function api(request, env, ctx) {
  const url = new URL(request.url);
  if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: CORS });
  if (request.method !== 'GET' && request.method !== 'HEAD') return json({ erreur: 'GET seulement' }, 405);
  if (url.pathname === '/' || url.pathname === '/v1') {
    return json({ ...META, endpoints: ENDPOINTS }, 200, { 'Cache-Control': 'public, max-age=3600' });
  }
  if (url.pathname.startsWith('/v1/historique')) {
    try { return await historique(url, env, ctx); }
    catch (e) { return json({ erreur: `Source indisponible (${e.message})` }, 502); }
  }
  if (url.pathname !== '/v1/prevision') return json({ erreur: 'Introuvable', endpoints: ENDPOINTS }, 404);
  const r = await fetch(SOURCE, { cf: { cacheTtl: 60, cacheEverything: true } });
  if (!r.ok) return json({ erreur: `Source indisponible (${r.status})` }, 502);
  const prevision = await r.json();
  return json({ ...prevision, ...META }, 200, { 'Cache-Control': 'public, max-age=60' });
}

export default {
  async scheduled(event, env, ctx) {
    ctx.waitUntil(tick(env).then(m => console.log(m)));
  },
  async fetch(request, env, ctx) {
    return api(request, env, ctx);
  },
};
