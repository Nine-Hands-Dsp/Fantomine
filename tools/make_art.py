"""Fantomine v2 (NINE HANDS | DSP) : fond du plugin au format double 2350 x 1800 px.

Source : design de l'utilisateur (design/fantomine_design_source.webp, 1680 x 1264, boîtier violet anodisé).
Règles NINE HANDS | DSP appliquées :
  - pédale plein cadre (boîtier haut / bas de l'image, jacks aux bords gauche / droit), transparence seulement
    autour des jacks et dans les coins arrondis ;
  - potards, LED, footswitch, levier d'octave, textes, graduations, titre néon et logo retirés du fond :
    le plugin les dessine (potards nh::Knob, kit photo, Poppins, SVG officiel du logo) ;
  - vis d'angle retirées (sobriété) ;
  - jacks du kit photo (jack_photo.png) : OUT à gauche, IN (et EXP) à droite, sans ombre portée.

Sorties : background.png (2350 x 1800, RGBA), assets/art/*.png (calques), tools/layout.json + Layout.h.
Repère du plugin : 1175 x 900 unités (image / 2).
"""
import json, os, sys, math
import numpy as np, cv2
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import photo_controls as pc                      # kit photo NINE HANDS | DSP (copie de Strong Pickle)

AS = 2.0                                         # px par unité dans l'image
UW, UH = 1175.0, 900.0                           # repère du plugin (unités)
SRC = np.asarray(Image.open(os.path.join(ROOT, 'design', 'fantomine_design_source.webp')).convert('RGB')).astype(np.float32)
H0, W0 = SRC.shape[:2]

# ------------------------------------------------------------------ géométrie du design (px du design)
BODY = (65.5, 7.0, 1605.5, 1253.0)               # x0, y0, x1, y1 du boîtier violet
BODY_R = 40.0                                    # rayon des coins
KNOBS_D = [(239, 587), (473, 587), (707, 587), (969, 587), (1204, 587), (1438, 587)]
KNOB_RD = 86.0                                   # rayon extérieur de la couronne
SCREEN_D = (856, 101, 1520, 349)                 # cadre complet de l'écran (gardé)
SCREEN_IN_D = (874, 118, 1498, 333)              # vitre (vidée)
LED_D = (838.5, 803.5)
FS_D = (840.0, 1091.0)
OCT_SLOT_D = (205, 1052, 466, 1112)              # fente du levier d'octave (gardée)
OCT_HANDLE_D = (288, 1038, 386, 1123)            # levier (retiré du fond, sprite à part)
OCT_SHADOW_D = (300, 1112, 400, 1138)            # ombre du levier sous la fente
STATUS_D = (575, 846, 1100, 902)
LOGO_D = (1215, 1062, 1470, 1118)
MONO_D = (1495, 1146, 1538, 1200)                # « F » gravé
SCREWS_D = [(114, 51), (1564, 51), (114, 1210), (1564, 1210)]
TEXT_BOXES_D = [
    (275, 296, 615, 330),                        # THEREMIN VOICE
    (78, 400, 112, 500), (1558, 412, 1594, 492), (1558, 610, 1594, 668),   # OUTPUT / INPUT / EXP
    (270, 990, 400, 1026), (132, 1058, 186, 1094), (490, 1058, 536, 1094), (318, 1118, 350, 1148),   # OCTAVE -1 +1 0
    (745, 944, 932, 976),                        # BYPASS · HOLD
]
for cx, cy in KNOBS_D:
    TEXT_BOXES_D.append((cx - 75, cy - 160, cx + 75, cy - 124))          # nom du potard
    TEXT_BOXES_D.append((cx - 112, cy + 92, cx + 116, cy + 122))         # min / max
TITLE_D = (80, 118, 830, 300)

JACK_LEN = 124.0                                 # longueur d'une embase le long de la tranche (unités)
JACK_PROT = JACK_LEN * (188 - 80) / (558 - 46)   # saillie de l'embase (photo du kit)
BOX_W = UW - 2 * JACK_PROT                       # le boîtier occupe tout le reste (jacks aux bords de l'image)
SX = BOX_W / (BODY[2] - BODY[0])                 # unités par px du design
SY = UH / (BODY[3] - BODY[1])                    # hauteur boîtier 900 u
BOX_X0 = JACK_PROT

