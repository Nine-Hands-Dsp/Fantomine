"""Fantomine v2 : calques du potard (nh::Knob) extraits du design de l'utilisateur.

Le potard du design (couronne moletée en pointes de diamant, chapeau violet en métal tourné, repère lumineux menthe)
est séparé en calques, sans retoucher sa matière :
  crown      couronne moletée : motif moyenné sur toutes les dents (invariant par rotation d'une dent), éclairage retiré
  cap        chapeau : profil radial du métal tourné (moyenne angulaire), sans reflet
  highlight  reflets fixes du chapeau et liseré de lumière de la couronne (lumière en haut à gauche, 45°)
  shadow     ombre portée centrée, sans décalage (le code la décale à 45° vers le bas à droite)
  marker_off rainure du repère (pédale en bypass) + point blanc sur la couronne
  marker_on  trait lumineux menthe (coeur, toujours plein quand la pédale est active)
  marker_glow halo du trait (dosé par le réglage Glow)
Les 6 potards du design sont moyennés (repère et point blanc exclus) : plus de détail, aucun reste de repère.
Sortie : assets/knob/*.png, 512 x 512, potard de rayon KR px centré.
"""
import os, math
import numpy as np, cv2
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, 'assets', 'knob'); os.makedirs(OUT, exist_ok=True)
SRC = np.asarray(Image.open(os.path.join(ROOT, 'design', 'fantomine_design_source.webp')).convert('RGB')).astype(np.float32)
KNOBS = [(239, 587), (473, 587), (707, 587), (969, 587), (1204, 587), (1438, 587)]
R_OUT, R_CAP = 86.0, 61.5          # rayon extérieur de la couronne, rayon du chapeau (px du design)
N = 512; KR = 196.0                # calque : 512 px, potard de rayon 196 px (marge pour l'ombre et le flou)
NT, NR = 4096, 400                 # échantillonnage polaire
rs = np.linspace(0, 1.03 * R_OUT, NR)
ths = np.linspace(-math.pi, math.pi, NT, endpoint=False)     # angle écran (0 = vers la droite, y vers le bas)

def mint(a): return np.clip((a[..., 1] - a[..., 0] - 10) / 90.0, 0, 1)

def polar(c):
    T, Rr = np.meshgrid(ths, rs)
    mx = (c[0] + Rr * np.cos(T)).astype(np.float32); my = (c[1] + Rr * np.sin(T)).astype(np.float32)
    return np.dstack([cv2.remap(SRC[..., k], mx, my, cv2.INTER_CUBIC) for k in range(3)])

def refine_centre(c):
    """centre exact : profil radial le plus net (bord sombre de la couronne et bord du chapeau)"""
    L = SRC.mean(2); best = None
    for dy in np.arange(-4, 4.01, 0.5):
        for dx in np.arange(-4, 4.01, 0.5):
            cx, cy = c[0] + dx, c[1] + dy
            T, Rr = np.meshgrid(np.linspace(-math.pi, math.pi, 720, endpoint=False), np.arange(76, 92, 0.5))
            v = cv2.remap(L, (cx + Rr * np.cos(T)).astype(np.float32), (cy + Rr * np.sin(T)).astype(np.float32), cv2.INTER_LINEAR)
            score = np.abs(np.diff(v.mean(1))).max()
            if best is None or score > best[0]: best = (score, cx, cy)
    return best[1], best[2]

def pointer_angle(P):
    m = mint(P); m[rs > 0.8 * R_OUT] = 0
    w = m.sum(0); return ths[int(np.argmax(np.convolve(w, np.ones(31), 'same')))]

centres = [refine_centre(c) for c in KNOBS]
print('centres', [(round(a, 1), round(b, 1)) for a, b in centres])
Ps, valid = [], []
for c in centres:
    P = polar(c)
    a = pointer_angle(P)
    d = np.abs((ths - a + math.pi) % (2 * math.pi) - math.pi)
    # repère + son halo + rainure (sur le chapeau) et point blanc (sur la couronne) exclus
    bad = np.zeros((NR, NT), bool)
    bad |= (d[None, :] * np.maximum(rs[:, None], 4) < 15) & (rs[:, None] < R_CAP + 2)
    bad |= (d[None, :] < 0.30) & (rs[:, None] >= R_CAP - 4)
    bad |= mint(P) > 0.03
    Ps.append(P); valid.append(~bad)
