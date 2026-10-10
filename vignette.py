"""Open Graph image (1200×630) drawn from prevision.json: the next 7 days, morning and afternoon, like the site.

Redrawn by every production run next to prevision.json, so a shared link shows the forecast of the moment
(apps keep the preview they fetched at sharing time: the image carries the time of the forecast).

Usage: python3 vignette.py [prevision.json] [og.png]
"""
import json, math, os, sys
from datetime import date, datetime
from PIL import Image, ImageChops, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
W, H, K = 1200, 630, 2                       # drawn at 2× then reduced: smooth edges
BG, TILE, INK, DIM = '#f1f1f3', '#ffffff', '#121316', '#6e7178'
# same skies as the site: a gradient per state (top, bottom), white text on it
SKY = {'soleil': ('#2f86f0', '#1652c8'), 'mitigé': ('#5b87c4', '#30589c'), 'couvert': ('#7d889a', '#4f5a6b'),
       'pluie': ('#4a5c7c', '#26334c'), 'nuit': ('#1c2860', '#0a102c')}
BRAND = '#1347c2'
MOIS_COURTS = ['janv.', 'févr.', 'mars', 'avr.', 'mai', 'juin', 'juil.', 'août', 'sept.', 'oct.', 'nov.', 'déc.']
JOURS = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
MOIS = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre',
        'novembre', 'décembre']


def font(name, size, axes):
    f = ImageFont.truetype(os.path.join(ROOT, 'polices', name), size * K)
    f.set_variation_by_axes(axes)
    return f


def hexa(c):
    return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))


def gradient(d, box, top, bottom):
    """Vertical gradient filling box, one line per pixel row."""
    x0, y0, x1, y1 = box
    a, b = hexa(top), hexa(bottom)
    n = max(1, int(y1 - y0))
    for k in range(n):
        t = k / n
        d.line([x0, y0 + k, x1, y0 + k], fill=tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3)))


def badge(im, x, y, size):
    """The site's icon: blue square, halftone dots that swell toward the bottom-left, cut by the rounded corners."""
    size = int(size)
    tile = Image.new('RGB', (size, size), BRAND)
    td = ImageDraw.Draw(tile)
    u, step = size / 48, 7.2
    for i in range(-1, 8):
        for j in range(-1, 8):
            cx, cy = 1 + j * step + (step / 2 if i % 2 else 0), 1 + i * step
            r = .4 + 3.3 * min(1, max(0, (cy * .85 + (48 - cx) * .55) / 58)) ** 1.2
            td.ellipse([(cx - r) * u, (cy - r) * u, (cx + r) * u, (cy + r) * u], fill='#ffffff')
    mask = Image.new('L', (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1], radius=size * .22, fill=255)
    im.paste(tile, (int(x), int(y)), mask)


# ---- weather symbols, same drawing as the site (filled, Apple Weather manner), on a 48-unit grid ----
# cloud = three circles on a flat base; shapes behind are cut by the front one grown by a gap
CLOUD = [(13.5, 29, 6), (24.5, 23, 9.8), (35, 28, 7)]
SUNC, RAINC = '#ffcc00', '#7cc4ff'


