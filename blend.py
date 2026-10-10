"""Mega-model: learn from all weather models at once to predict the general condition (sun / mixed / overcast / rain).

Honest test: leave-one-month-out. Each month is predicted by a blend trained on all other months only.
All variants are scored on the same test months (the last 13 months), so the numbers compare directly.

Variants (each adds to the previous one):
  A. 1 year of training, sunlight ratio + rain of each model, hour and season
  B. same features, 2.7 years of training
  C. + every parameter of each model (cloud cover, humidity, wind, gusts, pressure, temperature)
  D. + what was observed at the station when the forecast was made (persistence)
  E. (half-days only) one model for all lead times J+1..J+7, lead as a feature

Usage: .venv/bin/python blend.py   (needs the cache filled by score.py)
"""
import math
from datetime import date, timedelta
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
import score

C = np.zeros((4, 4))
for i in range(4):
    for j in range(4):
        C[i, j] = 1 if i == j else score.CREDIT.get((i, j), 0)

TEST_FROM = date(2025, 10, 1)       # scored months
ONE_YEAR_FROM = date(2025, 10, 1)   # variant A trains only inside this year
BASE = ['ratio', 'pluie_mm']
ALL = ['ratio', 'pluie_mm', 'cloud', 'humidite', 'vent', 'rafales', 'pression', 'temperature']


def summary(pred, obs):
    pred, obs = np.asarray(pred), np.asarray(obs)
    cond = 100 * np.mean(C[pred, obs])
    seen = lambda c: 100 * np.mean(pred[obs == c] == c) if (obs == c).any() else float('nan')
    false_rain = 100 * np.mean(obs[pred == 3] != 3) if (pred == 3).any() else float('nan')
    return cond, 100 * np.mean(pred == obs), seen(0), seen(2), seen(3), false_rain


def day_of(k):
    return (k if hasattr(k, 'year') and not isinstance(k, tuple) else k[0])


def month_id(d):
    d = d.date() if hasattr(d, 'date') and callable(d.date) else d
    return d.year * 12 + d.month


def calendar(k):
    if isinstance(k, tuple):
        doy, part = k[0].timetuple().tm_yday, float(k[1] == 'aprem')
    else:
        loc = k.astimezone(score.PARIS)
        doy, part = loc.timetuple().tm_yday, loc.hour
    return [part, math.sin(2 * math.pi * doy / 365), math.cos(2 * math.pi * doy / 365)]


def features(k, fcs, feats, persist, lead):
    row = calendar(k)
    for m in fcs:
        f = fcs[m].get(k, {})
        for v in feats:
            x = f.get(v)
            row.append(np.nan if x is None else float(x))
    if persist is not None:
        row += persist(k, lead)
    return row


def run_cv(X, y, months, test_mask, train_mask):
    """Leave-one-month-out on the test months; training restricted by train_mask."""
    pred = np.full(len(y), -1)
    for mo in np.unique(months[test_mask]):
        te = test_mask & (months == mo)
        tr = train_mask & (months != mo)
        clf = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, max_leaf_nodes=15,
                                             l2_regularization=1.0, random_state=0)
        # Columns with fewer than 2 distinct values (parameter a model never gives) crash the binning
        keep = [j for j in range(X.shape[1]) if len(np.unique(X[tr, j][~np.isnan(X[tr, j])])) >= 2]
        clf.fit(X[tr][:, keep], y[tr])
        p = np.zeros((te.sum(), 4))
        p[:, clf.classes_] = clf.predict_proba(X[te][:, keep])
        pred[te] = np.argmax(p @ C.T, axis=1)  # category with the best expected credit
    return pred[test_mask]


def table(title, rows, n, out):
    rows.sort(key=lambda r: -r[1][0])
    out.append(f'### {title} ({n} cas testés)\n')
    out.append('| Prévision | Condition /100 | Exactes | Soleil vu | Couvert vu | Pluie vue | Fausses alertes pluie |')
    out.append('|---|---|---|---|---|---|---|')
    for name, (cond, ex, su, ov, ra, fa) in rows:
        out.append(f'| {name} | {cond:.1f} | {ex:.0f}% | {su:.0f}% | {ov:.0f}% | {ra:.0f}% | {fa:.0f}% |')
    out.append('')
    print('\n'.join(out[-len(rows) - 4:]), flush=True)


def add_cloud(fc_by_key):
    for f in fc_by_key.values():
        f.setdefault('cloud', None)
    return fc_by_key


def hourly_with_cloud(H, suffix):
    hours = score.forecast_hours(H, suffix)
    cc = H.get('cloud_cover' + suffix)
    if cc:
        for (t, f), c in zip(hours.items(), cc):
            f['cloud'] = c
    return hours


def blocks_with_cloud(hours):
    blocks = score.to_blocks(hours)
    acc = {}
    for t, h in hours.items():
        loc = t.astimezone(score.PARIS)
        part = 'matin' if 7 <= loc.hour <= 12 else 'aprem' if 13 <= loc.hour <= 18 else None
        if part and h.get('cloud') is not None:
            acc.setdefault((loc.date(), part), []).append(h['cloud'])
    for k, b in blocks.items():
        b['cloud'] = sum(acc[k]) / len(acc[k]) if k in acc else None
    return blocks


