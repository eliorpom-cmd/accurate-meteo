"""Live forecast: fetch the current forecasts of every weather model, apply the frozen models, write prevision.json.

Runs every hour in GitHub Actions (.github/workflows/prevision.yml). No cache, no Météo-France observations needed.

Usage: python prevoir.py [output path]   (default: out/prevision.json)
"""
import json, os, subprocess, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import joblib
import numpy as np
import blend
import modeles
import radar
import score
import vignette

ROOT = os.path.dirname(os.path.abspath(__file__))
LIVE = 'https://api.open-meteo.com/v1/forecast'
CATS = ['soleil', 'mitigé', 'couvert', 'pluie']
# At night GRESIL has no sky (it learned from sunlight): the cloud cover of one raw model is relayed instead, uncorrected.
# ICON-EU = best raw hourly model the day before (RESULTATS.md), then ECMWF IFS (best at 3-7 days) beyond its horizon.
NUIT_MODELES = ['icon_eu', 'ecmwf_ifs025']


def nebulosite(k, fcs):
    """Raw cloud cover for the hour ending at k: mean of its start and end (instant values), first model that has both."""
    for m in NUIT_MODELES:
        f = fcs.get(m, {})
        a, b = (f.get(t, {}).get('cloud') for t in (k - timedelta(hours=1), k))
        if a is not None and b is not None:
            pct = round((a + b) / 2)
            return {'pct': pct, 'mot': 'dégagé' if pct < 30 else 'nuageux' if pct <= 70 else 'couvert',
                    'modele': m, 'corrigee': False}
    return None


def get(url):
    err = None
    for attempt in range(3):
        try:
            return json.load(urllib.request.urlopen(url, timeout=25))
        except Exception as e:
            err = e
            try:  # curl fallback: some Python builds reject Open-Meteo's certificate chain now and then
                return json.loads(subprocess.run(['curl', '-sf', '--max-time', '25', url],
                                                 capture_output=True, check=True).stdout)
            except Exception:
                time.sleep(3 * (attempt + 1))
    print(f'  échec Open-Meteo : {err}', flush=True)
    return None


def fetch_all(models, block, variables, days):
    """One request for several models: Open-Meteo suffixes each series with `_<model>`.
    Returns {model: block dict shaped like a single-model answer} (None for a model with no data)."""
    q = dict(latitude=score.LAT, longitude=score.LON, elevation=score.ELEV, timezone='GMT', wind_speed_unit='ms',
             models=','.join(models), forecast_days=days, past_days=1, **{block: variables})
    d = get(LIVE + '?' + '&'.join(f'{k}={v}' for k, v in q.items()))
    if not d or block not in d:
        return {m: None for m in models}
    B, out = d[block], {}
    for m in models:
        series = {v: B[f'{v}_{m}'] for v in variables.split(',') if f'{v}_{m}' in B}
        if len(models) == 1:
            series = {v: B[v] for v in variables.split(',') if v in B}
        has = any(any(x is not None for x in vals) for vals in series.values())
        out[m] = {'time': B['time'], **series} if has else None
    return out


def load(name):
    return joblib.load(os.path.join(score.MODELES, f'{name}.joblib'))


def run(name, rows):
    """Apply a frozen model to input rows; returns per-row outputs."""
    m = load(name)
    X = np.array(rows, dtype=float)[:, m['keep']]
    if m['kind'] == 'condition':
        p = np.zeros((len(X), 4))
        p[:, m['est'].classes_] = m['est'].predict_proba(X)
        return [{'condition': CATS[int(np.argmax(pp @ blend.C.T))],
                 'probas': {c: round(float(x), 2) for c, x in zip(CATS, pp)}} for pp in p]
    if m['kind'] == 'pluie':
        return [float(x) for x in m['est'].predict_proba(X)[:, 1]]
    return [float(x) for x in m['est'].predict(X)]


MF_OBS = 'https://public-api.meteofrance.fr/public/DPObs/station/horaire'


