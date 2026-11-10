"""Fantomine v2 : aperçu (avant code) de la pédale au format double 2350 x 1800.

Compose le fond (make_art.py), les potards (calques make_knob.py), le titre néon vectoriel (Lora),
les textes vectoriels (Poppins), le logo officiel NINE HANDS | DSP (SVG blanc), la barre de presets
de référence (400 x 38 unités, Poppins Medium 23), l'écran, la LED et le levier d'octave.
Usage : python3 tools/preview.py <dossier> [glow]
"""
import json, math, os, sys
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import knob_preview as kp

AS = 2.0
LAY = json.load(open(os.path.join(HERE, 'layout.json')))
POP_M = os.path.join(ROOT, 'Poppins-Medium.ttf'); POP_R = os.path.join(ROOT, 'Poppins-Regular.ttf'); POP_B = os.path.join(ROOT, 'Poppins-Bold.ttf')
LORA = '/usr/share/fonts/truetype/google-fonts/Lora-Variable.ttf'
MINT = (126, 240, 214)
SILK = (224, 222, 232)         # sérigraphie claire du design
SILK2 = (196, 192, 210)
KNOB_NAMES = ['GLIDE', 'RANGE', 'TONE', 'VIBRATO', 'SPEED', 'BLEND']
KNOB_MINMAX = [('FAST', 'SLOW'), ('±1', '±24'), ('PURE', 'REED'), ('0', 'WIDE'), ('SLOW', 'FAST'), ('DRY', 'VOICE')]
KNOB_VALS = [0.30, 0.50, 0.35, 0.30, 0.45, 0.80]

def P(u): return u * AS

def font(path, size_u, wght=None):
    f = ImageFont.truetype(path, int(round(P(size_u))))
    if wght is not None:
        try: f.set_variation_by_axes([wght])
        except Exception: pass
    return f

def text_c(d, xy_u, txt, f, fill, spacing_u=0.0, anchor='mm'):
    x, y = P(xy_u[0]), P(xy_u[1])
    if spacing_u <= 0:
        d.text((x, y), txt, font=f, fill=fill, anchor=anchor); return
    ws = [d.textlength(ch, font=f) for ch in txt]
    tot = sum(ws) + P(spacing_u) * (len(txt) - 1)
    cx = x - tot / 2
    for ch, w in zip(txt, ws):
        d.text((cx, y), ch, font=f, fill=fill, anchor='lm'); cx += w + P(spacing_u)

