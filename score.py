"""Score weather models near Grenoble, all parameters, weighted towards the general condition.

Ground truth:
  - GRENOBLE-CEA-RADOME (38185012): temperature, humidity, wind, gusts, direction, rain (hourly + 6-minute rain)
  - GRENOBLE-LVD (38538002): sea-level pressure
  - Satellite (Open-Meteo satellite API, EUMETSAT): sunlight reaching the ground, hourly → sun / mixed / overcast

General condition of an hour or a half-day = rain, else sun / mixed / overcast from the clear-sky index
(measured or forecast sunlight divided by the theoretical clear-sky sunlight). Daytime only (sun > 10°).

Three scales:
  1. 7-day trend: morning (6-12h) and afternoon (12-18h), forecasts made 1 to 7 days ahead
  2. Next day, hour by hour: forecast made the day before
  3. Next 2 hours: rain in 20-minute slots + hourly condition and parameters from the first hours of each run

The place (coordinates, stations) comes from ville.json; for another city see README « Your own city ».

Usage: python3 score.py   (downloads into data/, caches API answers in data/cache/, writes RESULTATS.md)
"""
import csv, gzip, hashlib, json, math, os, subprocess, time, urllib.error, urllib.request
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.abspath(__file__))
# The place comes from ville.json (Grenoble); another city: VILLE=villes/<name>.json python3 score.py
# Another city keeps its data, frozen models and reports in villes/<name>/: the API cache key does not
# contain the coordinates, so two places must never share a data/ folder.
VILLE_PATH = os.path.abspath(os.environ.get('VILLE', os.path.join(ROOT, 'ville.json')))
VILLE = json.load(open(VILLE_PATH))
SORTIE = ROOT if VILLE_PATH == os.path.join(ROOT, 'ville.json') else \
    os.path.join(ROOT, 'villes', os.path.splitext(os.path.basename(VILLE_PATH))[0])
DATA = os.path.join(SORTIE, 'data')
CACHE = os.path.join(DATA, 'cache')
MODELES = os.path.join(SORTIE, 'modeles')
NOM, STATION_NOM = VILLE['nom'], VILLE['station_nom']
SLUG = VILLE.get('slug') or os.path.basename(SORTIE)  # URL name: meteo.byelior.com/<slug>, <slug>/prevision.json
STATION = VILLE['station']
PRESSURE_STATION = VILLE.get('station_pression') or STATION  # sea-level pressure, often measured elsewhere
DEPT = STATION[:2]                                             # Météo-France files are split by département
LAT, LON, ELEV = VILLE['latitude'], VILLE['longitude'], VILLE['altitude_m']
# The API is fetched in chunks so a longer period reuses what is already cached
# Period downloaded, in chunks (forecast archives of the Previous Runs API start in early 2024), and first day of
# the honest test. A city can override them with "periode": {"tranches": [[start, end], …], "test_depuis": date}.
_P = VILLE.get('periode', {})
CHUNKS = [tuple(t) for t in _P.get('tranches', [('2024-02-01', '2024-12-31'), ('2025-01-01', '2025-09-30'),
                                                ('2025-10-01', '2026-10-08')])]
START, END = CHUNKS[0][0], CHUNKS[-1][1]
TEST_FROM = date.fromisoformat(_P.get('test_depuis', '2025-10-01'))
PARIS = ZoneInfo(VILLE.get('fuseau', 'Europe/Paris'))  # local time (name kept from the first version)
MF = 'https://meteofrance.s3.sbg.io.cloud.ovh.net/data/synchro_ftp/BASE'
PREVIOUS = 'https://previous-runs-api.open-meteo.com/v1/forecast'
HISTORICAL = 'https://historical-forecast-api.open-meteo.com/v1/forecast'
SATELLITE = 'https://satellite-api.open-meteo.com/v1/archive'

