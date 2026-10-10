// Reliable clock for the forecast: GitHub delays or drops scheduled workflows when busy, Cloudflare cron
// triggers fire on time. Every 15 minutes, start the forecast workflow unless a run is already queued or running.
// Secret: GITHUB_TOKEN (fine-grained, this repository only, Actions: read and write).
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

export default {
  async scheduled(event, env, ctx) {
    ctx.waitUntil(tick(env).then(m => console.log(m)));
  },
};
