"""Composite des calques du potard (même logique que nh::Knob) pour contrôle visuel / GIF."""
import os, sys, math
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); K = os.path.join(os.path.dirname(HERE), 'assets', 'knob')
L = {n: Image.open(os.path.join(K, n + '.png')).convert('RGBA') for n in ['shadow', 'crown', 'cap', 'highlight', 'marker_off', 'marker_on', 'marker_glow']}

def rot(im, deg, blur_deg=0.0, n=1):
    if abs(blur_deg) <= 0.5: return im.rotate(-deg, resample=Image.BICUBIC)
    acc = None; k = max(4, min(28, int(math.ceil(abs(blur_deg) / 1.5)) + 1))   # pas de 1,5° : ni stroboscope ni repère dédoublé
    for i in range(k):
        r = np.asarray(im.rotate(-(deg - blur_deg * i / (k - 1)), resample=Image.BICUBIC)).astype(np.float32)
        r[..., :3] *= r[..., 3:4] / 255
        acc = r if acc is None else acc + r
    acc /= k
    a = acc[..., 3:4]
    acc[..., :3] = np.where(a > 0.5, acc[..., :3] / np.maximum(a, 1e-3) * 255, 0)
    return Image.fromarray(np.clip(acc, 0, 255).astype(np.uint8), 'RGBA')

def knob(deg, light=1.0, glow=1.0, blur_deg=0.0, bg=None, size=None):
    N = L['crown'].size[0]
    base = Image.new('RGBA', (N, N), (0, 0, 0, 0)) if bg is None else bg.copy()
    off = int(0.025 * N)
    sh = rot(L['shadow'], deg)
    base.alpha_composite(sh, (off, off))
    # bloc qui tourne (matière) -> reflets fixes -> repère (rainure, point peint, trait lumineux : au-dessus des reflets,
    # une lumière émise n'est pas assombrie par le reflet du chapeau)
    stack = Image.new('RGBA', (N, N), (0, 0, 0, 0))
    for n in ['crown', 'cap']: stack.alpha_composite(L[n])
    base.alpha_composite(rot(stack, deg, blur_deg))
    base.alpha_composite(L['highlight'])
    mk = L['marker_off'].copy()
    if light > 0:
        on = L['marker_on'].copy(); on.putalpha(on.getchannel('A').point(lambda v: int(v * light)))
        mk.alpha_composite(on)
        g = L['marker_glow'].copy(); g.putalpha(g.getchannel('A').point(lambda v: int(v * light * glow)))
        mk.alpha_composite(g)
    base.alpha_composite(rot(mk, deg, blur_deg))
    return base if size is None else base.resize((size, size), Image.LANCZOS)

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else '/tmp/claude-0'
    bg = Image.new('RGBA', (512, 512), (84, 66, 118, 255))
    row = Image.new('RGB', (512 * 4, 512))
    for i, (d, li) in enumerate([(-80, 1), (0, 1), (100, 1), (-80, 0)]):
        row.paste(knob(d, li, bg=bg).convert('RGB'), (512 * i, 0))
    row.resize((1024, 256), Image.LANCZOS).save(os.path.join(out, 'knob_row.png'))