TREND_MODELS = ['ecmwf_ifs025', 'ecmwf_aifs025_single', 'icon_seamless', 'icon_eu', 'meteoswiss_icon_seamless',
                'gfs_seamless', 'gem_seamless', 'ukmo_seamless', 'meteofrance_seamless']
HOURLY_MODELS = ['meteofrance_arome_france', 'meteofrance_seamless', 'meteofrance_arpege_europe', 'icon_d2',
                 'icon_eu', 'icon_seamless', 'meteoswiss_icon_ch2', 'meteoswiss_icon_seamless', 'ecmwf_ifs025',
                 'ecmwf_aifs025_single', 'ukmo_seamless', 'gfs_seamless', 'gem_seamless',
                 'knmi_harmonie_arome_europe']
NOWCAST_MODELS = ['meteofrance_arome_france', 'meteofrance_seamless', 'icon_d2', 'meteoswiss_icon_ch1',
                  'meteoswiss_icon_ch2', 'knmi_harmonie_arome_europe', 'dmi_harmonie_arome_europe', 'ecmwf_ifs025']

VARS = ['temperature_2m', 'relative_humidity_2m', 'wind_speed_10m', 'wind_gusts_10m', 'wind_direction_10m',
        'pressure_msl', 'shortwave_radiation', 'cloud_cover', 'precipitation']

# Weights of the final score (out of 100). The general condition dominates.
WEIGHTS = {'condition': 60, 'pluie_mm': 10, 'vent': 5, 'rafales': 5, 'direction': 5,
           'temperature': 7, 'humidite': 4, 'pression': 4}
# Error at which a parameter scores 0/100 (score = 100 × (1 − error / tolerance))
TOL_HOUR = {'pluie_mm': 2, 'vent': 3, 'rafales': 6, 'direction': 90, 'temperature': 3, 'humidite': 20, 'pression': 4}
TOL_BLOCK = {**TOL_HOUR, 'pluie_mm': 5}

RAIN_HOUR, RAIN_BLOCK, RAIN_SLOT = 0.2, 0.5, 0.05   # mm
SUN, MIXED = 0.75, 0.4                              # clear-sky index thresholds
CATS = ['soleil', 'mitigé', 'couvert', 'pluie']
# Partial credit when the forecast condition is close to the observed one
CREDIT = {(0, 1): .5, (1, 0): .5, (1, 2): .5, (2, 1): .5, (2, 3): .3, (3, 2): .3}


# ---------- downloads ----------

def download(name, url):
    path = os.path.join(DATA, name)
    if not os.path.exists(path) or time.time() - os.path.getmtime(path) > 6 * 3600:
        # curl: Python 3.14 rejects the certificate of Météo-France's storage server
        subprocess.run(['curl', '-sfL', '-o', path, url], check=True)
    return path


def api(base, params):
    """Fetch the whole period chunk by chunk and merge the time series."""
    merged = None
    for s, e in CHUNKS:
        d = api_chunk(base, params, s, e)
        if d is None:
            return None
        if not d:
            continue  # model not available over this chunk
        if merged is None:
            merged = d
            continue
        for block in ('hourly', 'minutely_15'):
            if block in d:
                for k, v in d[block].items():
                    merged[block][k] = merged[block][k] + v
    return merged


