"""Fantomine v2 : calques lumineux et repères du plugin, à partir de tools/layout.json (make_art.py).

Sorties (racine du dépôt) :
  knob_shadow.png, knob_crown.png, knob_cap.png, knob_highlight.png, knob_marker_off.png, knob_marker_on.png,
  knob_marker_glow.png   calques du potard nh::Knob (copiés depuis assets/knob)
  glow_title.png         halo menthe du néon « Fantomine » (dosé par Glow), cadré sur la boîte du logo
  glow_led.png           lumière de la LED portée sur la façade (dosée par Glow)
  Layout.h               repères (unités du plugin, 1175 x 900)
"""
import io, json, os, shutil
import numpy as np, cv2
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
LAY = json.load(open(os.path.join(HERE, 'layout.json')))
AS = 2.0
MINT = np.array([126, 240, 214], np.float32)

for n in ['shadow', 'crown', 'cap', 'highlight', 'marker_off', 'marker_on', 'marker_glow']:
    shutil.copy(os.path.join(ROOT, 'assets', 'knob', n + '.png'), os.path.join(ROOT, f'knob_{n}.png'))

def svg_alpha(name, wpx, hpx):
    from playwright.sync_api import sync_playwright
    svg = open(os.path.join(ROOT, name)).read()
    with sync_playwright() as pw:
        b = pw.chromium.launch(); pg = b.new_page(viewport={'width': wpx, 'height': hpx})
        pg.set_content('<html><body style="margin:0;background:transparent">' + svg.replace('<svg ', f'<svg width="{wpx}" height="{hpx}" ', 1) + '</body></html>')
        png = pg.locator('svg').screenshot(omit_background=True); b.close()
    return np.asarray(Image.open(io.BytesIO(png)).convert('RGBA'))[..., 3].astype(np.float32) / 255

# ---- halo du titre : boîte du logo agrandie de 60 unités de chaque côté
bx, by, bw, bh = LAY['brand']
M = 60.0
W, H = int(round((bw + 2 * M) * AS)), int(round((bh + 2 * M) * AS))
a = svg_alpha('FantomineTitle.svg', int(round(bw * AS)), int(round(bh * AS)))
mask = np.zeros((H, W), np.float32); o = int(round(M * AS))
mask[o:o + a.shape[0], o:o + a.shape[1]] = a
halo = cv2.GaussianBlur(mask, (0, 0), 14) * 0.85 + cv2.GaussianBlur(mask, (0, 0), 40) * 0.45
halo = np.clip(halo * 0.55, 0, 1)
Image.fromarray(np.dstack([np.broadcast_to(MINT, (H, W, 3)), halo * 255]).astype(np.uint8), 'RGBA').save(os.path.join(ROOT, 'glow_title.png'))
glow_title_box = [bx - M, by - M, bw + 2 * M, bh + 2 * M]

# ---- néon du titre allumé (tube) et éteint (verre lavande + biseau + ombre), à 3 px par unité, cadrés sur glowTitle
TS = 3.0
TW, TH = int(round((bw + 2 * M) * TS)), int(round((bh + 2 * M) * TS))
a3 = svg_alpha('FantomineTitle.svg', int(round(bw * TS)), int(round(bh * TS)))
tA = np.zeros((TH, TW), np.float32); o3 = int(round(M * TS))
tA[o3:o3 + a3.shape[0], o3:o3 + a3.shape[1]] = a3
k = TS / 2.0
inner = cv2.GaussianBlur(tA, (0, 0), 1.2 * k)
core = np.array([178, 250, 230.0]); hot = np.array([232, 255, 248.0])
lit = core[None, None] * (1 - inner[..., None] * 0.5) + hot[None, None] * (inner[..., None] * 0.5)
Image.fromarray(np.dstack([np.clip(lit, 0, 255), tA * 255]).astype(np.uint8), 'RGBA').save(os.path.join(ROOT, 'title_on.png'))
edge = cv2.GaussianBlur(tA, (0, 0), 2.2 * k)
sft = int(round(3 * k))
bevel = np.clip((np.roll(np.roll(edge, sft, 0), sft, 1) - np.roll(np.roll(edge, -sft, 0), -sft, 1)) * 1.6, -1, 1)
glass = np.dstack([np.full_like(tA, 118), np.full_like(tA, 110), np.full_like(tA, 150)]) + (bevel * 60)[..., None]
s6 = int(round(6 * k))
shadow = cv2.GaussianBlur(np.roll(np.roll(tA, s6, 0), s6, 1), (0, 0), 5 * k) * 0.45 * (1 - tA)
# calque unique : ombre noire sous le verre, verre par-dessus
aout = tA + shadow * (1 - tA)
col = (glass * tA[..., None]) / np.maximum(aout, 1e-4)[..., None]
Image.fromarray(np.dstack([np.clip(col, 0, 255), np.clip(aout, 0, 1) * 255]).astype(np.uint8), 'RGBA').save(os.path.join(ROOT, 'title_off.png'))

