"""Train and freeze the production models (see modeles.py), and measure each one honestly first.

Honest check: train on everything before 2025-10-01, test on 2025-10-01 → end, compare with the best weather
model alone on the same cases. Then retrain on the whole period and save to modeles/*.joblib.

Usage: OMP_NUM_THREADS=4 nice -n 10 .venv/bin/python figer.py   (cache only, writes FIGE.md)
"""
import os
from datetime import date, timedelta
import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
import blend
import modeles
import score

OUT = score.MODELES
SPLIT = score.TEST_FROM
# Recent months weigh more only where it helped (recency.py: J+1 half-days +0.9 point with 12 months;
# no gain hourly nor at J+3)
BLOCK_HALF_LIFE = {1: 12}
REPORT = ['# Modèles figés\n',
          f'Test honnête : entraîné avant le {SPLIT}, noté du {SPLIT} au {score.END}, '
          'comparé au meilleur modèle météo seul sur les mêmes cas. Puis réentraîné sur toute la période.\n',
          '| Modèle figé | Mesure | Figé | Meilleur modèle seul | Cas testés |', '|---|---|---|---|---|']


def day(k):
    return k[0] if isinstance(k, tuple) else k.date()


def fit(kind, X, y, w=None):
    keep = [j for j in range(X.shape[1]) if len(np.unique(X[:, j][~np.isnan(X[:, j])])) >= 2]
    common = dict(max_iter=300, learning_rate=0.05, max_leaf_nodes=15, l2_regularization=1.0, random_state=0)
    est = HistGradientBoostingClassifier(**common) if kind == 'cls' else HistGradientBoostingRegressor(**common)
    est.fit(X[:, keep], y, sample_weight=w)
    return est, keep


def predict_condition(est, keep, X):
    p = np.zeros((len(X), 4))
    p[:, est.classes_] = est.predict_proba(X[:, keep])
    return np.argmax(p @ blend.C.T, axis=1)


def csi(pred, y):
    hit, miss, fa = np.sum(pred & y), np.sum(~pred & y), np.sum(pred & ~y)
    return 100 * hit / max(1, hit + miss + fa)


def recency(keys, until, half_life):
    """Weight 0.5 ** (age in months / half-life), age counted back from `until` (None → equal weights)."""
    if half_life is None:
        return None
    age = np.array([(until - day(k)).days / 30.4 for k in keys])
    return 0.5 ** (np.clip(age, 0, None) / half_life)


def freeze(name, kind, keys, X, y, singles, models, extra=None, half_life=None):
    """singles: {model: forecast value per key (None if missing)} for the baseline."""
    test = np.array([day(k) >= SPLIT for k in keys])
    tr_keys = [k for k, t in zip(keys, test) if not t]
    est, keep = fit('cls' if kind in ('condition', 'pluie') else 'reg', X[~test], y[~test],
                    recency(tr_keys, SPLIT, half_life))
    if kind == 'condition':
        got = blend.summary(predict_condition(est, keep, X[test]), y[test])[0]
        measure, fmt, better = 'condition /100', '{:.1f}', max
    elif kind == 'pluie':
        thr = extra or 0.5
        got = csi(est.predict_proba(X[test][:, keep])[:, 1] >= thr, y[test].astype(bool))
        measure, fmt, better = 'réussite pluie %', '{:.1f}', max
    else:
        got = np.mean(np.abs(est.predict(X[test][:, keep]) - y[test]))
        measure, fmt, better = 'erreur moyenne', '{:.2f}', min
    base = {}
    for m, vals in singles.items():
        v = [vals[i] for i in np.where(test)[0]]
        ok = [i for i, x in enumerate(v) if x is not None]
        if len(ok) < 0.9 * len(v):
            continue
        yt = y[test][ok]
        if kind == 'condition':
            base[m] = blend.summary([v[i] for i in ok], yt)[0]
        elif kind == 'pluie':
            base[m] = csi(np.array([v[i] for i in ok]), yt.astype(bool))
        else:
            base[m] = np.mean(np.abs(np.array([v[i] for i in ok]) - yt))
    bm = better(base, key=base.get) if base else None
    REPORT.append(f'| {name} | {measure} | **{fmt.format(got)}** | '
                  + (f'{fmt.format(base[bm])} ({bm})' if bm else '-') + f' | {test.sum()} |')
    print(REPORT[-1], flush=True)
    est, keep = fit('cls' if kind in ('condition', 'pluie') else 'reg', X, y,
                    recency(keys, max(day(k) for k in keys), half_life))
    joblib.dump({'est': est, 'keep': keep, 'models': models, 'kind': kind, 'threshold': extra,
                 'half_life': half_life},
                os.path.join(OUT, f'{name}.joblib'), compress=3)


