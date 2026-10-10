"""Sub-model: rain in the next 2 hours, 20-minute slots, at GRENOBLE-CEA-RADOME.

A slot is rainy when it gets >= 0.05 mm (score.RAIN_SLOT). Ground truth: 6-minute station rain spread into slots.

Two variants of a gradient-boosting classifier:
  1. models only: each model's slot rain, its rain in the previous / next slot, its hourly context, hour, season;
  2. + rain observed at the station in the 20 / 60 / 120 min before the forecast time, with forecast time =
     slot start minus 0, 20, ..., 100 min (lead 0-2 h, lead is a feature). Needs live 6-minute observations.

Honest test: leave-one-month-out on the months from 2025-10-01 to the end; the decision threshold is chosen
on the training months only (best critical success index). Everything is scored on exactly the same rows.

Usage: .venv/bin/python submodel_pluie_2h.py   (reads data/cache only, never downloads from Open-Meteo)
"""
import hashlib, json, math, os, time
from datetime import date, datetime, timedelta
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
import score

TEST_FROM = date(2025, 10, 1)
LEADS = [0, 20, 40, 60, 80, 100]          # minutes between forecast time and slot start
SLOT = timedelta(minutes=20)
CTX = ['relative_humidity_2m', 'cloud_cover', 'shortwave_radiation', 'wind_speed_10m', 'wind_gusts_10m',
       'pressure_msl', 'precipitation', 'temperature_2m']
TRAIN_ROWS_MAX = 80000                    # subsample of training rows per fit (keeps each fit short)
RNG = np.random.default_rng(0)


def cache_path(base, params, start, end):
    # Same path as score.api_chunk computes it
    key = base.split('//')[1].split('.')[0] + json.dumps(params, sort_keys=True) + start + end
    return os.path.join(score.CACHE, params.get('models', 'obs') + '_' + hashlib.md5(key.encode()).hexdigest()[:10] + '.json')


def cached_api(params):
    """score.api, but only when every chunk is already cached (the Open-Meteo quota is nearly exhausted)."""
    if not all(os.path.exists(cache_path(score.HISTORICAL, params, s, e)) for s, e in score.CHUNKS):
        print('   not cached, skipped:', params)
        return None
    return score.api(score.HISTORICAL, params)


def local_download(name, url):
    # Use the Météo-France files already on disk; download only if missing
    path = os.path.join(score.DATA, name)
    return path if os.path.exists(path) else _download(name, url)


_download = score.download
score.download = local_download


def load():
    rain6 = score.load_6min_rain()
    oslots = score.to_slots(rain6, 6)
    mslots, hourly = {}, {}
    for m in score.NOWCAST_MODELS:
        dm = cached_api({'minutely_15': 'precipitation', 'models': m})
        dh = cached_api({'hourly': ','.join(score.VARS), 'models': m})
        if not dm or not dh:
            continue
        M = dm['minutely_15']
        mslots[m] = score.to_slots({score.utc(t): v for t, v in zip(M['time'], M['precipitation']) if v is not None}, 15)
        H = dh['hourly']
        hourly[m] = {score.utc(t): [H.get(v, [None] * len(H['time']))[n] for v in CTX] for n, t in enumerate(H['time'])}
    return oslots, mslots, hourly


def nan(x):
    return np.nan if x is None else float(x)


def model_features(s, mslots, hourly):
    loc = s.astimezone(score.PARIS)
    doy = loc.timetuple().tm_yday
    row = [loc.hour + loc.minute / 60, math.sin(2 * math.pi * doy / 365), math.cos(2 * math.pi * doy / 365)]
    h = s.replace(minute=0) + timedelta(hours=1)  # hour ending after the slot (Open-Meteo convention)
    for m in mslots:
        sl = mslots[m]
        row += [nan(sl.get(s - SLOT)), nan(sl.get(s)), nan(sl.get(s + SLOT))]
        row += [nan(x) for x in hourly[m].get(h, [None] * len(CTX))]
    return row