Ps = np.array(Ps); valid = np.array(valid)

# ---------------- chapeau : profil radial moyen (métal tourné, sans reflet)
w = valid[..., None].astype(np.float32)
ws = w.sum((0, 2))
radial = (Ps * w).sum((0, 2)) / np.maximum(ws, 1)                         # (NR, 3)
first = int(np.argmax(ws[:, 0] > NT * 0.5))                                # au centre, tout est masqué : on prolonge
radial[:first] = radial[first]

# ---------------- couronne : nombre de dents et motif moyen d'une dent
ring = (rs > R_CAP + 5) & (rs < R_OUT - 4)
lum0 = Ps[0][ring].mean(2).mean(0) - Ps[0][ring].mean()
spec = np.abs(np.fft.rfft(lum0)); nteeth = int(np.argmax(spec[20:90]) + 20)
print('dents', nteeth)
per = NT / nteeth
# motif d'une dent : moyenne de toutes les dents de tous les potards, chaque potard recalé en phase
tooth_len = int(round(per)) * 4
def fold(P, V, phase):
    acc = np.zeros((NR, tooth_len, 3)); cnt = np.zeros((NR, tooth_len, 1))
    k = (np.arange(NT) - phase) % per                                       # position dans la dent
    idx = np.floor(k / per * tooth_len).astype(int) % tooth_len
    for j in range(tooth_len):
        sel = idx == j
        vv = V[:, sel][..., None].astype(np.float32)
        acc[:, j] += (P[:, sel] * vv).sum(1); cnt[:, j] += vv.sum(1)
    return acc, cnt
# phase de chaque potard : maximum de corrélation avec le potard 0
ref_lum = Ps[0][ring].mean(2).mean(0)
phases = []
for i in range(len(Ps)):
    l = Ps[i][ring].mean(2).mean(0)
    best = max(((np.dot(np.roll(l, -s) - l.mean(), ref_lum - ref_lum.mean()), s) for s in range(int(per) + 1)))
    phases.append(best[1])
acc = 0; cnt = 0
for i in range(len(Ps)):
    a_, c_ = fold(Ps[i], valid[i], phases[i]); acc = acc + a_; cnt = cnt + c_
tooth = acc / np.maximum(cnt, 1)                                            # (NR, tooth_len, 3) éclairage moyen
# la moyenne sur toutes les dents d'un même potard garde l'éclairage moyen ; l'éclairage directionnel va dans highlight
# ---------------- carte polaire de la matière (ce qui tourne) ; détail des dents renforcé (le moyennage l'adoucit)
crown_r = (rs > R_CAP + 1.5) & (rs <= R_OUT + 1.5)
tmean = tooth.mean(1, keepdims=True)
tooth = tmean + (tooth - tmean) * 1.55
def matter_at(phase):
    k = ((np.arange(NT) - phase) % per) / per
    idx = np.floor(k * tooth_len).astype(int) % tooth_len
    return np.where(crown_r[:, None, None], tooth[:, idx], radial[:, None, :])
matter = matter_at(0.0)

# ---------------- éclairage fixe (repère écran, jamais décalé) : écart potard réel - matière à SA phase, basse fréquence
# médiane sur les 6 potards : les restes d'un repère (propres à un potard) sont écartés
stackL = np.stack([np.where(valid[i][..., None], Ps[i] - matter_at(phases[i]), np.nan) for i in range(len(Ps))])
import warnings
with warnings.catch_warnings():
    warnings.simplefilter('ignore'); light = np.nanmedian(stackL, axis=0)
# trous (repère sur tous les potards à ce rayon) : interpolation angulaire périodique, rayon par rayon
for ri in range(NR):
    row = light[ri]; bad = np.isnan(row[:, 0])
    if bad.all(): continue
    if bad.any():
        xs = np.arange(NT); good = ~bad
        for c in range(3):
            row[bad, c] = np.interp(xs[bad], xs[good], row[good, c], period=NT)