def api_chunk(base, params, start, end):
    os.makedirs(CACHE, exist_ok=True)
    key = base.split('//')[1].split('.')[0] + json.dumps(params, sort_keys=True) + start + end
    path = os.path.join(CACHE, params.get('models', 'obs') + '_' + hashlib.md5(key.encode()).hexdigest()[:10] + '.json')
    if os.path.exists(path):
        return json.load(open(path))
    q = dict(latitude=LAT, longitude=LON, elevation=ELEV, timezone='GMT', wind_speed_unit='ms',
             start_date=start, end_date=end, **params)
    url = base + '?' + '&'.join(f'{k}={v}' for k, v in q.items())
    for attempt in range(6):
        try:
            d = json.load(urllib.request.urlopen(url, timeout=300))
            break
        except urllib.error.HTTPError as e:
            if e.code == 400:  # "no data for this model / period": remember it as empty
                d = {}
                break
            if attempt == 5:
                print('   ', params.get('models'), start, 'failed:', e)
                return None
            time.sleep(90)
        except Exception as e:
            if attempt == 5:
                print('   ', params.get('models'), start, 'failed:', e)
                return None
            time.sleep(90)
    json.dump(d, open(path, 'w'))
    # Open-Meteo free tier: 600 weighted calls per minute, 5000 per hour, 10000 per day
    # (weight ≈ variables/10 × days/14); this pause keeps under the per-minute cap, 429s are retried
    nvars = len(next(v for k, v in params.items() if k in ('hourly', 'minutely_15')).split(','))
    days = (datetime.fromisoformat(end) - datetime.fromisoformat(start)).days + 1
    time.sleep(max(1, nvars / 10 * days / 14 * 0.11))
    return d


def utc(s):
    return datetime.strptime(s, '%Y-%m-%dT%H:%M').replace(tzinfo=timezone.utc)


# ---------- sun ----------

def sun_elevation(t):
    """Solar elevation in degrees (NOAA approximation)."""
    doy = t.timetuple().tm_yday
    g = 2 * math.pi / 365 * (doy - 1 + (t.hour + t.minute / 60 - 12) / 24)
    decl = (0.006918 - 0.399912 * math.cos(g) + 0.070257 * math.sin(g) - 0.006758 * math.cos(2 * g)
            + 0.000907 * math.sin(2 * g) - 0.002697 * math.cos(3 * g) + 0.00148 * math.sin(3 * g))
    eqt = 229.18 * (0.000075 + 0.001868 * math.cos(g) - 0.032077 * math.sin(g)
                    - 0.014615 * math.cos(2 * g) - 0.040849 * math.sin(2 * g))
    tst = t.hour * 60 + t.minute + eqt + 4 * LON
    ha = math.radians(tst / 4 - 180)
    lat = math.radians(LAT)
    cz = math.sin(lat) * math.sin(decl) + math.cos(lat) * math.cos(decl) * math.cos(ha)
    return math.degrees(math.asin(max(-1, min(1, cz))))


def clear_sky(t):
    """Mean clear-sky sunlight (W/m², Haurwitz) over the hour ending at t, and sun elevation at mid-hour."""
    vals = []
    for k in range(4):
        e = sun_elevation(t - timedelta(minutes=7.5 + 15 * k))
        cz = math.sin(math.radians(e))
        vals.append(1098 * cz * math.exp(-0.057 / cz) if cz > 0.01 else 0)
    return sum(vals) / 4, sun_elevation(t - timedelta(minutes=30))


SKY = {}


def sky_info(t):
    if t not in SKY:
        SKY[t] = clear_sky(t)
    return SKY[t]


def category(rain_mm, sun_ratio, rain_thr):
    # No sunlight value = night (or no sky data): the condition is not scored, rain included
    if sun_ratio is None or rain_mm is None:
        return None
    if rain_mm >= rain_thr:
        return 3
    return 0 if sun_ratio >= SUN else 1 if sun_ratio >= MIXED else 2


def cloud_ratio(cc):
    """Fallback when a model gives no sunlight: cloud cover → equivalent clear-sky index."""
    return None if cc is None else 1 - 0.75 * (cc / 100) ** 3.4  # Kasten-Czeplak


# ---------- observations ----------