def obs_features(s, lead, oslots):
    """Observed rain in the 20, 60 and 120 min before forecast time T = s - lead (NaN if any slot is missing)."""
    t = s - timedelta(minutes=lead)
    prev = [oslots.get(t - SLOT * (k + 1)) for k in range(6)]
    tot = lambda n: np.nan if any(p is None for p in prev[:n]) else sum(prev[:n])
    return [tot(1), tot(3), tot(6), float(lead)]


def scores(pred, y):
    pred, y = np.asarray(pred, bool), np.asarray(y, bool)
    hit, miss, fa = (pred & y).sum(), (~pred & y).sum(), (pred & ~y).sum()
    csi = 100 * hit / max(1, hit + miss + fa)
    caught = 100 * hit / max(1, hit + miss)
    false_alarms = 100 * fa / max(1, hit + fa)      # share of forecast rainy slots that stayed dry
    return csi, caught, false_alarms, 100 * np.mean(pred == y)


def best_threshold(p, y):
    """Threshold maximising the critical success index."""
    best = (0, 0.5)
    for th in np.arange(0.05, 0.91, 0.01):
        pred = p >= th
        hit = (pred & y).sum()
        csi = hit / max(1, pred.sum() + (y & ~pred).sum())
        best = max(best, (csi, th))
    return best[1]


def run_cv(X, y, months, test_months, group=None):
    """Leave-one-month-out. Returns predictions on every row of the test months, and the thresholds used."""
    pred = np.zeros(len(y), bool)
    ths = []
    for mo in test_months:
        te = months == mo
        tr = np.flatnonzero(~te)
        if group is not None:
            # Variant 2: one random lead per slot in training (each lead row repeats the same slot)
            tr = tr[group[tr] == RNG.integers(0, len(LEADS), len(tr))]
        if len(tr) > TRAIN_ROWS_MAX:
            tr = RNG.choice(tr, TRAIN_ROWS_MAX, replace=False)
        keep = [j for j in range(X.shape[1]) if len(np.unique(X[tr, j][~np.isnan(X[tr, j])])) >= 2]
        clf = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, max_leaf_nodes=15,
                                             l2_regularization=1.0, random_state=0)
        clf.fit(X[tr][:, keep], y[tr])
        th = best_threshold(clf.predict_proba(X[tr][:, keep])[:, 1], y[tr])
        pred[te] = clf.predict_proba(X[te][:, keep])[:, 1] >= th
        ths.append(th)
        print(f'    month {mo // 12}-{mo % 12 + 1:02d} thr {th:.2f}', flush=True)
    return pred, ths


