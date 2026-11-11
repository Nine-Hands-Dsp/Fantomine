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
BODY = (65.5 + 14, 7.0 + 14, 1605.5 - 14, 1253.0 - 14)   # boîtier violet du design, 14 px à l'intérieur de ses bords
                                                 # (biseaux d'origine irréguliers : redessinés par make_edges)
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
MONO_D = (1484, 1134, 1550, 1212)                # « F » gravé (retiré à la demande de l'utilisateur)
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

    # ombre portée du footswitch d'origine (plus grand, ombre jusqu'à ~210 px vers le bas à droite) : on la retire
    # par division (gain d'éclairage), ce qui garde les gravures et le grain de la façade intacts
    rf = np.hypot(xx - FS_D[0], yy - FS_D[1])
    rz = np.hypot(xx - FS_D[0] - 40, yy - FS_D[1] - 50)
    inside_box = (xx > BODY[0] + 8) & (xx < BODY[2] - 8) & (yy > BODY[1] + 8) & (yy < BODY[3] - 8)
    Lsrc = lum(A)
    def ncv(img, msk, sig):
        return cv2.GaussianBlur(img * msk, (0, 0), sig) / np.maximum(cv2.GaussianBlur(msk, (0, 0), sig), 1e-5)
    m_obs = ((rf > 123) & inside_box).astype(np.float32)
    m_ref = ((rz > 250) & inside_box).astype(np.float32)
    # gravures exclues de l'estimation (traits clairs fins)
    fine = (Lsrc - cv2.GaussianBlur(Lsrc, (0, 0), 3)) > 6
    m_obs *= ~fine; m_ref *= ~fine
    observed = ncv(Lsrc, m_obs, 4)
    expected = ncv(Lsrc, m_ref, 70)
    gain = np.clip(observed / np.maximum(expected, 1), 0.06, 1.0)
    zone = np.clip((300 - rz) / 60.0, 0, 1) * inside_box
    gain = 1 - (1 - gain) * zone
    # seule la composante lisse est corrigée : le grain et les gravures gardent leur amplitude (aucun bruit amplifié)
    A_low = cv2.GaussianBlur(A, (0, 0), 2.2)
    A = A_low / gain[..., None] + (A - A_low) * np.clip(1.0 / gain, 1.0, 1.6)[..., None]
    m = np.zeros((h, w), bool)
    for cx, cy in KNOBS_D: m |= np.hypot(xx - cx - 2, yy - cy - 3) < 124
    for (x0, y0, x1, y1) in TEXT_BOXES_D + [TITLE_D, STATUS_D, LOGO_D, OCT_HANDLE_D, OCT_SHADOW_D, MONO_D]:   # MONO_D : « F » gravé retiré (demande)
        m[y0:y1, x0:x1] = True
    for sx, sy in SCREWS_D: m |= np.hypot(xx - sx - 1, yy - sy - 1) < 34
    m |= np.hypot(xx - LED_D[0], yy - LED_D[1]) < 64
    m |= np.hypot(xx - FS_D[0], yy - FS_D[1]) < 128
    # la fente du levier reste : on ne remplit que le levier (fait à part)
    keep_slot = np.zeros_like(m); x0, y0, x1, y1 = OCT_SLOT_D; keep_slot[y0:y1, x0:x1] = True
    m_plate = m & ~keep_slot

    # basse fréquence : convolution normalisée multi-échelle des pixels sains DE LA FAÇADE (jamais le fond noir)
    inside = (xx > BODY[0] + 6) & (xx < BODY[2] - 6) & (yy > BODY[1] + 6) & (yy < BODY[3] - 6)
    scr = np.zeros_like(m); x0, y0, x1, y1 = SCREEN_D; scr[y0 - 6:y1 + 6, x0 - 6:x1 + 6] = True   # cadre de l'écran : jamais pris comme modèle
    clean = (~m & inside & ~scr).astype(np.float32)
    # base de l'interpolation : façade sans grain ni gravures (médiane), sinon l'échelle fine crée des taches
    A_s = cv2.medianBlur(np.clip(A, 0, 255).astype(np.uint8), 7).astype(np.float32)
    A_s = cv2.GaussianBlur(A_s, (0, 0), 3)
    def nconv(sig):
        num = np.dstack([cv2.GaussianBlur(A_s[..., c] * clean, (0, 0), sig) for c in range(3)])
        den = cv2.GaussianBlur(clean, (0, 0), sig)[..., None]
        return num / np.maximum(den, 1e-5), den
    low = None
    for sig in (60, 24, 12):
        p, d = nconv(sig)
        a_ = np.clip((d - 0.04) / 0.3, 0, 1)
        low = p if low is None else low * (1 - a_) + p * a_
    # détail de la façade (grain, gravures) : recopié d'une zone saine voisine, décalée horizontalement
    # (les lignes de champ sont presque horizontales : elles se prolongent), jamais de bruit synthétique
    detail = A - A_s
    grain = np.zeros_like(A)
    # par rangée : chaque segment masqué reçoit le détail du segment sain de même longueur juste à sa gauche
    # (ou à sa droite) ; seuls les pixels sains de la source sont recopiés
    okmask = (~m) & inside & ~scr
    sx0, sy0, sx1, sy1 = OCT_SLOT_D; okmask[sy0 - 10:sy1 + 10, sx0 - 10:sx1 + 10] = False   # fente d'octave : jamais recopiée
    okmask &= np.hypot(xx - FS_D[0], yy - FS_D[1]) > 140                                      # ni l'ancien footswitch
    okmask &= np.abs(detail).max(2) < 24                                                     # ni une arête franche (gravures seulement)
    target = m_plate
    left_over = np.zeros_like(m_plate)
    for y in range(h):
        row = target[y]
        if not row.any(): continue
        xs = np.nonzero(row)[0]
        runs = np.split(xs, np.nonzero(np.diff(xs) > 1)[0] + 1)
        for r_ in runs:
            a0, b0 = r_[0], r_[-1] + 1; n_ = b0 - a0
            for src0 in (a0 - n_ - 4, b0 + 4, a0 - 2 * n_ - 8, b0 + n_ + 8):
                if src0 < 0 or src0 + n_ > w: continue
                okr = okmask[y, src0:src0 + n_]
                if okr.mean() > 0.9:
                    grain[y, a0:b0] = detail[y, src0:src0 + n_] * okr[:, None]
                    break
            else:
                left_over[y, a0:b0] = True
    # zones sans source horizontale (bord du boîtier, titre) : copie 2D d'un bloc sain voisin (même décalage
    # pour toute la zone, donc aucune strie)
    # par carreaux de 48 px, chacun pris dans un carreau sain voisin (grain fin : aucune couture visible)
    T = 48
    lo = ndi_dilate(left_over, 3) if left_over.any() else left_over
    for ty in range(0, h, T):
        for tx in range(0, w, T):
            sub = lo[ty:ty + T, tx:tx + T]
            if not sub.any(): continue
            th_, tw_ = sub.shape
            for dy, dx in ((-T, 0), (T, 0), (0, T), (0, -T), (-2 * T, 0), (2 * T, 0), (-T, T), (-T, -T), (T, T), (T, -T),
                           (-3 * T, 0), (3 * T, 0), (0, 2 * T), (0, -2 * T)):
                y2, x2 = ty + dy, tx + dx
                if y2 < 0 or x2 < 0 or y2 + th_ > h or x2 + tw_ > w: continue
                okr = okmask[y2:y2 + th_, x2:x2 + tw_]
                if okr.mean() > 0.9:
                    g = grain[ty:ty + th_, tx:tx + tw_]
                    g[sub] = (detail[y2:y2 + th_, x2:x2 + tw_] * okr[..., None])[sub]
                    break
            else:
                # dernier recours (bord du boîtier) : carreau sain le plus proche, cherché en spirale
                found = False
                for rad in range(2, 12):
                    for dy, dx in ((-rad * T, 0), (rad * T, 0), (0, rad * T), (0, -rad * T)):
                        y2, x2 = ty + dy, tx + dx
                        if y2 < 0 or x2 < 0 or y2 + th_ > h or x2 + tw_ > w: continue
                        okr = okmask[y2:y2 + th_, x2:x2 + tw_]
                        if okr.mean() > 0.8:
                            g = grain[ty:ty + th_, tx:tx + tw_]
                            g[sub] = (detail[y2:y2 + th_, x2:x2 + tw_] * okr[..., None])[sub]
                            found = True; break
                    if found: break
    # pixels restés sans détail (quelques px au bord du boîtier) : grain fin de même amplitude que la façade voisine
    rng = np.random.default_rng(4)
    empty = m_plate & (np.abs(grain).max(2) < 1e-6)
    if empty.any():
        sd = float(np.std(detail[okmask].mean(1)))
        nz = cv2.GaussianBlur(rng.normal(0, 1, (h, w)).astype(np.float32), (0, 0), 0.8)
        nz *= sd / max(1e-6, float(np.std(nz)))
        grain[empty] = np.dstack([nz, nz, nz * 1.03])[empty]
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


