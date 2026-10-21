"""Is GRESIL more reliable than the weather models it combines? Month-by-month study over the whole period.

figer.py tests once (train before TEST_FROM, score after): for a short period that is a few months, often one season.
Here every month is forecast by a model trained on all the other months (same recipes as retro.py), so every month
of the period is scored, winter included. GRESIL and each weather model are scored on exactly the same cases, then:
  - overall score of GRESIL and of every model;
  - months won against the best single model (chosen after the fact on the whole period: a strict baseline);
  - a 90 % range on the gap, by resampling whole months (bootstrap), so one lucky month cannot decide.

Usage: VILLE=villes/<city>.json .venv/bin/python etude.py   (cache only) → <city>/ETUDE.md
"""
import os
from collections import defaultdict
import numpy as np
import blend
import figer
import modeles
import retro
import score

BOOT = 2000
rng = np.random.default_rng(0)


def per_case(kind, pred, y, thr=0.5):
    """Score of each case (higher is better), so months and bootstrap samples can be averaged."""
    if kind == 'condition':
        return blend.C[pred, y]
    return -np.abs(pred - y)   # regression: minus the error


def month_scores(kind, keys, pred, y):
    """{month: (sum, count)} for condition / regression, {month: (hits, misses, false alarms)} for rain."""
    out = defaultdict(lambda: np.zeros(3))
    for k, p, o in zip(keys, pred, y):
        m = retro.month(k)
        if kind == 'pluie':
            out[m] += [p and o, (not p) and o, p and not o]
        else:
            out[m] += [per_case(kind, np.array([p]), np.array([o]))[0], 1, 0]
    return out


def total(kind, ms, months):
    s = sum((ms[m] for m in months if m in ms), np.zeros(3))
    if kind == 'pluie':
        return 100 * s[0] / max(1, s.sum())
    return 100 * s[0] / max(1, s[1]) if kind == "condition" else s[0] / max(1, s[1])   # reg: minus the mean error


def fmt(kind, x):
    return f'{x:.1f}' if kind != 'reg' else f'{x:.2f}'


def study(label, kind, keys, X, y, singles, half_life=None, thr=0.5):
    """singles: {model: [forecast per key or None]} (category, rain yes/no, or value)."""
    oof = retro.out_of_fold(label, 'pluie' if kind == 'pluie' else kind, keys, X, y, half_life)
    keys = [k for k in keys if k in oof]
    # GRESIL decisions
    if kind == 'condition':
        g = {k: int(np.argmax(oof[k] @ blend.C.T)) for k in keys}
    elif kind == 'pluie':
        g = {k: bool(oof[k] >= thr) for k in keys}
    else:
        g = {k: float(oof[k]) for k in keys}
    obs = dict(zip(ALL_KEYS[label], ALL_Y[label]))
    # only the cases every compared model covers, so all are scored on the same ground
    models = [m for m, v in singles.items() if sum(x is not None for x in v) >= 0.9 * len(v)]
    sv = {m: dict(zip(ALL_KEYS[label], singles[m])) for m in models}
    common = [k for k in keys if all(sv[m].get(k) is not None for m in models)]
    yk = [obs[k] for k in common]
    msg = month_scores(kind, common, [g[k] for k in common], yk)
    months = sorted(msg)
    res = {'GRESIL': msg}
    for m in models:
        res[m] = month_scores(kind, common, [sv[m][k] for k in common], yk)
    tot = {n: total(kind, ms, months) for n, ms in res.items()}
    best = max(models, key=lambda m: tot[m])   # scores are "higher is better" (errors negated)
    won = sum(total(kind, res['GRESIL'], [m]) > total(kind, res[best], [m]) for m in months)
    gaps = []
    for _ in range(BOOT):
        s = list(rng.choice(months, len(months)))
        gaps.append(total(kind, res['GRESIL'], s) - total(kind, res[best], s))
    lo, hi = np.percentile(gaps, [5, 95])
    sign = -1 if kind == 'reg' else 1
    return {'label': label, 'kind': kind, 'n': len(common), 'months': len(months), 'tot': tot, 'best': best,
            'won': won, 'lo': lo, 'hi': hi, 'sign': sign,
            'by_month': {m: (total(kind, res['GRESIL'], [m]), total(kind, res[best], [m])) for m in months}}


ALL_KEYS, ALL_Y = {}, {}


def run(label, kind, keys, X, y, singles, **kw):
    ALL_KEYS[label], ALL_Y[label] = keys, list(y)
    r = study(label, kind, keys, X, y, singles, **kw)
    print(line(r), flush=True)
    return r


MEASURE = {'condition': 'ciel /100 (plus haut = mieux)', 'pluie': 'réussite pluie % (plus haut = mieux)',
           'reg': 'erreur moyenne (plus bas = mieux)'}


def line(r):
    k, s, t = r['kind'], r['sign'], r['tot']
    show = lambda x: fmt(k, s * x if k == 'reg' else x)
    gap = lambda x: f'{x:+.{1 if k != "reg" else 2}f}'
    verdict = ('**GRESIL meilleur**' if r['lo'] > 0 else 'GRESIL moins bon' if r['hi'] < 0 else 'pas de différence sûre')
    return (f"| {r['label']} | {MEASURE[k]} | **{show(t['GRESIL'])}** | {show(t[r['best']])} ({r['best']}) | "
            f"{gap(r['lo'])} à {gap(r['hi'])} | {r['won']}/{r['months']} | {verdict} | {r['n']} |")


