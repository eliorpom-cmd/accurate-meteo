# Accurate Meteo

A local weather forecast that learns which weather models are right *where you live*, and combines them.

Most weather apps show one model, or an average. This project scores 27 public weather models against a real weather station over 2.7 years of archived forecasts, then trains a small "mega-model" (gradient boosting) that reads all of them at once and predicts what the station will actually measure. It runs every hour on GitHub Actions and publishes a JSON file any app can read.

Built for Grenoble, France. Every setting that ties it to Grenoble is in one place, so it can be pointed at another city that has a station with open data.

## Results (Grenoble, honest test on Oct 2025 → Oct 2026)

The mega-model was trained on data before October 2025, then scored on the following 12 months it had never seen, against the best single weather model on the same cases.

| Forecast | Measure | Mega-model | Best single model |
|---|---|---|---|
| Next day, hour by hour | sky condition score /100 | **87.9** | 84.8 (ECMWF IFS) |
| Next day, hour by hour | temperature error | **1.05 °C** | 1.45 °C (ICON-EU) |
| Next day, hour by hour | gust error | **1.59 m/s** | 2.07 m/s (ICON-D2) |
| 1 day ahead, morning / afternoon | sky condition score /100 | **90.7** | 87.7 (ICON) |
| 7 days ahead, morning / afternoon | sky condition score /100 | **76.2** | 71.5 (ECMWF IFS) |
| Rain in the next 2 hours, 20-min slots | rain hit rate (CSI) | **55.8 %** | 51.0 % (ICON-D2) |

Full tables: `FIGE.md` (frozen models), `RESULTATS.md` (ranking of every model), `RETRO.md` (our own past forecasts, month by month). Reports are written in French.

**Sky condition** is one of sunny / mixed / overcast / rain, derived from satellite radiation (clear-sky index) and station rainfall, daytime only. Neighbouring categories get partial credit.

## How it works

1. **Ground truth**: Météo-France station GRENOBLE-CEA-RADOME (hourly and 6-minute data), satellite radiation (EUMETSAT via Open-Meteo) for sunshine.
2. **Archived forecasts**: Open-Meteo Previous Runs API (what each model predicted 1 to 7 days before) and Historical Forecast API (first hours of each run, for the 2-hour rain).
3. **Scoring** (`score.py`): every model on three scales, compared only over the period they all cover.
4. **Mega-model** (`blend.py`, `figer.py`): scikit-learn `HistGradientBoosting`, one model per variable and lead time (27 in total), validated by leaving one month out. Frozen models are in `modeles/`.
5. **Live forecast** (`prevoir.py`): fetches the current forecasts of every model in two requests, applies the frozen models, writes `prevision.json`. Runs hourly in `.github/workflows/prevision.yml` and publishes to the `prevision` branch.
6. **Our own track record** (`retro.py`, `retro/`): what the mega-model would have predicted for every case since February 2024, next to what happened. Live forecasts are also logged hourly on the `journal` branch. Both serve to correct the mega-model on its own errors later.

## Run it

Python 3.14 (the frozen models are pickled with it).

```sh
python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python prevoir.py out/prevision.json   # live forecast, ~5 s, no account needed
```

Rebuilding everything from scratch downloads ~3 years of archives (cached in `data/`, about a day of Open-Meteo's free quota):

```sh
.venv/bin/python score.py    # rank the models          → RESULTATS.md
.venv/bin/python figer.py    # train and freeze          → modeles/, FIGE.md
.venv/bin/python retro.py    # our past forecasts        → retro/, RETRO.md
```

## Use it for another city

Edit the top of `score.py`:

- `STATION`, `PRESSURE_STATION`: Météo-France station IDs (any station from the open [Météo-France climatological data](https://meteo.data.gouv.fr)); outside France, `load_obs()` must be adapted to your station's format.
- `LAT`, `LON`, `ELEV`: the station's coordinates.
- `TREND_MODELS`, `HOURLY_MODELS`, `NOWCAST_MODELS`: models that cover your area.

Then run the three rebuild steps above.

## `prevision.json`

```json
{
  "genere_le": "2026-10-09T20:09+02:00",
  "deux_heures": [{"debut": "…", "pluie": false, "pluie_proba": 0.0}],
  "heures": [{"heure": "…", "condition": "pluie", "probas": {"soleil": 0, "mitigé": 0.05, "couvert": 0.02, "pluie": 0.92},
              "pluie_proba": 0.78, "temperature": 11.2, "vent_kmh": 3.1, "rafales_kmh": 9.0, "precision_reduite": false}],
  "jours": [{"date": "2026-10-10", "matin": {"condition": "pluie", "probas": {}, "temperature": 12.0, "rafales_kmh": 14.4}, "aprem": {}}]
}
```

## Public API

The latest forecast, refreshed every 15 minutes, free and without a key:

```
GET https://meteo-api.byelior.com/v1/prevision
```

- JSON, same fields as `prevision.json` below, plus `api_version`, `lieu` (place and coordinates), `attribution` and `usage`.
- CORS open (`Access-Control-Allow-Origin: *`): call it straight from a web page.
- Cached 60 s at the edge: polling more often than once a minute gains nothing.
- Times are local (Europe/Paris) with their offset. `deux_heures` holds 3 hours of 20-minute slots: keep those that start from your own clock, so a forecast computed a few minutes ago still shows the right 2 hours.
- Grenoble only. Non-commercial use (a condition of Open-Meteo's free tier), and please credit the source as given in `attribution`.
- Breaking changes will get a new version path (`/v2/…`).

## Limits

- Forecast archives start in early 2024: 2.7 years of training, no more.
- One grid point, one station. Adding neighbouring grid points is the most promising next gain.
- The 2-hour archive (first hours of each run) is kinder than live conditions; the `journal` branch measures the real thing.
- Hour-by-hour models are trained on next-day forecasts; beyond 48 h, hours are flagged `precision_reduite`.

## Data and licences

- Code: see `LICENSE`.
- Forecast data: [Open-Meteo](https://open-meteo.com), CC BY 4.0. The free API is for non-commercial use.
- Observations: [Météo-France](https://meteo.data.gouv.fr), Licence Ouverte / Etalab 2.0.
- Satellite radiation: EUMETSAT, via Open-Meteo.

## Contributing

See `CONTRIBUTING.md`. Every change goes through a pull request reviewed by the maintainer.