# ---- lumière de la LED sur la façade (petite source au-dessus : tache serrée + diffusion large)
lx, ly = LAY['led']; R = 90.0
n = int(round(2 * R * AS))
yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
d = np.hypot(xx - n / 2, yy - n / 2) / AS
illum = (np.exp(-(d / 26) ** 2) * 0.55 + np.exp(-(d / 70) ** 2) * 0.18) * (d > LAY['ledR'] * 1.05)
illum *= np.clip((R - d) / 12, 0, 1)
Image.fromarray(np.dstack([np.broadcast_to(MINT, (n, n, 3)), np.clip(illum * 0.9, 0, 1) * 255]).astype(np.uint8), 'RGBA').save(os.path.join(ROOT, 'glow_led.png'))
glow_led_box = [lx - R, ly - R, 2 * R, 2 * R]

# ---- Layout.h
def P(v): return f'{{ {v[0]:.2f}f, {v[1]:.2f}f }}'
def RC(v): return f'{{ {v[0]:.2f}f, {v[1]:.2f}f, {v[2]:.2f}f, {v[3]:.2f}f }}'
o_ = LAY['octave']; j = LAY['jacks']
box = LAY['box']
lines = [
    '// généré par tools/make_layers.py (d\'après tools/layout.json) - ne pas modifier à la main',
    '// repère du plugin : 1175 x 900 unités (background.png 2350 x 1800 / 2)',
    '#pragma once', '#include <juce_graphics/juce_graphics.h>', 'namespace layout', '{',
    f'    constexpr float frameW = {LAY["frame"][0]:.1f}f, frameH = {LAY["frame"][1]:.1f}f;',
    f'    const juce::Rectangle<float> box {RC(box)};   // boîtier (notice)',
    f'    constexpr float boxR = {LAY["boxR"]:.2f}f;',
    '    // ordre : glide, range, tone, vibrato, speed, blend',
    '    const juce::Point<float> knobPos[6] = { ' + ', '.join(P(k) for k in LAY['knobs']) + ' };',
    f'    constexpr float knobR = {LAY["knobR"]:.2f}f, knobLayer = {LAY["knobR"] * 512 / 196:.2f}f;   // calques 512 px, potard de rayon 196 px',
    f'    constexpr float knobLabelY = {LAY["knobLabelY"]:.2f}f, knobMinMaxY = {LAY["knobMinMaxY"]:.2f}f, knobMinMaxDX = {LAY["knobMinMaxDX"]:.2f}f;',
    f'    constexpr float tickR0 = {LAY["tickR0"]:.2f}f, tickR1 = {LAY["tickR1"]:.2f}f;',
    f'    constexpr float sepX = {LAY["separator"][0]:.2f}f, sepY0 = {LAY["separator"][1]:.2f}f, sepY1 = {LAY["separator"][2]:.2f}f;',
    f'    const juce::Rectangle<float> screen {RC(LAY["screen"])};',
    f'    const juce::Point<float> ledPos {P(LAY["led"])}; constexpr float ledS = {LAY["ledS"]:.2f}f, ledR = {LAY["ledR"]:.2f}f;',
    f'    const juce::Rectangle<float> glowLed {RC(glow_led_box)};',
    f'    const juce::Point<float> fsPos {P(LAY["foot"])}; constexpr float footR = {LAY["footR"]:.2f}f, fsS = {LAY["fsS"]:.2f}f, fsFlats = {LAY["flats"]:.2f}f;',
    f'    const juce::Rectangle<float> brand {RC(LAY["brand"])};   // viewBox 3000 x 1000 du logo Fantomine',
    f'    const juce::Rectangle<float> glowTitle {RC(glow_title_box)};',
    f'    const juce::Rectangle<float> presetRect {RC(LAY["pill"])};',
    '    constexpr float presetFont = 23.0f;',
    f'    const juce::Point<float> octLabel {P(o_["label"])}, octM1 {P(o_["m1"])}, octP1 {P(o_["p1"])}, octZero {P(o_["zero"])};',
    f'    const juce::Rectangle<float> octHandle {RC(o_["handleBox"])};   // levier en position 0',
    f'    const juce::Rectangle<float> octSlot {RC(o_["slot"])};',
    f'    constexpr float octTravel = {o_["travel"]:.2f}f;',
    f'    const juce::Point<float> bypassLabel {P(LAY["bypassLabel"])};',
    f'    const juce::Point<float> logoPos {P(LAY["logo"])}; constexpr float logoW = {LAY["logoW"]:.2f}f;',
    f'    constexpr float jackOutY = {j["outY"]:.2f}f, jackInY = {j["inY"]:.2f}f, jackExpY = {j["expY"]:.2f}f;',
    f'    constexpr float jackLabelL = {box[0] + 16:.2f}f, jackLabelR = {box[0] + box[2] - 16:.2f}f;',
    '}',
]
open(os.path.join(ROOT, 'Layout.h'), 'w').write('\n'.join(lines) + '\n')
LAY['glowTitle'] = glow_title_box; LAY['glowLed'] = glow_led_box
json.dump(LAY, open(os.path.join(HERE, 'layout.json'), 'w'), indent=1)
print(open(os.path.join(ROOT, 'Layout.h')).read())