BRAND_K = 416.0 / 2499.0                           # unités par unité du viewBox du logo Fantomine

def ndi_dilate(mk, it):
    from scipy import ndimage as ndi
    return ndi.binary_dilation(mk, iterations=it)


def make_edges(body, rpx):
    """Biseau usiné identique sur tout le pourtour (coins arrondis compris), lumière en haut à gauche à 45° :
    arête claire côté haut / gauche, arête sombre côté bas / droite, légère ombre interne."""
    h, w = body.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32) + 0.5
    # distance signée au rectangle arrondi (positive à l'intérieur) et normale sortante
    qx = np.abs(xx - w / 2) - (w / 2 - rpx); qy = np.abs(yy - h / 2) - (h / 2 - rpx)
    ox, oy = np.maximum(qx, 0), np.maximum(qy, 0)
    outside = np.hypot(ox, oy) + np.minimum(np.maximum(qx, qy), 0)
    d = rpx - outside                                   # profondeur depuis le bord (px)
    nx = np.where(qx > qy, np.sign(xx - w / 2), 0.0); ny = np.where(qy >= qx, np.sign(yy - h / 2), 0.0)
    corner = (qx > 0) & (qy > 0)
    ln = np.maximum(np.hypot(ox, oy), 1e-3)
    nx = np.where(corner, np.sign(xx - w / 2) * ox / ln, nx); ny = np.where(corner, np.sign(yy - h / 2) * oy / ln, ny)
    facing = -(nx + ny) / math.sqrt(2)                  # +1 face à la lumière (haut gauche), -1 à l'opposé
    out = body.copy()
    bevel_w = 5.0 * AS                                  # largeur du biseau
    t = np.clip(d / bevel_w, 0, 1)
    prof = np.exp(-((d - 1.6 * AS) / (1.1 * AS)) ** 2)  # arête fine
    lift = np.where(facing > 0, 0.55, 0.42) * facing * prof * 255 * 0.55
    out = out + lift[..., None] * np.array([1.0, 0.96, 1.08])
    # chanfrein : légère pente qui s'assombrit côté bas / droite, s'éclaircit côté haut / gauche
    ramp = (1 - t) * 0.10 * facing
    out = out * (1 + ramp[..., None])
    # ombre interne très douce sous l'arête (épaisseur de la peinture)
    inner = np.exp(-((d - 4.2 * AS) / (1.6 * AS)) ** 2) * 0.06
    out = out * (1 - inner[..., None])
    # liseré extérieur sombre (contact avec le fond)
    rim = np.clip(1 - d / (0.9 * AS), 0, 1) * 0.55
    out = out * (1 - rim[..., None])
    return out


