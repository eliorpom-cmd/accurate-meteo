"""EUMETSAT cloud mask (MSG 0°, CLM: infrared + visible, day and night) around Grenoble, one value per hour.

Read from EUMETSAT's public map server (view.eumetsat.int, WMS, no account, archive since 09/2020):
a 5 x 5 pixel image centred on Grenoble (~20 x 20 km, about the satellite's own pixel size) at mid-hour,
white = cloud, green/blue = clear. Each pixel is kept, row by row from the north-west ("1" = cloud, "0" = clear),
so the valley pixel and the mountains around can be told apart:
data/ciel_nuit/clm_px.json {"2024-02-01T03:00": "0011001110...", ...}, resumable.
(clm.json, the first run, only kept the cloud share of a 6 x 5 box: the mountains blurred the valley's sky.)
Also the cloud top height (msg_fes:cth, colour-coded, legend not published): `clm.py cth` keeps each pixel's
colour as 6 hex digits ("ffff00..." x 25) in data/ciel_nuit/cth_px.json, read as height classes by a learned model.
Run: .venv/bin/python clm.py [cth]
"""
import io
import json
import os
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

from PIL import Image

import score

LAYER = sys.argv[1] if len(sys.argv) > 1 else 'clm'
OUT = os.path.join(score.DATA, 'ciel_nuit', f'{LAYER}_px.json')
WMS = ('https://view.eumetsat.int/geoserver/ows?service=WMS&version=1.3.0&request=GetMap&layers=msg_fes:' + LAYER + '&styles='
       '&crs=EPSG:4326&bbox={s},{w},{n},{e}&width=5&height=5&format=image/png&time={t}')
BOX = dict(s=score.LAT - .1, n=score.LAT + .1, w=score.LON - .11, e=score.LON + .11)   # centre pixel = Grenoble


def pixels(t):
    """Cloud mask of the 25 pixels at mid-hour of the hour ending at t (None if the image fails)."""
    url = WMS.format(**BOX, t=(t - timedelta(minutes=30)).strftime('%Y-%m-%dT%H:%M:00Z'))
    for attempt in range(4):
        try:
            im = Image.open(io.BytesIO(urllib.request.urlopen(url, timeout=60).read())).convert('RGB')
            px = [im.getpixel((x, y)) for y in range(5) for x in range(5)]
            if LAYER == 'cth':
                return ''.join('%02x%02x%02x' % p for p in px)
            return ''.join('1' if min(p) > 200 else '0' for p in px)
        except Exception:
            time.sleep(5 * (attempt + 1))
    return None


def main():
    done = json.load(open(OUT)) if os.path.exists(OUT) else {}
    t, end = datetime(2024, 2, 1, 1, tzinfo=timezone.utc), datetime(2026, 10, 9, tzinfo=timezone.utc)
    todo = []
    while t < end:
        if t.strftime('%Y-%m-%dT%H:%M') not in done:
            todo.append(t)
        t += timedelta(hours=1)
    print(len(done), 'déjà là,', len(todo), 'à télécharger', flush=True)
    # parallel requests to EUMETSAT's public server: 16 made the server answer in 3.5 s instead of 0.6 s: keep 6
    with ThreadPoolExecutor(int(os.environ.get('FILS', 6))) as pool:
        for n, (t, f) in enumerate(zip(todo, pool.map(pixels, todo)), 1):
            if f is not None:
                done[t.strftime('%Y-%m-%dT%H:%M')] = f
            if n % 500 == 0 or n == len(todo):
                json.dump(done, open(OUT, 'w'))
                print(n, '/', len(todo), flush=True)


if __name__ == '__main__':
    main()
