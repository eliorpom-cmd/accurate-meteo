"""Find the Météo-France station to train on for a place: nearest automatic stations and what they measure.

Usage: python3 trouver_station.py <département(s)> <latitude> <longitude> [--minutes]
  e.g.  python3 trouver_station.py 69,01 45.7578 4.8320
  --minutes also checks 6-minute rain (needed by the 2-hour rain model; large download)

A good station: within ~10 km, similar altitude, and every column marked ✓ (temperature, humidity, wind, gusts,
hourly rain). Pressure is often measured elsewhere: pick the nearest station with PMER as "station_pression".
Then copy ville.json to villes/<name>.json, fill it in, and run the pipeline with VILLE=villes/<name>.json.
"""
import csv, gzip, math, os, subprocess, sys
from collections import defaultdict

MF = 'https://meteofrance.s3.sbg.io.cloud.ovh.net/data/synchro_ftp/BASE'
DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'stations')
COLS = {'T': 'temp.', 'U': 'humid.', 'FF': 'vent', 'FXI': 'rafales', 'RR1': 'pluie', 'PMER': 'pression'}
RECENT = '2025'   # only rows from this year on: a station must still be measuring


def fetch(name, url):
    os.makedirs(DIR, exist_ok=True)
    path = os.path.join(DIR, name)
    if not os.path.exists(path):
        # curl: Python 3.14 rejects the certificate of Météo-France's storage server
        subprocess.run(['curl', '-sfL', '-o', path, url], check=True)
    return path


def km(lat1, lon1, lat2, lon2):
    r = math.radians
    a = math.sin(r(lat2 - lat1) / 2) ** 2 + math.cos(r(lat1)) * math.cos(r(lat2)) * math.sin(r(lon2 - lon1) / 2) ** 2
    return 12742 * math.asin(math.sqrt(a))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if len(args) != 3:
        sys.exit(__doc__)
    depts, lat, lon = args[0].split(','), float(args[1]), float(args[2])
    info, rows, seen = {}, defaultdict(int), defaultdict(lambda: defaultdict(int))
    for d in depts:
        with gzip.open(fetch(f'H_{d}_latest.csv.gz', f'{MF}/HOR/H_{d}_latest-2025-2026.csv.gz'), 'rt') as f:
            r = csv.reader(f, delimiter=';')
            i = {k.strip(): n for n, k in enumerate(next(r))}
            for row in r:
                if row[5][:4] < RECENT:
                    continue
                s = row[0]
                info[s] = (row[1], float(row[2]), float(row[3]), row[4])
                rows[s] += 1
                for c in COLS:
                    if c in i and row[i[c]].strip():
                        seen[s][c] += 1
    minutes = set()
    if '--minutes' in sys.argv:
        for d in depts:
            with gzip.open(fetch(f'MN_{d}_latest.csv.gz', f'{MF}/MIN/MN_{d}_latest-2025-2026.csv.gz'), 'rt') as f:
                r = csv.reader(f, delimiter=';')
                next(r)
                minutes |= {row[0] for row in r if row[6].strip()}
    near = sorted(info, key=lambda s: km(lat, lon, info[s][1], info[s][2]))[:12]
    print(f"{'station':<10} {'nom':<26} {'km':>5} {'alt.':>5}  " + '  '.join(f'{v:<8}' for v in COLS.values())
          + ('  6 min' if minutes else ''))
    for s in near:
        name, slat, slon, alt = info[s]
        marks = '  '.join(f"{'✓' if seen[s][c] > .9 * rows[s] else '·' if seen[s][c] else ' ':<8}" for c in COLS)
        print(f'{s:<10} {name[:26]:<26} {km(lat, lon, slat, slon):>5.1f} {alt:>5}  {marks}'
              + (f"  {'✓' if s in minutes else ' '}" if minutes else ''))
    print('\n✓ = measured more than 90 % of the hours since', RECENT, ' · = partly measured')


if __name__ == '__main__':
    main()
