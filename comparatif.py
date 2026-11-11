"""Live reliability check: GRESIL as it was really published (journal branch) against each weather model
and against the station, over the same cases, since the launch.

Unlike FIGE.md / ETUDE.md (models replayed on the past), nothing here is replayed for GRESIL: its forecasts
are the ones recorded every hour by the production run. The weather models come from the Open-Meteo Previous
Runs API (`*_previous_dayN` = what the model said N days before), as in score.py.

Same lead for everyone:
- hour by hour: the model's `previous_day1` value against the GRESIL run recorded 24 h (or a bit more) before;
- half-days J+N: the model's `previous_dayN` values against the last GRESIL run recorded at least N×24 h
  before the middle of the half-day;
- rain within 2 hours: every source as recorded in the same journal entry.

Usage: .venv/bin/python comparatif.py            (Grenoble → COMPARATIF.md)
       VILLE=villes/neffies.json .venv/bin/python comparatif.py
"""
import glob, json, os, subprocess
from datetime import datetime, timedelta, timezone
import numpy as np
import bilan
import blend
import modeles
import score

JOURNAL_ROOT = os.path.join(score.ROOT, 'data', 'journal')   # one clone of the journal branch for every city
N_BOOT = 2000


def fetch_journal():
    if os.path.isdir(os.path.join(JOURNAL_ROOT, '.git')):
        subprocess.run(['git', '-C', JOURNAL_ROOT, 'pull', '-q', '--ff-only'], check=True)
    else:
        subprocess.run(['git', 'clone', '-q', '--depth', '1', '--branch', 'journal', bilan.REPO, JOURNAL_ROOT], check=True)
    sub = 'journal' if score.SORTIE == score.ROOT else os.path.join(score.SLUG, 'journal')
    runs = [json.load(open(p)) for p in sorted(glob.glob(os.path.join(JOURNAL_ROOT, sub, '*.json')))]
    for r in runs:
        r['made'] = datetime.fromisoformat(r['genere_le'])
    return sorted(runs, key=lambda r: r['made'])


def gresil_hourly(runs):
    """For each target hour, the forecast of the last run recorded at least 24 h before (same lead as previous_day1)."""
    out = {}
    for r in runs:
        H = r.get('heures')
        if not H:
            continue
        for i, ts in enumerate(H['heure_utc']):
            t = datetime.fromisoformat(ts)
            if t - r['made'] >= timedelta(hours=24):
                out[t] = {'cat': bilan.decide(H['probas'][i]) if H['probas'][i] else None,
                          'pluie': H['pluie_proba'][i] >= .5 if H['pluie_proba'][i] is not None else None,
                          'temperature': H['temperature'][i], 'vent': H['vent_ms'][i], 'rafales': H['rafales_ms'][i]}
    return out


def gresil_halfdays(runs):
    """(lead, date, part) → forecast of the last run recorded at least lead×24 h before the middle of the half-day."""
    out = {}
    for r in runs:
        for j in r.get('jours', []):
            d = datetime.fromisoformat(j['date']).date()
            lead = (d - r['made'].astimezone(score.PARIS).date()).days
            for part, mid in (('matin', (9, 30)), ('aprem', (15, 30))):
                f = j.get(part)
                middle = datetime(d.year, d.month, d.day, *mid, tzinfo=score.PARIS)
                if not f or lead < 1 or r['made'] > middle - timedelta(days=lead):
                    continue
                out[(lead, d, part)] = {'cat': score.CATS.index(f['condition']), 'temperature': f.get('temperature')}
    return out


def model_hourly(fc):
    return {t: {'cat': f['cat'], 'pluie': f['pluie_mm'] >= score.RAIN_HOUR if f['pluie_mm'] is not None else None,
                'temperature': f['temperature'], 'vent': f['vent'], 'rafales': f['rafales']} for t, f in fc.items()}


def csi(p, y):
    p, y = np.asarray(p, dtype=bool), np.asarray(y, dtype=bool)
    return 100 * np.sum(p & y) / np.sum(p | y) if np.any(p | y) else float('nan')


# One metric = (label, forecast field, observed value, statistic, higher is better)
def credit(f, o):
    return 100 * np.mean(blend.C[np.asarray(f, dtype=int), np.asarray(o, dtype=int)])


def mae(f, o):
    return float(np.mean(np.abs(np.asarray(f, dtype=float) - np.asarray(o, dtype=float))))


