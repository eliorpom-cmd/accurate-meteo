"""Temperature sub-model: learn from all weather models at once to predict the 2 m temperature
measured at GRENOBLE-CEA-RADOME, hour by hour.

Two experiments:
  1. The day before (lead 1), HOURLY_MODELS.
  2. Leads 1..7, TREND_MODELS: one regression per lead vs one pooled model with the lead as a feature.

Honest test: leave-one-month-out. Each test month (2025-10 → end) is predicted by a model trained on all other
months (training data from 2024-02-01). Sub-model, single models, plain average and per-model bias correction
are all scored on exactly the same hours.

Only cached API answers are used (no download): a model whose cache is incomplete is skipped.

Usage: OMP_NUM_THREADS=2 .venv/bin/python submodel_temperature.py   (writes SOUS-MODELE-TEMPERATURE.md)
"""
import hashlib, json, math, os, time
from datetime import date, datetime, timedelta, timezone
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
import score

TEST_FROM = score.TEST_FROM
T0 = datetime(2024, 2, 1, tzinfo=timezone.utc)
T1 = datetime(2026, 10, 9, tzinfo=timezone.utc)
N = int((T1 - T0).total_seconds() // 3600)
GRID = [T0 + timedelta(hours=i) for i in range(N)]
VARS = score.VARS  # temperature first, then humidity, wind, gusts, direction, pressure, sunlight, cloud, rain
LOG = []


def log(*a):
    s = ' '.join(str(x) for x in a)
    LOG.append(s)
    print(s, flush=True)


# ---------- data (cache only) ----------

def cached(base, params):
    """True if every chunk of this call is already in data/cache/ (same path as score.api_chunk)."""
    for s, e in score.CHUNKS:
        key = base.split('//')[1].split('.')[0] + json.dumps(params, sort_keys=True) + s + e
        path = os.path.join(score.CACHE, params.get('models', 'obs') + '_'
                            + hashlib.md5(key.encode()).hexdigest()[:10] + '.json')
        if not os.path.exists(path):
            return False
    return True


def load_models(models, leads):
    """{lead: {model: array (N, len(VARS))}} on the hourly UTC grid, NaN where missing."""
    hv = ','.join(f'{v}_previous_day{d}' for d in leads for v in VARS)
    out = {L: {} for L in leads}
    for m in models:
        params = {'hourly': hv, 'models': m}
        if not cached(score.PREVIOUS, params):
            log('  skipped (not cached):', m)
            continue
        d = score.api(score.PREVIOUS, params)
        if not d:
            continue
        H = d['hourly']
        idx = np.array([int((score.utc(t) - T0).total_seconds() // 3600) for t in H['time']])
        ok = (idx >= 0) & (idx < N)
        for L in leads:
            a = np.full((N, len(VARS)), np.nan)
            for j, v in enumerate(VARS):
                col = H.get(f'{v}_previous_day{L}')
                if col is not None:
                    a[idx[ok], j] = np.array([np.nan if x is None else x for x in col], float)[ok]
            if np.isfinite(a[:, 0]).sum() > 1000:
                out[L][m] = a
    return out


def load_obs():
    if not cached(score.SATELLITE, {'hourly': 'shortwave_radiation'}):
        raise SystemExit('satellite cache missing: refusing to download')
    obs = score.load_obs()
    a = np.full((N, 4), np.nan)  # temperature, humidity, wind, pressure
    for t, o in obs.items():
        i = int((t - T0).total_seconds() // 3600)
        if 0 <= i < N:
            for j, k in enumerate(('temperature', 'humidite', 'vent', 'pression')):
                if o.get(k) is not None:
                    a[i, j] = o[k]
    return a


# ---------- features ----------

LOCAL = [t.astimezone(score.PARIS) for t in GRID]
HOUR = np.array([t.hour for t in LOCAL], float)
DOY = np.array([t.timetuple().tm_yday for t in LOCAL], float)
MONTH = np.array([t.year * 12 + t.month for t in GRID])
DAY = np.array([t.date() for t in GRID])
SEASON_M = np.array([t.month for t in LOCAL])


def shift(a, h):
    """Value h hours earlier (NaN before the start of the grid)."""
    out = np.full_like(a, np.nan)
    out[h:] = a[:-h]
    return out


def build_X(fc, obs, lead):
    """Calendar + every parameter of every model + persistence known when the forecast was issued."""
    cols = [HOUR, np.sin(2 * math.pi * DOY / 365), np.cos(2 * math.pi * DOY / 365)]
    names = ['heure', 'sin_jour', 'cos_jour']
    for m, a in fc.items():
        for j, v in enumerate(VARS):
            cols.append(a[:, j])
            names.append(f'{m}:{v}')
    # Persistence: observed `lead` days + 6 h before the target (surely known at issue time)
    back = 24 * lead + 6
    for j, k in enumerate(('T', 'U', 'vent', 'P')):
        cols.append(shift(obs[:, j], back))
        names.append(f'obs_{k}_-{back}h')
    # Observed temperature at the same clock hour, one day before issue
    cols.append(shift(obs[:, 0], 24 * (lead + 1)))
    names.append(f'obs_T_-{24 * (lead + 1)}h')
    # Recent error of the plain model average, over the 24 h ending at the last known observation
    mean_fc = np.nanmean(np.column_stack([a[:, 0] for a in fc.values()]), axis=1)
    err = mean_fc - obs[:, 0]
    e = np.where(np.isfinite(err), err, 0.0)
    n = np.isfinite(err).astype(float)
    ce, cn = np.concatenate([[0], np.cumsum(e)]), np.concatenate([[0], np.cumsum(n)])
    roll = np.full(N, np.nan)
    i = np.arange(N)
    lo, hi = np.clip(i - back - 23, 0, N), np.clip(i - back + 1, 0, N)
    cnt = cn[hi] - cn[lo]
    roll[cnt > 6] = ((ce[hi] - ce[lo])[cnt > 6]) / cnt[cnt > 6]
    cols.append(roll)
    names.append('erreur_recente_moyenne')
    return np.column_stack(cols), names


# ---------- model ----------

def fit_predict(X, y, tr, te, loss):
    keep = [j for j in range(X.shape[1]) if len(np.unique(X[tr, j][np.isfinite(X[tr, j])])) >= 2]
    reg = HistGradientBoostingRegressor(loss=loss, max_iter=300, learning_rate=0.05, max_leaf_nodes=31,
                                        l2_regularization=1.0, early_stopping=False, random_state=0)
    reg.fit(X[tr][:, keep], y[tr])
    return reg.predict(X[te][:, keep]), reg, keep


def loo(X, y, rows, months, loss):
    """Leave-one-month-out prediction of every test row; rows = usable rows (target known)."""
    pred = np.full(len(y), np.nan)
    test = rows & (DAY >= TEST_FROM)
    for mo in np.unique(months[test]):
        te = test & (months == mo)
        tr = rows & (months != mo)
        pred[te] = fit_predict(X, y, tr, te, loss)[0]
    return pred


def eval_set(fc, obs):
    """Test hours with an observation where every comparable model has a temperature.
    Comparable = temperature on ≥ 90 % of the observed test hours."""
    test = np.isfinite(obs[:, 0]) & (DAY >= TEST_FROM)
    comp = [m for m, a in fc.items() if np.isfinite(a[test, 0]).mean() >= 0.9]
    mask = test.copy()
    for m in comp:
        mask &= np.isfinite(fc[m][:, 0])
    return mask, comp


def metrics(p, o):
    e = p - o
    return np.mean(np.abs(e)), np.mean(e), 100 * np.mean(np.abs(e) <= 1), 100 * np.mean(np.abs(e) <= 2)


def baselines(fc, obs, comp, mask):
    """Single models, plain average, per-model bias correction (learned on the other months), corrected average."""
    out = {}
    o = obs[:, 0]
    for m in comp:
        out[m] = fc[m][:, 0].copy()
    out['moyenne des modèles'] = np.mean(np.column_stack([fc[m][:, 0] for m in comp]), axis=1)
    corr = {m: np.full(N, np.nan) for m in comp}
    for mo in np.unique(MONTH[mask]):
        te = mask & (MONTH == mo)
        for m in comp:
            f = fc[m][:, 0]
            tr = (MONTH != mo) & np.isfinite(f) & np.isfinite(o)
            corr[m][te] = f[te] - np.mean(f[tr] - o[tr])
    for m in comp:
        out[m + ' (biais corrigé)'] = corr[m]
    out['moyenne des modèles (biais corrigés)'] = np.mean(np.column_stack([corr[m] for m in comp]), axis=1)
    return out


def subsets(mask):
    winter = np.isin(SEASON_M, (12, 1, 2))
    summer = np.isin(SEASON_M, (6, 7, 8))
    inversion = winter & (HOUR >= 6) & (HOUR <= 9)
    return {'toutes': mask, 'hiver (DJF)': mask & winter, 'été (JJA)': mask & summer,
            'matins d\'hiver 6-9 h': mask & inversion}


def table(title, preds, obs, mask, out, top=None):
    o = obs[:, 0]
    rows = sorted(((n, metrics(p[mask], o[mask])) for n, p in preds.items()), key=lambda r: r[1][0])
    if top:
        rows = [r for r in rows if r[0].startswith('**')] + [r for r in rows if not r[0].startswith('**')][:top]
    out.append(f'### {title} ({mask.sum()} heures)\n')
    out.append('| Prévision | Erreur moyenne | Biais | à ±1 °C | à ±2 °C |')
    out.append('|---|---|---|---|---|')
    for n, (mae, b, p1, p2) in rows:
        out.append(f'| {n} | {mae:.2f} °C | {b:+.2f} °C | {p1:.0f} % | {p2:.0f} % |')
    out.append('')


def breakdown(title, preds, obs, mask, out):
    o = obs[:, 0]
    subs = subsets(mask)
    out.append(f'### {title} : erreur moyenne par saison\n')
    out.append('| Prévision | ' + ' | '.join(f'{k} ({v.sum()} h)' for k, v in subs.items()) + ' |')
    out.append('|---|' + '---|' * len(subs))
    for n, p in preds.items():
        out.append(f'| {n} | ' + ' | '.join(f'{np.mean(np.abs(p[s] - o[s])):.2f}' for s in subs.values()) + ' |')
    out.append('')


def group_importance(X, y, names, rows, mo, loss, groups):
    """Permutation importance by group of columns (all parameters of a model together), one fold."""
    te = rows & (MONTH == mo)
    tr = rows & (MONTH != mo)
    _, reg, keep = fit_predict(X, y, tr, te, loss)
    Xt = X[te][:, keep]
    base = np.mean(np.abs(reg.predict(Xt) - y[te]))
    rng = np.random.default_rng(0)
    res = []
    kn = [names[j] for j in keep]
    for g, test_fn in groups.items():
        cols = [i for i, n in enumerate(kn) if test_fn(n)]
        if not cols:
            continue
        d = []
        for _ in range(3):
            Xp = Xt.copy()
            perm = rng.permutation(len(Xp))
            Xp[:, cols] = Xp[perm][:, cols]
            d.append(np.mean(np.abs(reg.predict(Xp) - y[te])) - base)
        res.append((g, float(np.mean(d))))
    return base, sorted(res, key=lambda r: -r[1])


# ---------- main ----------

if __name__ == '__main__':
    t_start = time.time()
    obs = load_obs()
    y = obs[:, 0]
    rows = np.isfinite(y)
    out = ['# Sous-modèle température\n',
           f'Cible : température à 2 m mesurée à {score.STATION_NOM}, heure par heure. Test honnête : chaque mois de '
           f'{TEST_FROM} au {score.END} est prédit par un modèle entraîné sur tous les autres mois (données depuis le '
           f'{score.START}). Toutes les prévisions sont notées sur exactement les mêmes heures.\n',
           'Sous-modèle : gradient boosting (scikit-learn, 300 arbres) avec la température et les autres paramètres '
           '(humidité, vent, rafales, direction, pression, soleil, nuages, pluie) de chaque modèle, l\'heure, la saison, '
           'et ce qui était observé à la station au moment de la prévision (échéance + 6 h avant) : température, '
           'humidité, vent, pression, température à la même heure la veille, erreur récente de la moyenne des modèles.\n',
           'Correction de biais : chaque modèle moins son erreur moyenne apprise sur les mois d\'entraînement.\n']

    # ---- 1. The day before, HOURLY_MODELS ----
    log('lead 1, hourly models…')
    fc1 = load_models(score.HOURLY_MODELS, [1])[1]
    X1, names1 = build_X(fc1, obs, 1)
    mask1, comp1 = eval_set(fc1, obs)
    log(f'  {len(fc1)} models, {X1.shape[1]} features, {mask1.sum()} test hours, comparable: {len(comp1)}')
    preds = {}
    for loss in ('squared_error', 'absolute_error'):
        t = time.time()
        preds[f'**sous-modèle ({loss})**'] = loo(X1, y, rows, MONTH, loss)
        log(f'  {loss}: MAE {np.mean(np.abs(preds[f"**sous-modèle ({loss})**"][mask1] - y[mask1])):.3f}'
            f' ({time.time() - t:.0f} s)')
    best_loss = min(('squared_error', 'absolute_error'),
                    key=lambda l: np.mean(np.abs(preds[f'**sous-modèle ({l})**'][mask1] - y[mask1])))
    base1 = baselines(fc1, obs, comp1, mask1)
    out.append('## 1. La veille pour le lendemain (J+1), heure par heure\n')
    out.append('Modèles comparés : ' + ', '.join(comp1) + '.\n')
    table('Toutes les heures testées', {**preds, **base1}, obs, mask1, out)
    singles = [m for m in comp1]
    best1 = min(singles, key=lambda m: np.mean(np.abs(base1[m][mask1] - y[mask1])))
    best1c = min(singles, key=lambda m: np.mean(np.abs(base1[m + ' (biais corrigé)'][mask1] - y[mask1])))
    sel = {f'**sous-modèle ({best_loss})**': preds[f'**sous-modèle ({best_loss})**'], best1: base1[best1],
           best1c + ' (biais corrigé)': base1[best1c + ' (biais corrigé)'],
           'moyenne des modèles': base1['moyenne des modèles'],
           'moyenne des modèles (biais corrigés)': base1['moyenne des modèles (biais corrigés)']}
    breakdown('J+1', sel, obs, mask1, out)

    # Permutation importance on one winter fold (January 2026), grouped by model
    groups = {m: (lambda n, m=m: n.startswith(m + ':')) for m in fc1}
    groups['observations à la station'] = lambda n: n.startswith('obs_') or n == 'erreur_recente_moyenne'
    groups['heure + saison'] = lambda n: n in ('heure', 'sin_jour', 'cos_jour')
    mo = 2026 * 12 + 1
    base_mae, imp = group_importance(X1, y, names1, rows, mo, best_loss, groups)
    out.append(f'### Sur quoi s\'appuie le sous-modèle (J+1, janvier 2026)\n')
    out.append(f'Hausse de l\'erreur moyenne quand on brouille toutes les colonnes d\'un modèle '
               f'(erreur de départ {base_mae:.2f} °C) :\n')
    out.append('| Source | Hausse de l\'erreur |')
    out.append('|---|---|')
    for g, d in imp:
        out.append(f'| {g} | +{d:.2f} °C |')
    out.append('')
    log('  importance:', ', '.join(f'{g} {d:+.2f}' for g, d in imp[:6]))

    # ---- 2. Leads 1..7, TREND_MODELS ----
    leads = list(range(1, 8))
    log('leads 1..7, trend models…')
    fcs = load_models(score.TREND_MODELS, leads)
    models = sorted(set().union(*[set(f) for f in fcs.values()]), key=score.TREND_MODELS.index)
    # Same model list at every lead (missing → NaN) so the pooled features line up
    for L in leads:
        for m in models:
            fcs[L].setdefault(m, np.full((N, len(VARS)), np.nan))
        fcs[L] = {m: fcs[L][m] for m in models}
    Xs, masks, comps = {}, {}, {}
    per_lead = {}
    for L in leads:
        Xs[L], _ = build_X(fcs[L], obs, L)
        masks[L], comps[L] = eval_set(fcs[L], obs)
        t = time.time()
        per_lead[L] = loo(Xs[L], y, rows, MONTH, best_loss)
        log(f'  lead {L}: per-lead MAE {np.mean(np.abs(per_lead[L][masks[L]] - y[masks[L]])):.3f}'
            f' ({time.time() - t:.0f} s)')
    # Pooled: stack all leads, lead as a feature
    Xp = np.vstack([np.column_stack([Xs[L], np.full(N, L)]) for L in leads])
    yp = np.tile(y, len(leads))
    rp = np.tile(rows, len(leads))
    mp = np.tile(MONTH, len(leads))
    tp = rp & np.tile(DAY >= TEST_FROM, len(leads))
    pp = np.full(len(yp), np.nan)
    t = time.time()
    for mo in np.unique(mp[tp]):
        te = tp & (mp == mo)
        tr = rp & (mp != mo)
        pp[te] = fit_predict(Xp, yp, tr, te, best_loss)[0]
    log(f'  pooled: {time.time() - t:.0f} s')
    pooled = {L: pp[i * N:(i + 1) * N] for i, L in enumerate(leads)}

    out.append('## 2. De J+1 à J+7, heure par heure\n')
    out.append(f'Modèles : ' + ', '.join(models) + f'. Perte du sous-modèle : {best_loss} (meilleure à J+1).\n')
    out.append('Erreur moyenne (°C) selon le nombre de jours d\'avance, chaque échéance notée sur ses heures communes :\n')
    summary = {}
    for L in leads:
        b = baselines(fcs[L], obs, comps[L], masks[L])
        mk, o = masks[L], y
        mae = lambda p: np.mean(np.abs(p[mk] - o[mk]))
        bs = min(comps[L], key=lambda m: mae(b[m]))
        bc = min(comps[L], key=lambda m: mae(b[m + ' (biais corrigé)']))
        summary[L] = {'un modèle par échéance': mae(per_lead[L]), 'un modèle pour toutes': mae(pooled[L]),
                      'meilleur modèle seul': (mae(b[bs]), bs),
                      'meilleur modèle seul, biais corrigé': (mae(b[bc + ' (biais corrigé)']), bc),
                      'moyenne des modèles': mae(b['moyenne des modèles']),
                      'moyenne, biais corrigés': mae(b['moyenne des modèles (biais corrigés)']),
                      'n': mk.sum()}
        if L in (1, 3, 5, 7):
            summary[L]['_preds'] = {'**sous-modèle, un par échéance**': per_lead[L],
                                    '**sous-modèle, un pour toutes**': pooled[L], **b}
    out.append('| | ' + ' | '.join(f'J+{L}' for L in leads) + ' |')
    out.append('|---|' + '---|' * len(leads))
    for k in ('un modèle par échéance', 'un modèle pour toutes', 'meilleur modèle seul',
              'meilleur modèle seul, biais corrigé', 'moyenne des modèles', 'moyenne, biais corrigés'):
        cells = []
        for L in leads:
            v = summary[L][k]
            cells.append(f'{v[0]:.2f} ({v[1]})' if isinstance(v, tuple) else f'{v:.2f}')
        label = f'**sous-modèle, {k}**' if k.startswith('un ') else k
        out.append(f'| {label} | ' + ' | '.join(cells) + ' |')
    out.append('| heures testées | ' + ' | '.join(str(summary[L]['n']) for L in leads) + ' |')
    out.append('')
    for L in (3, 7):
        table(f'J+{L}, détail', summary[L]['_preds'], obs, masks[L], out, top=6)
    for L in leads:
        log(f'  J+{L}: ' + ', '.join(f'{k} {v[0] if isinstance(v, tuple) else v:.2f}'
                                     for k, v in summary[L].items() if not k.startswith('_') and k != 'n'))

    out.append(f'_Calcul : {(time.time() - t_start) / 60:.0f} min._\n')
    open(os.path.join(score.SORTIE, 'SOUS-MODELE-TEMPERATURE.md'), 'w').write('\n'.join(out))
    log(f'done in {(time.time() - t_start) / 60:.1f} min')