def U(x, y):
    """px du design -> unités du plugin"""
    return ((x - BODY[0]) * SX + BOX_X0, (y - BODY[1]) * SY)


# ------------------------------------------------------------------ 1. nettoyage de la façade (dans le design)
def lum(a): return a[..., 0] * 0.299 + a[..., 1] * 0.587 + a[..., 2] * 0.114

def build_clean():
    A = SRC.copy()
    h, w = A.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    m = np.zeros((h, w), bool)
    for cx, cy in KNOBS_D: m |= np.hypot(xx - cx - 2, yy - cy - 3) < 124
    for (x0, y0, x1, y1) in TEXT_BOXES_D + [TITLE_D, STATUS_D, LOGO_D, OCT_HANDLE_D, OCT_SHADOW_D]:
        m[y0:y1, x0:x1] = True
    for sx, sy in SCREWS_D: m |= np.hypot(xx - sx - 1, yy - sy - 1) < 34
    m |= np.hypot(xx - LED_D[0], yy - LED_D[1]) < 64
    m |= np.hypot(xx - FS_D[0], yy - FS_D[1]) < 122
    # la fente du levier reste : on ne remplit que le levier (fait à part)
    keep_slot = np.zeros_like(m); x0, y0, x1, y1 = OCT_SLOT_D; keep_slot[y0:y1, x0:x1] = True
    m_plate = m & ~keep_slot

    # basse fréquence : convolution normalisée multi-échelle des pixels sains DE LA FAÇADE (jamais le fond noir)
    inside = (xx > BODY[0] + 6) & (xx < BODY[2] - 6) & (yy > BODY[1] + 6) & (yy < BODY[3] - 6)
    scr = np.zeros_like(m); x0, y0, x1, y1 = SCREEN_D; scr[y0 - 6:y1 + 6, x0 - 6:x1 + 6] = True   # cadre de l'écran : jamais pris comme modèle
    clean = (~m & inside & ~scr).astype(np.float32)
    def nconv(sig):
        num = np.dstack([cv2.GaussianBlur(A[..., c] * clean, (0, 0), sig) for c in range(3)])
        den = cv2.GaussianBlur(clean, (0, 0), sig)[..., None]
        return num / np.maximum(den, 1e-5), den
    low = None
    for sig in (60, 24, 9):
        p, d = nconv(sig)
        a_ = np.clip((d - 0.04) / 0.3, 0, 1)
        low = p if low is None else low * (1 - a_) + p * a_
    # grain de la façade : bruit fin synthétique (aucune mosaïque, donc aucun motif répété),
    # amplitude mesurée sur une zone de façade saine
    rng = np.random.default_rng(4)
    hp = A - cv2.GaussianBlur(A, (0, 0), 2.2)
    ref = hp[1150:1235, 600:760]
    sd = float(np.std(ref.mean(2)))
    nz = cv2.GaussianBlur(rng.normal(0, 1, (h, w)).astype(np.float32), (0, 0), 0.75)
    nz *= sd / max(1e-6, float(np.std(nz)))
    grain = np.dstack([nz, nz * 0.97, nz * 1.04])
    fill = low + grain
    soft = cv2.GaussianBlur(m_plate.astype(np.float32), (0, 0), 3.0)[..., None]
    soft = np.clip(soft * 1.6, 0, 1)
    out = A * (1 - soft) + fill * soft

    # vitre de l'écran : on enlève tout contenu clair, on garde le dégradé et le reflet
    x0, y0, x1, y1 = SCREEN_IN_D
    reg = Image.fromarray(np.clip(out[y0:y1, x0:x1], 0, 255).astype(np.uint8))
    from PIL import ImageFilter
    base = reg.filter(ImageFilter.MinFilter(45)).filter(ImageFilter.GaussianBlur(15))
    out[y0:y1, x0:x1] = np.asarray(base).astype(np.float32)

    # levier d'octave : fente reconstruite ligne par ligne (dégradé entre les bords)
    x0, y0, x1, y1 = OCT_HANDLE_D
    n = x1 - x0; t = (np.arange(n) + 0.5) / n
    for y in range(max(y0, 1042), min(y1, 1119)):
        left = np.median(SRC[y, x0 - 24:x0 - 2], axis=0); right = np.median(SRC[y, x1 + 2:x1 + 24], axis=0)
        out[y, x0:x1] = left[None] * (1 - t[:, None]) + right[None] * t[:, None] + rng.normal(0, 1.2, (n, 1))
    return out


