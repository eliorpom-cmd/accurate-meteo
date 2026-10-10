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
import score

ROOT = os.path.dirname(os.path.abspath(__file__))
LIVE = 'https://api.open-meteo.com/v1/forecast'
CATS = ['soleil', 'mitigé', 'couvert', 'pluie']


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
    return joblib.load(os.path.join(ROOT, 'modeles', f'{name}.joblib'))


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
    rows = [modeles.row(k, fcs, hourly_models) for k in keys]
    cond, rain = run('heure_condition', rows), run('heure_pluie', rows)
    temp, wind, gust = (run(f'heure_{v}', rows) for v in ('temperature', 'vent', 'rafales'))
    heures = []
    for i, k in enumerate(keys):
        day = score.sky_info(k)[1] > 10  # condition is only learned in daylight
        heures.append({'heure': k.astimezone(score.PARIS).isoformat(timespec='minutes'),
                       'condition': cond[i]['condition'] if day else ('pluie' if rain[i] >= 0.5 else 'nuit'),
                       'probas': cond[i]['probas'] if day else None,
                       'pluie_proba': round(rain[i], 2), 'temperature': r1(temp[i]),
                       'vent_kmh': r1(wind[i] * 3.6), 'rafales_kmh': r1(gust[i] * 3.6),
                       'precision_reduite': (k - now).total_seconds() > 48 * 3600})

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
            if end <= now or not any(k in bfcs[m] for m in bfcs):
                continue  # half-day already over, or beyond every model
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
    jpath = os.path.join(os.path.dirname(out_path) or '.', 'journal', now.strftime('%Y-%m-%dT%HZ') + '.json')
    os.makedirs(os.path.dirname(jpath), exist_ok=True)
    with open(jpath, 'w') as f:
        json.dump(journal, f, separators=(',', ':'))

    out = {'genere_le': now.astimezone(score.PARIS).isoformat(timespec='minutes'),
           'lieu': 'Grenoble', 'modeles_absents': missing,
           'deux_heures': tranches, 'heures': heures, 'jours': jours}
    os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
    with open(out_path, 'w') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f'{out_path} écrit ({len(heures)} heures, {len(jours)} jours, {len(tranches)} tranches, absents : {missing})')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'out', 'prevision.json'))