def station_hour(t):
    """One hour measured at the station, from Météo-France's real-time observation API (last 24 h only).
    Needs the MF_API_KEY environment variable (free key from portail-api.meteofrance.fr); None without it."""
    key = os.environ.get('MF_API_KEY')
    if not key:
        return None
    url = f'{MF_OBS}?id_station={score.STATION}&date={t:%Y-%m-%dT%H:%M:%SZ}&format=json'
    try:  # curl: same certificate trouble as Météo-France's file server with some Python builds
        d = json.loads(subprocess.run(['curl', '-sf', '--max-time', '20', '-H', f'apikey: {key}', url],
                                      capture_output=True, check=True).stdout)
    except Exception as e:
        print(f'  station {t:%H} h indisponible : {e}', flush=True)
        return None
    d = d[0] if isinstance(d, list) and d else d if isinstance(d, dict) else None
    if not d or not str(d.get('validity_time', '')).startswith(t.strftime('%Y-%m-%dT%H')):
        return None
    num = lambda k: None if d.get(k) in (None, '') else float(d[k])
    tk, gust = num('t'), num('fxi') if num('fxi') is not None else num('fxy')
    return {'temperature': None if tk is None else tk - 273.15, 'pluie_mm': num('rr1'),
            'vent': num('ff'), 'rafales': gust}


def sky_today(start, end):
    """Sunlight measured by satellite (Open-Meteo satellite API, published within about an hour)."""
    q = dict(latitude=score.LAT, longitude=score.LON, hourly='shortwave_radiation', timezone='GMT',
             start_date=start, end_date=end)
    d = get(score.SATELLITE + '?' + '&'.join(f'{k}={v}' for k, v in q.items())) or {}
    H = d.get('hourly', {})
    return {score.utc(t): g for t, g in zip(H.get('time', []), H.get('shortwave_radiation', []))}