# ------------------------------------------------------------------ 2. mise au format 2350 x 1800
def body_alpha(wpx, hpx, rpx):
    a = np.zeros((hpx, wpx), np.float32)
    ss = 4
    big = np.zeros((hpx * ss, wpx * ss), np.uint8)
    cv2.rectangle(big, (int(rpx * ss), 0), (int((wpx - rpx) * ss), hpx * ss), 255, -1)
    cv2.rectangle(big, (0, int(rpx * ss)), (wpx * ss, int((hpx - rpx) * ss)), 255, -1)
    for cx, cy in ((rpx, rpx), (wpx - rpx, rpx), (rpx, hpx - rpx), (wpx - rpx, hpx - rpx)):
        cv2.circle(big, (int(cx * ss), int(cy * ss)), int(rpx * ss), 255, -1)
    return cv2.resize(big, (wpx, hpx), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0


def make():
    clean = build_clean()
    W, Hh = int(UW * AS), int(UH * AS)                    # 2350 x 1800
    bx0 = int(round(BOX_X0 * AS)); bw = int(round(BOX_W * AS)); bh = Hh
    x0, y0, x1, y1 = BODY
    crop = clean[int(y0):int(math.ceil(y1)), int(x0):int(math.ceil(x1))]
    body = cv2.resize(crop, (bw, bh), interpolation=cv2.INTER_LANCZOS4)
    # grain fin à la résolution finale (l'agrandissement 1,45x adoucit la peinture)
    rng = np.random.default_rng(11)
    g = cv2.GaussianBlur(rng.normal(0, 1, (bh, bw)).astype(np.float32), (0, 0), 0.7) * 3.2
    body = body + g[..., None]
    a_body = body_alpha(bw, bh, BODY_R * SY * AS)
    canvas = np.zeros((Hh, W, 4), np.float32)
    canvas[:, bx0:bx0 + bw, :3] = body
    canvas[:, bx0:bx0 + bw, 3] = a_body * 255

    def over(spr, cx_u, cy_u, below=False):
        """pose un sprite rgba (float, 0-255) centré en (cx_u, cy_u) unités"""
        sh, sw = spr.shape[:2]
        px, py = int(round(cx_u * AS - sw / 2)), int(round(cy_u * AS - sh / 2))
        xa, ya = max(0, px), max(0, py); xb, yb = min(W, px + sw), min(Hh, py + sh)
        s = spr[ya - py:yb - py, xa - px:xb - px]
        sa = s[..., 3:4] / 255.0
        d = canvas[ya:yb, xa:xb]
        da = d[..., 3:4] / 255.0
        outa = sa + da * (1 - sa)
        d[..., :3] = np.where(outa > 1e-4, (s[..., :3] * sa + d[..., :3] * da * (1 - sa)) / np.maximum(outa, 1e-4), 0)
        d[..., 3:4] = outa * 255

    def occlusion(cx_u, cy_u, r_u, strength=0.28, spread=0.22):
        """ombre de contact douce sur la coque autour d'une pièce (lumière en haut à gauche)"""
        yy, xx = np.mgrid[0:Hh, 0:W].astype(np.float32)
        d = np.hypot(xx / AS - (cx_u + r_u * 0.05), yy / AS - (cy_u + r_u * 0.07)) / r_u
        o = np.clip(1 - (d - 1) / spread, 0, 1) ** 2 * (d > 0.9) * strength
        canvas[..., :3] *= (1 - o)[..., None]

    L = {}
    # --- jacks (kit photo) : OUT à gauche, IN et EXP à droite, affleurant le bord du boîtier, sans ombre portée
    jack_len = JACK_LEN
    jl, jw, jh = pc.jack_sprite(jack_len, AS, -1)
    jr, _, _ = pc.jack_sprite(jack_len, AS, +1)
    # hauteur des embases réduite de 10 % (demande de l'utilisateur) ; la saillie reste la même (jacks aux bords de l'image)
    JACK_HK = 0.90
    def squash(spr):
        pm = spr.copy(); pm[..., :3] *= pm[..., 3:4] / 255.0
        n_h = int(round(spr.shape[0] * JACK_HK))
        sm = cv2.resize(pm, (spr.shape[1], n_h), interpolation=cv2.INTER_AREA)
        a_ = sm[..., 3:4] / 255.0
        sm[..., :3] = np.where(a_ > 1e-4, sm[..., :3] / np.maximum(a_, 1e-4), 0)
        return sm
    jl, jr = squash(jl), squash(jr); jh *= JACK_HK
    jack_out_y = U(0, 452)[1]; jack_in_y = U(0, 452)[1]; jack_exp_y = U(0, 640)[1]
    over(jr, BOX_X0 + BOX_W + jw / 2 - 0.6, jack_in_y)
    over(jr, BOX_X0 + BOX_W + jw / 2 - 0.6, jack_exp_y)
    over(jl, BOX_X0 - jw / 2 + 0.6, jack_out_y)
    L['jacks'] = dict(len=jack_len * JACK_HK, w=jw, outY=jack_out_y, inY=jack_in_y, expY=jack_exp_y)

    # --- occlusions douces : potards, LED, footswitch
    knobs_u = [U(x, y) for x, y in KNOBS_D]
    knob_r_u = KNOB_RD * SX
    for (cx, cy) in knobs_u: occlusion(cx, cy, knob_r_u * 1.02, 0.22, 0.30)
    led_u = U(*LED_D); fs_u = U(*FS_D)

    # --- footswitch d'Echoflex (kit photo) : ce n'est pas un calque mobile, il fait partie du fond
    flats = 112.0                                  # 140 x 0,8 : footswitch réduit de 20 % (demande de l'utilisateur)
    fs, fs_refl, fsS, fsBtn = pc.footswitch_sprite(flats, AS, refl_colour=(126.0, 240.0, 214.0))
    occlusion(fs_u[0], fs_u[1], flats * 0.55, 0.30, 0.28)
    over(fs, *fs_u)
    Image.fromarray(np.clip(fs_refl, 0, 255).astype(np.uint8)).save(os.path.join(ROOT, 'fs_refl.png'))

    # --- LED menthe (kit photo) : lentille éteinte dans le fond, allumée en calque
    led_r = 13.0
    led_off, led_on, ledS = pc.led_sprites(led_r, AS, colour='mint')
    occlusion(led_u[0], led_u[1], led_r * 1.25, 0.25, 0.5)
    over(led_off, *led_u)
    Image.fromarray(np.clip(led_on, 0, 255).astype(np.uint8)).save(os.path.join(ROOT, 'led_on.png'))

    rgba = np.clip(canvas, 0, 255).astype(np.uint8)
    Image.fromarray(rgba, 'RGBA').save(os.path.join(ROOT, 'background.png'), optimize=True)

    # --- levier d'octave : sprite détouré à la résolution d'origine du design (ombre portée à 45° vers le bas à droite)
    from scipy import ndimage as ndi
    pad = 12
    x0, y0, x1, y1 = OCT_HANDLE_D[0] - pad, OCT_HANDLE_D[1] - pad, OCT_HANDLE_D[2] + pad, OCT_HANDLE_D[3] + pad
    on = SRC[y0:y1, x0:x1]
    Lh = lum(on); sat = on.max(axis=2) - on.min(axis=2)
    lab, _ = ndi.label((sat < 22) & (Lh > 60))
    cyy, cxx = 1085 - y0, 335 - x0
    keep = lab == lab[cyy, cxx]
    keep = ndi.binary_fill_holes(ndi.binary_closing(keep, iterations=3))
    keep = ndi.binary_opening(keep, structure=np.ones((3, 3)), iterations=8)
    lab2, _ = ndi.label(keep); keep = lab2 == lab2[cyy, cxx]
    keep = ndi.binary_erosion(keep, iterations=1)
    a_ = np.clip(ndi.gaussian_filter(keep.astype(np.float32), 0.7) * 1.25, 0, 1)
    sh = ndi.gaussian_filter(ndi.shift(keep.astype(np.float32), (4, 4), order=1), 3.5) * 0.6
    out_a = a_ + sh * (1 - a_)
    col = (on * a_[..., None]) / np.maximum(out_a, 1e-4)[..., None]
    os.makedirs(os.path.join(ROOT, 'assets', 'art'), exist_ok=True)
    Image.fromarray(np.dstack([np.clip(col, 0, 255), out_a * 255]).astype(np.uint8), 'RGBA').save(os.path.join(ROOT, 'oct_handle.png'))
    handle_box_u = [U(x0, y0)[0], U(x0, y0)[1], (x1 - x0) * SX, (y1 - y0) * SY]

    # ------------------------------------------------------------------ repères
    sc = lambda r: [round(r[0], 2), round(r[1], 2)]
    # barre presets / état (400 x 38, référence Strong Pickle) centrée verticalement entre le bas de la LED
    # (joint compris) et le haut des lettres de « BYPASS · HOLD » (Poppins Medium 15, mesuré sur la police)
    from PIL import ImageFont
    by = fs_u[1] - flats / math.sqrt(3) - 15.0
    f15 = ImageFont.truetype(os.path.join(ROOT, 'Poppins-Medium.ttf'), 1500)
    bb = f15.getbbox('BYPASS · HOLD', anchor='mm')          # en 1/100 d'unité
    label_top = by + bb[1] / 100.0
    led_bottom = led_u[1] + led_r * 1.07
    pill_cy = (led_bottom + label_top) / 2
    pill_box = [round(UW / 2 - 200, 2), round(pill_cy - 19, 2), 400.0, 38.0]
    print('LED bas', round(led_bottom, 2), '| haut des lettres', round(label_top, 2), '| centre barre', round(pill_cy, 2))
    s_box = lambda b: [round(U(b[0], b[1])[0], 2), round(U(b[0], b[1])[1], 2),
                       round((b[2] - b[0]) * SX, 2), round((b[3] - b[1]) * SY, 2)]
    lay = dict(
        frame=[UW, UH], box=[round(BOX_X0, 3), 0.0, round(BOX_W, 3), UH], boxR=round(BODY_R * SY, 2),
        knobs=[sc(k) for k in knobs_u], knobR=round(knob_r_u, 2),
        knobLabelY=round(U(0, 587 - 142)[1], 2), knobMinMaxY=round(U(0, 587 + 107)[1], 2),
        knobMinMaxDX=round(80 * SX, 2), tickR0=round(98 * SX, 2), tickR1=round(108 * SX, 2),
        separator=[round(U(838, 0)[0], 2), round(U(0, 480)[1], 2), round(U(0, 690)[1], 2)],
        screen=s_box(SCREEN_IN_D), led=sc(led_u), ledS=round(ledS, 2), ledR=led_r,
        foot=sc(fs_u), footR=round(fsBtn, 2), fsS=round(fsS, 2), flats=flats,
        title=sc(U(445, 207)), titleH=round(118 * SY, 2), subtitle=sc(U(445, 313)),
        pill=pill_box,
        octave=dict(label=sc(U(335, 1008)), m1=sc(U(158, 1076)), p1=sc(U(512, 1076)), zero=sc(U(334, 1133)),
                    handle=sc(U((OCT_HANDLE_D[0] + OCT_HANDLE_D[2]) / 2, (OCT_HANDLE_D[1] + OCT_HANDLE_D[3]) / 2)),
                    handleBox=[round(v, 3) for v in handle_box_u],
                    travel=round(90 * SX, 2), slot=s_box(OCT_SLOT_D)),
        bypassLabel=[round(fs_u[0], 2), round(fs_u[1] - flats / math.sqrt(3) - 15.0, 2)],   # 15 unités au-dessus de l'écrou
        logo=sc(U(1342, 1090)), logoW=round(232 * SX, 2),
        jacks=L['jacks'], scale=dict(sx=SX, sy=SY),
    )
    with open(os.path.join(HERE, 'layout.json'), 'w') as f: json.dump(lay, f, indent=1)
    print(json.dumps(lay)[:400])
    return lay


if __name__ == '__main__':
    make()
