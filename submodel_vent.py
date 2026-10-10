"""Wind + gusts sub-models: learn from all weather models at once to predict, at GRENOBLE-CEA-RADOME,
the 10 m mean wind speed ('vent', m/s) and the hourly max gust ('rafales', m/s).

Scales (hourly targets, forecast made N days before):
  - the day before: N = 1, models score.HOURLY_MODELS
  - trend: N = 1, 3, 5, 7, models score.TREND_MODELS

Honest test: leave-one-month-out on the months from 2025-10-01 to the end; each test month is predicted by a
model trained on all other months (from 2024-02-01). Every forecast is scored on exactly the same hours:
the sub-model, each single model, the plain average and a per-model linear correction (a·forecast + b,
fitted on the training months only).

Only cached API answers are used (no download): a model whose cache files are missing is skipped.

Usage: OMP_NUM_THREADS=2 .venv/bin/python submodel_vent.py   (writes SOUS-MODELE-VENT.md)
"""
import hashlib, json, math, os, time
from datetime import date, timedelta
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
import score

TEST_FROM = date(2025, 10, 1)
WINDY = 10.0  # m/s: a "windy hour" for gust detection
TARGETS = {'vent': 'wind_speed_10m', 'rafales': 'wind_gusts_10m'}
# Written after reading the results of the run of 09/10/2026 (update them if the data change)
CONCLUSIONS = [
    '- Le sous-modèle a la plus petite erreur partout : vent moyen 0,59 m/s la veille contre 0,86 pour le meilleur '
    'modèle seul (ICON-EU) et 0,74 pour le meilleur modèle corrigé ; rafales 1,47 m/s contre 2,10 et 1,77.',
    '- L\'écart reste net jusqu\'à J+7 (vent 0,78 contre 0,84 corrigé ; rafales 2,04 contre 2,27).',
    '- Les modèles bruts ont de gros biais (GFS et GEM sous-estiment les rafales de 3,5 m/s, ICON-CH et HARMONIE '
    'surestiment le vent) ; une simple droite par modèle ramène l\'erreur des rafales la veille de 2,1-3,8 à 1,8-2,4 m/s.',
    '- Heures venteuses la veille : le sous-modèle en voit 51 % avec 29 % de fausses alertes ; ICON-D2 brut en voit '
    '67 % mais avec 49 % de fausses alertes. Le sous-modèle vise l\'erreur moyenne, il lisse les pics.',
    '- Météo-France (AROME, ARPEGE) n\'a le vent que sur 17 % des heures testées dans les archives : il sert '
    'quand il est là mais n\'est pas comparé seul ; ECMWF ne donne pas de rafales.',
    '',
]
COVER = 0.9   # a single model is compared if it has the variable on >= 90 % of the test hours


# ---------- data (cache only) ----------

def cache_path(base, params, start, end):
    """Same path as score.api_chunk computes."""
    key = base.split('//')[1].split('.')[0] + json.dumps(params, sort_keys=True) + start + end
    return os.path.join(score.CACHE, params.get('models', 'obs') + '_' + hashlib.md5(key.encode()).hexdigest()[:10] + '.json')


def cached_api(params):
    """score.api, but only if every chunk is already in the cache; None otherwise (never downloads)."""
    if not all(os.path.exists(cache_path(score.PREVIOUS, params, s, e)) for s, e in score.CHUNKS):
        print('   skipped (not cached):', params['models'])
        return None
    return score.api(score.PREVIOUS, params)


def model_columns(H, suffix, keys):
    """Feature columns of one model for the given hours: every parameter, direction as sin/cos."""
    idx = {score.utc(ts): n for n, ts in enumerate(H['time'])}
    rows = np.array([idx.get(k, -1) for k in keys])
    cols, names = [], []

    def series(v):
        raw = H.get(v + suffix)
        if raw is None:
            return np.full(len(keys), np.nan)
        a = np.array([np.nan if x is None else x for x in raw], dtype=float)
        out = np.full(len(keys), np.nan)
        ok = rows >= 0
        out[ok] = a[rows[ok]]
        return out

    for v in score.VARS:
        s = series(v)
        if v == 'wind_direction_10m':
            r = np.radians(s)
            cols += [np.sin(r), np.cos(r)]
            names += ['dir_sin', 'dir_cos']
        else:
            cols.append(s)
            names.append(v)
    return np.column_stack(cols), names


def calendar(keys):
    out = []
    for k in keys:
        loc = k.astimezone(score.PARIS)
        doy = loc.timetuple().tm_yday
        out.append([loc.hour, math.sin(2 * math.pi * doy / 365), math.cos(2 * math.pi * doy / 365)])
    return np.array(out, dtype=float)


