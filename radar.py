"""Rain radar around the station, recorded live to train a 2-hour rain model later (no free radar archive exists).

Source: RainViewer public API (national radars merged, one frame every 10 minutes, the last 2 hours kept,
zoom 7 at most ≈ 0.9 km per pixel). Its "Universal Blue" colours map one-to-one to reflectivity (dBZ),
so each pixel is decoded back to dBZ with RainViewer's own colour table.

Each hourly journal record keeps the 13 frames then available: frames overlap from one hour to the next,
so the record stays continuous even when a run is skipped. Per frame: reflectivity at the station (max over
3×3 pixels) and a 16×16 grid of 4×4-pixel maxima (≈3.5 km cells, ≈55 km square centred on the station),
stored as base64 int8 dBZ, row by row from the north-west corner (decode: np.frombuffer(base64.b64decode(g), np.int8)).

Usage (test): python3 radar.py
"""
import base64, csv, io, json, math, subprocess
import numpy as np
from PIL import Image
import score

MAPS = 'https://api.rainviewer.com/public/weather-maps.json'
COLOURS = 'https://www.rainviewer.com/files/rainviewer_api_colors_table.csv'
ZOOM, TILE, SCHEME = 7, 256, 2          # 2 = Universal Blue, the only scheme of the public API
CROP, CELL = 64, 4                      # 64×64 pixels around the station, kept as 16×16 cells
NONE = -32                              # no echo


def _get(url, binary=False):
    # curl: same certificate trouble as other hosts with some Python builds
    out = subprocess.run(['curl', '-sf', '--max-time', '20', url], capture_output=True, check=True).stdout
    return out if binary else out.decode()


def _palette():
    rows = list(csv.reader(io.StringIO(_get(COLOURS))))
    col = rows[0].index('Universal Blue')
    pal = {}
    for r in rows[1:]:
        h = r[col].lstrip('#').lower()
        if not h.endswith('00'):   # fully transparent = no echo
            pal.setdefault(tuple(int(h[i:i + 2], 16) for i in (0, 2, 4, 6)), int(r[0]))
    return pal


def _pixel(lat, lon):
    n = 2 ** ZOOM * TILE
    x = (lon + 180) / 360 * n
    y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n
    return int(x), int(y)


def frames():
    """[{'temps_utc', 'centre_dbz', 'grille'}] for every frame RainViewer currently serves."""
    maps, pal = json.loads(_get(MAPS)), _palette()
    cx, cy = _pixel(score.LAT, score.LON)
    x0, y0 = cx - CROP // 2, cy - CROP // 2
    tiles = {(tx, ty) for tx in (x0 // TILE, (x0 + CROP - 1) // TILE) for ty in (y0 // TILE, (y0 + CROP - 1) // TILE)}
    out = []
    for f in maps['radar']['past']:
        canvas = np.full((CROP, CROP), NONE, dtype=np.int16)
        for tx, ty in tiles:
            png = _get(f"{maps['host']}{f['path']}/{TILE}/{ZOOM}/{tx}/{ty}/{SCHEME}/0_0.png", binary=True)
            px = np.asarray(Image.open(io.BytesIO(png)).convert('RGBA'))
            dbz = np.full(px.shape[:2], NONE, dtype=np.int16)
            for rgba, v in pal.items():
                dbz[np.all(px == rgba, axis=-1)] = v
            # paste the part of this tile that falls inside the crop
            gx, gy = tx * TILE, ty * TILE
            a0, a1 = max(x0, gx), min(x0 + CROP, gx + TILE)
            b0, b1 = max(y0, gy), min(y0 + CROP, gy + TILE)
            if a0 < a1 and b0 < b1:
                canvas[b0 - y0:b1 - y0, a0 - x0:a1 - x0] = dbz[b0 - gy:b1 - gy, a0 - gx:a1 - gx]
        c = CROP // 2
        grid = canvas.reshape(CROP // CELL, CELL, CROP // CELL, CELL).max(axis=(1, 3))
        out.append({'temps_utc': f['time'], 'centre_dbz': int(canvas[c - 1:c + 2, c - 1:c + 2].max()),
                    'grille': base64.b64encode(grid.astype(np.int8).tobytes()).decode()})
    return out


def record():
    """Journal block; never raises (the forecast must not depend on the radar)."""
    try:
        fr = frames()
        return {'source': 'RainViewer', 'zoom': ZOOM, 'cellule_px': CELL, 'taille': CROP // CELL, 'images': fr}
    except Exception as e:
        print(f'  radar indisponible : {e}', flush=True)
        return None


if __name__ == '__main__':
    r = record()
    if r:
        last = r['images'][-1]
        g = np.frombuffer(base64.b64decode(last['grille']), np.int8).reshape(r['taille'], r['taille'])
        print(len(r['images']), 'images ; dernière :', last['temps_utc'], '; au-dessus de la station :', last['centre_dbz'], 'dBZ')
        print('\n'.join(''.join(' ' if v <= 5 else '.' if v < 20 else 'o' if v < 35 else '#' for v in row) for row in g))
