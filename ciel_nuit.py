"""Night sky, step 1: can the Grenoble-Isère airport METAR (LFLS, ~40 km) stand in for Grenoble's sky?

By day, Grenoble's sky is known from satellite sunlight (score.py). At night nothing measures it near Grenoble,
except the airport's automatic METAR (ceilometer, day and night). This script compares, on daytime hours,
LFLS cloud cover with the satellite sky at Grenoble, next to a raw forecast (Météo-France, day before):
LFLS is a usable night truth only if it agrees with Grenoble's sky clearly better than a forecast does.

Data: data/ciel_nuit/lfls_metar.csv (Iowa Environmental Mesonet ASOS/METAR archive, routine + specials).
Run: .venv/bin/python ciel_nuit.py
"""
import csv
import os
from collections import Counter
from datetime import datetime, timedelta, timezone

import score

METAR = os.path.join(score.DATA, 'ciel_nuit', 'lfls_metar.csv')
OCTAS = {'FEW': 1.5, 'SCT': 3.5, 'BKN': 6, 'OVC': 8, 'VV': 8, 'NSC': 0, 'NCD': 0, 'SKC': 0, 'CLR': 0}


def load_metar():
    """Cloud cover in octas at each report: the densest layer; CAVOK / no layer = 0 (clear below ~1 500 m only)."""
    out = {}
    with open(METAR) as f:
        for row in csv.DictReader(f):
            t = datetime.strptime(row['valid'], '%Y-%m-%d %H:%M').replace(tzinfo=timezone.utc)
            layers = [row[f'skyc{k}'].strip() for k in (1, 2, 3, 4)]
            if '///' in layers:
                continue  # cover not determined
            known = [OCTAS[c] for c in layers if c in OCTAS]
            cavok = 'CAVOK' in row['metar']
            out[t] = {'octas': max(known) if known else 0.0, 'cavok': cavok or not known}
    return out


def hour_mean(metar, t):
    """Mean cover over the hour ending at t (reports at t-30 min and t), like the satellite hour."""
    v = [metar[x]['octas'] for x in (t - timedelta(minutes=30), t) if x in metar]
    return sum(v) / len(v) if v else None


def to_cat(x, lo, hi):
    return 0 if x < lo else 1 if x < hi else 2


def credit(a, b):
    return 1 if a == b else score.CREDIT.get((a, b), 0)


def agreement(pairs, lo, hi):
    """(weighted credit, exact share) of the predicted category against the satellite category."""
    n = len(pairs)
    cats = [(to_cat(x, lo, hi), c) for x, c in pairs]
    return sum(credit(p, c) for p, c in cats) / n, sum(p == c for p, c in cats) / n


def best_thresholds(pairs, grid):
    return max(((lo, hi) for lo in grid for hi in grid if hi > lo), key=lambda th: agreement(pairs, *th)[0])


def main():
    obs = score.load_obs()
    metar = load_metar()
    fc = score.api(score.PREVIOUS, {'hourly': 'cloud_cover_previous_day1', 'models': 'meteofrance_seamless'})
    cc = {score.utc(ts): v for ts, v in zip(fc['hourly']['time'], fc['hourly']['cloud_cover_previous_day1'])}
    # undocumented cloud_cover of Open-Meteo's satellite API: filled day and night, origin unknown
    sat = score.api(score.SATELLITE, {'hourly': 'cloud_cover'})
    scc = {score.utc(ts): v for ts, v in zip(sat['hourly']['time'], sat['hourly']['cloud_cover'])}

    # daytime, dry hours with a satellite sky (soleil / mitigé / couvert), LFLS and the forecast both present
    rows = []
    for t, o in obs.items():
        if o.get('cat') not in (0, 1, 2):
            continue
        m, f, c = hour_mean(metar, t), cc.get(t), scc.get(t)
        if m is None or f is None or c is None:
            continue
        rows.append((t, o['cat'], m, f, c))
    print(f'{len(rows)} heures de jour sèches communes ({rows[0][0]:%Y-%m-%d} → {rows[-1][0]:%Y-%m-%d})')
    print('Ciel satellite :', {score.CATS[k]: f'{v / len(rows):.0%}' for k, v in sorted(Counter(r[1] for r in rows).items())})

    # thresholds fitted on odd months, measured on even months (no flattering in-sample fit)
    fit = [r for r in rows if r[0].month % 2]
    test = [r for r in rows if not r[0].month % 2]
    lines = []
    for name, idx, grid in (('METAR LFLS (octas)', 2, [x / 2 for x in range(1, 17)]),
                            ('Prévision Météo-France J-1 (nébulosité %)', 3, list(range(5, 105, 5))),
                            ('Nébulosité « satellite » Open-Meteo (%)', 4, list(range(5, 105, 5)))):
        th = best_thresholds([(r[idx], r[1]) for r in fit], grid)
        w, e = agreement([(r[idx], r[1]) for r in test], *th)
        lines.append(f'| {name} | {th[0]} / {th[1]} | {w * 100:.1f} | {e:.0%} |')
    w, e = agreement([(0, r[1]) for r in test], 1, 2)
    lines.append(f'| Toujours « soleil » | - | {w * 100:.1f} | {e:.0%} |')
    print('\n| Source | Seuils soleil / couvert | Accord pondéré /100 | Catégorie exacte |\n|---|---|---|---|')
    print('\n'.join(lines))

    # where the airport goes wrong: confusion table and CAVOK hours
    th = best_thresholds([(r[2], r[1]) for r in fit], [x / 2 for x in range(1, 17)])
    conf = Counter((r[1], to_cat(r[2], *th)) for r in test)
    print('\nMETAR (lignes = satellite, colonnes = LFLS) :')
    for a in range(3):
        tot = sum(conf[(a, b)] for b in range(3))
        print(f'  {score.CATS[a]:8}', '  '.join(f'{score.CATS[b]} {conf[(a, b)] / tot:4.0%}' for b in range(3)))
    cav = [r for r in test if r[0] in metar and metar[r[0]]['cavok']]
    night = [scc[t] for t in scc if score.sky_info(t)[1] < -6]
    print(f'\nNébulosité « satellite » la nuit : {len(night)} heures, {sum(v is not None for v in night) / len(night):.0%} remplies,',
          f'valeurs distinctes {len(set(night))}')
    print(f'CAVOK / aucune couche : {len(cav) / len(test):.0%} des heures ;',
          'ciel satellite à ces heures :', {score.CATS[k]: f'{v / len(cav):.0%}' for k, v in sorted(Counter(r[1] for r in cav).items())})


if __name__ == '__main__':
    main()