HOUR_METRICS = [('Ciel /100', 'cat', lambda o: o.get('cat'), credit, True),
                ('Pluie, réussite %', 'pluie', lambda o: None if o.get('pluie_mm') is None else o['pluie_mm'] >= score.RAIN_HOUR, csi, True),
                ('Température, erreur °C', 'temperature', lambda o: o.get('temperature'), mae, False),
                ('Vent, erreur m/s', 'vent', lambda o: o.get('vent'), mae, False),
                ('Rafales, erreur m/s', 'rafales', lambda o: o.get('rafales'), mae, False)]
HALF_METRICS = [('Ciel /100', 'cat', lambda o: o.get('cat'), credit, True),
                ('Température, erreur °C', 'temperature', lambda o: o.get('temperature'), mae, False)]


def day_of(k):
    return k[0] if isinstance(k, tuple) else k.astimezone(score.PARIS).date()


def evaluate(sources, obs, metrics, min_cover=0.5):
    """Score every source on the cases where all of them (and the station) have a value.
    Returns {label: {'n', 'days', 'scores': {source: value}, 'best', 'diff', 'lo', 'hi', 'beaten', 'dropped'}}."""
    res = {}
    for label, field, truth, stat, higher in metrics:
        keys = [k for k in obs if truth(obs[k]) is not None and (sources['GRESIL'].get(k) or {}).get(field) is not None]
        has = lambda s, k: (s.get(k) or {}).get(field) is not None
        kept = {m: s for m, s in sources.items() if m == 'GRESIL' or sum(has(s, k) for k in keys) >= min_cover * len(keys)}
        dropped = sorted(set(sources) - set(kept))
        keys = sorted(k for k in keys if all(has(s, k) for s in kept.values()))
        if len(keys) < 20 or len(kept) < 2:
            res[label] = None
            continue
        y = np.array([truth(obs[k]) for k in keys])
        F = {m: np.array([s[k][field] for k in keys]) for m, s in kept.items()}
        scores = {m: stat(F[m], y) for m in F}
        others = {m: v for m, v in scores.items() if m != 'GRESIL' and not np.isnan(v)}
        if not others or np.isnan(scores['GRESIL']):
            res[label] = {'n': len(keys), 'scores': scores, 'best': None, 'dropped': dropped, 'higher': higher,
                          'days': len({day_of(k) for k in keys})}
            continue
        best = (max if higher else min)(others, key=others.get)
        sign = 1 if higher else -1
        days = np.array([day_of(k).toordinal() for k in keys])
        r = {'n': len(keys), 'days': len(np.unique(days)), 'scores': scores, 'best': best, 'higher': higher,
             'dropped': dropped, 'beaten': sum(sign * (scores['GRESIL'] - v) > 0 for v in others.values()),
             'others': len(others), 'events': int(np.sum(y)) if field == 'pluie' else None,
             '_boot': (F, y, days, stat, sign)}
        r['diff'], r['lo'], r['hi'] = gain(r, best)
        res[label] = r
    return res


def gain(r, m):
    """Gain of GRESIL over model m (positive = GRESIL better) with a 90 % interval.
    Bootstrap on whole days: the hours of one day are not independent."""
    F, y, days, stat, sign = r['_boot']
    uniq = np.unique(days)
    idx = {d: np.flatnonzero(days == d) for d in uniq}
    rng = np.random.default_rng(0)
    gains = []
    for _ in range(N_BOOT):
        pick = np.concatenate([idx[d] for d in rng.choice(uniq, len(uniq))])
        g = sign * (stat(F['GRESIL'][pick], y[pick]) - stat(F[m][pick], y[pick]))
        if not np.isnan(g):
            gains.append(g)
    lo, hi = np.percentile(gains, [5, 95]) if gains else (float('nan'),) * 2
    return sign * (r['scores']['GRESIL'] - r['scores'][m]), lo, hi


def versus(title, res, names, out):
    """One row per well-known model: GRESIL against that model alone, same cases as the tables."""
    for label, r in res.items():
        if not r or not r.get('best'):
            continue
        nd = 1 if r['higher'] else 2
        for m in names:
            if m not in r['scores'] or np.isnan(r['scores'][m]):
                continue
            d, lo, hi = gain(r, m)
            out.append(f"| {title} | {label} | {m} | {fr(r['scores']['GRESIL'], nd)} | {fr(r['scores'][m], nd)} | "
                       f"{'+' if d >= 0 else '−'}{fr(abs(d), nd)} [{fr(lo, nd)} ; {fr(hi, nd)}] | "
                       f"{'GRESIL meilleur' if lo > 0 else 'GRESIL moins bon' if hi < 0 else 'pas de différence sûre'} |")