def load_obs():
    paths = [download(f'H_{DEPT}_previous.csv.gz', f'{MF}/HOR/H_{DEPT}_previous-2020-2024.csv.gz'),
             download(f'H_{DEPT}_latest.csv.gz', f'{MF}/HOR/H_{DEPT}_latest-2025-2026.csv.gz')]
    obs, pres = {}, {}
    for path in paths:
        with gzip.open(path, 'rt') as f:
            r = csv.reader(f, delimiter=';')
            i = {k.strip(): n for n, k in enumerate(next(r))}
            for row in r:
                if row[0] not in (STATION, PRESSURE_STATION) or row[5] < START.replace('-', '') + '00':
                    continue
                t = datetime.strptime(row[5], '%Y%m%d%H').replace(tzinfo=timezone.utc)
                val = lambda k: float(row[i[k]]) if row[i[k]].strip() else None
                if row[0] == PRESSURE_STATION:
                    pres[t] = val('PMER')
                else:
                    obs[t] = {'temperature': val('T'), 'humidite': val('U'), 'vent': val('FF'), 'rafales': val('FXI'),
                              'direction': val('DD'), 'pluie_mm': val('RR1')}
    for t, p in pres.items():
        if t in obs:
            obs[t]['pression'] = p
    sat = api(SATELLITE, {'hourly': 'shortwave_radiation'})
    for ts, g in zip(sat['hourly']['time'], sat['hourly']['shortwave_radiation']):
        t = utc(ts)
        if t in obs:
            cs, elev = sky_info(t)
            obs[t]['ratio'] = g / cs if g is not None and elev > 10 and cs > 50 else None
    for o in obs.values():
        o['cat'] = category(o['pluie_mm'], o.get('ratio'), RAIN_HOUR)
    return obs


def load_6min_rain():
    rain = {}
    for name, period in ((f'MN_{DEPT}_previous.csv.gz', 'previous-2020-2024'), (f'MN_{DEPT}_latest.csv.gz', 'latest-2025-2026')):
        with gzip.open(download(name, f'{MF}/MIN/MN_{DEPT}_{period}.csv.gz'), 'rt') as f:
            r = csv.reader(f, delimiter=';')
            next(r)
            for row in r:
                if row[0] == STATION and row[6].strip() and row[5] >= START.replace('-', ''):
                    rain[datetime.strptime(row[5], '%Y%m%d%H%M').replace(tzinfo=timezone.utc)] = float(row[6])
    return rain