def main():
    t0 = time.time()
    oslots, mslots, hourly = load()
    models = list(mslots)
    # Slots kept: observed, the last 20 min before each lead observed, and every model has a value in the test
    # months (same rows for everyone); training slots only need AROME (models starting later give NaN)
    need = lambda s: models if s.date() >= TEST_FROM else ['meteofrance_arome_france']
    keys = sorted(s for s in oslots
                  if all(s in mslots[m] for m in need(s))
                  and all(s - timedelta(minutes=L) - SLOT in oslots for L in LEADS))
    print(f'{len(keys)} slots, models: {models}', flush=True)
    y = np.array([oslots[s] >= score.RAIN_SLOT for s in keys])
    mid = lambda s: s.year * 12 + s.month - 1   # month index (month = mid % 12 + 1)
    months = np.array([mid(s) for s in keys])
    test_months = sorted({mo for s, mo in zip(keys, months) if s.date() >= TEST_FROM})

    # Variant 1: one row per slot
    X1 = np.array([model_features(s, mslots, hourly) for s in keys])
    print(f'variant 1: {X1.shape}', flush=True)
    p1, th1 = run_cv(X1, y, months, test_months)
    print(f'  done {time.time() - t0:.0f}s', flush=True)

    # Variant 2: one row per (slot, lead)
    n = len(keys)
    X2 = np.hstack([np.repeat(X1, len(LEADS), axis=0),
                    np.array([obs_features(s, L, oslots) for s in keys for L in LEADS])])
    y2 = np.repeat(y, len(LEADS))
    months2 = np.repeat(months, len(LEADS))
    lead_idx = np.tile(np.arange(len(LEADS)), n)
    print(f'variant 2: {X2.shape}', flush=True)
    p2, th2 = run_cv(X2, y2, months2, test_months, group=lead_idx)
    print(f'  done {time.time() - t0:.0f}s', flush=True)

    # Everything scored on the same (slot, lead) rows of the test months
    te = np.isin(months2, test_months)
    yt = y2[te]
    lt = np.array(LEADS)[lead_idx[te]]
    rows = [('**Sous-modèle 1 : modèles seuls**', np.repeat(p1, len(LEADS))[te]),
            ('**Sous-modèle 2 : + pluie observée**', p2[te])]
    single = {m: np.repeat(np.array([(mslots[m].get(s, 0) >= score.RAIN_SLOT) for s in keys]), len(LEADS))[te] for m in models}
    for m in models:
        rows.append((m, single[m]))
    rows.append(('AROME et ICON-D2 d\'accord', single['meteofrance_arome_france'] & single['icon_d2']))
    persist = X2[te][:, X1.shape[1]] >= score.RAIN_SLOT   # observed rain in the last 20 min
    rows.append(('Persistance (comme les 20 dernières min)', persist))

    res = [(name, scores(p, yt)) for name, p in rows]
    res.sort(key=lambda r: -r[1][0])
    n_test = te.sum() // len(LEADS)
    out = ['# Sous-modèle : pluie dans les 2 prochaines heures (tranches de 20 min)\n',
           f'Station GRENOBLE-CEA-RADOME. Une tranche est pluvieuse à partir de {score.RAIN_SLOT} mm. '
           f'Test honnête : chaque mois de {TEST_FROM} à {score.END} est prédit par un modèle entraîné sur tous les '
           'autres mois (depuis 2024-02-01). Le seuil de décision est choisi sur les mois d\'entraînement seulement.\n',
           f'{n_test} tranches testées, dont {100 * y[np.isin(months, test_months)].mean():.1f} % pluvieuses. '
           f'Chaque tranche est notée 6 fois (prévision faite 0, 20, 40, 60, 80 et 100 min avant son début), '
           'toutes les prévisions sur exactement les mêmes lignes.\n',
           '- Indice de réussite : tranches pluvieuses prévues et vues / tranches où il a plu ou été prévu de pleuvoir.',
           '- Pluie vue : part des tranches pluvieuses annoncées.',
           '- Fausses alertes : part des tranches annoncées pluvieuses restées sèches.',
           '- Justes : part de toutes les tranches (sèches ou pluvieuses) bien prévues.\n',
           '| Prévision | Indice de réussite | Pluie vue | Fausses alertes | Justes |', '|---|---|---|---|---|']
    for name, (csi, ca, fa, ok) in res:
        out.append(f'| {name} | {csi:.1f} % | {ca:.0f} % | {fa:.0f} % | {ok:.1f} % |')
    out.append('')
    out.append('Indice de réussite selon l\'avance de la prévision :\n')
    out.append('| Avance | Sous-modèle 1 | Sous-modèle 2 | Persistance | AROME |')
    out.append('|---|---|---|---|---|')
    for L in LEADS:
        k = lt == L
        out.append(f'| {L} min | {scores(rows[0][1][k], yt[k])[0]:.1f} % | {scores(p2[te][k], yt[k])[0]:.1f} % | '
                   f'{scores(persist[k], yt[k])[0]:.1f} % | {scores(single["meteofrance_arome_france"][k], yt[k])[0]:.1f} % |')
    out.append('')
    out.append(f'Seuils choisis : variante 1 de {min(th1):.2f} à {max(th1):.2f}, variante 2 de {min(th2):.2f} à {max(th2):.2f}. '
               f'Durée du calcul : {(time.time() - t0) / 60:.0f} min.\n')
    open(os.path.join(score.ROOT, 'SOUS-MODELE-PLUIE-2H.md'), 'w').write('\n'.join(out))
    print('\n'.join(out))


if __name__ == '__main__':
    main()