class Sym:
    """Draws one icon of `size` px whose top-left corner is (x0, y0): every shape is a mask, colours at the end."""
    def __init__(self, size):
        self.n, self.u = int(size), size / 48

    def mask(self):
        return Image.new('L', (self.n, self.n), 0)

    def cloud(self, dx=0, dy=0, k=1, grow=0):
        m = self.mask(); d = ImageDraw.Draw(m); u = self.u
        for cx, cy, r in CLOUD:
            x, y, rr = (dx + k * cx) * u, (dy + k * cy) * u, (k * r + grow) * u
            d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=255)
        d.rectangle([(dx + k * 13.5) * u, (dy + k * 28) * u, (dx + k * 35) * u, (dy + k * 35 + grow) * u], fill=255)
        return m

    def sun(self, x, y, r):
        m = self.mask(); d = ImageDraw.Draw(m); u = self.u
        d.ellipse([(x - r) * u, (y - r) * u, (x + r) * u, (y + r) * u], fill=255)
        for i in range(8):
            t = i * math.pi / 4
            self.stroke(d, x + (r + 3.4) * math.cos(t), y + (r + 3.4) * math.sin(t), x + (r + 7) * math.cos(t), y + (r + 7) * math.sin(t), 2.8)
        return m

    def moon(self, dx=0, dy=0, k=1):
        m = self.mask(); d = ImageDraw.Draw(m); u = self.u
        a, b = (27.06, 22, 12.5), (32.8, 18.15, 10.42)   # crescent = disc a minus disc b (the site's path)
        d.ellipse([(dx + k * (a[0] - a[2])) * u, (dy + k * (a[1] - a[2])) * u, (dx + k * (a[0] + a[2])) * u, (dy + k * (a[1] + a[2])) * u], fill=255)
        d.ellipse([(dx + k * (b[0] - b[2])) * u, (dy + k * (b[1] - b[2])) * u, (dx + k * (b[0] + b[2])) * u, (dy + k * (b[1] + b[2])) * u], fill=0)
        return m

    def star(self, x, y, r):
        m = self.mask(); u = self.u
        pts = []
        for i in range(16):   # four-point sparkle: long tips, pinched waist
            t = i * math.pi / 8; rr = r if i % 4 == 0 else r * (.32 if i % 2 else .45)
            pts.append(((x + rr * math.cos(t)) * u, (y + rr * math.sin(t)) * u))
        ImageDraw.Draw(m).polygon(pts, fill=255)
        return m

    def rain(self, xs=(17, 24, 31), y=38):
        m = self.mask(); d = ImageDraw.Draw(m)
        for x in xs:
            self.stroke(d, x, y, x - 2.4, y + 6, 3)
        return m

    def stroke(self, d, x1, y1, x2, y2, w):
        u = self.u
        d.line([x1 * u, y1 * u, x2 * u, y2 * u], fill=255, width=max(1, round(w * u)))
        for x, y in ((x1, y1), (x2, y2)):   # round caps
            d.ellipse([(x - w / 2) * u, (y - w / 2) * u, (x + w / 2) * u, (y + w / 2) * u], fill=255)

    @staticmethod
    def cut(back, front):
        return ImageChops.subtract(back, front)


def icon(layer, cond, cx, cy, s):
    """Symbol of about s px centred on (cx, cy), drawn onto `layer` (white cloud, light rain: they sit on a sky)."""
    S = Sym(s * 1.65)
    parts = []   # (mask, colour), painted in order
    c = lambda *a, **k: S.cloud(*a, **k)
    if cond == 'soleil':
        parts = [(S.sun(24, 24, 9), SUNC)]
    elif cond == 'mitigé':
        parts = [(Sym.cut(S.sun(31, 17, 7), c(-3, 7, .95, 2.6)), SUNC), (c(-3, 7, .95), '#ffffff')]
    elif cond == 'couvert':
        parts = [(Sym.cut(c(9, -3, .72), c(-3, 6, 1, 2.6)), '#c9d3e3'), (c(-3, 6), '#ffffff')]
    elif cond == 'pluie':
        parts = [(c(0, -4), '#ffffff'), (Sym.cut(S.rain(), c(0, -4, 1, 1.6)), RAINC)]
    else:   # nuit
        parts = [(S.moon(-2, 0), '#ffffff'), (S.star(36, 12, 3.2), SUNC), (S.star(39, 22, 2), SUNC)]
    x0, y0 = int(cx - S.n / 2), int(cy - S.n / 2)
    for m, col in parts:
        layer.paste(Image.new('RGB', m.size, col), (x0, y0), m)


def draw(prev, out_path):
    im = Image.new('RGB', (W * K, H * K), BG)
    d = ImageDraw.Draw(im)
    title, small = font('HostGrotesk.ttf', 64, [700]), font('HostGrotesk.ttf', 24, [500])
    name, temp = font('HostGrotesk.ttf', 24, [700]), font('HostGrotesk.ttf', 30, [500])
    made = datetime.fromisoformat(prev['genere_le'])
    d.text((56 * K, 52 * K), 'Météo Grenoble', font=title, fill=INK)
    badge(im, (W - 56 - 96) * K, 48 * K, 96 * K)
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
        while size > 16 and d.textlength(label, font=font('HostGrotesk.ttf', size, [700])) > tw - 28 * K:
            size -= 1   # long names ("Aujourd'hui", "Mercredi") shrink to fit the tile
        d.text((x + 14 * K, top + 14 * K), label, font=font('HostGrotesk.ttf', size, [700]), fill=INK)
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
            gradient(ld, [x + pad, y, x + tw - pad, y + hh], *SKY.get(h['condition'], SKY['couvert']))
            # icon in the upper part, temperature below with clear air between them (rays used to touch it)
            icon(layer, h['condition'], x + tw / 2, y + hh * .37, 40 * K)
            t = f"{round(h['temperature'])}°"
            ld.text((x + tw / 2, y + hh * .78), t, font=temp, fill='#ffffff', anchor='mm')
        im.paste(layer, (0, 0), mask)
    im.resize((W, H), Image.LANCZOS).save(out_path, optimize=True)


if __name__ == '__main__':
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'out', 'prevision.json')
    draw(json.load(open(src)), sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(src), 'og.png'))