def to_slots(amounts, minutes):
    """Spread each interval amount (ending at its timestamp) over its minutes, sum into 20-min slots."""
    slots = {}
    for end, mm in amounts.items():
        if mm is None:
            continue
        for k in range(minutes):
            t = end - timedelta(minutes=k + 1)
            s = t.replace(minute=t.minute // 20 * 20, second=0)
            slots[s] = slots.get(s, 0) + mm / minutes
    return slots


# ---------- forecasts → same shape as observations ----------

def forecast_hours(H, suffix=''):
    out = {}
    g = lambda v, n: H.get(v + suffix, [None] * (n + 1))[n]
    for n, ts in enumerate(H['time']):
        t = utc(ts)
        cs, elev = sky_info(t)
        sw, cc = g('shortwave_radiation', n), g('cloud_cover', n)
        ratio = None
        if elev > 10 and cs > 50:
            ratio = sw / cs if sw is not None else cloud_ratio(cc)
        f = {'temperature': g('temperature_2m', n), 'humidite': g('relative_humidity_2m', n),
             'vent': g('wind_speed_10m', n), 'rafales': g('wind_gusts_10m', n),
             'direction': g('wind_direction_10m', n), 'pression': g('pressure_msl', n),
             'pluie_mm': g('precipitation', n), 'ratio': ratio}
        f['cat'] = category(f['pluie_mm'], ratio, RAIN_HOUR) if f['pluie_mm'] is not None else None
        out[t] = f
    return out


def to_blocks(hours):
    """Morning (hours ending 7-12h local) and afternoon (13-18h) blocks."""
    raw = {}
    for t, h in hours.items():
        loc = t.astimezone(PARIS)
        part = 'matin' if 7 <= loc.hour <= 12 else 'aprem' if 13 <= loc.hour <= 18 else None
        if part:
            raw.setdefault((loc.date(), part), []).append(h)
    blocks = {}
    for k, hs in raw.items():
        if len(hs) != 6:
            continue
        mean = lambda v: (sum(h[v] for h in hs) / 6) if all(h.get(v) is not None for h in hs) else None
        rain = sum(h['pluie_mm'] for h in hs) if all(h['pluie_mm'] is not None for h in hs) else None
        ratios = [h['ratio'] for h in hs if h.get('ratio') is not None]
        ratio = sum(ratios) / len(ratios) if len(ratios) >= 2 else None
        gusts = [h['rafales'] for h in hs]
        blocks[k] = {'temperature': mean('temperature'), 'humidite': mean('humidite'), 'vent': mean('vent'),
                     'rafales': max(gusts) if None not in gusts else None, 'direction': hs[3]['direction'],
                     'pression': mean('pression'), 'pluie_mm': rain, 'ratio': ratio,
                     'cat': category(rain, ratio, RAIN_BLOCK) if rain is not None else None}
    return blocks


# ---------- scoring ----------

def compare(fc, obs, tol):
    """Return per-component scores (0-100) and the confusion counts of the condition."""
    err = {k: [] for k in tol}
    cond, conf = [], {}
    for t, o in obs.items():
        f = fc.get(t)
        if not f:
            continue
        for k in tol:
            fv, ov = f.get(k), o.get(k)
            if fv is None or ov is None:
                continue
            if k == 'direction':
                if (o.get('vent') or 0) < 2:
                    continue  # direction is meaningless in calm air
                e = abs(fv - ov) % 360
                err[k].append(min(e, 360 - e))
            elif k == 'pluie_mm':
                if fv >= 0.1 or ov >= 0.1:  # amount error only where it rained (or was forecast to)
                    err[k].append(abs(fv - ov))
            else:
                err[k].append(abs(fv - ov))
        if f.get('cat') is not None and o.get('cat') is not None:
            a, b = f['cat'], o['cat']
            cond.append(1 if a == b else CREDIT.get((a, b), 0))
            conf[(a, b)] = conf.get((a, b), 0) + 1
    s = {k: max(0, 100 * (1 - sum(v) / len(v) / tol[k])) for k, v in err.items() if len(v) > 50}
    if len(cond) > 100:
        s['condition'] = 100 * sum(cond) / len(cond)
    mae = {k: sum(v) / len(v) for k, v in err.items() if len(v) > 50}
    return s, mae, conf, len(cond)


def total(s):
    """Weighted score; missing components are left out and the weights re-normalised."""
    if 'condition' not in s:
        return None
    w = {k: WEIGHTS[k] for k in s if k in WEIGHTS}
    return sum(s[k] * w[k] for k in w) / sum(w.values())


def exact_rates(conf):
    """% of exact conditions, and % of observed sun / rain correctly forecast."""
    n = sum(conf.values())
    ex = sum(v for (a, b), v in conf.items() if a == b)
    obs_c = lambda c: sum(v for (a, b), v in conf.items() if b == c)
    hit = lambda c: conf.get((c, c), 0) / obs_c(c) * 100 if obs_c(c) else 0
    return 100 * ex / n, hit(0), hit(2), hit(3)


def f1(x, unit=''):
    return f'{x:.1f}{unit}' if x is not None else '-'


def table_rows(results, out, tol):
    out.append('| Rang | Modèle | **Score /100** | Condition (pondérée) | Conditions exactes | Soleil vu | Couvert vu | Pluie vue | '
               'Pluie mm | Vent | Rafales | Direction | Temp. | Humidité | Pression |')
    out.append('|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|')
    ranked = sorted([r for r in results if r[0] is not None], key=lambda r: -r[0])
    for i, (tot, m, s, mae, conf, n) in enumerate(ranked, 1):
        ex, sun, ovc, rain = exact_rates(conf)
        cell = lambda k, u: f'{mae[k]:.1f}{u}' if k in mae else '-'
        out.append(f'| {i} | {m} | **{tot:.1f}** | {s["condition"]:.1f} | {ex:.0f}% | {sun:.0f}% | {ovc:.0f}% | {rain:.0f}% | '
                   f'{cell("pluie_mm", " mm")} | {cell("vent", " m/s")} | {cell("rafales", " m/s")} | '
                   f'{cell("direction", "°")} | {cell("temperature", "°C")} | {cell("humidite", " %")} | {cell("pression", " hPa")} |')
    out.append('')
    return ranked


def common_period(fcs, obs):
    """Keep only the hours / half-days where every compared model has data, so all are scored on the same cases.
    Models with (almost) no data over the period are dropped first."""
    has = lambda f, k: k in f and f[k].get('pluie_mm') is not None
    fcs = {m: f for m, f in fcs.items() if sum(has(f, k) for k in obs) > 0.2 * len(obs)}
    keys = [k for k in obs if all(has(f, k) for f in fcs.values())]
    return fcs, {k: obs[k] for k in keys}


def period_label(keys):
    days = [k[0] if isinstance(k, tuple) else k.date() for k in keys]
    return f'période commune {min(days)} → {max(days)}' if days else 'aucune période commune'


def scale_trend(obs, out):
    out.append('## 1. Tendance à 7 jours, matin et après-midi\n')
    out.append('Score /100 de chaque modèle selon le nombre de jours d\'avance (60 % = condition générale du créneau). '
               'À chaque échéance, tous les modèles sont notés sur les mêmes créneaux.\n')
    oblocks = to_blocks(obs)
    leads = range(1, 8)
    hv = ','.join(f'{v}_previous_day{d}' for d in leads for v in VARS)
    raw = {}
    for m in TREND_MODELS:
        print('  trend', m)
        d = api(PREVIOUS, {'hourly': hv, 'models': m})
        if d:
            raw[m] = d
    res, periods = {}, {}
    for lead in leads:
        fcs = {m: to_blocks(forecast_hours(d['hourly'], f'_previous_day{lead}')) for m, d in raw.items()}
        fcs, ob = common_period(fcs, oblocks)
        periods[lead] = period_label(ob)
        for m, fb in fcs.items():
            s, mae, conf, n = compare(fb, ob, TOL_BLOCK)
            if n > 100:
                res[(m, lead)] = (total(s), s, mae, conf, n)
    out.append('| Modèle | ' + ' | '.join(f'J+{d}' for d in leads) + ' |')
    out.append('|---|' + '---|' * len(leads))
    for m in TREND_MODELS:
        cells = []
        for d in leads:
            r = res.get((m, d))
            best = r and r[0] == max(v[0] for (mm, dd), v in res.items() if dd == d)
            cells.append('-' if not r else f'**{r[0]:.1f}**' if best else f'{r[0]:.1f}')
        out.append(f'| {m} | ' + ' | '.join(cells) + ' |')
    out.append('')
    for d in leads:
        out.append(f'- J+{d} : {periods[d]}')
    out.append('\nDétail à J+1, J+3 et J+5 :\n')
    for d in (1, 3, 5):
        out.append(f'### J+{d}\n')
        table_rows([(v[0], m, v[1], v[2], v[3], v[4]) for (m, dd), v in res.items() if dd == d], out, TOL_BLOCK)
    return res


def scale_hourly(obs, out):
    out.append('## 2. La veille pour le lendemain, heure par heure\n')
    hv = ','.join(f'{v}_previous_day1' for v in VARS)
    fcs = {}
    for m in HOURLY_MODELS:
        print('  hourly', m)
        d = api(PREVIOUS, {'hourly': hv, 'models': m})
        if d:
            fcs[m] = forecast_hours(d['hourly'], '_previous_day1')
    fcs, ob = common_period(fcs, obs)
    out.append(f'Tous les modèles notés sur les mêmes heures ({period_label(ob)}).\n')
    results = []
    for m, fc in fcs.items():
        s, mae, conf, n = compare(fc, ob, TOL_HOUR)
        results.append((total(s), m, s, mae, conf, n))
    return table_rows(results, out, TOL_HOUR)


def scale_nowcast(obs, rain6, out):
    out.append('## 3. Les 2 prochaines heures\n')
    out.append('Condition = 50 % pluie par tranches de 20 min (indice de réussite) + 50 % ciel heure par heure '
               '(soleil / mitigé / couvert / pluie). Autres paramètres : premières heures de chaque run.\n')
    oslots = to_slots(rain6, 6)
    fcs, slots = {}, {}
    for m in NOWCAST_MODELS:
        print('  nowcast', m)
        dh = api(HISTORICAL, {'hourly': ','.join(VARS), 'models': m})
        dm = api(HISTORICAL, {'minutely_15': 'precipitation', 'models': m})
        if not dh or not dm:
            continue
        fcs[m] = forecast_hours(dh['hourly'])
        M = dm['minutely_15']
        slots[m] = to_slots({utc(t): v for t, v in zip(M['time'], M['precipitation']) if v is not None}, 15)
    fcs, ob = common_period(fcs, obs)
    out.append(f'Tous les modèles notés sur les mêmes heures ({period_label(ob)}).\n')
    common_slots = [k for k in oslots if k.replace(minute=0) + timedelta(hours=1) in ob
                    and all(k in slots[m] for m in fcs)]
    results = []
    for m, fc in fcs.items():
        s, mae, conf, n = compare(fc, ob, TOL_HOUR)
        hit = miss = fa = 0
        for k in common_slots:
            fy, oy = slots[m][k] >= RAIN_SLOT, oslots[k] >= RAIN_SLOT
            hit += fy and oy; miss += oy and not fy; fa += fy and not oy
        if 'condition' not in s or hit + miss + fa == 0:
            print('    no condition data')
            continue
        csi = 100 * hit / (hit + miss + fa)
        s['condition'] = (s['condition'] + csi) / 2
        s['_csi'] = csi
        results.append((total(s), m, s, mae, conf, n))
    ranked = table_rows(results, out, TOL_HOUR)
    out.append('Pluie par tranches de 20 min (indice de réussite = tranches pluvieuses prévues et vues, '
               'sur toutes les tranches où il a plu ou été prévu de pleuvoir) :\n')
    for tot, m, s, *_ in ranked:
        out.append(f'- {m} : {s["_csi"]:.0f} %')
    out.append('')
    return ranked


if __name__ == '__main__':
    os.makedirs(DATA, exist_ok=True)
    print('observations…')
    obs = load_obs()
    rain6 = load_6min_rain()
    oc = [o['cat'] for o in obs.values() if o['cat'] is not None]
    out = [f'# Fiabilité des modèles météo à {NOM}\n',
           f'Période {START} → {END}. Vérité terrain : station {STATION_NOM} (température, humidité, vent, pluie), '
           f'station {PRESSURE_STATION} (pression), satellite EUMETSAT (soleil). Heures de jour seulement pour la condition.\n',
           'Score /100 = ' + ', '.join(f'{k} {v} %' for k, v in WEIGHTS.items()) + '. '
           'Condition : bonne catégorie = 1 point, voisine (soleil↔mitigé, mitigé↔couvert) = 0,5, couvert↔pluie = 0,3. '
           'Les autres paramètres : 100 × (1 − erreur moyenne / tolérance), tolérances heure : '
           + ', '.join(f'{k} {v}' for k, v in TOL_HOUR.items()) + '.\n',
           'Répartition observée des heures de jour : '
           + ', '.join(f'{c} {100 * oc.count(i) / len(oc):.0f} %' for i, c in enumerate(CATS)) + '.\n',
           'Colonnes « vu » : part des heures (ou créneaux) observés dans cette condition que le modèle avait prévus exactement. '
           'Colonnes mm, m/s, °… : erreur moyenne.\n']
    scale_trend(obs, out)
    scale_hourly(obs, out)
    scale_nowcast(obs, rain6, out)
    open(os.path.join(SORTIE, 'RESULTATS.md'), 'w').write('\n'.join(out))
    print('\n'.join(out))