def verdict(r):
    if r['lo'] > 0:
        return 'GRESIL meilleur'
    if r['hi'] < 0:
        return 'GRESIL moins bon'
    return 'pas de différence sûre'


def fr(x, nd=1):
    return '-' if x is None or np.isnan(x) else f'{x:.{nd}f}'.replace('.', ',')


def summary_rows(title, res, out):
    for label, r in res.items():
        if not r or not r.get('best'):
            out.append(f'| {title} | {label} | - | - | - | - | - | trop peu de cas |')
            continue
        nd = 2 if not r['higher'] else 1
        cases = f"{r['n']} ({r['days']} j)" + (f", {r['events']} avec pluie" if r.get('events') is not None else '')
        out.append(f"| {title} | {label} | {fr(r['scores']['GRESIL'], nd)} | {fr(r['scores'][r['best']], nd)} ({r['best']}) | "
                   f"{'+' if r['diff'] >= 0 else '−'}{fr(abs(r['diff']), nd)} [{fr(r['lo'], nd)} ; {fr(r['hi'], nd)}] | "
                   f"{r['beaten']}/{r['others']} | {cases} | {verdict(r)} |")


def detail_table(res, out):
    labels = [l for l, r in res.items() if r]
    if not labels:
        out.append('Trop peu de cas.\n')
        return
    names = sorted({m for l in labels for m in res[l]['scores']}, key=lambda m: (m != 'GRESIL', m))
    out.append('| Source | ' + ' | '.join(labels) + ' |')
    out.append('|---|' + '---|' * len(labels))
    for m in names:
        cells = []
        for l in labels:
            r = res[l]
            v = r['scores'].get(m)
            s = fr(v, 1 if r['higher'] else 2) if v is not None else '-'
            vals = [x for x in r['scores'].values() if not np.isnan(x)]
            top = v is not None and vals and v == (max if r['higher'] else min)(vals)
            cells.append(f'**{s}**' if top else s)
        out.append(f"| {m} | " + ' | '.join(cells) + ' |')
    out.append('\nCas notés : ' + ' ; '.join(f"{l} {res[l]['n']}" for l in labels) + '.')
    dropped = sorted({m for l in labels for m in res[l].get('dropped', [])})
    if dropped:
        out.append('Écartés faute de données sur la période (au moins une variable) : ' + ', '.join(dropped) + '.')
    out.append('')


