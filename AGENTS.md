# AGENTS.md

Guide for coding agents working in this repository. Humans: start with `README.md`.

## What this is

GRESIL, a local weather forecast for one place (Grenoble). It does not simulate the atmosphere: it takes the
forecasts of 16 public weather models (via Open-Meteo), and gradient-boosting models (scikit-learn) learned on
~2.7 years how each one is wrong at this place, by comparing archived forecasts with what a Météo-France
station measured. Production runs every 15 minutes and publishes `prevision.json`, served by a public API.

## Data flow

```
Open-Meteo forecasts ─┐                                  ┌─> branch `prevision`: prevision.json + og.png (force-pushed)
satellite sunlight ───┼─> prevoir.py + modeles/*.joblib ─┤
RainViewer radar ─────┤   (GitHub Action, every 15 min)  └─> branch `journal`: one file per UTC hour (never rewritten)
station (optional) ───┘
                       horloge/ (Cloudflare Worker): triggers the Action every 15 min + public API /v1/prevision
```

Training is offline and manual: `score.py` (rank models) → `figer.py` (train, test, freeze to `modeles/`)
→ `retro.py` (replay our own past forecasts). Production never trains.

## Files

| File | Role |
|---|---|
| `ville.json` | The place: coordinates, Météo-France station ids. Another city: `villes/<city>.json` + env `VILLE`. |
| `score.py` | Shared config and helpers (models lists, downloads, sun position, categories), ranks models → `RESULTATS.md`. |
| `modeles.py` | Builds model inputs. Used by both training and production, so columns always line up. |
| `figer.py` | Trains and freezes production models, honest test → `FIGE.md`. |
| `prevoir.py` | Live forecast (production entry point) → `out/prevision.json`, `out/og.png`, `out/journal/`. |
| `retro.py`, `bilan.py` | Past forecasts replayed (`RETRO.md`); live journal scored against the station (`BILAN.md`). |
| `submodel_*.py`, `blend.py`, `recency.py`, `voisins.py` | Experiments, each with its French report (`*.md`). |
| `radar.py`, `vignette.py` | Radar recording for the journal; sharing image (fonts in `polices/`). |
| `trouver_station.py` | Lists the Météo-France stations near a place and what they measure. |
| `horloge/` | Cloudflare Worker (cron + public API). Deployed separately with `wrangler`. |

## Commands

```sh
python -m venv .venv && .venv/bin/pip install -r requirements.txt   # Python 3.14
.venv/bin/python prevoir.py /tmp/out/prevision.json                  # live forecast, ~5 s, the check before any PR
VILLE=villes/lyon.json .venv/bin/python score.py                     # another city (see README)
```

Training scripts read `data/cache/` first; with an empty cache they download ~3 years from Open-Meteo
(about a day of the free quota: 10,000 calls/day, 600/min). Run long jobs in the background.

## Rules that matter

- **Honest tests only.** Every claimed gain is measured on months not seen in training, against the same
  cases without the change. `figer.py` splits at 2025-10-01; `retro.py` / `voisins.py --mois` leave one month out.
  A gain on one split is not a result: confirm month by month before changing production.
- **Frozen models are pickles.** Python 3.14 and the versions in `requirements.txt` are fixed; changing
  scikit-learn means rerunning `figer.py`. Never edit `modeles/*.joblib` without the script and report.
- **Production must not break.** `prevoir.py` feeds a live site and API. Optional sources (radar, station,
  sharing image) are wrapped so their failure never stops the forecast. Check that the output keeps the
  same shape: the API promises a new path (`/v2/`) for breaking changes.
- **The cache key has no coordinates.** Two places must never share a `data/` folder (`score.SORTIE` handles it).
- **Branches:** `main` is protected (pull request + review). `prevision` is force-pushed on every run;
  `journal` keeps the first run of each hour and is never rewritten (it is the live track record).
- **Conventions:** code and comments in English; reports, the site and the JSON field names in French.
  Times: UTC inside, Europe/Paris in `prevision.json`. Hour keys follow Open-Meteo (value = hour ending at the key).
- **Data and secrets:** only open data (Open-Meteo CC BY 4.0, Météo-France Licence Ouverte, EUMETSAT,
  RainViewer). No personal data, no tokens in the repo; secrets live in GitHub/Cloudflare settings
  (`MF_API_KEY` is optional). Open-Meteo's free tier is non-commercial.

## Known traps

- Python 3.14 rejects the certificate of Météo-France's file server: downloads go through `curl`.
- HistGradientBoosting crashes on a column with fewer than 2 distinct values: such columns are dropped
  before each fit (`keep`, saved in the `.joblib`).
- Compare weather models only on their common period (MeteoSwiss starts in July 2025), or a wrong winner appears.
- Night: the sky category is only defined with the sun above 10° (clear-sky index); no rain at night is not "sun".
- GitHub delays scheduled runs under load: the Cloudflare Worker is the real clock, the cron is a fallback.