def make():
    clean = build_clean()
    W, Hh = int(UW * AS), int(UH * AS)                    # 2350 x 1800
    bx0 = int(round(BOX_X0 * AS)); bw = int(round(BOX_W * AS)); bh = Hh
    x0, y0, x1, y1 = BODY
    # bords du design retirés (biseaux irréguliers d'un coin à l'autre) : on recadre 14 px à l'intérieur puis on
    # étire légèrement ; le biseau est redessiné identique sur les quatre coins (make_edges)
    IN = 0
    crop = clean[int(y0) + IN:int(math.ceil(y1)) - IN, int(x0) + IN:int(math.ceil(x1)) - IN]
    body = cv2.resize(crop, (bw, bh), interpolation=cv2.INTER_LANCZOS4)
    # grain fin à la résolution finale (l'agrandissement 1,45x adoucit la peinture)
    rng = np.random.default_rng(11)
    g = cv2.GaussianBlur(rng.normal(0, 1, (bh, bw)).astype(np.float32), (0, 0), 0.7) * 3.2
    body = body + g[..., None]
    a_body = body_alpha(bw, bh, BODY_R * SY * AS)
    body = make_edges(body, BODY_R * SY * AS)
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
        # logo Fantomine (SVG fourni, viewBox 3000 x 1000, dessin de x 249 à 2748 et de y 129 à 870) :
        # 416 unités de large (520 réduit de 20 %, demande de l'utilisateur), centré sur (310, 158)
        brand=[round(310 - 1500 * BRAND_K, 3), round(158 - (129 + 870) / 2 * BRAND_K, 3), round(3000 * BRAND_K, 3), round(1000 * BRAND_K, 3)],
        pill=pill_box,
        octave=dict(label=sc(U(335, 1008)), m1=sc(U(158, 1076)), p1=sc(U(512, 1076)), zero=sc(U(334, 1133)),
                    handle=sc(U((OCT_HANDLE_D[0] + OCT_HANDLE_D[2]) / 2, (OCT_HANDLE_D[1] + OCT_HANDLE_D[3]) / 2)),
                    handleBox=[round(v, 3) for v in handle_box_u],
                    travel=round(90 * SX, 2), slot=s_box(OCT_SLOT_D)),
        bypassLabel=[round(fs_u[0], 2), round(fs_u[1] - flats / math.sqrt(3) - 15.0, 2)],   # 15 unités au-dessus de l'écrou
        # logo NINE HANDS | DSP centré sous le footswitch, à mi-chemin entre le bas de l'écrou et le bas du boîtier
        logo=[round(fs_u[0], 2), round((fs_u[1] + flats / 2 + UH) / 2, 2)], logoW=round(232 * SX, 2),
        jacks=L['jacks'], scale=dict(sx=SX, sy=SY),
    )
    with open(os.path.join(HERE, 'layout.json'), 'w') as f: json.dump(lay, f, indent=1)
    print(json.dumps(lay)[:400])
    return lay


if __name__ == '__main__':
    make()
