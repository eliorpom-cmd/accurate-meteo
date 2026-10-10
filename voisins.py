"""Experiment: do forecasts at points around the city improve the frozen models? (roadmap 3b)

The frozen models only see each weather model at the station's grid point. Weather often arrives from a
neighbouring valley or ridge first, so here each model is also read at 8 points around (4 at ~15 km, 4 at ~30 km),
for the variables that decide the sky (sunlight, cloud cover, rain), forecast made 1 and 2 days before.

Same honest test as figer.py: train before SPLIT, score after, with and without the neighbours, on the same cases.
Targets: hourly condition and rain (day before), half-day condition at D+1 and D+2.

Usage: OMP_NUM_THREADS=4 nice -n 10 .venv/bin/python voisins.py   (≈1,700 weighted Open-Meteo calls, writes VOISINS.md)
"""
import json, math, os, urllib.request
import numpy as np
import figer
import modeles
import score

KM = 1 / 111.2   # degrees of latitude per km
RINGS = [(15, d) for d in (0, 90, 180, 270)] + [(30, d) for d in (45, 135, 225, 315)]  # (km, bearing)
MODELS = ['icon_eu', 'meteofrance_arome_france', 'meteofrance_seamless', 'ecmwf_ifs025', 'icon_seamless']
VARS = 'shortwave_radiation,cloud_cover,precipitation'
FEATS = ['ratio', 'pluie_mm', 'cloud']


def points():
    pts = []
    for dist, bearing in RINGS:
        b = math.radians(bearing)
        lat = score.LAT + dist * KM * math.cos(b)
        lon = score.LON + dist * KM * math.sin(b) / math.cos(math.radians(score.LAT))
        pts.append((f'{dist}km_{bearing}', round(lat, 4), round(lon, 4)))
    # terrain height of each point (one call): forecasts are then read at the real ground, not at the station's
    url = 'https://api.open-meteo.com/v1/elevation?latitude={}&longitude={}'.format(
        ','.join(str(p[1]) for p in pts), ','.join(str(p[2]) for p in pts))
    elev = json.load(urllib.request.urlopen(url, timeout=60))['elevation']
    return [(n, la, lo, e) for (n, la, lo), e in zip(pts, elev)]


def fetch(point):
    """Day-1 and day-2 forecasts of MODELS at one point. The API cache key has no coordinates, so each point
    gets its own cache folder."""
    name, lat, lon, elev = point
    keep = score.LAT, score.LON, score.ELEV, score.CACHE
    score.LAT, score.LON, score.ELEV = lat, lon, elev
    score.CACHE = os.path.join(score.DATA, 'cache_voisins', name)
    hv = ','.join(f'{v}_previous_day{d}' for d in (1, 2) for v in VARS.split(','))
    try:
        return {m: score.api(score.PREVIOUS, {'hourly': hv, 'models': m}) for m in MODELS}
    finally:
        score.LAT, score.LON, score.ELEV, score.CACHE = keep


def neighbour_rows(keys, nb, lead):
    """Extra columns: FEATS of every model at every point, for the given lead (1 or 2)."""
    cols = []
    for raw in nb.values():
        for m in MODELS:
            d = raw.get(m)
            if not d:
                cols.append(np.full((len(keys), len(FEATS)), np.nan))
                continue
            h = modeles.hours(d['hourly'], f'_previous_day{lead}')
            src = modeles.blocks(h) if isinstance(keys[0], tuple) else h
            cols.append(np.array([[np.nan if src.get(k, {}).get(v) is None else float(src[k][v]) for v in FEATS]
                                  for k in keys]))
    return np.hstack(cols)


def test(name, kind, keys, X, Xn, y):
    """Honest split: same cases, with and without the neighbours."""
    t = np.array([figer.day(k) >= figer.SPLIT for k in keys])
    out = []
    for X_ in (X, np.hstack([X, Xn])):
        est, keep = figer.fit('cls', X_[~t], y[~t])
        if kind == 'condition':
            from blend import summary
            out.append(summary(figer.predict_condition(est, keep, X_[t]), y[t])[0])
        else:
            out.append(figer.csi(est.predict_proba(X_[t][:, keep])[:, 1] >= .5, y[t].astype(bool)))
    line = f'| {name} | {out[0]:.1f} | **{out[1]:.1f}** | {out[1] - out[0]:+.1f} | {t.sum()} |'
    print(line, flush=True)
    return line


def main():
    pts = points()
    print('points :', pts, flush=True)
    nb = {p[0]: fetch(p) for p in pts}
    obs = score.load_obs()
    lines = []

    # hourly, day before
    hv = ','.join(f'{v}_previous_day1' for v in score.VARS)
    fcs = {m: modeles.hours(score.api(score.PREVIOUS, {'hourly': hv, 'models': m})['hourly'], '_previous_day1')
           for m in score.HOURLY_MODELS}
    keys, X, y = figer.build(fcs, obs, score.HOURLY_MODELS, lambda o: o['cat'], lambda o, k: o['cat'] is not None)
    lines.append(test('heure_condition (veille)', 'condition', keys, X, neighbour_rows(keys, nb, 1), y))
    keys, X, y = figer.build(fcs, obs, score.HOURLY_MODELS, lambda o: o['pluie_mm'] >= score.RAIN_HOUR,
                             lambda o, k: o['pluie_mm'] is not None)
    lines.append(test('heure_pluie (veille, réussite %)', 'pluie', keys, X, neighbour_rows(keys, nb, 1), y.astype(int)))

    # half-days, D+1 and D+2
    oblocks = score.to_blocks(obs)
    hv = ','.join(f'{v}_previous_day{d}' for d in (1, 2) for v in score.VARS)
    raw = {m: score.api(score.PREVIOUS, {'hourly': hv, 'models': m}) for m in score.TREND_MODELS}
    for lead in (1, 2):
        fcs = {m: modeles.blocks(modeles.hours(d['hourly'], f'_previous_day{lead}')) for m, d in raw.items()}
        keys, X, y = figer.build(fcs, oblocks, score.TREND_MODELS, lambda o: o['cat'], lambda o, k: o['cat'] is not None)
        lines.append(test(f'bloc{lead}_condition (J+{lead})', 'condition', keys, X, neighbour_rows(keys, nb, lead), y))

    report = ['# Points voisins (roadmap 3b)\n',
              f'Chaque modèle lu aussi en {len(pts)} points autour de {score.NOM} '
              f'({", ".join(p[0] for p in pts)}), modèles {", ".join(MODELS)}, variables {VARS}. '
              f'Test honnête : entraîné avant le {figer.SPLIT}, noté après, mêmes cas avec et sans voisins.\n',
              '| Modèle | Sans voisins | Avec voisins | Écart | Cas testés |', '|---|---|---|---|---|', *lines]
    open(os.path.join(score.SORTIE, 'VOISINS.md'), 'w').write('\n'.join(report) + '\n')


if __name__ == '__main__':
    main()
