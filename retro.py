"""Retroactive record of our own forecasts: what the frozen models would have said, case by case, since 2024-02.

Same recipes as figer.py (same inputs, same settings), but leave-one-month-out: each month is forecast by a model
trained on every other month, so no forecast has seen its own outcome. The result is a history of
"our forecast vs what really happened" at each lead time, to fine-tune the mega-model later on its own errors,
the way it was trained on the errors of the weather models.

Lead times: 1 to 7 days (morning / afternoon), the day before hour by hour (~24 h), next 2 hours (20-min slots).
Limits: the 2-hour archive (first hours of each run) is more generous than live; the hour-by-hour record is the
day-before forecast only (the live site also uses it up to day 7, with reduced precision beyond 48 h).

Usage: .venv/bin/python retro.py   (cache only, ~writes retro/*.csv.gz + RETRO.md)
"""
import csv, gzip, os
from datetime import date
import numpy as np
from joblib import Parallel, delayed
import blend
import figer
import modeles
import score

OUT = os.path.join(score.SORTIE, 'retro')
CATS = ['soleil', 'mitigé', 'couvert', 'pluie']
JOBS = 6


def month(k):
    d = figer.day(k)
    return d.year * 12 + d.month - 1


def weights(keys, test_month, half_life):
    """Recency weights centred on the held-out month (both directions), as figer.recency does live."""
    if half_life is None:
        return None
    age = np.abs(np.array([month(k) for k in keys]) - test_month)
    return 0.5 ** (age / half_life)


def one_fold(kind, X, y, months, mo, keys_tr, half_life):
    te, tr = months == mo, months != mo
    est, keep = figer.fit('cls' if kind in ('condition', 'pluie') else 'reg', X[tr], y[tr],
                          weights(keys_tr, mo, half_life))
    if kind == 'condition':
        p = np.zeros((te.sum(), 4))
        p[:, est.classes_] = est.predict_proba(X[te][:, keep])
        return te, p
    if kind == 'pluie':
        return te, est.predict_proba(X[te][:, keep])[:, 1]
    return te, est.predict(X[te][:, keep])


def out_of_fold(name, kind, keys, X, y, half_life=None):
    """{key: prediction} where each month comes from a model that never saw it."""
    months = np.array([month(k) for k in keys])
    folds = Parallel(n_jobs=JOBS)(
        delayed(one_fold)(kind, X, y, months, mo, [k for k, m in zip(keys, months) if m != mo], half_life)
        for mo in np.unique(months))
    pred = {}
    for te, p in folds:
        for k, v in zip([k for k, t in zip(keys, te) if t], p):
            pred[k] = v
    print(f'  {name} : {len(pred)} cas, {len(folds)} mois', flush=True)
    return pred


def r(x, n=2):
    return '' if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), n)


def write(path, header, rows):
    with gzip.open(os.path.join(OUT, path), 'wt', newline='') as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def condition_cols(p, obs_cat):
    """Predicted category (best expected credit), its 4 probabilities, observed category."""
    if p is None:
        return ['', '', '', '', '', obs_cat]
    return [CATS[int(np.argmax(p @ blend.C.T))]] + [r(x) for x in p] + [obs_cat]


def cat_name(c):
    return '' if c is None else CATS[c]