def main():
    obs = score.load_obs()
    rows = []

    # ---------- hourly, the day before ----------
    hv = ','.join(f'{v}_previous_day1' for v in score.VARS)
    models = score.HOURLY_MODELS
    fcs = {m: modeles.hours(score.api(score.PREVIOUS, {'hourly': hv, 'models': m})['hourly'], '_previous_day1')
           for m in models}
    single = lambda keys, v: {m: [fcs[m].get(k, {}).get(v) for k in keys] for m in models}
    keys, X, y = figer.build(fcs, obs, models, lambda o: o['cat'], lambda o, k: o['cat'] is not None)
    rows.append(run('Veille, heure par heure : ciel', 'condition', keys, X, y, single(keys, 'cat')))
    keys, X, y = figer.build(fcs, obs, models, lambda o: o['pluie_mm'] >= score.RAIN_HOUR,
                             lambda o, k: o['pluie_mm'] is not None)
    rain = {m: [None if v is None else v >= score.RAIN_HOUR for v in vals] for m, vals in single(keys, 'pluie_mm').items()}
    rows.append(run('Veille, heure par heure : pluie', 'pluie', keys, X, y.astype(int), rain))
    for v, nom in (('temperature', 'température °C'), ('rafales', 'rafales m/s')):
        keys, X, y = figer.build(fcs, obs, models, lambda o, v=v: o[v], lambda o, k, v=v: o.get(v) is not None)
        rows.append(run(f'Veille, heure par heure : {nom}', 'reg', keys, X, y, single(keys, v)))

    # ---------- half-days ----------
    oblocks = score.to_blocks(obs)
    hv = ','.join(f'{v}_previous_day{d}' for d in range(1, 8) for v in score.VARS)
    models = score.TREND_MODELS
    raw = {m: score.api(score.PREVIOUS, {'hourly': hv, 'models': m}) for m in models}
    for lead in (1, 2, 3, 5, 7):
        fcs = {m: modeles.blocks(modeles.hours(d['hourly'], f'_previous_day{lead}')) for m, d in raw.items()}
        single = lambda keys, v: {m: [fcs[m].get(k, {}).get(v) for k in keys] for m in models}
        hl = figer.BLOCK_HALF_LIFE.get(lead)
        keys, X, y = figer.build(fcs, oblocks, models, lambda o: o['cat'], lambda o, k: o['cat'] is not None)
        rows.append(run(f'J+{lead}, matin / après-midi : ciel', 'condition', keys, X, y, single(keys, 'cat'), half_life=hl))
        keys, X, y = figer.build(fcs, oblocks, models, lambda o: o['temperature'], lambda o, k: o.get('temperature') is not None)
        rows.append(run(f'J+{lead}, matin / après-midi : température °C', 'reg', keys, X, y, single(keys, 'temperature'), half_life=hl))

    # ---------- rain in the next 2 hours ----------
    models = score.NOWCAST_MODELS
    oslots = score.to_slots(score.load_6min_rain(), 6)
    mslots, hctx = {}, {}
    for m in models:
        mslots[m] = modeles.slots(score.api(score.HISTORICAL, {'minutely_15': 'precipitation', 'models': m})['minutely_15'])
        hctx[m] = modeles.hourly_ctx(score.api(score.HISTORICAL, {'hourly': ','.join(score.VARS), 'models': m})['hourly'])
    keys = sorted(s for s in oslots if s in mslots['meteofrance_arome_france'])
    X = np.array([modeles.rain_row(s, mslots, hctx, models) for s in keys])
    y = np.array([oslots[s] >= score.RAIN_SLOT for s in keys]).astype(int)
    single = {m: [None if s not in mslots[m] else mslots[m][s] >= score.RAIN_SLOT for s in keys] for m in models}
    rows.append(run('2 prochaines heures : pluie', 'pluie', keys, X, y, single, thr=modeles.RAIN_2H_THRESHOLD))

    rep = [f'# GRESIL est-il plus fiable que les modèles météo ? ({score.NOM})\n',
           f'Période : {score.START} → {score.END}, station {score.STATION_NOM}. Chaque mois est prévu par un GRESIL '
           'entraîné sur tous les autres mois : chaque prévision notée est faite sans avoir vu son mois. '
           'GRESIL et chaque modèle météo sont notés sur exactement les mêmes cas.\n',
           '- **Meilleur modèle seul** : celui qui fait le mieux sur toute la période, choisi après coup (avantage au modèle).',
           '- **Écart sûr à 90 %** : GRESIL moins le meilleur modèle, en retirant des mois entiers au hasard 2 000 fois '
           '(positif = GRESIL meilleur, y compris pour les erreurs). Si l\'intervalle ne passe pas par 0, la différence est sûre.',
           '- **Mois gagnés** : mois où GRESIL fait mieux que ce modèle.\n',
           '| Prévision | Mesure | GRESIL | Meilleur modèle seul | Écart sûr à 90 % | Mois gagnés | Verdict | Cas |',
           '|---|---|---|---|---|---|---|---|']
    rep += [line(r) for r in rows]
    rep += ['\n## Mois par mois (GRESIL / meilleur modèle seul)\n']
    for r in rows:
        k, s = r['kind'], r['sign']
        cells = ', '.join(f"{(m // 12)}-{m % 12 + 1:02d} {fmt(k, s * a if k == 'reg' else a)}/{fmt(k, s * b if k == 'reg' else b)}"
                          for m, (a, b) in r['by_month'].items())
        rep.append(f"- {r['label']} : {cells}")
    open(os.path.join(score.SORTIE, 'ETUDE.md'), 'w').write('\n'.join(rep) + '\n')
    print('\n'.join(rep[:len(rows) + 8]))


if __name__ == '__main__':
    main()
