"""Test: give more weight to recent months when training the mega-model (general condition).

Weight of a training month = 0.5 ** (distance in months to the predicted month / half-life).
In leave-one-month-out, the "distance" mimics production, where the newest data is closest to the forecast.
Features = variant C of blend.py (every parameter of every model + hour and season).

Usage: OMP_NUM_THREADS=4 nice -n 15 .venv/bin/python recency.py   (cache only, writes RECENCE.md)
"""
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
import blend
import score

HALF_LIVES = [None, 18, 12, 6, 3]  # months; None = all months weigh the same


def run_cv_weighted(X, y, months, test, half_life):
    pred = np.full(len(y), -1)
    for mo in np.unique(months[test]):
        te = test & (months == mo)
        tr = months != mo
        w = np.ones(tr.sum()) if half_life is None else 0.5 ** (np.abs(months[tr] - mo) / half_life)
        keep = [j for j in range(X.shape[1]) if len(np.unique(X[tr, j][~np.isnan(X[tr, j])])) >= 2]
        clf = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, max_leaf_nodes=15,
                                             l2_regularization=1.0, random_state=0)
        clf.fit(X[tr][:, keep], y[tr], sample_weight=w)
        p = np.zeros((te.sum(), 4))
        p[:, clf.classes_] = clf.predict_proba(X[te][:, keep])
        pred[te] = np.argmax(p @ blend.C.T, axis=1)
    return pred[test]


def dataset(fcs, obs):
    keys = [k for k in sorted(obs) if obs[k]['cat'] is not None
            and sum(fcs[m].get(k, {}).get('cat') is not None for m in fcs) >= max(1, len(fcs) // 2)]
    y = np.array([obs[k]['cat'] for k in keys])
    days = [blend.day_of(k) for k in keys]
    days = [d.date() if hasattr(d, 'hour') else d for d in days]
    months = np.array([d.year * 12 + d.month for d in days])
    test = np.array([d >= blend.TEST_FROM for d in days])
    X = np.array([blend.features(k, fcs, blend.ALL, None, 1) for k in keys])
    return X, y, months, test


def evaluate(title, fcs, obs, out):
    X, y, months, test = dataset(fcs, obs)
    out.append(f'### {title} ({test.sum()} cas testés)\n')
    out.append('| Poids des mois | Condition /100 | Exactes | Soleil vu | Couvert vu | Pluie vue | Fausses alertes pluie |')
    out.append('|---|---|---|---|---|---|---|')
    for h in HALF_LIVES:
        cond, ex, su, ov, ra, fa = blend.summary(run_cv_weighted(X, y, months, test, h), y[test])
        name = 'tous pareils' if h is None else f'demi-vie {h} mois'
        out.append(f'| {name} | {cond:.1f} | {ex:.0f}% | {su:.0f}% | {ov:.0f}% | {ra:.0f}% | {fa:.0f}% |')
        print(out[-1], flush=True)
    out.append('')


if __name__ == '__main__':
    obs = score.load_obs()
    out = ['# Donner plus de poids aux mois récents\n',
           'Demi-vie 6 mois = un mois vieux de 6 mois compte moitié moins que le mois le plus proche. '
           f'Test honnête sur {blend.TEST_FROM} → {score.END}, un mois laissé de côté à chaque fois.\n']
    hv = ','.join(f'{v}_previous_day1' for v in score.VARS)
    fcs = {m: blend.hourly_with_cloud(score.api(score.PREVIOUS, {'hourly': hv, 'models': m})['hourly'], '_previous_day1')
           for m in score.HOURLY_MODELS}
    evaluate('La veille pour le lendemain, heure par heure', fcs, obs, out)

    oblocks = score.to_blocks(obs)
    hv = ','.join(f'{v}_previous_day{d}' for d in range(1, 8) for v in score.VARS)
    raw = {m: score.api(score.PREVIOUS, {'hourly': hv, 'models': m}) for m in score.TREND_MODELS}
    for lead in (1, 3, 5):
        fcs = {m: blend.blocks_with_cloud(blend.hourly_with_cloud(d['hourly'], f'_previous_day{lead}'))
               for m, d in raw.items()}
        evaluate(f'Créneaux matin / après-midi à J+{lead}', fcs, oblocks, out)

    open(score.os.path.join(score.SORTIE, 'RECENCE.md'), 'w').write('\n'.join(out))