def persistence(keys, obs, lead):
    """Observations surely known at issue time: `lead` days + 6 h before the target (like blend.make_persist),
    plus the mean wind and max gust over the 24 h before that moment."""
    g = lambda o, v: np.nan if o is None or o.get(v) is None else float(o[v])
    out = []
    for k in keys:
        t0 = k - timedelta(days=lead, hours=6)
        o = obs.get(t0)
        d = g(o, 'direction')
        past = [obs.get(t0 - timedelta(hours=h)) for h in range(24)]
        ws = [p['vent'] for p in past if p and p.get('vent') is not None]
        gs = [p['rafales'] for p in past if p and p.get('rafales') is not None]
        out.append([g(o, 'vent'), g(o, 'rafales'), math.sin(math.radians(d)), math.cos(math.radians(d)),
                    g(o, 'pression'), np.mean(ws) if ws else np.nan, max(gs) if gs else np.nan])
    return np.array(out, dtype=float)


# ---------- metrics ----------

def metrics(pred, y, gust):
    e = pred - y
    r = {'mae': float(np.mean(np.abs(e))), 'bias': float(np.mean(e))}
    if gust:
        obs_w, pred_w = y >= WINDY, pred >= WINDY
        r['caught'] = 100 * np.mean(pred_w[obs_w]) if obs_w.any() else float('nan')
        r['false'] = 100 * np.mean(~obs_w[pred_w]) if pred_w.any() else float('nan')
        r['n_windy'] = int(obs_w.sum())
    return r


# ---------- one scale / lead / target ----------

def evaluate(raw, suffix, lead, target, obs, keys_all):
    """raw: {model: hourly dict}. Returns rows [(name, metrics)] and the number of test hours."""
    var = TARGETS[target]
    keys = [k for k in keys_all if obs[k].get(target) is not None]
    y = np.array([obs[k][target] for k in keys], dtype=float)
    days = [k.date() for k in keys]
    months = np.array([d.year * 12 + d.month for d in days])
    test = np.array([d >= TEST_FROM for d in days])

    blocks, fc = [calendar(keys), persistence(keys, obs, lead)], {}
    for m, H in raw.items():
        X, names = model_columns(H, suffix, keys)
        blocks.append(X)
        fc[m] = X[:, names.index(var)]
    X = np.hstack(blocks)

    # Single models compared: those that give the variable on almost all test hours
    singles = [m for m in fc if np.mean(~np.isnan(fc[m][test])) >= COVER]
    # Same hours for everyone: test hours where all compared models have the variable
    same = test & np.all([~np.isnan(fc[m]) for m in singles], axis=0)
    train_ok = np.ones(len(y), bool)  # all hours with an observation (2024-02 onwards)

    pred = np.full(len(y), np.nan)
    corr = {m: np.full(len(y), np.nan) for m in singles}
    for mo in np.unique(months[same]):
        te = same & (months == mo)
        tr = train_ok & (months != mo)
        keep = [j for j in range(X.shape[1]) if len(np.unique(X[tr, j][~np.isnan(X[tr, j])])) >= 2]
        reg = HistGradientBoostingRegressor(loss='absolute_error', max_iter=300, learning_rate=0.05,
                                            max_leaf_nodes=15, l2_regularization=1.0, random_state=0)
        reg.fit(X[tr][:, keep], y[tr])
        pred[te] = reg.predict(X[te][:, keep])
        # Per-model linear correction a·forecast + b fitted on the same training months
        for m in singles:
            ok = tr & ~np.isnan(fc[m])
            a, b = np.polyfit(fc[m][ok], y[ok], 1)
            corr[m][te] = np.maximum(0, a * fc[m][te] + b)

    gust = target == 'rafales'
    ys = y[same]
    rows = [('**Sous-modèle**', metrics(pred[same], ys, gust)),
            ('Moyenne simple des modèles', metrics(np.mean([fc[m][same] for m in singles], axis=0), ys, gust))]
    single_rows = [(m, metrics(fc[m][same], ys, gust), metrics(corr[m][same], ys, gust)) for m in singles]
    return rows, single_rows, int(same.sum())


# ---------- report ----------

def fmt(r, gust):
    s = f'{r["mae"]:.2f} | {r["bias"]:+.2f}'
    if gust:
        pct = lambda x: '-' if np.isnan(x) else f'{x:.0f} %'
        s += f' | {pct(r["caught"])} | {pct(r["false"])}'
    return s


def write_table(title, rows, single_rows, n, gust, out):
    out.append(f'### {title} ({n} heures testées)\n')
    head = '| Prévision | Erreur moy. (m/s) | Biais | Erreur moy. corrigé | Biais corrigé |'
    sep = '|---|---|---|---|---|'
    if gust:
        head = ('| Prévision | Erreur moy. (m/s) | Biais | Heures ≥ 10 m/s vues | Fausses alertes '
                '| Erreur moy. corrigé | Biais corrigé | Vues corrigé | Fausses alertes corrigé |')
        sep = '|---|---|---|---|---|---|---|---|---|'
    out.append(head)
    out.append(sep)
    dash = ' | - | -' + (' | - | -' if gust else '')
    for name, r in rows:
        out.append(f'| {name} | {fmt(r, gust)}{dash} |')
    for m, r, c in sorted(single_rows, key=lambda s: s[2]['mae']):
        out.append(f'| {m} | {fmt(r, gust)} | {fmt(c, gust)} |')
    out.append('')


