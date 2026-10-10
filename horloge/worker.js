// Two jobs on Cloudflare:
// 1. Reliable clock: GitHub delays or drops scheduled workflows when busy, Cloudflare cron triggers fire on time.
//    Every 15 minutes, start the forecast workflow unless a run is already queued or running.
//    Secret: GITHUB_TOKEN (fine-grained, this repository only, Actions: read and write).
// 2. Public API (https://meteo-api.byelior.com/v1/prevision): the latest prevision.json, open to everyone, no key,
//    cached 60 s at Cloudflare's edge so traffic never reaches GitHub more than once a minute per location.
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
const CORS = { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'GET, OPTIONS' };
const META = {
  api_version: 1,
  doc: `https://github.com/${REPO}#public-api`,
  lieu: { nom: 'Grenoble', latitude: 45.2115, longitude: 5.6828, altitude_m: 213 },
  attribution: 'Accurate Meteo (MIT). Données : Open-Meteo (CC BY 4.0), Météo-France (Licence Ouverte 2.0), EUMETSAT.',
  usage: 'Libre et sans clé, usage non commercial (condition de l\'offre gratuite Open-Meteo). Citez la source.',
};

function json(body, status = 200, extra = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json; charset=utf-8', ...CORS, ...extra },
  });
}

async function api(request) {
  const url = new URL(request.url);
  if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: CORS });
  if (request.method !== 'GET' && request.method !== 'HEAD') return json({ erreur: 'GET seulement' }, 405);
  if (url.pathname === '/' || url.pathname === '/v1') {
    return json({ ...META, endpoints: { prevision: '/v1/prevision' } }, 200, { 'Cache-Control': 'public, max-age=3600' });
  }
  if (url.pathname !== '/v1/prevision') return json({ erreur: 'Introuvable', endpoints: { prevision: '/v1/prevision' } }, 404);
  const r = await fetch(SOURCE, { cf: { cacheTtl: 60, cacheEverything: true } });
  if (!r.ok) return json({ erreur: `Source indisponible (${r.status})` }, 502);
  const prevision = await r.json();
  return json({ ...prevision, ...META }, 200, { 'Cache-Control': 'public, max-age=60' });
}

export default {
  async scheduled(event, env, ctx) {
    ctx.waitUntil(tick(env).then(m => console.log(m)));
  },
  async fetch(request) {
    return api(request);
  },
};