def compose(on=True, glow=1.0, note='A3', cents='+0 ¢', status=None):
    bg = Image.open(os.path.join(ROOT, 'background.png')).convert('RGBA')
    W, H = bg.size
    img = Image.new('RGBA', (W, H), (22, 21, 26, 255)); img.alpha_composite(bg)
    d = ImageDraw.Draw(img)
    lightL = 1.0 if on else 0.0

    # ---------------- titre néon (vectoriel, police du design : Lora)
    tf = font(LORA, 100, 640)
    tl = Image.new('L', (W, H), 0); ImageDraw.Draw(tl).text((P(LAY['title'][0]), P(LAY['title'][1])), 'Fantomine', font=tf, anchor='mm', fill=255)
    tA = np.asarray(tl).astype(np.float32) / 255
    # tube de verre éteint : lavande grise, relief (biseau éclairé en haut à gauche)
    edge = cv2.GaussianBlur(tA, (0, 0), 2.2)
    bevel = np.clip((np.roll(np.roll(edge, 3, 0), 3, 1) - np.roll(np.roll(edge, -3, 0), -3, 1)) * 1.6, -1, 1)
    glass = np.dstack([np.full_like(tA, 118), np.full_like(tA, 110), np.full_like(tA, 150)]) + (bevel * 60)[..., None]
    base = np.asarray(img).astype(np.float32)
    shadow = cv2.GaussianBlur(np.roll(np.roll(tA, 6, 0), 6, 1), (0, 0), 5) * 0.45 * (1 - tA)
    base[..., :3] *= (1 - shadow)[..., None]
    if on:
        core = np.array([178, 250, 230.0]); hot = np.array([232, 255, 248.0])
        inner = cv2.GaussianBlur(tA, (0, 0), 1.2)
        lit = core[None, None] * (1 - inner[..., None] * 0.5) + hot[None, None] * (inner[..., None] * 0.5)
        col = lit
        halo = (cv2.GaussianBlur(tA, (0, 0), 14) * 0.85 + cv2.GaussianBlur(tA, (0, 0), 40) * 0.45) * glow
        base[..., :3] = base[..., :3] * (1 - halo[..., None] * 0.55) + np.array(MINT, np.float32) * (halo[..., None] * 0.55)
    else:
        col = glass
    base[..., :3] = base[..., :3] * (1 - tA[..., None]) + col * tA[..., None]
    img = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8), 'RGBA'); d = ImageDraw.Draw(img)
    text_c(d, LAY['subtitle'], 'THEREMIN VOICE', font(POP_M, 17.5), SILK2, 6.2)

    # ---------------- graduations, noms, min / max
    lf = font(POP_M, 21); sf = font(POP_R, 13.5)
    for i, (cx, cy) in enumerate(LAY['knobs']):
        for k in range(11):
            a = math.radians(-225 + 27 * k)
            r0, r1 = LAY['tickR0'], LAY['tickR1']
            d.line([(P(cx + r0 * math.cos(a)), P(cy + r0 * math.sin(a))), (P(cx + r1 * math.cos(a)), P(cy + r1 * math.sin(a)))],
                   fill=SILK2, width=int(P(1.6)))
        text_c(d, (cx, LAY['knobLabelY']), KNOB_NAMES[i], lf, SILK)
        lo, hi = KNOB_MINMAX[i]
        text_c(d, (cx - LAY['knobMinMaxDX'], LAY['knobMinMaxY']), lo, sf, SILK2)
        text_c(d, (cx + LAY['knobMinMaxDX'], LAY['knobMinMaxY']), hi, sf, SILK2)

    # ---------------- potards (calques nh::Knob)
    layer_u = 512 / 196 * LAY['knobR']
    npx = int(round(P(layer_u)))
    for i, (cx, cy) in enumerate(LAY['knobs']):
        deg = -135 + 270 * KNOB_VALS[i]
        k = kp.knob(deg, lightL, glow).resize((npx, npx), Image.LANCZOS)
        img.alpha_composite(k, (int(round(P(cx) - npx / 2)), int(round(P(cy) - npx / 2))))
    d = ImageDraw.Draw(img)

    # ---------------- octave
    o = LAY['octave']
    text_c(d, o['label'], 'OCTAVE', font(POP_M, 18), SILK)
    text_c(d, o['m1'], '−1', font(POP_R, 16.5), SILK2)
    text_c(d, o['p1'], '+1', font(POP_R, 16.5), SILK2)
    text_c(d, o['zero'], '0', font(POP_R, 15), SILK2)
    h = Image.open(os.path.join(ROOT, 'oct_handle.png')).convert('RGBA')
    hb = o['handleBox']
    hs = h.resize((int(round(P(hb[2]))), int(round(P(hb[3])))), Image.LANCZOS)
    img.alpha_composite(hs, (int(round(P(hb[0]))), int(round(P(hb[1])))))
    d = ImageDraw.Draw(img)

    # ---------------- footswitch : inscription
    text_c(d, LAY['bypassLabel'], 'BYPASS  ·  HOLD', font(POP_M, 15), SILK2)
    # ---------------- jacks : inscriptions
    for name, y, x, rot in (('OUT', LAY['jacks']['outY'], LAY['box'][0] + 16, 90), ('IN', LAY['jacks']['inY'], LAY['box'][0] + LAY['box'][2] - 16, -90),
                            ('EXP', LAY['jacks']['expY'], LAY['box'][0] + LAY['box'][2] - 16, -90)):
        t = Image.new('L', (int(P(80)), int(P(24))), 0)
        ImageDraw.Draw(t).text((P(40), P(12)), name, font=font(POP_M, 13), fill=255, anchor='mm')
        t = t.rotate(rot, expand=True)
        layer = Image.new('RGBA', t.size, SILK2 + (0,)); layer.putalpha(t)
        img.alpha_composite(layer, (int(P(x) - t.size[0] / 2), int(P(y) - t.size[1] / 2)))
    d = ImageDraw.Draw(img)

    # ---------------- logo NINE HANDS | DSP (SVG officiel, blanc)
    lg = Image.open(os.path.join(HERE, 'logo_white_preview.png'))
    lw = int(round(P(LAY['logoW']))); lh = int(round(lw * lg.size[1] / lg.size[0]))
    lg = lg.resize((lw, lh), Image.LANCZOS)
    a = np.asarray(lg).astype(np.float32); a[..., 3] *= 0.92
    img.alpha_composite(Image.fromarray(a.astype(np.uint8)), (int(P(LAY['logo'][0]) - lw / 2), int(P(LAY['logo'][1]) - lh / 2)))
    d = ImageDraw.Draw(img)

    # ---------------- LED
    lx, ly = LAY['led']
    if on:
        hl = np.zeros((H, W), np.float32)
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        dd = np.hypot(xx / AS - lx, yy / AS - ly)
        illum = (np.exp(-(dd / 26) ** 2) * 0.55 + np.exp(-(dd / 70) ** 2) * 0.18) * glow * (dd > LAY['ledR'] * 1.05)
        b = np.asarray(img).astype(np.float32)
        b[..., :3] = b[..., :3] * (1 + illum[..., None] * (np.array(MINT) / 255.0 * 1.6 - 0.15))
        img = Image.fromarray(np.clip(b, 0, 255).astype(np.uint8), 'RGBA')
        led = Image.open(os.path.join(ROOT, 'led_on.png')).convert('RGBA')
        n = int(round(P(LAY['ledS']))); led = led.resize((n, n), Image.LANCZOS)
        img.alpha_composite(led, (int(P(lx) - n / 2), int(P(ly) - n / 2)))
    d = ImageDraw.Draw(img)

    # ---------------- barre de presets / ligne d'état (référence Strong Pickle : 400 x 38, Poppins Medium 23)
    px, py, pw, ph = LAY['pill']
    r = ph / 2
    d.rounded_rectangle([P(px - 1.5), P(py - 1.5), P(px + pw + 1.5), P(py + ph + 1.5)], radius=P(r + 1.5), fill=(14, 12, 20, 255))
    d.rounded_rectangle([P(px), P(py), P(px + pw), P(py + ph)], radius=P(r), fill=(6, 6, 9, 255), outline=(120, 116, 136, 255), width=int(P(0.6)))
    pf = font(POP_M, 23)
    if status is None:
        text_c(d, (px + pw / 2, py + ph / 2 + 0.5), 'Classic Theremin', pf, (232, 234, 240))
        for sgn, xa in ((-1, px + 17), (1, px + pw - 17)):
            c = (P(xa), P(py + ph / 2)); s_ = P(5.5)
            pts = [(c[0] - sgn * s_ * 0.6, c[1] - s_), (c[0] - sgn * s_ * 0.6, c[1] + s_), (c[0] + sgn * s_ * 0.9, c[1])]
            d.polygon(pts, fill=(150, 150, 158))
    else:
        text_c(d, (px + pw / 2, py + ph / 2 + 0.5), status, pf, (232, 234, 240))

    # ---------------- écran (sans le nom du preset : il est dans la barre)
    sx, sy, sw, sh = LAY['screen']
    if on:
        ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        for yy_ in np.arange(sy + 8, sy + sh - 4, 7.5):
            od.line([(P(sx + 8), P(yy_)), (P(sx + sw - 50), P(yy_))], fill=MINT + (12,), width=1)
        pts = []
        cyw = sy + sh * 0.52
        for i in range(800):
            t = i / 799
            x = sx + 16 + (sw - 76) * t
            y = cyw - 38 * math.sin(math.pi * t) * (0.82 * math.sin(2 * math.pi * 3.0 * t) + 0.16 * math.sin(2 * math.pi * 6.0 * t))
            pts.append((P(x), P(y)))
        for wdt, al in ((12, int(26 * glow)), (6, int(60 * glow)), (2.2, 245)):
            od.line(pts, fill=MINT + (al,), width=int(P(wdt) / 2), joint='curve')
        img.alpha_composite(ov); d = ImageDraw.Draw(img)
        # rangée du haut : mode de pédale, point MIDI, EXP
        tf2 = font(POP_M, 15)
        d.rounded_rectangle([P(sx + 16), P(sy + 12), P(sx + 96), P(sy + 35)], radius=P(11.5), outline=(120, 190, 180), width=int(P(1.2)))
        text_c(d, (sx + 56, sy + 23.8), 'UP', tf2, (226, 236, 236))
        d.ellipse([P(sx + sw - 74), P(sy + 19), P(sx + sw - 66), P(sy + 27)], fill=MINT)
        text_c(d, (sx + sw - 30, sy + 16), 'EXP', font(POP_M, 13), (120, 190, 180))
        d.rounded_rectangle([P(sx + sw - 45), P(sy + 28), P(sx + sw - 15), P(sy + sh - 11)], radius=P(6), outline=(90, 140, 136), width=int(P(1.2)))
        fh = (sh - 39 - 7) * 0.35
        d.rounded_rectangle([P(sx + sw - 41.5), P(sy + sh - 14.5 - fh), P(sx + sw - 18.5), P(sy + sh - 14.5)], radius=P(3.5), fill=(110, 220, 190))
        text_c(d, (sx + 16, sy + sh - 22), note, font(POP_M, 30), (226, 236, 236), anchor='lm')
        nw = d.textlength(note, font=font(POP_M, 30)) / AS
        text_c(d, (sx + 16 + nw + 12, sy + sh - 20), cents, font(POP_R, 16), (120, 190, 180), anchor='lm')
    return img


def save_views(out, glow=1.0):
    os.makedirs(out, exist_ok=True)
    on = compose(True, glow); off = compose(False, glow)
    on.save(os.path.join(out, 'fantomine_v2_active.png')); off.save(os.path.join(out, 'fantomine_v2_bypass.png'))
    # taille d'ouverture : 495 px de haut (« 60 % »)
    h = 495; w = int(round(h * 2350 / 1800))
    on.resize((w, h), Image.LANCZOS).save(os.path.join(out, 'fantomine_v2_60.png'))
    return on, off


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'design', 'preview')
    save_views(out, float(sys.argv[2]) if len(sys.argv) > 2 else 1.0)
    print('ok', out)
