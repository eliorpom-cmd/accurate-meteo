# GRESIL

A local weather forecast model for Grenoble that learns which weather models are right *where you live*, and combines them.

GRESIL (named after *grésil*, graupel in French, and **Gre**noble) is the model; this repository, Accurate Meteo, is its code.

Most weather apps show one model, or an average. This project scores 27 public weather models against a real weather station over 2.7 years of archived forecasts, then trains GRESIL, a small "mega-model" (gradient boosting), that reads all of them at once and predicts what the station will actually measure. It runs every 15 minutes on GitHub Actions and publishes a JSON file any app can read (see Public API).

Built for Grenoble, France. Every setting that ties it to Grenoble is in one place, so it can be pointed at another city that has a station with open data.

## Results (Grenoble, honest test on Oct 2025 → Oct 2026)

The mega-model was trained on data before October 2025, then scored on the following 12 months it had never seen, against the best single weather model on the same cases.

| Forecast | Measure | GRESIL | Best single model |
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
5. **Live forecast** (`prevoir.py`): fetches the current forecasts of every model in two requests, applies the frozen models, writes `prevision.json`. Runs every 15 minutes in `.github/workflows/prevision.yml` and publishes to the `prevision` branch.
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

Anyone in France can train the same model for their own place. The location lives in `ville.json` (Grenoble); another city gets its own file in `villes/` and its own folder for data, frozen models and reports, so cities never mix.

1. Find a station: the nearest Météo-France automatic station that measures temperature, humidity, wind, gusts and hourly rain.

   ```sh
   python3 trouver_station.py 69 45.7578 4.8320            # département(s), latitude, longitude
   python3 trouver_station.py 69,01 45.7578 4.8320 --minutes  # also check 6-minute rain (2-hour model)
   ```

   Pick one marked ✓ everywhere, within ~10 km and at a similar altitude. Pressure is often measured elsewhere: use the nearest station with ✓ under *pression* as `station_pression`.

2. Describe the city: copy `ville.json` to `villes/<city>.json` and fill it in (see `villes/lyon.json`).