def evaluate(title, fcs_by_lead, obs, persist, out, pooled=False):
    """fcs_by_lead: {lead: {model: {key: forecast}}}."""
    leads = sorted(fcs_by_lead)
    variants = {}
    singles_rows = []
    for lead in leads:
        fcs = fcs_by_lead[lead]
        keys = [k for k in sorted(obs) if obs[k]['cat'] is not None
                and sum(fcs[m].get(k, {}).get('cat') is not None for m in fcs) >= max(1, len(fcs) // 2)]
        y = np.array([obs[k]['cat'] for k in keys])
        days = [day_of(k) for k in keys]
        days = [d.date() if hasattr(d, 'hour') else d for d in days]
        months = np.array([d.year * 12 + d.month for d in days])
        test = np.array([d >= TEST_FROM for d in days])
        one_year = np.array([d >= ONE_YEAR_FROM for d in days])
        everything = np.ones(len(y), bool)
        XA = np.array([features(k, fcs, BASE, None, lead) for k in keys])
        XC = np.array([features(k, fcs, ALL, None, lead) for k in keys])
        XD = np.array([features(k, fcs, ALL, persist, lead) for k in keys])
        variants.setdefault('A', []).append((run_cv(XA, y, months, test, one_year), y[test]))
        variants.setdefault('B', []).append((run_cv(XA, y, months, test, everything), y[test]))
        variants.setdefault('C', []).append((run_cv(XC, y, months, test, everything), y[test]))
        variants.setdefault('D', []).append((run_cv(XD, y, months, test, everything), y[test]))
        variants.setdefault('_data', []).append((XD, y, months, test, lead))
        # Single models on the same test cases
        for m in fcs:
            cats = [fcs[m].get(k, {}).get('cat') for k, t in zip(keys, test) if t]
            ok = [i for i, c in enumerate(cats) if c is not None]
            if len(ok) > 0.9 * test.sum():
                singles_rows.append((lead, m, summary([cats[i] for i in ok], y[test][ok])))
        singles_rows.append((lead, '« toujours soleil »', summary([0] * test.sum(), y[test])))

    if pooled:
        # E: one model over all leads (features aligned: same model list for every lead, lead as a feature)
        width = max(d[0].shape[1] for d in variants['_data'])
        X = np.vstack([np.hstack([np.pad(d[0], ((0, 0), (0, width - d[0].shape[1])), constant_values=np.nan),
                                  np.full((len(d[1]), 1), d[4])]) for d in variants['_data']])
        y = np.concatenate([d[1] for d in variants['_data']])
        months = np.concatenate([d[2] for d in variants['_data']])
        test = np.concatenate([d[3] for d in variants['_data']])
        lead_col = X[:, -1]
        predE = run_cv(X, y, months, test, np.ones(len(y), bool))
        lead_test = lead_col[test]
        variants['E'] = [(predE[lead_test == L], y[test][lead_test == L]) for L in leads]

    names = {'A': 'A. 1 an, soleil + pluie', 'B': 'B. 2,7 ans, soleil + pluie', 'C': 'C. + tous les paramètres',
             'D': 'D. + observations du moment', 'E': 'E. + un seul modèle pour J+1 à J+7'}
    for i, lead in enumerate(leads):
        rows = [(f'**{names[v]}**', summary(*variants[v][i])) for v in 'ABCDE' if v in variants]
        rows += [(m, s) for L, m, s in singles_rows if L == lead]
        table(title + (f' à J+{lead}' if len(leads) > 1 else ''), rows, len(variants['A'][i][1]), out)


def make_persist(obs, hourly):
    """Observed values surely known when the forecast was issued (run started ~`lead` days before the target):
    hourly → `lead` days + 6 h earlier; half-days → the half-day just before, `lead` days earlier."""
    def persist(k, lead):
        if hourly:
            prev = k - timedelta(days=lead, hours=6)
        elif k[1] == 'aprem':
            prev = (k[0] - timedelta(days=lead), 'matin')
        else:
            prev = (k[0] - timedelta(days=lead + 1), 'aprem')
        o = obs.get(prev)
        if not o:
            return [np.nan] * 4
        g = lambda v: np.nan if o.get(v) is None else float(o[v])
        return [g('ratio'), g('pluie_mm'), g('humidite'), np.nan if o['cat'] is None else float(o['cat'])]
    return persist


if __name__ == '__main__':
    obs = score.load_obs()
    out = ['# Mega-modèle : combiner tous les modèles\n',
           f'Test honnête : chaque mois de {TEST_FROM} à {score.END} est prédit par un mélange entraîné sans ce mois. '
           'Toutes les variantes et tous les modèles sont notés sur exactement les mêmes cas.\n']

    hv = ','.join(f'{v}_previous_day1' for v in score.VARS)
    fcs = {}
    for m in score.HOURLY_MODELS:
        d = score.api(score.PREVIOUS, {'hourly': hv, 'models': m})
        if d:
            fcs[m] = hourly_with_cloud(d['hourly'], '_previous_day1')
    evaluate('La veille pour le lendemain, heure par heure', {1: fcs}, obs, make_persist(obs, True), out)

    oblocks = score.to_blocks(obs)
    hv = ','.join(f'{v}_previous_day{d}' for d in range(1, 8) for v in score.VARS)
    raw = {m: score.api(score.PREVIOUS, {'hourly': hv, 'models': m}) for m in score.TREND_MODELS}
    by_lead = {}
    for lead in range(1, 8):
        # Same model list at every lead (missing leads → empty), so pooled features line up
        by_lead[lead] = {m: blocks_with_cloud(hourly_with_cloud(d['hourly'], f'_previous_day{lead}'))
                         for m, d in raw.items() if d}
    evaluate('Créneaux matin / après-midi', by_lead, oblocks, make_persist(oblocks, False), out, pooled=True)

    open(score.os.path.join(score.ROOT, 'MEGA-MODELE.md'), 'w').write('\n'.join(out))