def main():
    os.makedirs(OUT, exist_ok=True)
    obs = score.load_obs()
    report = ['# Nos prévisions rétroactives\n',
              'Chaque mois prévu par un modèle entraîné sur tous les autres mois (recettes de `figer.py`). '
              'Fichiers dans `retro/`, une ligne par cas.\n',
              '| Échéance | Mesure | Mega-modèle (rétroactif) | Cas |', '|---|---|---|---|']

    # ---------- hourly, the day before (~24 h) ----------
    print('Heure par heure, la veille', flush=True)
    hv = ','.join(f'{v}_previous_day1' for v in score.VARS)
    models = score.HOURLY_MODELS
    fcs = {m: modeles.hours(score.api(score.PREVIOUS, {'hourly': hv, 'models': m})['hourly'], '_previous_day1')
           for m in models}
    preds = {}
    keys, X, y = figer.build(fcs, obs, models, lambda o: o['cat'], lambda o, k: o['cat'] is not None)
    preds['condition'] = out_of_fold('heure_condition', 'condition', keys, X, y)
    keys, X, y = figer.build(fcs, obs, models, lambda o: o['pluie_mm'] >= score.RAIN_HOUR,
                             lambda o, k: o['pluie_mm'] is not None)
    preds['pluie'] = out_of_fold('heure_pluie', 'pluie', keys, X, y.astype(int))
    for v in ('temperature', 'vent', 'rafales'):
        keys, X, y = figer.build(fcs, obs, models, lambda o, v=v: o[v], lambda o, k, v=v: o.get(v) is not None)
        preds[v] = out_of_fold(f'heure_{v}', 'reg', keys, X, y)
    rows = []
    for k in sorted(set().union(*preds.values())):
        o, g = obs[k], lambda v: preds[v].get(k)
        rows.append([k.isoformat(), 'veille']
                    + condition_cols(g('condition'), cat_name(o['cat']))
                    + [r(g('pluie')), r(o['pluie_mm'], 1)]
                    + [x for v in ('temperature', 'vent', 'rafales') for x in (r(g(v), 1), r(o.get(v), 1))])
    write('heures_veille.csv.gz',
          ['heure_utc', 'echeance', 'condition_prevue', 'p_soleil', 'p_mitige', 'p_couvert', 'p_pluie',
           'condition_observee', 'pluie_proba', 'pluie_observee_mm', 'temperature_prevue', 'temperature_observee',
           'vent_prevu_ms', 'vent_observe_ms', 'rafales_prevues_ms', 'rafales_observees_ms'], rows)
    report += summarize('veille, heure par heure', preds, obs, hourly=True)

    # ---------- half-days, 1 to 7 days ahead ----------
    print('Matin / après-midi, J+1 à J+7', flush=True)
    oblocks = score.to_blocks(obs)
    hv = ','.join(f'{v}_previous_day{d}' for d in range(1, 8) for v in score.VARS)
    models = score.TREND_MODELS
    raw = {m: score.api(score.PREVIOUS, {'hourly': hv, 'models': m}) for m in models}
    rows = []
    for lead in range(1, 8):
        fcs = {m: modeles.blocks(modeles.hours(d['hourly'], f'_previous_day{lead}')) for m, d in raw.items()}
        hl, preds = figer.BLOCK_HALF_LIFE.get(lead), {}
        keys, X, y = figer.build(fcs, oblocks, models, lambda o: o['cat'], lambda o, k: o['cat'] is not None)
        preds['condition'] = out_of_fold(f'bloc{lead}_condition', 'condition', keys, X, y, hl)
        for v in ('temperature', 'rafales'):
            keys, X, y = figer.build(fcs, oblocks, models, lambda o, v=v: o[v], lambda o, k, v=v: o.get(v) is not None)
            preds[v] = out_of_fold(f'bloc{lead}_{v}', 'reg', keys, X, y, hl)
        for k in sorted(set().union(*preds.values())):
            o, g = oblocks[k], lambda v: preds[v].get(k)
            rows.append([k[0].isoformat(), k[1], lead]
                        + condition_cols(g('condition'), cat_name(o['cat']))
                        + [r(o['pluie_mm'], 1)]
                        + [x for v in ('temperature', 'rafales') for x in (r(g(v), 1), r(o.get(v), 1))])
        report += summarize(f'J+{lead}, matin / après-midi', preds, oblocks)
    write('demi_journees_J1-J7.csv.gz',
          ['date', 'partie', 'echeance_jours', 'condition_prevue', 'p_soleil', 'p_mitige', 'p_couvert', 'p_pluie',
           'condition_observee', 'pluie_observee_mm', 'temperature_prevue', 'temperature_observee',
           'rafales_prevues_ms', 'rafales_observees_ms'], rows)

    # ---------- rain in the next 2 hours, 20-minute slots ----------
    print('Pluie dans les 2 heures', flush=True)
    models = score.NOWCAST_MODELS
    oslots = score.to_slots(score.load_6min_rain(), 6)
    mslots, hctx = {}, {}
    for m in models:
        mslots[m] = modeles.slots(score.api(score.HISTORICAL, {'minutely_15': 'precipitation', 'models': m})['minutely_15'])
        hctx[m] = modeles.hourly_ctx(score.api(score.HISTORICAL, {'hourly': ','.join(score.VARS), 'models': m})['hourly'])
    keys = sorted(s for s in oslots if s in mslots['meteofrance_arome_france'])
    X = np.array([modeles.rain_row(s, mslots, hctx, models) for s in keys])
    y = np.array([oslots[s] >= score.RAIN_SLOT for s in keys]).astype(int)
    pred = out_of_fold('pluie2h', 'pluie', keys, X, y)
    thr = modeles.RAIN_2H_THRESHOLD
    write('pluie_2h.csv.gz', ['tranche_utc', 'echeance', 'pluie_proba', 'pluie_annoncee', 'pluie_observee_mm'],
          [[s.isoformat(), '2h', r(pred[s], 3), int(pred[s] >= thr), r(oslots[s], 2)] for s in sorted(pred)])
    hit = np.array([pred[s] >= thr for s in sorted(pred)])
    real = np.array([oslots[s] >= score.RAIN_SLOT for s in sorted(pred)])
    report.append(f'| 2 h, tranches de 20 min | réussite pluie % | {figer.csi(hit, real):.1f} | {len(pred)} |')

    open(os.path.join(score.SORTIE, 'RETRO.md'), 'w').write('\n'.join(report) + '\n')
    print('\n'.join(report))


def summarize(label, preds, obs, hourly=False):
    lines = []
    c = preds['condition']
    pc = [int(np.argmax(p @ blend.C.T)) for p in c.values()]
    lines.append(f'| {label} | condition /100 | {blend.summary(pc, [obs[k]["cat"] for k in c])[0]:.1f} | {len(c)} |')
    if hourly:
        p = preds['pluie']
        lines.append(f'| {label} | réussite pluie % | '
                     f'{figer.csi(np.array([x >= 0.5 for x in p.values()]), np.array([obs[k]["pluie_mm"] >= score.RAIN_HOUR for k in p])):.1f} | {len(p)} |')
    for v in ('temperature', 'vent', 'rafales'):
        if v in preds:
            e = np.mean([abs(x - obs[k][v]) for k, x in preds[v].items()])
            lines.append(f'| {label} | erreur {v} | {e:.2f} | {len(preds[v])} |')
    return lines


if __name__ == '__main__':
    main()