if __name__ == '__main__':
    t_start = time.time()
    obs = score.load_obs()
    keys_all = sorted(k for k in obs if k.date() >= date.fromisoformat(score.START))
    summary, details = [], []

    jobs = []
    hv1 = ','.join(f'{v}_previous_day1' for v in score.VARS)
    raw1 = {m: d['hourly'] for m in score.HOURLY_MODELS if (d := cached_api({'hourly': hv1, 'models': m}))}
    jobs.append(('Veille → lendemain, heure par heure', raw1, '_previous_day1', 1))
    hv7 = ','.join(f'{v}_previous_day{d}' for d in range(1, 8) for v in score.VARS)
    raw7 = {m: d['hourly'] for m in score.TREND_MODELS if (d := cached_api({'hourly': hv7, 'models': m}))}
    for lead in (1, 3, 5, 7):
        jobs.append((f'Tendance (modèles globaux), J+{lead}', raw7, f'_previous_day{lead}', lead))

    for title, raw, suffix, lead in jobs:
        for target in TARGETS:
            t0 = time.time()
            rows, singles, n = evaluate(raw, suffix, lead, target, obs, keys_all)
            gust = target == 'rafales'
            label = 'Vent moyen' if target == 'vent' else 'Rafales'
            write_table(f'{label} — {title}', rows, singles, n, gust, details)
            best_raw = min(singles, key=lambda s: s[1]['mae'])
            best_corr = min(singles, key=lambda s: s[2]['mae'])
            summary.append((label, title, rows[0][1], best_raw, best_corr, rows[1][1], gust, n))
            print(f'{label} | {title}: sub {rows[0][1]["mae"]:.2f}  best {best_raw[0]} {best_raw[1]["mae"]:.2f}  '
                  f'best corr {best_corr[0]} {best_corr[2]["mae"]:.2f}  avg {rows[1][1]["mae"]:.2f}  '
                  f'({n} h, {time.time() - t0:.0f} s)', flush=True)

    out = ['# Sous-modèles vent et rafales\n',
           f'Station {score.STATION_NOM} : vent moyen à 10 m (m/s) et rafale maximale de l\'heure (m/s). '
           f'Test honnête : chaque mois de {TEST_FROM} à {score.END} est prédit par un modèle entraîné sans ce mois '
           f'(entraînement depuis {score.START}). Toutes les prévisions sont notées sur les mêmes heures.\n',
           'Sous-modèle : gradient boosting (scikit-learn) sur tous les paramètres de tous les modèles, l\'heure, '
           'la saison et les observations connues au moment de la prévision. « Corrigé » : chaque modèle seul '
           'recalé par une droite a·prévision + b apprise sur les mois d\'entraînement. '
           f'Heure venteuse = rafale ≥ {WINDY:.0f} m/s ; « vues » = part des heures venteuses annoncées, '
           '« fausses alertes » = part des heures annoncées venteuses qui ne l\'étaient pas.\n',
           '## Résumé (erreur moyenne en m/s)\n',
           '| Paramètre | Échelle | Sous-modèle | Meilleur modèle seul | Meilleur modèle corrigé | Moyenne simple |',
           '|---|---|---|---|---|---|']
    for label, title, sub, br, bc, avg, gust, n in summary:
        out.append(f'| {label} | {title} | **{sub["mae"]:.2f}** | {br[1]["mae"]:.2f} ({br[0]}) | '
                   f'{bc[2]["mae"]:.2f} ({bc[0]}) | {avg["mae"]:.2f} |')
    out.append('')
    out.append('## Détection des heures venteuses (rafale ≥ 10 m/s)\n')
    out.append('| Échelle | Heures venteuses | Sous-modèle : vues / fausses alertes | Meilleur modèle seul : vues / fausses alertes |')
    out.append('|---|---|---|---|')
    for label, title, sub, br, bc, avg, gust, n in summary:
        if gust:
            out.append(f'| {title} | {sub["n_windy"]} | {sub["caught"]:.0f} % / {sub["false"]:.0f} % | '
                       f'{br[1]["caught"]:.0f} % / {br[1]["false"]:.0f} % ({br[0]}) |')
    out.append('')
    out.append('## Conclusions\n')
    out += CONCLUSIONS
    out.append('## Détail\n')
    out += details
    out.append(f'Durée du calcul : {(time.time() - t_start) / 60:.0f} min.\n')
    open(os.path.join(score.SORTIE, 'SOUS-MODELE-VENT.md'), 'w').write('\n'.join(out))
    print(f'done in {(time.time() - t_start) / 60:.1f} min')