def build(fcs, obs, models, target, valid):
    keys = [k for k in sorted(obs) if valid(obs[k], k)
            and sum(fcs[m].get(k, {}).get('pluie_mm') is not None for m in models) >= len(models) // 2]
    X = np.array([modeles.row(k, fcs, models) for k in keys])
    y = np.array([target(obs[k]) for k in keys])
    return keys, X, y


def main():
    os.makedirs(OUT, exist_ok=True)
    obs = score.load_obs()

    # ---------- hourly, the day before ----------
    hv = ','.join(f'{v}_previous_day1' for v in score.VARS)
    models = score.HOURLY_MODELS
    fcs = {m: modeles.hours(score.api(score.PREVIOUS, {'hourly': hv, 'models': m})['hourly'], '_previous_day1')
           for m in models}
    single = lambda keys, v: {m: [fcs[m].get(k, {}).get(v) for k in keys] for m in models}
    keys, X, y = build(fcs, obs, models, lambda o: o['cat'], lambda o, k: o['cat'] is not None)
    freeze('heure_condition', 'condition', keys, X, y, single(keys, 'cat'), models)
    keys, X, y = build(fcs, obs, models, lambda o: o['pluie_mm'] >= score.RAIN_HOUR, lambda o, k: o['pluie_mm'] is not None)
    rain_single = {m: [None if v is None else v >= score.RAIN_HOUR for v in vals]
                   for m, vals in single(keys, 'pluie_mm').items()}
    freeze('heure_pluie', 'pluie', keys, X, y.astype(int), rain_single, models, extra=0.5)
    for v in ('temperature', 'vent', 'rafales'):
        keys, X, y = build(fcs, obs, models, lambda o, v=v: o[v], lambda o, k, v=v: o.get(v) is not None)
        freeze(f'heure_{v}', 'reg', keys, X, y, single(keys, v), models)

    # ---------- half-days, 1 to 7 days ahead ----------
    oblocks = score.to_blocks(obs)
    hv = ','.join(f'{v}_previous_day{d}' for d in range(1, 8) for v in score.VARS)
    models = score.TREND_MODELS
    raw = {m: score.api(score.PREVIOUS, {'hourly': hv, 'models': m}) for m in models}
    for lead in range(1, 8):
        fcs = {m: modeles.blocks(modeles.hours(d['hourly'], f'_previous_day{lead}')) for m, d in raw.items()}
        single = lambda keys, v: {m: [fcs[m].get(k, {}).get(v) for k in keys] for m in models}
        keys, X, y = build(fcs, oblocks, models, lambda o: o['cat'], lambda o, k: o['cat'] is not None)
        freeze(f'bloc{lead}_condition', 'condition', keys, X, y, single(keys, 'cat'), models,
               half_life=BLOCK_HALF_LIFE.get(lead))
        for v in ('temperature', 'rafales'):
            keys, X, y = build(fcs, oblocks, models, lambda o, v=v: o[v], lambda o, k, v=v: o.get(v) is not None)
            freeze(f'bloc{lead}_{v}', 'reg', keys, X, y, single(keys, v), models, half_life=BLOCK_HALF_LIFE.get(lead))

    # ---------- rain in the next 2 hours, 20-minute slots ----------
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
    freeze('pluie2h', 'pluie', keys, X, y, single, models, extra=modeles.RAIN_2H_THRESHOLD)

    open(os.path.join(score.SORTIE, 'FIGE.md'), 'w').write('\n'.join(REPORT) + '\n')


if __name__ == '__main__':
    main()