def main():
    runs = fetch_journal()
    if not runs:
        raise SystemExit('journal vide')
    first, last = runs[0]['made'], runs[-1]['made']
    start = first.date().isoformat()
    end = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()
    obs = {t: o for t, o in bilan.observations(start, end).items() if t >= first}
    last_obs = max((t for t, o in obs.items() if o.get('temperature') is not None), default=None)
    oblocks = score.to_blocks(obs)

    # ---- hour by hour, one day ahead ----
    hv = ','.join(f'{v}_previous_day1' for v in score.VARS)
    hourly = {'GRESIL': gresil_hourly(runs)}
    for m in score.HOURLY_MODELS:
        d = score.api_chunk(score.PREVIOUS, {'hourly': hv, 'models': m}, start, end)
        if d:
            hourly[m] = model_hourly(score.forecast_hours(d['hourly'], '_previous_day1'))
    res_hour = evaluate(hourly, obs, HOUR_METRICS)

    # ---- half-days J+1 … J+7 ----
    leads = range(1, 8)
    tv = ','.join(f'{v}_previous_day{d}' for d in leads for v in score.VARS)
    raw = {}
    for m in score.TREND_MODELS:
        d = score.api_chunk(score.PREVIOUS, {'hourly': tv, 'models': m}, start, end)
        if d:
            raw[m] = d
    gh = gresil_halfdays(runs)
    res_half = {}
    for lead in leads:
        src = {'GRESIL': {(d, p): f for (l, d, p), f in gh.items() if l == lead}}
        for m, d in raw.items():
            src[m] = score.to_blocks(score.forecast_hours(d['hourly'], f'_previous_day{lead}'))
        res_half[lead] = evaluate(src, oblocks, HALF_METRICS)

    # ---- rain within 2 hours (20-min slots), every source from the same journal entry ----
    slots = score.to_slots(score.load_6min_rain(), 6)
    now = {}
    for r in runs:
        for k, ts in enumerate(r['tranches_utc']):
            s = datetime.fromisoformat(ts)
            if s not in slots or any(v[k] is None for v in r['modeles'].values()):
                continue
            key = (s, r['made'])
            now.setdefault('GRESIL', {})[key] = {'pluie': r['mega_proba'][k] >= modeles.RAIN_2H_THRESHOLD}
            for m, v in r['modeles'].items():
                now.setdefault(m, {})[key] = {'pluie': v[k] >= score.RAIN_SLOT}
    oslots = {key: {'pluie_mm': slots[key[0]]} for key in now.get('GRESIL', {})}
    res_now = evaluate(now, oslots, [('Pluie, réussite %', 'pluie', lambda o: o['pluie_mm'] >= score.RAIN_SLOT, csi, True)])
    for r in res_now.values():
        if r:  # bootstrap days come from the slot start
            r['events'] = int(sum(o['pluie_mm'] >= score.RAIN_SLOT for o in oslots.values()))

    out = [f'# GRESIL en direct contre chaque modèle météo — {score.VILLE.get("nom", score.SLUG)}\n',
           f'Prévisions de GRESIL réellement publiées (journal de production, {len(runs)} enregistrements du '
           f'{first:%d/%m/%Y %H h} UTC au {last:%d/%m/%Y %H h} UTC), comparées à ce que chaque modèle météo annonçait '
           f'avec la même avance (Open-Meteo Previous Runs) et à la station {score.STATION_NOM} '
           f'(dernière mesure : {last_obs:%d/%m/%Y %H h} UTC ; ciel : satellite). '
           'Tous notés sur les mêmes cas. Rien n\'est rejoué pour GRESIL.\n',
           '## Résumé\n',
           '« Meilleur modèle seul » = le meilleur des modèles sur cette ligne, choisi après coup (avantage aux modèles). '
           'Écart : positif = GRESIL meilleur ; entre crochets, intervalle à 90 % par tirage de jours entiers. '
           '« Bat » = nombre de modèles que GRESIL dépasse.\n',
           '| Échéance | Variable | GRESIL | Meilleur modèle seul | Écart [90 %] | Bat | Cas | Verdict |',
           '|---|---|---|---|---|---|---|---|']
    summary_rows('Veille, heure par heure', res_hour, out)
    for lead in leads:
        summary_rows(f'Demi-journées J+{lead}', res_half[lead], out)
    summary_rows('2 prochaines heures', res_now, out)
    out.append('\nCiel = soleil / mitigé / couvert / pluie, de jour seulement, crédit partiel entre catégories voisines. '
               'Réussite pluie = cas de pluie bien annoncés / (bien annoncés + manqués + fausses alertes) ; '
               f'pluie = au moins {score.RAIN_HOUR} mm dans l\'heure, {score.RAIN_SLOT} mm par tranche de 20 min.\n')
    out += ['## Contre quatre modèles connus, un par un\n',
            'Météo-France (meteofrance_seamless), ECMWF IFS (européen), ICON (allemand, icon_seamless), '
            'GFS (américain). Mêmes cas que le résumé, même lecture de l\'écart.\n',
            '| Échéance | Variable | Modèle | GRESIL | Modèle | Écart [90 %] | Verdict |', '|---|---|---|---|---|---|---|']
    known = ['meteofrance_seamless', 'ecmwf_ifs025', 'icon_seamless', 'gfs_seamless']
    versus('Veille, heure par heure', res_hour, known, out)
    for lead in (1, 3, 5, 7):
        versus(f'Demi-journées J+{lead}', res_half[lead], known, out)
    versus('2 prochaines heures', res_now, known + ['meteofrance_arome_france', 'icon_d2'], out)
    out.append('')
    out.append('## Veille pour le lendemain, heure par heure : tous les modèles\n')
    detail_table(res_hour, out)
    for lead in leads:
        out.append(f'## Demi-journées J+{lead} : tous les modèles\n')
        detail_table(res_half[lead], out)
    out.append('## Pluie dans les 2 heures (tranches de 20 min) : toutes les sources\n')
    detail_table(res_now, out)
    path = os.path.join(score.SORTIE, 'COMPARATIF.md')
    open(path, 'w').write('\n'.join(out) + '\n')
    clean = lambda res: {l: r and {k: v for k, v in r.items() if k != '_boot'} for l, r in res.items()}
    json.dump({'heure': clean(res_hour), 'demi': {str(k): clean(v) for k, v in res_half.items()}, 'pluie2h': clean(res_now)},
              open(os.path.join(score.DATA, 'comparatif.json'), 'w'), default=float, ensure_ascii=False, indent=1)
    print('\n'.join(out))


if __name__ == '__main__':
    main()