3. Rebuild with `VILLE` set (about a day of Open-Meteo's free quota; results go to `villes/<city>/`):

   ```sh
   export VILLE=villes/lyon.json
   .venv/bin/python score.py && .venv/bin/python figer.py && .venv/bin/python retro.py
   .venv/bin/python prevoir.py      # → villes/lyon/out/prevision.json
   ```

The model list (`TREND_MODELS`, `HOURLY_MODELS`, `NOWCAST_MODELS` in `score.py`) covers France and its neighbours; outside France, `load_obs()` must also be adapted to your station's data.

## `prevision.json`

```json
{
  "genere_le": "2026-10-09T20:09+02:00",
  "deux_heures": [{"debut": "…", "pluie": false, "pluie_proba": 0.0}],
  "passe": [{"heure": "…", "condition": "couvert", "temperature": 12.0, "pluie_mm": 0.0, "vent_kmh": 7.2, "rafales_kmh": 16.6,
             "ratio": 0.22, "mesure": {"ciel": true, "station": true}}],
  "heures": [{"heure": "…", "condition": "pluie", "probas": {"soleil": 0, "mitigé": 0.05, "couvert": 0.02, "pluie": 0.92},
              "pluie_proba": 0.78, "temperature": 11.2, "vent_kmh": 3.1, "rafales_kmh": 9.0, "precision_reduite": false}],
  "jours": [{"date": "2026-10-10", "matin": {"condition": "pluie", "probas": {}, "temperature": 12.0, "rafales_kmh": 14.4}, "aprem": {}}]
}
```

Night hours (sun below the horizon): `condition` is `"nuit"` (or `"pluie"`) and `probas` is null, because GRESIL learned the sky from measured sunlight, which does not exist at night (tested alternatives: [CIEL-NUIT.md](CIEL-NUIT.md)). They carry instead the raw cloud cover of one weather model, not corrected by GRESIL: `"nebulosite": {"pct": 74, "mot": "couvert", "modele": "icon_eu", "corrigee": false}` (`mot`: `dégagé` under 30 %, `nuageux` up to 70 %, `couvert` above; ICON-EU, the best raw hourly model the day before, then ECMWF IFS beyond its horizon). Temperature, rain and wind stay GRESIL's at night.

`passe` = today's hours already over (from 6 am): the sky measured by satellite and, when the `MF_API_KEY` secret holds a free key from [Météo-France's API portal](https://portail-api.meteofrance.fr) (*Données d'observation*), the station's temperature, rain and wind; otherwise the forecast values. A half-day already over comes back in `jours` with `"passe": true`.

## Public API

The latest forecast, refreshed every 15 minutes, free and without a key:

```
GET https://meteo-api.byelior.com/v1/prevision
```

- JSON, same fields as `prevision.json` below, plus `modele` ("GRESIL"), `api_version`, `lieu` (place and coordinates), `attribution` and `usage`.
- CORS open (`Access-Control-Allow-Origin: *`): call it straight from a web page.
- Cached 60 s at the edge: polling more often than once a minute gains nothing.
- Times are local (Europe/Paris) with their offset. Each hour in `heures` and `passe` is labelled by its **start**: `"19:00"` = 19:00 to 20:00 (sky, rain probability, gusts over that hour; temperature and wind at 19:00). Before 10 October 2026, 14:30 Paris time, hours were labelled by their end; `/v1/historique` entries from before that keep the old labels. `deux_heures` holds 3 hours of 20-minute slots: keep those that start from your own clock, so a forecast computed a few minutes ago still shows the right 2 hours.
- Grenoble only. Non-commercial use (a condition of Open-Meteo's free tier), and please credit the source as given in `attribution`.
- Breaking changes will get a new version path (`/v2/…`).

### Past forecasts

What the API served at a given hour, kept since 10 October 2026 (the first run of each hour, never rewritten):

```
GET https://meteo-api.byelior.com/v1/historique                       list of recorded hours ("2026-10-10T12Z", UTC)
GET https://meteo-api.byelior.com/v1/historique/2026-10-10T12Z        the forecast recorded that hour
GET https://meteo-api.byelior.com/v1/historique?le=2026-10-09T18:30Z  the last one recorded at or before that moment
```

- Same fields as `/v1/prevision`, plus `enregistree` (the hour key). `le` takes any ISO date or time, with its offset (`2026-10-09T20:30+02:00`), or a plain date (the day's last forecast).
- Yesterday's forecast for today: `?le=` with yesterday's date and time.
- Hours missing from the list were not recorded (GitHub skipped the run).

Example, to paste into any web page (no build step, no key):

```html
<div id="meteo"></div>
<script type="module">
  const p = await (await fetch('https://meteo-api.byelior.com/v1/prevision')).json();
  const now = Date.now();
  // current hour: the one not over yet (each hour is labelled by its start)
  const h = p.heures.find(x => Date.parse(x.heure) + 3600000 > now);
  // rain in the next 2 hours: the 20-minute slots not over yet
  const slots = p.deux_heures.filter(s => Date.parse(s.debut) + 20 * 60000 > now).slice(0, 6);
  const rain = slots.find(s => s.pluie);
  document.getElementById('meteo').innerHTML = `
    <strong>Grenoble : ${Math.round(h.temperature)}°, ${h.condition}</strong><br>
    ${rain ? `Pluie à partir de ${rain.debut.slice(11, 16)}` : 'Pas de pluie dans les 2 heures'}<br>
    <small>${p.attribution}</small>`;
</script>
```

`condition` is one of `soleil`, `mitigé` (sun and clouds), `couvert` (overcast), `pluie` (rain) or `nuit` (night, sky not forecast).

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