def passees(now, fcs, hourly_models):
    """Today's hours already over (from 6 h local): what was measured, else what was forecast.
    Sky from the satellite, temperature / rain / wind from the station when MF_API_KEY is set.
    Labelled by their start like the forecast hours: sky and rain of the hour ending at k, temperature and wind at k - 1 h
    (the first key, the hour ending at 6 h, only lends its end values to the 6 h hour)."""
    local = now.astimezone(score.PARIS)
    first = datetime(local.year, local.month, local.day, 6, tzinfo=score.PARIS).astimezone(timezone.utc)
    last = now.replace(minute=0, second=0, microsecond=0)   # hour ending at the last round hour
    keys = [first + timedelta(hours=i) for i in range(int((last - first).total_seconds() // 3600) + 1)]
    if len(keys) < 2:
        return []
    rows = [modeles.row(k, fcs, hourly_models) for k in keys]
    cond, temp = run('heure_condition', rows), run('heure_temperature', rows)
    wind, gust = run('heure_vent', rows), run('heure_rafales', rows)
    sky = sky_today(keys[0].date().isoformat(), keys[-1].date().isoformat())
    out = []
    for i, k in enumerate(keys):
        o = station_hour(k) or {}
        cs, elev = score.sky_info(k)
        g = sky.get(k)
        ratio = g / cs if g is not None and elev > 10 and cs > 50 else None
        rain = o.get('pluie_mm')
        if ratio is not None:
            c = CATS[score.category(rain or 0, ratio, score.RAIN_HOUR)]
        elif elev <= 0:
            c = 'pluie' if rain is not None and rain >= score.RAIN_HOUR else 'nuit'
        else:
            c = cond[i]['condition']
        val = lambda v, f: o[v] if o.get(v) is not None else f
        out.append({'heure': k.astimezone(score.PARIS).isoformat(timespec='minutes'), 'condition': c,
                    'temperature': r1(val('temperature', temp[i])), 'pluie_mm': r1(rain),
                    'vent_kmh': r1(val('vent', wind[i]) * 3.6), 'rafales_kmh': r1(val('rafales', gust[i]) * 3.6),
                    'ratio': None if ratio is None else round(ratio, 2),
                    'mesure': {'ciel': ratio is not None or elev <= 0, 'station': bool(o)}})
    # start labels: hour ending at k → labelled k - 1 h, with the instant values (temperature, wind) taken at k - 1 h
    return [{**h, 'heure': prev['heure'], 'temperature': prev['temperature'], 'vent_kmh': prev['vent_kmh']}
            for prev, h in zip(out, out[1:])]


def demi_passee(hs, part):
    """Morning (hours starting 6-11 h) or afternoon (12-17 h) already over, rebuilt from the past hours."""
    lo, hi = (6, 11) if part == 'matin' else (12, 17)
    sel = [h for h in hs if lo <= int(h['heure'][11:13]) <= hi]
    if len(sel) != 6:
        return None
    ratios = [h['ratio'] for h in sel if h['ratio'] is not None]
    rains = [h['pluie_mm'] for h in sel]
    rain = sum(rains) if None not in rains else 0
    if len(ratios) >= 2:
        c = CATS[score.category(rain, sum(ratios) / len(ratios), score.RAIN_BLOCK)]
    else:
        c = max(CATS, key=lambda x: sum(h['condition'] == x for h in sel))
    return {'condition': c, 'temperature': r1(sum(h['temperature'] for h in sel) / 6),
            'rafales_kmh': max(h['rafales_kmh'] for h in sel), 'passe': True,
            'mesure': {'ciel': len(ratios) >= 2, 'station': all(h['mesure']['station'] for h in sel)}}


def r1(x):
    return None if x is None else round(x, 1)


def main(out_path):
    now = datetime.now(timezone.utc)
    hourly_models, trend_models, now_models = score.HOURLY_MODELS, score.TREND_MODELS, score.NOWCAST_MODELS
    # Two requests in all (several models per request): from GitHub's shared runners, dozens of separate
    # requests got throttled and some hung for minutes
    all_models = sorted(set(hourly_models + trend_models + now_models))
    with ThreadPoolExecutor(max_workers=2) as pool:
        hj = pool.submit(fetch_all, all_models, 'hourly', ','.join(score.VARS), 9)
        mj = pool.submit(fetch_all, now_models, 'minutely_15', 'precipitation', 1)
        raw, minutes = hj.result(), mj.result()
    fcs = {m: modeles.hours(H) for m, H in raw.items() if H}
    missing = sorted(m for m, H in raw.items() if not H)

    # ---------- hour by hour, until the end of the 7th day ----------
    # The hourly models were trained on day-before forecasts: beyond 48 h the fine models are missing,
    # so those hours are flagged as less precise (the half-day models stay the reference there)
    start = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    last_day = now.astimezone(score.PARIS).date() + timedelta(days=7)
    end = datetime(last_day.year, last_day.month, last_day.day, 23, tzinfo=score.PARIS).astimezone(timezone.utc)
    keys = [start + timedelta(hours=i) for i in range(int((end - start).total_seconds() // 3600) + 1)]
    # Model keys are hour ENDS (Météo-France / Open-Meteo: rain, sky and gusts of the hour ending at k). Published hours
    # carry their START, as people read them ("19 h" = 19 h to 20 h): sky, rain and gusts of the hour ending at k,
    # temperature and wind measured at its start (k - 1 h, one extra key computed for that)
    rows = [modeles.row(k, fcs, hourly_models) for k in [keys[0] - timedelta(hours=1)] + keys]
    cond, rain = run('heure_condition', rows[1:]), run('heure_pluie', rows[1:])
    temp, wind = run('heure_temperature', rows), run('heure_vent', rows)
    gust = run('heure_rafales', rows[1:])
    heures = []
    for i, k in enumerate(keys):
        day = score.sky_info(k)[1] > 10  # condition is only learned in daylight (probas kept for those hours)
        up = score.sky_info(k)[1] > 0    # low sun at dawn / dusk: still the model's sky, not a moon
        heures.append({'heure': (k - timedelta(hours=1)).astimezone(score.PARIS).isoformat(timespec='minutes'),
                       'condition': cond[i]['condition'] if up else ('pluie' if rain[i] >= 0.5 else 'nuit'),
                       'probas': cond[i]['probas'] if day else None,
                       'pluie_proba': round(rain[i], 2), 'temperature': r1(temp[i]),   # temp[i] = at k - 1 h
                       'vent_kmh': r1(wind[i] * 3.6), 'rafales_kmh': r1(gust[i] * 3.6),
                       'precision_reduite': (k - now).total_seconds() > 48 * 3600,
                       **({} if up else {'nebulosite': nebulosite(k, fcs)})})

    passe = passees(now, fcs, hourly_models)

    # ---------- 7 days, morning / afternoon ----------
    bfcs = {m: modeles.blocks(f) for m, f in fcs.items() if m in trend_models}
    today = now.astimezone(score.PARIS).date()
    jours = []
    for d in range(0, 8):
        date = today + timedelta(days=d)
        lead = min(7, max(1, d))
        entry = {'date': date.isoformat()}
        for part in ('matin', 'aprem'):
            k = (date, part)
            end = datetime(date.year, date.month, date.day, 12 if part == 'matin' else 18, tzinfo=score.PARIS)
            if end <= now:
                if d == 0 and (p := demi_passee(passe, part)):
                    entry[part] = p   # already over today: what happened (measured where possible)
                continue
            if not any(k in bfcs[m] for m in bfcs):
                continue  # beyond every model
            row = [modeles.row(k, bfcs, trend_models)]
            c = run(f'bloc{lead}_condition', row)[0]
            entry[part] = {**c, 'temperature': r1(run(f'bloc{lead}_temperature', row)[0]),
                           'rafales_kmh': r1(run(f'bloc{lead}_rafales', row)[0] * 3.6)}
        if len(entry) > 1:
            jours.append(entry)

    # ---------- next 2 hours, 20-minute slots ----------
    mslots, hctx = {}, {}
    for m in now_models:
        M = minutes.get(m)
        if M:
            mslots[m] = modeles.slots(M)
        if raw.get(m):
            hctx[m] = modeles.hourly_ctx(raw[m])
    s0 = now.replace(minute=now.minute // 20 * 20, second=0, microsecond=0)
    # 3 hours of slots: the site keeps the 6 that start from the phone's own clock, so a forecast computed
    # up to an hour ago still shows the right 2 hours (the journal keeps the first 6 only)
    slots = [s0 + modeles.SLOT * i for i in range(9)]
    p = run('pluie2h', [modeles.rain_row(s, mslots, hctx, now_models) for s in slots])
    seuil = load('pluie2h')['threshold']
    tranches = [{'debut': s.astimezone(score.PARIS).isoformat(timespec='minutes'),
                 'pluie': bool(x >= seuil), 'pluie_proba': round(x, 2)} for s, x in zip(slots, p)]

    # Live record of every model's 20-minute rain, to measure later the true 2-hour skill (archives are too generous),
    # plus our own hours (next 48 h) and half-days (1 to 7 days): with retro/ (backfill), the history used to
    # fine-tune the mega-model on its own errors
    h48 = [i for i, k in enumerate(keys) if (k - now).total_seconds() <= 48 * 3600]
    journal = {'genere_le': now.isoformat(timespec='minutes'), 'tranches_utc': [s.isoformat() for s in slots[:6]],
               'mega_proba': [round(x, 3) for x in p[:6]],
               'modeles': {m: [None if s not in mslots.get(m, {}) else round(mslots[m][s], 3) for s in slots[:6]]
                           for m in now_models},
               'heures': {'heure_utc': [keys[i].isoformat() for i in h48],
                          'probas': [[round(float(x), 2) for x in cond[i]['probas'].values()] for i in h48],
                          'pluie_proba': [round(rain[i], 3) for i in h48],
                          'temperature': [r1(temp[i]) for i in h48], 'vent_ms': [r1(wind[i]) for i in h48],
                          'rafales_ms': [r1(gust[i]) for i in h48]},
               'jours': jours}
    # Radar frames of the last 2 hours, recorded once per hour (the journal keeps the hour's first run;
    # frames overlap from one hour to the next): material for a future radar-based 2-hour rain model
    if now.minute < 15:
        journal['radar'] = radar.record()
    jpath = os.path.join(os.path.dirname(out_path) or '.', 'journal', now.strftime('%Y-%m-%dT%HZ') + '.json')
    os.makedirs(os.path.dirname(jpath), exist_ok=True)
    with open(jpath, 'w') as f:
        json.dump(journal, f, separators=(',', ':'))

    out = {'modele': 'GRESIL', 'genere_le': now.astimezone(score.PARIS).isoformat(timespec='minutes'),
           'lieu': score.NOM, 'modeles_absents': missing,
           'deux_heures': tranches, 'passe': passe, 'heures': heures, 'jours': jours}
    os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
    with open(out_path, 'w') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    try:   # sharing preview with the next 7 days; the forecast itself must not depend on it
        vignette.draw(out, os.path.join(os.path.dirname(out_path) or '.', 'og.png'))
    except Exception as e:
        print(f'  image de partage non dessinée : {e}', flush=True)
    print(f'{out_path} écrit ({len(heures)} heures, {len(jours)} jours, {len(tranches)} tranches, absents : {missing})')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(score.SORTIE, 'out', 'prevision.json'))
