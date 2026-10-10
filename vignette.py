"""Open Graph image (1200×630) drawn from prevision.json: the next 7 days, morning and afternoon, like the site.

Redrawn by every production run next to prevision.json, so a shared link shows the forecast of the moment
(apps keep the preview they fetched at sharing time: the image carries the time of the forecast).

Usage: python3 vignette.py [prevision.json] [og.png]
"""
import json, math, os, sys
from datetime import date, datetime
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
W, H, K = 1200, 630, 2                       # drawn at 2× then reduced: smooth edges
BG, TILE, INK, DIM = '#f1f1f3', '#ffffff', '#121316', '#6e7178'
SKY = {'soleil': '#ffe39a', 'mitigé': '#fdf0cc', 'couvert': '#e3e7ee', 'pluie': '#cfe1ff', 'nuit': '#dde2ec'}
SUN, CLOUD, CLOUD2, DROP = '#ffb800', '#8f9bab', '#bcc5d1', '#1d5fd6'
MOIS_COURTS = ['janv.', 'févr.', 'mars', 'avr.', 'mai', 'juin', 'juil.', 'août', 'sept.', 'oct.', 'nov.', 'déc.']
JOURS = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
MOIS = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre',
        'novembre', 'décembre']


def font(name, size, axes):
    f = ImageFont.truetype(os.path.join(ROOT, 'polices', name), size * K)
    f.set_variation_by_axes(axes)
    return f


def sun(d, cx, cy, r):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=SUN)
    for i in range(8):
        a = i * math.pi / 4
        d.line([cx + (r * 1.35) * math.cos(a), cy + (r * 1.35) * math.sin(a),
                cx + (r * 1.75) * math.cos(a), cy + (r * 1.75) * math.sin(a)], fill=SUN, width=max(2, int(r * .28)))


def cloud(d, cx, cy, s, col):
    """Cloud of width ≈ 2.2 s centred on (cx, cy): flat base, two bumps."""
    d.rounded_rectangle([cx - 1.1 * s, cy - .1 * s, cx + 1.1 * s, cy + .55 * s], radius=.33 * s, fill=col)
    d.ellipse([cx - .85 * s, cy - .55 * s, cx - .05 * s, cy + .25 * s], fill=col)
    d.ellipse([cx - .35 * s, cy - .85 * s, cx + .75 * s, cy + .25 * s], fill=col)


def icon(d, cond, cx, cy, s):
    if cond == 'soleil':
        sun(d, cx, cy, .42 * s)
    elif cond == 'mitigé':
        sun(d, cx + .35 * s, cy - .3 * s, .3 * s)
        cloud(d, cx - .1 * s, cy + .15 * s, .5 * s, CLOUD)
    elif cond == 'couvert':
        cloud(d, cx + .3 * s, cy - .2 * s, .38 * s, CLOUD2)
        cloud(d, cx - .1 * s, cy + .12 * s, .5 * s, CLOUD)
    elif cond == 'pluie':
        cloud(d, cx, cy - .1 * s, .5 * s, CLOUD)
        for dx in (-.3, 0, .3):
            x = cx + dx * s
            d.line([x, cy + .38 * s, x - .1 * s, cy + .62 * s], fill=DROP, width=max(2, int(.08 * s)))
    else:   # nuit
        r = .38 * s
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill='#7b8494')
        d.ellipse([cx - r + .32 * s, cy - r - .1 * s, cx + r + .32 * s, cy + r - .1 * s], fill=SKY['nuit'])


def draw(prev, out_path):
    im = Image.new('RGB', (W * K, H * K), BG)
    d = ImageDraw.Draw(im)
    title, small = font('BricolageGrotesque.ttf', 64, [48, 700, 100]), font('Figtree.ttf', 24, [500])
    name, temp = font('BricolageGrotesque.ttf', 24, [24, 700, 100]), font('BricolageGrotesque.ttf', 30, [24, 500, 100])
    made = datetime.fromisoformat(prev['genere_le'])
    d.text((56 * K, 52 * K), 'Météo Grenoble', font=title, fill=INK)
    d.text((58 * K, 136 * K), f"Prévision du {JOURS[made.weekday()].lower()} {made.day} {MOIS[made.month - 1]}, "
           f"{made.hour} h {made.minute:02d}", font=small, fill=DIM)

    jours = [j for j in prev['jours'] if j.get('matin') or j.get('aprem')][:7]
    x0, gap, top, bottom = 56 * K, 12 * K, 196 * K, (H - 52) * K
    tw = (W * K - 2 * x0 - gap * (len(jours) - 1)) / max(1, len(jours))
    today = made.date()
    for i, j in enumerate(jours):
        x = x0 + i * (tw + gap)
        d.rounded_rectangle([x, top, x + tw, bottom], radius=26 * K, fill=TILE)
        dd = date.fromisoformat(j['date'])
        label = "Aujourd'hui" if dd == today else 'Demain' if (dd - today).days == 1 else JOURS[dd.weekday()]
        size = 24
        while size > 16 and d.textlength(label, font=font('BricolageGrotesque.ttf', size, [24, 700, 100])) > tw - 28 * K:
            size -= 1   # long names ("Aujourd'hui", "Mercredi") shrink to fit the tile
        d.text((x + 14 * K, top + 14 * K), label, font=font('BricolageGrotesque.ttf', size, [24, 700, 100]), fill=INK)
        d.text((x + 14 * K, top + 46 * K), f'{dd.day} {MOIS_COURTS[dd.month - 1]}', font=small, fill=DIM)
        halves = [j[p] for p in ('matin', 'aprem') if j.get(p)]
        py0, py1, pad = top + 86 * K, bottom - 6 * K, 6 * K
        hh = (py1 - py0) / len(halves)
        # one pill per day: the halves are clipped to a rounded shape, no divider between them
        mask = Image.new('L', im.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle([x + pad, py0, x + tw - pad, py1], radius=20 * K, fill=255)
        layer = Image.new('RGB', im.size, TILE)
        ld = ImageDraw.Draw(layer)
        for k, h in enumerate(halves):
            y = py0 + k * hh
            ld.rectangle([x + pad, y, x + tw - pad, y + hh], fill=SKY.get(h['condition'], SKY['couvert']))
            icon(ld, h['condition'], x + tw / 2, y + hh * .4, 58 * K)
            t = f"{round(h['temperature'])}°"
            ld.text((x + tw / 2, y + hh * .78), t, font=temp, fill=INK, anchor='mm')
        im.paste(layer, (0, 0), mask)
    im.resize((W, H), Image.LANCZOS).save(out_path, optimize=True)


if __name__ == '__main__':
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'out', 'prevision.json')
    draw(json.load(open(src)), sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(src), 'og.png'))
