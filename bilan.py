"""Score the live forecasts recorded on the `journal` branch against what the station really measured.

Every hour the production run records (journal/<UTC hour>.json): our next 48 hours, our half-days up to 7 days
and the 2-hour rain of the mega-model and of each weather model. This script compares them with Météo-France
observations once those are published (about a day later) and puts the result next to the backfilled scores
of RETRO.md, so a drift between "tested on the past" and "live" shows up.

Usage: .venv/bin/python bilan.py   (fetches the journal branch from GitHub, writes BILAN.md)
"""
import glob, json, os, subprocess
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import numpy as np
import blend
import modeles
import score

REPO = 'https://github.com/eliorpom-cmd/accurate-meteo.git'
JOURNAL = os.path.join(score.DATA, 'journal')


def fetch_journal():
    """Shallow copy of the journal branch in data/journal (updated on each run)."""
    if os.path.isdir(os.path.join(JOURNAL, '.git')):
        subprocess.run(['git', '-C', JOURNAL, 'pull', '-q', '--ff-only'], check=True)
    else:
        subprocess.run(['git', 'clone', '-q', '--depth', '1', '--branch', 'journal', REPO, JOURNAL], check=True)
    return [json.load(open(p)) for p in sorted(glob.glob(os.path.join(JOURNAL, 'journal', '*.json')))]


def observations(start, end):
    """Hourly station data + satellite sky over the journal period (load_obs only covers the training period)."""
    obs = score.load_obs()
    sat = score.api_chunk(score.SATELLITE, {'hourly': 'shortwave_radiation'}, start, end) or {}
    for ts, g in zip(sat.get('hourly', {}).get('time', []), sat.get('hourly', {}).get('shortwave_radiation', [])):
        t = score.utc(ts)
        if t in obs:
            cs, elev = score.sky_info(t)
            obs[t]['ratio'] = g / cs if g is not None and elev > 10 and cs > 50 else None
            obs[t]['cat'] = score.category(obs[t]['pluie_mm'], obs[t]['ratio'], score.RAIN_HOUR)
    return obs


def decide(p):
    """Same decision as the frozen models: the category with the best expected credit."""
    return int(np.argmax(np.asarray(p) @ blend.C.T))


def main():
    runs = fetch_journal()
    if not runs:
        raise SystemExit('journal vide')
    first = datetime.fromisoformat(runs[0]['genere_le'])
    today = datetime.now(timezone.utc).date()
    obs = observations(first.date().isoformat(), (today - timedelta(days=1)).isoformat())
    blocks = score.to_blocks(obs)
    slots = score.to_slots(score.load_6min_rain(), 6)

    hour = defaultdict(lambda: {'cond': ([], []), 'rain': ([], []), 'temp': []})
    half = defaultdict(lambda: {'cond': ([], []), 'temp': []})
    now2h = defaultdict(lambda: ([], []))
    for r in runs:
        made = datetime.fromisoformat(r['genere_le'])
        H = r.get('heures') or {'heure_utc': []}   # the first records only had the 2-hour rain
        for i, ts in enumerate(H['heure_utc']):
            t = datetime.fromisoformat(ts)
            o = obs.get(t)
            if not o:
                continue
            band = '0-12 h' if t - made <= timedelta(hours=12) else '12-24 h' if t - made <= timedelta(hours=24) else '24-48 h'
            if o.get('cat') is not None:
                hour[band]['cond'][0].append(decide(H['probas'][i])); hour[band]['cond'][1].append(o['cat'])
            if o.get('pluie_mm') is not None:
                hour[band]['rain'][0].append(H['pluie_proba'][i] >= .5); hour[band]['rain'][1].append(o['pluie_mm'] >= score.RAIN_HOUR)
            if o.get('temperature') is not None and H['temperature'][i] is not None:
                hour[band]['temp'].append(abs(H['temperature'][i] - o['temperature']))
        for j in r.get('jours', []):
            d = datetime.fromisoformat(j['date']).date()
            lead = (d - made.astimezone(score.PARIS).date()).days
            for part in ('matin', 'aprem'):
                o, f = blocks.get((d, part)), j.get(part)
                if not o or not f or lead < 1:
                    continue
                if o.get('cat') is not None:
                    half[lead]['cond'][0].append(score.CATS.index(f['condition'])); half[lead]['cond'][1].append(o['cat'])
                if o.get('temperature') is not None:
                    half[lead]['temp'].append(abs(f['temperature'] - o['temperature']))
        for k, ts in enumerate(r['tranches_utc']):
            s = datetime.fromisoformat(ts)
            if s not in slots:
                continue
            y = slots[s] >= score.RAIN_SLOT
            now2h['GRESIL'][0].append(r['mega_proba'][k] >= modeles.RAIN_2H_THRESHOLD); now2h['GRESIL'][1].append(y)
            for m, v in r['modeles'].items():
                if v[k] is not None:
                    now2h[m][0].append(v[k] >= score.RAIN_SLOT); now2h[m][1].append(y)

    def csi(p, y):
        p, y = np.array(p, dtype=bool), np.array(y, dtype=bool)
        return 100 * np.sum(p & y) / np.sum(p | y) if np.any(p | y) else float('nan')
    cond = lambda p, y: blend.summary(p, y)[0] if p else float('nan')
    out = ['# Bilan des prévisions en direct\n',
           f'{len(runs)} prévisions enregistrées du {first:%d/%m/%Y %H h} UTC au '
           f'{datetime.fromisoformat(runs[-1]["genere_le"]):%d/%m/%Y %H h} UTC, comparées à la station '
           f'{score.STATION_NOM} (observations publiées jusqu\'à la veille). '
           'Repères tirés de RETRO.md (prévisions rejouées sur le passé) : veille heure par heure 85,3/100, '
           'J+1 88,4, J+3 83,0, J+7 76,9, pluie 2 h 51,9 %.\n',
           '## Heure par heure\n', '| Échéance | Condition /100 | Réussite pluie % | Erreur temp. °C | Heures (jour) |',
           '|---|---|---|---|---|']
    for band in ('0-12 h', '12-24 h', '24-48 h'):
        h = hour[band]
        out.append(f"| {band} | {cond(*h['cond']):.1f} | {csi(*h['rain']):.1f} | "
                   f"{np.mean(h['temp']) if h['temp'] else float('nan'):.2f} | {len(h['cond'][0])} |")
    out += ['\n## Demi-journées\n', '| Échéance | Condition /100 | Erreur temp. °C | Demi-journées |', '|---|---|---|---|']
    for lead in sorted(half):
        h = half[lead]
        out.append(f"| J+{lead} | {cond(*h['cond']):.1f} | {np.mean(h['temp']) if h['temp'] else float('nan'):.2f} | {len(h['cond'][0])} |")
    out += ['\n## Pluie dans les 2 heures (tranches de 20 min)\n', '| Source | Réussite % | Tranches |', '|---|---|---|']
    for m, (p, y) in sorted(now2h.items(), key=lambda x: -csi(*x[1])):
        out.append(f'| {m} | {csi(p, y):.1f} | {len(p)} |')
    out.append('\nRéussite = cas de pluie bien annoncés / (bien annoncés + manqués + fausses alertes). '
               'Peu de cas = chiffres encore instables : attendre quelques semaines, et surtout des jours de pluie.')
    open(os.path.join(score.SORTIE, 'BILAN.md'), 'w').write('\n'.join(out) + '\n')
    print('\n'.join(out))


if __name__ == '__main__':
    main()
