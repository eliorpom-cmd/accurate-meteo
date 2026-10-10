"""Shared definitions of the frozen production models: which models feed them and how inputs are built.

The same functions build the inputs for training (archived forecasts) and for the live forecast (prevoir.py),
so both always line up column for column.

Frozen models (HistGradientBoosting, every parameter of every weather model, no live observations):
  - heure_*  : hourly, forecast made the day before (score.HOURLY_MODELS)
               condition (daytime), pluie (rain ≥ 0.2 mm in the hour, day and night), temperature, vent, rafales
  - bloc{L}_*: morning / afternoon half-days, L = 1..7 days ahead (score.TREND_MODELS)
               condition, temperature (mean), rafales (max)
  - pluie2h  : rain in 20-minute slots over the next 2 hours (score.NOWCAST_MODELS)
"""
import math
from datetime import timedelta
import numpy as np
import score

FEATS = ['ratio', 'pluie_mm', 'cloud', 'humidite', 'vent', 'rafales', 'pression', 'temperature']
NOW_CTX = ['relative_humidity_2m', 'cloud_cover', 'shortwave_radiation', 'wind_speed_10m', 'wind_gusts_10m',
           'pressure_msl', 'precipitation', 'temperature_2m']
SLOT = timedelta(minutes=20)
RAIN_2H_THRESHOLD = 0.38  # probability above which a slot is announced rainy (chosen on training months)


def hours(H, suffix=''):
    """Open-Meteo hourly block → {utc time: forecast dict}, with cloud cover kept as a feature."""
    out = score.forecast_hours(H, suffix)
    cc = H.get('cloud_cover' + suffix)
    for (t, f), n in zip(out.items(), range(len(H['time']))):
        f['cloud'] = cc[n] if cc else None
    return out


def blocks(hrs):
    """Hourly forecasts → morning / afternoon blocks, with mean cloud cover."""
    b = score.to_blocks(hrs)
    acc = {}
    for t, h in hrs.items():
        loc = t.astimezone(score.PARIS)
        part = 'matin' if 7 <= loc.hour <= 12 else 'aprem' if 13 <= loc.hour <= 18 else None
        if part and h.get('cloud') is not None:
            acc.setdefault((loc.date(), part), []).append(h['cloud'])
    for k, v in b.items():
        v['cloud'] = sum(acc[k]) / len(acc[k]) if k in acc else None
    return b


def calendar(k):
    if isinstance(k, tuple):
        doy, part = k[0].timetuple().tm_yday, float(k[1] == 'aprem')
    else:
        loc = k.astimezone(score.PARIS)
        doy, part = loc.timetuple().tm_yday, loc.hour
    return [part, math.sin(2 * math.pi * doy / 365), math.cos(2 * math.pi * doy / 365)]


def row(k, fcs, models):
    """One input row: calendar + FEATS of every model, in the frozen model order (missing → NaN)."""
    r = calendar(k)
    for m in models:
        f = fcs.get(m, {}).get(k, {})
        r += [np.nan if f.get(v) is None else float(f[v]) for v in FEATS]
    return r


def slots(M):
    """Open-Meteo minutely_15 block → rain per 20-minute slot."""
    return score.to_slots({score.utc(t): v for t, v in zip(M['time'], M['precipitation']) if v is not None}, 15)


def hourly_ctx(H):
    n = len(H['time'])
    return {score.utc(t): [H.get(v, [None] * n)[i] for v in NOW_CTX] for i, t in enumerate(H['time'])}


def rain_row(s, mslots, hctx, models):
    """Same inputs as submodel_pluie_2h.model_features (variant 1, models only)."""
    loc = s.astimezone(score.PARIS)
    doy = loc.timetuple().tm_yday
    r = [loc.hour + loc.minute / 60, math.sin(2 * math.pi * doy / 365), math.cos(2 * math.pi * doy / 365)]
    h = s.replace(minute=0) + timedelta(hours=1)  # hour ending after the slot (Open-Meteo convention)
    nan = lambda x: np.nan if x is None else float(x)
    for m in models:
        sl = mslots.get(m, {})
        r += [nan(sl.get(s - SLOT)), nan(sl.get(s)), nan(sl.get(s + SLOT))]
        r += [nan(x) for x in hctx.get(m, {}).get(h, [None] * len(NOW_CTX))]
    return r