light = np.where(np.isnan(light), 0.0, light)
# centre du chapeau (masqué partout) : prolongé depuis le premier anneau valide
ok = np.isfinite(stackL).any(0).all(1).mean(1) > 0.9
f = int(np.argmax(ok)) + 2; light[:f] = light[f][None]
ksz = int(per * 2.2) | 1
light = cv2.blur(np.concatenate([light[:, -ksz:], light, light[:, :ksz]], 1), (ksz, 1))[:, ksz:-ksz]
# près de l'axe, lissage angulaire de plus en plus large (largeur d'arc constante ~ 14 px du design) :
# plus aucun pli au centre du cône de métal tourné
for ri in range(NR):
    r_ = rs[ri]
    if r_ > 22: break
    k_ = int(min(NT // 3, 14.0 / max(r_, 0.5) / (2 * math.pi) * NT)) | 1
    row = light[ri]
    ext = np.concatenate([row[-k_:], row, row[:k_]], 0)
    light[ri] = cv2.blur(ext[:, None, :].astype(np.float32), (1, k_))[k_:-k_, 0, :]
# lumière à 45° en haut à gauche : vérification de l'angle du reflet le plus clair sur le chapeau
capL = light[(rs > 15) & (rs < R_CAP - 4)].mean(2).mean(0)
peak = math.degrees(ths[int(np.argmax(np.convolve(capL, np.ones(61), 'same')))])
print('angle du reflet du chapeau (écran, -135 attendu) :', round(peak, 1))

# ---------------- passage en image cartésienne 512 x 512
yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
dx, dy = (xx - N / 2 + 0.5) / KR * R_OUT, (yy - N / 2 + 0.5) / KR * R_OUT
rr = np.hypot(dx, dy); tt = np.arctan2(dy, dx)
ri = (rr / rs[-1] * (NR - 1)).astype(np.float32)
ti = ((tt + math.pi) / (2 * math.pi) * NT).astype(np.float32)
def to_cart(Pp):
    ext = np.concatenate([Pp, Pp[:, :2]], 1)
    return np.dstack([cv2.remap(ext[..., c].astype(np.float32), ti, ri, cv2.INTER_LINEAR) for c in range(Pp.shape[2])])
alpha = np.clip((R_OUT + 0.6 - rr) / 1.2, 0, 1)          # bord extérieur net (anticrénelé)
# le potard a été dessiné sans repère : le chapeau sous l'ancien repère est la matière ; on fixe le sens du haut
mat_c = to_cart(matter)
crown_a = alpha * np.clip((rr - (R_CAP + 1.0)) / 1.0, 0, 1)
cap_a = np.clip((R_CAP + 1.5 - rr) / 1.0, 0, 1)
def save(name, rgb, a):
    Image.fromarray(np.dstack([np.clip(rgb, 0, 255), np.clip(a, 0, 1) * 255]).astype(np.uint8), 'RGBA').save(os.path.join(OUT, name + '.png'))
save('crown', mat_c, crown_a)
save('cap', mat_c, cap_a * alpha)
# highlight : calque de recouvrement qui ramène la matière à l'aspect du design (éclairé haut-gauche)
lc = to_cart(light)
# couleur du recouvrement calculée sur la matière MOYENNE (invariante par rotation) : aucune dent dans le reflet
mean_polar = np.where(crown_r[:, None, None], tooth.mean(1)[:, None, :], radial[:, None, :]) * np.ones((1, NT, 1))
bbar = to_cart(mean_polar)
ld = lc.mean(2)
up = ld > 0
a_h = np.where(up, ld / np.maximum(255 - bbar.mean(2), 1), -ld / np.maximum(bbar.mean(2), 1))
a_h = np.clip(a_h * 1.0, 0, 0.95)
col = np.clip(bbar + lc / np.maximum(a_h, 1e-3)[..., None], 0, 255)
save('highlight', col, a_h * alpha)
# ombre portée : disque flou centré (le code la décale)
sh = cv2.GaussianBlur((rr < R_OUT * 1.0).astype(np.float32), (0, 0), KR * 0.07) * 0.72
save('shadow', np.zeros((N, N, 3)), sh)

# ---------------- repère : rainure + trait menthe (pointé vers le haut), point blanc sur la couronne
# géométrie du design : trait de 0,21 R à 0,73 R, rainure 0,058 R de large, point blanc à 0,88 R
ss = 4
def line_mask(r0, r1, width, blur):
    big = np.zeros((N * ss, N * ss), np.float32)
    cxp = N * ss / 2
    k_ = KR / R_OUT * ss * R_OUT
    p0 = (int(cxp), int(cxp - r0 * KR * ss)); p1 = (int(cxp), int(cxp - r1 * KR * ss))
    cv2.line(big, p0, p1, 1.0, max(1, int(width * KR * ss)), cv2.LINE_AA)
    m = cv2.resize(big, (N, N), interpolation=cv2.INTER_AREA)
    return cv2.GaussianBlur(m, (0, 0), blur) if blur > 0 else m
groove = line_mask(0.20, 0.74, 0.070, 0.6)
groove_lip = line_mask(0.20, 0.74, 0.070, 0.6)
lip = np.roll(np.roll(groove_lip, 2, 0), 2, 1) * (1 - groove)              # liseré éclairé en bas à droite de la rainure
off_rgb = np.dstack([np.full((N, N), 30.0), np.full((N, N), 24.0), np.full((N, N), 44.0)])
off_rgb = off_rgb * (1 - lip[..., None]) + np.array([150, 140, 190.0]) * lip[..., None]
dot = np.zeros((N * ss, N * ss), np.float32); cv2.circle(dot, (N * ss // 2, int(N * ss / 2 - 0.88 * KR * ss)), int(0.042 * KR * ss), 1.0, -1, cv2.LINE_AA)
dot = cv2.resize(dot, (N, N), interpolation=cv2.INTER_AREA)
dot_sh = np.roll(np.roll(cv2.GaussianBlur(dot, (0, 0), 1.6), 2, 0), 2, 1) * (1 - dot) * 0.5
mk_rgb = off_rgb.copy(); mk_a = np.clip(groove * 0.9 + lip * 0.25, 0, 1)
# point blanc (gris quand la pédale est éteinte : même calque, le code assombrit le point via marker_on)
mk_rgb = mk_rgb * (1 - dot[..., None]) + np.array([238, 242, 250.0]) * dot[..., None]
mk_a = np.maximum(mk_a, dot); mk_rgb = mk_rgb * (1 - dot_sh[..., None]); mk_a = np.maximum(mk_a, dot_sh)
save('marker_off', mk_rgb, mk_a)
core = line_mask(0.21, 0.73, 0.040, 0.5)
core_hot = line_mask(0.21, 0.73, 0.018, 0.4)
on_rgb = np.dstack([np.full((N, N), 126.0), np.full((N, N), 240.0), np.full((N, N), 214.0)])
on_rgb = on_rgb * (1 - core_hot[..., None]) + np.array([200, 255, 244.0]) * core_hot[..., None]
save('marker_on', on_rgb, np.clip(core * 1.1, 0, 1))
glow = np.clip(line_mask(0.20, 0.74, 0.10, KR * 0.035) * 0.55 + line_mask(0.18, 0.76, 0.06, KR * 0.012) * 0.35, 0, 1)
save('marker_glow', np.dstack([np.full((N, N), 126.0), np.full((N, N), 240.0), np.full((N, N), 214.0)]), glow)
print('ok', OUT)

if os.environ.get('KNOB_DEBUG'):
    for i, P in enumerate(Ps):
        print(i, 'angle repère', round(math.degrees(pointer_angle(P)), 1))
    v = (valid.astype(np.float32).mean(0) * 255).astype(np.uint8)
    Image.fromarray(v[:200:2, ::8]).resize((1024, 400)).save('/tmp/claude-0/valid.png')
    d = Ps[0].mean(2)
    Image.fromarray(np.clip(d[:200:2, ::8], 0, 255).astype(np.uint8)).resize((1024, 400)).save('/tmp/claude-0/polar0.png')

if os.environ.get('KNOB_CHECK'):
    capm = (rs > 20) & (rs < R_CAP - 3)
    print('Ps cap', np.nanmean(np.where(valid[..., None], Ps, np.nan)[:, capm], axis=(0, 1, 2)).round(1))
    print('matter cap', matter[capm].mean((0, 1)).round(1), 'light cap', light[capm].mean((0, 1)).round(1))
    print('cart cap matter', mat_c[(rr > 20) & (rr < R_CAP - 3)].mean(0).round(1))
    comp = mat_c * (1 - a_h[..., None]) + col * a_h[..., None]
    print('cart recomposé', comp[(rr > 20) & (rr < R_CAP - 3)].mean(0).round(1))
