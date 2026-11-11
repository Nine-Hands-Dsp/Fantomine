# FANTOMINE (NINE HANDS | DSP) - notice PDF en francais, illustree avec le rendu reel du plugin (tools/render).
# Usage : python3 tools/manual.py [<dossier des captures (tools/render)>] <fichier PDF de sortie>
#   avec captures : recompose les images et les copie dans tools/manual_assets/ ;
#   sans captures : reprend les images composees de tools/manual_assets/.
# Version lue dans CMakeLists.txt. Couverture « minimale » (gabarit fixe commun a toutes les notices NINE HANDS | DSP).
import os, re, sys, json, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (BaseDocTemplate, PageTemplate, NextPageTemplate, Frame, Paragraph, Spacer, Image as RLImage,
                                Table, TableStyle, PageBreak, KeepTogether)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERSION = re.search(r"project\s*\(\s*\w+\s+VERSION\s+([0-9.]+)", open(os.path.join(ROOT, "CMakeLists.txt")).read()).group(1)
SHOTS = sys.argv[1] if len(sys.argv) > 2 else None
OUT = sys.argv[-1] if len(sys.argv) > 1 else os.path.join(ROOT, "docs", "Fantomine_Notice_FR_v" + VERSION + ".pdf")
TMP = os.path.dirname(os.path.abspath(OUT))
FONTS = os.path.join(ROOT, "assets", "fonts")
ASSETS = os.path.join(ROOT, "tools", "manual_assets")
LOGO_PNG = os.path.join(ROOT, "assets", "nine_hands_logo_blanc.png")      # rendu du SVG officiel blanc (v003)

for n, f in (("Pop", "Poppins-Regular"), ("PopL", "Poppins-Light"), ("PopM", "Poppins-Medium"), ("PopB", "Poppins-Bold"),
             ("Title", "BarlowCondensed-ExtraBold")):
    pdfmetrics.registerFont(TTFont(n, os.path.join(FONTS, f + ".ttf")))

ACC = colors.HexColor("#2E9C8A"); ACC_L = colors.HexColor("#9FF5E2"); MINT = colors.HexColor("#7EF0D6")   # menthe du neon
DARK = colors.HexColor("#1D1B26"); GREY = colors.HexColor("#625E6E"); LIGHT = colors.HexColor("#EAF7F4")
LAY = json.load(open(os.path.join(ROOT, "tools", "layout.json")))

NAMES = ["fm_annotated.png", "fm_onoff.png", "fm_octave.png", "fm_bar.png", "fm_glow.png", "fm_menus.png", "fm_screen.png", "fm_cover.png"]
if SHOTS:
    def shot(name): return Image.open(os.path.join(SHOTS, name)).convert("RGB")
    src = shot("fm_exact_on.png")
    k = src.height / 900.0                          # repere du plugin : 1175 x 900 unites (fond 2350 x 1800 / 2)
    kn = LAY["knobs"]; sx, sy, sw, sh = LAY["screen"]; lx, ly = LAY["led"]; fx, fy = LAY["foot"]
    px, py, pw, ph = LAY["pill"]; bx, by, bw, bh = LAY["brand"]; o = LAY["octave"]; box = LAY["box"]; j = LAY["jacks"]

    # ---------- capture annotee ----------
    marks = [(1, bx + 30, by + 20), (2, sx + sw - 10, sy - 14), (3, kn[0][0] + 66, kn[0][1] - 72), (4, kn[1][0] + 66, kn[1][1] - 72),
             (5, kn[2][0] + 66, kn[2][1] - 72), (6, kn[3][0] + 66, kn[3][1] - 72), (7, kn[4][0] + 66, kn[4][1] - 72),
             (8, kn[5][0] + 66, kn[5][1] - 72), (9, o["slot"][0] + o["slot"][2] + 50, o["slot"][1] - 6), (10, lx + 34, ly - 14),
             (11, px + pw + 24, py + ph / 2), (12, fx + 84, fy - 40), (13, box[0] + box[2] - 50, j["inY"] - 40),
             (14, box[0] + box[2] - 50, j["expY"] + 42), (15, box[0] + 46, j["outY"] - 40)]
    ann = src.copy(); dr = ImageDraw.Draw(ann)
    fnt = ImageFont.truetype(os.path.join(FONTS, "Poppins-Bold.ttf"), 30)
    for n, x, y in marks:
        cx, cy, r = x * k, y * k, 26
        dr.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 255, 255), outline=(46, 156, 138), width=5)
        dr.text((cx, cy + 1), str(n), font=fnt, fill=(29, 27, 38), anchor="mm")
    ann.save(os.path.join(TMP, NAMES[0]))

    def crop_u(im, b): return im.crop(tuple(int(round(v * k)) for v in b))
    gap = 18
    def strip(parts, path, bg=(255, 255, 255)):
        s = Image.new("RGB", (sum(p.width for p in parts) + gap * (len(parts) - 1), max(p.height for p in parts)), bg)
        x = 0
        for p in parts: s.paste(p, (x, 0)); x += p.width + gap
        s.save(path); return path

    byp = shot("fm_exact_bypass.png")
    strip([byp.resize((940, 720), Image.LANCZOS), src.resize((940, 720), Image.LANCZOS)], os.path.join(TMP, NAMES[1]))
    # levier d'octave : 0 puis +1
    sl = o["slot"]; box_oc = (sl[0] - 50, o["label"][1] - 18, sl[0] + sl[2] + 50, o["zero"][1] + 16)
    strip([crop_u(src, box_oc), crop_u(shot("fm_exact_oct_up.png"), box_oc)], os.path.join(TMP, NAMES[2]))
    # pastille : barre de presets, ligne d'etat
    box_bar = (px - 8, py - 8, px + pw + 8, py + ph + 8)
    bars = [crop_u(shot(n), box_bar) for n in ("fm_exact_on.png", "fm_exact_status.png")]
    bw_, bh_ = bars[0].size
    col = Image.new("RGB", (bw_, bh_ * 2 + gap), (255, 255, 255))
    for i, b in enumerate(bars): col.paste(b, (0, i * (bh_ + gap)))
    col.save(os.path.join(TMP, NAMES[3]))
    # reglage Glow : 25 / 50 / 75 / 100 % (titre neon + LED)
    box_gl = (lx - 120, ly - 90, lx + 120, ly + 60)
    box_t = (bx - 10, by + 10, bx + bw + 10, by + bh - 10)
    tiles = []
    for n in ("fm_glow_25.png", "fm_glow_50.png", "fm_glow_75.png", "fm_exact_on.png"):
        im = shot(n); t = crop_u(im, box_t); l = crop_u(im, box_gl).resize((int(t.width * 0.5), int(t.width * 0.5 * 150 / 240)), Image.LANCZOS)
        c = Image.new("RGB", (t.width, t.height + l.height), (255, 255, 255)); c.paste(t, (0, 0)); c.paste(l, ((t.width - l.width) // 2, t.height))
        tiles.append(c)
    strip(tiles, os.path.join(TMP, NAMES[4]))
    # menus clic droit
    ms = [Image.open(os.path.join(SHOTS, n)).convert("RGBA") for n in ("fm_menu.png", "fm_menu_knob.png", "fm_menu_glow.png")]
    mm_ = Image.new("RGBA", (sum(m.width for m in ms) + gap * 4, max(m.height for m in ms)), (255, 255, 255, 255))
    x = 0
    for m in ms: mm_.alpha_composite(m, (x, 0)); x += m.width + gap * 2
    mm_.convert("RGB").save(os.path.join(TMP, NAMES[5]))
    # ecran : normal puis HOLD
    box_sc = (sx - 6, sy - 6, sx + sw + 6, sy + sh + 6)
    strip([crop_u(src, box_sc), crop_u(shot("fm_exact_hold.png"), box_sc)], os.path.join(TMP, NAMES[6]))

    # ---------- couverture : pedale detouree (canal alpha du fond), reflet au sol, halo menthe tres doux ----------
    bg_a = Image.open(os.path.join(ROOT, "background.png")).split()[3].resize(src.size, Image.LANCZOS)
    cut = Image.new("RGBA", src.size, (0, 0, 0, 0)); cut.paste(src, (0, 0), bg_a)
    cut = cut.crop(cut.getbbox())
    cw, ch = cut.size
    pad = int(cw * 0.16)
    canvas = Image.new("RGBA", (cw + 2 * pad, int(ch * 1.30) + pad), (0, 0, 0, 255))
    yy, xx = np.mgrid[0:canvas.height, 0:canvas.width].astype(np.float64)
    gcx, gcy = canvas.width / 2, pad + ch * 0.45
    glow = np.exp(-(((xx - gcx) / (cw * 0.62)) ** 2 + ((yy - gcy) / (ch * 0.48)) ** 2)) * 26
    edge = np.clip(np.minimum.reduce([xx, canvas.width - 1 - xx, yy, canvas.height - 1 - yy]) / (pad * 0.9), 0, 1)
    glow *= edge ** 2
    halo = np.dstack([glow * 0.50, glow * 0.95, glow * 0.85, np.full_like(glow, 255)]).astype(np.uint8)
    canvas = Image.alpha_composite(canvas, Image.fromarray(halo, "RGBA"))
    refl = cut.transpose(Image.FLIP_TOP_BOTTOM)
    ra = np.array(refl).astype(np.float64)
    fade = np.clip(1 - np.arange(refl.height) / (refl.height * 0.22), 0, 1) ** 1.6 * 0.22
    ra[..., 3] *= fade[:, None]
    canvas.alpha_composite(Image.fromarray(ra.astype(np.uint8), "RGBA"), (pad, pad + ch + 6))
    canvas.alpha_composite(cut, (pad, pad))
    canvas = canvas.crop((0, 0, canvas.width, pad + int(ch * 1.20)))
    canvas.convert("RGB").save(os.path.join(TMP, NAMES[7]))
    os.makedirs(ASSETS, exist_ok=True)
    for n in NAMES: shutil.copy(os.path.join(TMP, n), os.path.join(ASSETS, n))
annotated, onoff, oct_img, bar_img, glow_img, menus_img, screen_img, cover = [os.path.join(ASSETS, n) for n in NAMES]

def img(path, width):
    im = Image.open(path); h = width * im.height / im.width
    return RLImage(path, width=width, height=h)

# ---------- styles ----------
st = {
    "h1": ParagraphStyle("h1", fontName="PopB", fontSize=20, leading=24, textColor=ACC, spaceAfter=8, spaceBefore=4, keepWithNext=1),
    "h2": ParagraphStyle("h2", fontName="PopM", fontSize=13, leading=17, textColor=DARK, spaceAfter=4, spaceBefore=10, keepWithNext=1),
    "p": ParagraphStyle("p", fontName="Pop", fontSize=9.6, leading=14, textColor=DARK, spaceAfter=5),
    "tip": ParagraphStyle("tip", fontName="Pop", fontSize=9.2, leading=13, textColor=DARK, spaceAfter=4),
    "small": ParagraphStyle("small", fontName="Pop", fontSize=8.2, leading=11.5, textColor=GREY, spaceAfter=4),
    "cell": ParagraphStyle("cell", fontName="Pop", fontSize=8.6, leading=11.4, textColor=DARK),
    "cellb": ParagraphStyle("cellb", fontName="PopM", fontSize=8.6, leading=11.4, textColor=DARK),
}
def P(t, s="p"): return Paragraph(t, st[s])
def bullets(items, s="p"): return [P("&bull;&nbsp;&nbsp;" + i, s) for i in items]
def table(rows, widths, header=True):
    data = [[P(c, "cellb" if (header and r == 0) else "cell") for c in row] for r, row in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    style = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.HexColor("#D2E6E1")),
             ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
    if header: style += [("BACKGROUND", (0, 0), (-1, 0), LIGHT), ("LINEBELOW", (0, 0), (-1, 0), 0.8, ACC)]
    t.setStyle(TableStyle(style)); return t
def side(left, right, wl):
    t = Table([[left, right]], colWidths=[wl, W - wl])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (0, 0), 0), ("RIGHTPADDING", (-1, 0), (-1, 0), 0)]))
    return t

# ---------- donnees (identiques au code livre : PluginProcessor.cpp) ----------
#            nom                   glide range tone vib speed blend oct mode
FACTORY = [("Classic Theremin",    35, 12, 35, 30, 45, 75,  0, "UP", "La référence : portamento doux, vibrato chantant (preset par défaut)."),
           ("Clara (Pure Sine)",   45, 12,  5, 35, 40, 85,  0, "UP", "Sinusoïde presque pure, glide lent : le thérémine de concert."),
           ("Sci-Fi Swoop",        80, 24, 40, 15, 55, 90,  0, "BIP.", "Glissandos énormes, ±2 octaves, pédale bipolaire : SF des années 50."),
           ("Ghost Choir +1",      30,  7, 55, 30, 40, 60, +1, "UP", "Une octave au-dessus, timbre vocal : une soprano fantôme."),
           ("Spectre Bass -1",     25, 12, 45, 10, 35, 65, -1, "DOWN", "Une octave en dessous, plongées à la pédale : basse spectrale."),
           ("Saucer Wobble",       55,  5, 30, 85, 85, 85,  0, "BIP.", "Vibrato rapide et profond : soucoupe volante."),
           ("Haunted Lead",        15,  2, 70, 40, 50, 70,  0, "UP", "Suivi serré, timbre d'anche : suit les traits rapides."),
           ("Ondes Blend",         40, 12, 60, 25, 45, 45,  0, "UP", "Guitare et voix à parts presque égales, couleur Ondes Martenot."),
           ("Slow Phantom",       100, 24, 20, 25, 30, 100, 0, "DOWN", "Glide très lent, voix seule : maison hantée."),
           ("Tight Tracker",        2,  2, 25,  0, 50, 80,  0, "UP", "Glide instantané, sans vibrato : le suivi le plus précis."),
           ("Reed Wraith",         30, 12, 100, 35, 50, 80, 0, "UP", "TONE à fond : nasal, façon hautbois."),
           ("Drone Ghost (Hold)",  60, 12, 30, 20, 35, 70, -1, "BIP.", "Pensé pour HOLD : figer une note grave et la jouer à la pédale.")]

W = A4[0] - 36 * mm
f = [NextPageTemplate("p"), Spacer(1, 1), PageBreak()]     # page 1 = couverture dessinee a positions fixes (cover_bg)

f += [P("1. Présentation", "h1"),
      P("<b>FANTOMINE</b> transforme votre guitare en <b>thérémine</b>. Elle écoute la note jouée et la rechante avec une voix spectrale qui glisse "
        "d'une note à l'autre : le glissando reconnaissable entre mille des films de science-fiction des années 1950, des musiques de Hitchcock et de "
        "<i>Good Vibrations</i>."),
      P("Un vrai thérémine a deux antennes, l'une pour la hauteur, l'autre pour le volume. Fantomine les transpose dans le monde du guitariste : la "
        "<b>hauteur</b> vient de la main gauche et une pédale d'expression MIDI la courbe en continu, comme une main qui s'approche de l'antenne ; le "
        "<b>volume</b> suit la dynamique de la main droite : jouez doucement et le fantôme murmure, attaquez fort et il chante."),
      P("Six potards règlent la façon dont la voix bouge (GLIDE, VIBRATO, SPEED), jusqu'où la pédale la courbe (RANGE), son timbre (TONE) et sa place "
        "à côté de la guitare (BLEND). Le levier OCTAVE monte ou descend la voix d'une octave, ou balaie entre les octaves comme une Whammy quand une "
        "pédale le pilote."),
      P("<b>Trajet du signal.</b> Guitare (stéréo sommée en mono) &gt; suivi de note &gt; voix (glide, vibrato, tone) &gt; niveau qui suit votre jeu "
        "&gt; BLEND avec la guitare directe, qui passe toujours en parallèle sans aucun retard. Hauteur et octave sont lissées : jamais d'escalier, même "
        "avec une pédale 7 bits. Monophonique comme le vrai instrument : sur un accord, la voix suit la note la plus forte, en général la plus grave."),
      P("La version 2 redessine entièrement la pédale : façade violette au grand format, titre néon qui s'allume, potards animés (repère lumineux, "
        "flou de mouvement), levier, LED, footswitch et jacks photographiés, sérigraphie vectorielle nette à toutes les tailles, barre de presets sous "
        "la LED, halos lumineux réglables (<b>Glow</b>) et menus du clic droit au style NINE HANDS | DSP."),
      P("2. Installation", "h1")]
f += bullets(["<b>Windows</b> : téléchargez <b>Fantomine-VST3-Windows.zip</b> (page Releases du dépôt GitHub Nine-Hands-Dsp/Fantomine), "
              "décompressez-le et copiez tout le dossier <b>Fantomine.vst3</b> dans <b>C:\\Program Files\\Common Files\\VST3\\</b>. "
              "Aucun redistribuable Visual C++ n'est nécessaire.",
              "<b>macOS</b> (universel, Apple Silicon et Intel) : téléchargez <b>Fantomine-VST3-macOS.zip</b>, copiez <b>Fantomine.vst3</b> dans "
              "<b>~/Library/Audio/Plug-Ins/VST3/</b>, puis lancez une fois dans le Terminal : "
              "<i>xattr -cr ~/Library/Audio/Plug-Ins/VST3/Fantomine.vst3</i> (retire la quarantaine du téléchargement).",
              "<b>Reaper</b> : Options &gt; Préférences &gt; Plug-ins &gt; VST &gt; <i>Re-scan</i>. Le plugin apparaît sous le nom "
              "<b>Fantomine (NINE HANDS | DSP)</b>, catégorie Fx | Pitch Shift."])
f += [P("Faire entrer la pédale d'expression dans Reaper", "h2")]
f += bullets(["Insérez Fantomine sur la piste guitare, avant le simulateur d'ampli (Ampire, par exemple).",
              "Créez une piste <b>Pédales</b> : entrée <b>MIDI &gt; votre contrôleur &gt; All channels</b>, armée, monitoring activé.",
              "Dans le routage de la piste Pédales, ajoutez un envoi vers la piste guitare avec <b>Audio : None</b> et <b>MIDI : All</b>.",
              "Bougez la pédale : le petit point MIDI de l'écran clignote. Aucune commande n'est assignée par défaut : confiez la pédale à PITCH "
              "(ou à toute autre commande) par MIDI Learn (section 6)."])
f.append(PageBreak())

ov = [["N°", "Commande", "Rôle"],
      ["1", "Titre néon", "Allumé quand la pédale est active, éteint en bypass."],
      ["2", "Écran", "Mode de la pédale, voix en direct, note jouée, barre EXP, point MIDI."],
      ["3", "GLIDE", "Temps de glissement vers chaque note."],
      ["4", "RANGE", "Amplitude de la pédale de hauteur, ±1 à ±24 demi-tons."],
      ["5", "TONE", "De la sinusoïde pure au timbre d'anche."],
      ["6", "VIBRATO", "Profondeur du vibrato."],
      ["7", "SPEED", "Vitesse du vibrato, 3 à 9 Hz."],
      ["8", "BLEND", "Mélange guitare / voix."],
      ["9", "Levier OCTAVE", "−1, 0, +1 octave ; whammy avec une pédale."],
      ["10", "LED", "Suit la voix ; pulse en HOLD."],
      ["11", "Barre de presets / ligne d'état", "Au repos : flèches = preset précédent / suivant, clic sur le nom = menu. Pendant un réglage : la valeur en direct."],
      ["12", "Footswitch", "Clic : bypass · appui de 0,6 s : HOLD."],
      ["13", "IN", "Décoratif (l'audio vient de la piste)."],
      ["14", "EXP", "Décoratif (les pédales arrivent en MIDI)."],
      ["15", "OUT", "Décoratif."]]
f += [P("3. Vue d'ensemble de l'interface", "h1"), img(annotated, W), Spacer(1, 3 * mm),
      table(ov, [9 * mm, 48 * mm, W - 57 * mm]), PageBreak(),
      KeepTogether([img(onoff, W), P("À gauche : bypass (titre, potards, écran et LED éteints) · À droite : pédale active.", "small")])]

f += [P("4. Les commandes en détail", "h1")]
ctl = [("GLIDE (FAST &gt; SLOW)", "Temps que met la voix pour atteindre une nouvelle note, de 2 ms (collée à votre jeu) à environ 0,7 s (un fantôme "
        "paresseux qui glisse). Courbe exponentielle : la première moitié couvre la zone jouable (2 à environ 40 ms), la seconde les grands glissandos. "
        "Seuls les changements de note glissent ; la pédale de hauteur et la whammy ont leur propre lissage très court. Vers 11 h : le portamento "
        "classique du thérémine. Défaut 35 %."),
       ("RANGE (±1 &gt; ±24)", "Nombre de demi-tons dont la pédale de hauteur courbe la voix en fin de course, par pas entiers de 1 à 24. RANGE ±12 "
        "avec la pédale en mode UP : pointe enfoncée = une octave au-dessus de la note jouée. Sans effet sur le levier OCTAVE. Défaut ±12."),
       ("TONE (PURE &gt; REED)", "Tout à gauche : une sinusoïde presque pure, comme le thérémine RCA de Clara Rockmore. En tournant, des harmoniques "
        "s'ajoutent avec un léger déséquilibre pair / impair (la couleur hétérodyne des vrais thérémines) et un formant vocal monte vers 1,1 kHz, "
        "jusqu'à un son d'anche proche du hautbois ou des Ondes Martenot. Défaut 35 %."),
       ("VIBRATO (0 &gt; WIDE)", "Profondeur du vibrato, jusqu'à environ ±0,65 demi-ton. Humanisé : sur chaque nouvelle note il part de zéro et "
        "s'épanouit en un tiers de seconde, sa vitesse et sa profondeur dérivent très légèrement. Défaut 30 %."),
       ("SPEED (SLOW &gt; FAST)", "Vitesse du vibrato, 3 à 9 Hz (affichée en Hz). Les thérémistes classiques restent vers 5 à 6 Hz (midi). "
        "Défaut 45 % (environ 4,9 Hz)."),
       ("BLEND (DRY &gt; VOICE)", "Équilibre guitare / voix à puissance constante : le volume perçu reste égal sur toute la course. Entre les deux, "
        "la guitare donne l'attaque et la voix le sustain. Défaut 75 %.")]
for name, txt in ctl: f += [P(name, "h2"), P(txt)]
f += [P("Utiliser les potards", "h2")]
f += bullets(["Tirez vers le haut ou le bas (<b>Maj</b> = 5 fois plus fin), ou utilisez la molette ; <b>double-clic</b> = valeur par défaut. "
              "La ligne d'état affiche la valeur exacte (<i>GLIDE 35 %</i>, <i>SPEED 4.9 Hz</i>, <i>RANGE ±12 st</i>).",
              "Le repère s'allume en menthe quand la pédale est active et s'éteint en bypass. Chapeau, couronne crantée, repère et ombre tournent ensemble, "
              "avec un léger flou de mouvement quand le potard tourne vite (automation, pédale) ; les reflets restent fixes.",
              "<b>Clic droit sur un potard</b> : son MIDI Learn (section 6)."])

f += [P("Levier OCTAVE et whammy", "h2"),
      side(bullets(["Cliquez à gauche ou à droite de la poignée, faites-la glisser ou utilisez la molette : trois positions, −1, 0 et +1 octave.",
                    "<b>Whammy</b> : affectez une pédale d'expression MIDI à OCTAVE (clic droit sur le levier &gt; MIDI Learn) et le levier glisse "
                    "en continu avec le pied, la voix suivant entre les octaves sans paliers. La ligne d'état affiche la transposition exacte "
                    "(<i>OCTAVE +7.0 st</i>).",
                    "Toucher le levier à la souris (ou charger un preset) rend la main aux trois positions ; le mouvement suivant de la pédale reprend "
                    "le contrôle. La whammy et la pédale de hauteur s'additionnent."]),
           [img(oct_img, 66 * mm), P("Levier sur 0 puis sur +1.", "small")], W - 70 * mm)]
wr = [["Plage de la whammy (clic droit &gt; Settings)", "Talon", "Centre", "Pointe"],
      ["Heel -1 oct &gt; centre 0 &gt; toe +1 oct (défaut)", "−1", "0", "+1"], ["Heel 0 &gt; toe +1 oct", "0", "+0,5", "+1"],
      ["Heel 0 &gt; toe -1 oct", "0", "−0,5", "−1"]]
f += [KeepTogether([Spacer(1, 1 * mm), table(wr, [W - 54 * mm, 18 * mm, 18 * mm, 18 * mm])])]

scr = [["Élément", "Rôle"],
       ["Pastille UP / DOWN / BIPOLAR", "Sens de la pédale de hauteur ; un clic pour changer (clic droit : MIDI Learn de PEDAL MODE)."],
       ["Point MIDI", "Clignote à chaque message de contrôleur MIDI reçu."],
       ["Barre EXP", "Position de la pédale de hauteur ; à tirer à la souris (ou molette) pour tester sans pédale. Clic droit : MIDI Learn de PITCH."],
       ["Voix fantôme", "La vraie forme d'onde de la voix, dessinée en direct."],
       ["Note", "Note chantée (après pédale, octave et glide), avec les cents."],
       ["HOLD / LEARN", "En violet : note figée (HOLD) ou MIDI Learn en attente."]]
f += [P("L'écran", "h2"), img(screen_img, W * 0.9), P("L'écran en jeu, puis avec HOLD.", "small"), table(scr, [44 * mm, W - 44 * mm])]

f += [P("5. Footswitch, LED, bypass, HOLD et Glow", "h1")]
fs = [["Action", "Résultat"],
      ["Appui court", "Bypass on / off. Si HOLD est actif, un appui court relâche HOLD."],
      ["Appui long (0,6 s)", "HOLD on / off ; HOLD réactive aussi la pédale si elle était en bypass."]]
f += [table(fs, [40 * mm, W - 40 * mm]), Spacer(1, 2 * mm)]
f += bullets(["<b>HOLD</b> fige la note en cours et son niveau : le fantôme continue de chanter pendant que vous arrêtez de jouer ou jouez autre chose "
              "par-dessus. La pédale de hauteur, la whammy et le vibrato agissent toujours sur la note figée. La LED pulse, l'écran affiche HOLD en violet "
              "et la ligne d'état indique <i>HOLD - tap to release</i>.",
              "<b>LED</b> : pédale active, elle brille avec la voix ; en HOLD elle pulse ; en bypass elle est éteinte. Sa lumière se reflète sur la façade "
              "et dans le chrome du footswitch.",
              "<b>Bypass : tout s'éteint.</b> Le titre néon, les repères des potards, l'écran et la LED s'éteignent ensemble ; l'audio passe par un fondu "
              "de 12 ms, sans clic. Au rallumage, le néon scintille brièvement avant de se stabiliser.",
              "<b>Glow</b> (clic droit &gt; <i>Glow (halo of the lights)</i>) : règle le halo autour des lumières (néon du titre, LED, repères des potards, "
              "voix de l'écran) : <b>25 %</b>, <b>50 %</b>, <b>75 %</b> ou <b>100 %</b> (par défaut). Seul le halo change ; la lumière elle-même garde "
              "son éclat. Réglage commun à toutes les instances, enregistré sur l'ordinateur."])
f += [KeepTogether([Spacer(1, 1 * mm), img(glow_img, W), P("Glow 25 %, 50 %, 75 % et 100 %.", "small")])]

lc = [["Commande", "Type"],
      ["PITCH (pédale de hauteur)", "Continu, ±RANGE ; 14 bits accepté (CC 0-31 + LSB sur le CC n+32)."],
      ["OCTAVE (whammy)", "Continu : le levier glisse entre les octaves (plage de la whammy)."],
      ["VIBRATO, SPEED, BLEND, GLIDE, TONE", "Continu : le potard suit la pédale."],
      ["RANGE", "Continu, demi-tons entiers ±1 à ±24."],
      ["PEDAL MODE", "Sélecteur 3 positions : 0-42 UP, 43-85 DOWN, 86-127 BIPOLAR."],
      ["FOOTSWITCH", "Momentané : 64 ou plus = appuyé, moins de 64 = relâché ; appui court = bypass, appui long = HOLD."]]
pd = [["Mode", "Talon", "Pointe"], ["UP (défaut)", "votre note", "+RANGE"], ["DOWN", "votre note", "−RANGE"],
      ["BIPOLAR", "−RANGE (centre = votre note)", "+RANGE"]]
f += [P("6. MIDI", "h1"),
      P("Fantomine lit les messages MIDI Control Change sur tous les canaux. <b>Aucun CC n'est assigné par défaut</b> : toutes les commandes, PITCH "
        "compris, s'affectent par <b>MIDI Learn</b>. Un CC = une fonction : apprendre un CC pour une commande le retire des autres. Les assignations "
        "sont <b>sauvegardées avec le projet</b>, pas avec les presets.")]
f += bullets(["<b>Clic droit sur une commande</b> : un potard, le levier OCTAVE, le footswitch, la barre EXP ou l'écran (PITCH), la pastille "
              "UP / DOWN / BIPOLAR (PEDAL MODE). Le menu s'ouvre sur cette commande (son CC actuel ou <i>not assigned</i>), avec <b>MIDI Learn</b> et "
              "<b>Clear MIDI</b> ; pendant l'attente, <b>Cancel MIDI learn</b>.",
              "Bougez la pédale ou appuyez sur le footswitch : la ligne d'état affiche <i>MIDI LEARN · &lt;NOM&gt;</i> (l'écran affiche LEARN), puis "
              "<i>&lt;NOM&gt; = CC n</i>.",
              "<b>Clic droit ailleurs &gt; MIDI</b> : <b>Learn</b> de chaque commande avec son CC actuel, sous-menu <b>Footswitch</b> (MIDI Learn, "
              "Clear, CC 64 ou CC 80 en un clic), <b>Clear all MIDI assignments</b> et <b>MIDI pedals inverted (heel / toe)</b>.",
              "<b>MIDI pedals inverted</b> est coché par défaut et inverse seulement les pédales PITCH et OCTAVE ; décochez-le si talon et pointe sont "
              "inversés avec votre pédale. Les premiers 4 % de course au talon (et 4 % autour du centre en BIPOLAR) sont une zone morte.",
              "Tout est aussi automatisable depuis le DAW : Glide, Range, Tone, Vibrato, Speed, Blend, Octave, Octave Whammy, Whammy Range, Pedal Mode, "
              "Expression, MIDI Pedal Invert, Bypass, Hold."])
f += [KeepTogether([Spacer(1, 1 * mm), table(lc, [52 * mm, W - 52 * mm])]),
      KeepTogether([P("Sens de la pédale de hauteur (pastille de l'écran ou clic droit &gt; Settings)", "h2"), table(pd, [40 * mm, 70 * mm, W - 110 * mm])])]

f += [P("7. Fenêtre et menus", "h1")]
f += bullets(["La fenêtre s'ouvre à la taille par défaut, <b>60 %</b> tant que vous n'en choisissez pas une autre, et ne peut jamais être plus petite que 60 %.",
              "Clic droit &gt; <b>Plugin size</b> : <b>60 %</b>, <b>75 %</b> ou <b>100 %</b> pour cette fenêtre (la taille actuelle est cochée, "
              "« (default) » marque la taille par défaut). On peut aussi agrandir la fenêtre par son coin, jusqu'à 150 % (proportions conservées).",
              "<b>Plugin size &gt; Default size (new windows)</b> : choisit la taille d'ouverture de toutes les nouvelles fenêtres de Fantomine (réglage "
              "commun à toutes les instances, enregistré sur l'ordinateur) ; la fenêtre ouverte prend aussitôt cette taille.",
              "Une instance dont la fenêtre a été redimensionnée garde sa taille dans le projet ; une instance jamais redimensionnée s'ouvre à la taille par défaut.",
              "La <b>barre de presets</b> et la <b>ligne d'état</b> partagent la même pastille, sous la LED. Au repos, elle affiche le preset en cours "
              "(un astérisque * signale un potard bougé depuis le chargement). Dès qu'un réglage bouge (souris, molette, automation, MIDI), la ligne "
              "d'état prend sa place en fondu et affiche la valeur, puis s'efface ; un clic sur la pastille fait revenir la barre de presets tout de suite."])
f += [side([img(bar_img, 70 * mm), P("Barre de presets au repos, puis ligne d'état pendant un réglage.", "small")],
           [P("Tous les menus s'ouvrent là où vous cliquez. Le menu principal contient : <b>Plugin size</b>, <b>Glow</b>, <b>Factory presets</b>, "
              "<b>Load / Save user preset</b>, <b>Settings</b> (sens de la pédale de hauteur, plage de la whammy), <b>MIDI</b>, puis la ligne de version.")],
           76 * mm),
      Spacer(1, 2 * mm), KeepTogether([img(menus_img, W), P("Menu principal, menu d'un potard et sous-menu Glow.", "small")])]

pre = [["N°", "Preset", "Glide", "Range", "Tone", "Vib.", "Speed", "Blend", "Oct.", "Pédale"]] + \
      [[str(i + 1), "<b>" + n + "</b>", str(g), "±" + str(r), str(t), str(v), str(s), str(b), ("+" if oc > 0 else "") + str(oc), m]
       for i, (n, g, r, t, v, s, b, oc, m, _) in enumerate(FACTORY)]
chars = [["N°", "Preset", "Caractère"]] + [[str(i + 1), n, d] for i, (n, *_, d) in enumerate(FACTORY)]
f += [P("8. Presets", "h1"),
      P("12 presets usine et 9 emplacements utilisateur. Flèches de la barre = preset usine précédent / suivant, clic sur le nom = menu des presets ; "
        "ils apparaissent aussi dans la liste de programmes du DAW. Un preset mémorise les six potards, l'octave et le mode de pédale (les "
        "assignations MIDI restent dans le projet). <b>Save user preset</b> enregistre dans les emplacements 1 à 9, partagés par tous les projets "
        "(dossier Nine Hands DSP/Fantomine des données de l'utilisateur)."),
      KeepTogether([table(pre, [8 * mm, 36 * mm] + [(W - 44 * mm - 16 * mm) / 7] * 7 + [16 * mm]),
                    P("Valeurs en % sauf Range (demi-tons), Oct. (octave) et Pédale (sens de la pédale de hauteur).", "small")]),
      KeepTogether([table(chars, [8 * mm, 36 * mm, W - 44 * mm])])]

f += [P("9. Conseils d'utilisation", "h1")]
f += bullets(["Dans Reaper, placez Fantomine <b>avant le simulateur d'ampli</b> : la voix passe par l'ampli et le baffle comme la guitare, chaude et "
              "vintage. Sur un canal clair avec BLEND sur VOICE, vous obtenez le thérémine le plus pur ; une longue réverbe à plaque ou un écho à bande "
              "après, c'est le son classique.",
              "<b>Suivi de note</b> : micro manche, tonalité un peu fermée, entrée propre (drive après), une note à la fois.",
              "<b>7 cordes et accordages graves</b> : le suivi descend jusqu'à environ 33 Hz, une 7 cordes accordée en Sol (49 Hz) est suivie avec "
              "précision. Sur les notes les plus graves, mettez OCTAVE sur +1 pour chanter dans le vrai registre du thérémine, ou un peu plus de GLIDE "
              "pour masquer le temps de détection.",
              "<b>Mélodies à la pédale</b> : tenez une note (ou HOLD), RANGE ±12 en BIPOLAR, jouez la mélodie au pied en regardant la note à l'écran. "
              "BLEND sur une pédale = pédale de volume du fantôme."], "tip")
ts = [["Problème", "Solution"],
      ["Pas de voix", "Titre allumé (pas de bypass) ? BLEND pas tout à fait sur DRY ? Niveau d'entrée suffisant ? Jouez une note seule et nette."],
      ["La voix saute d'une octave", "Fondamentale faible : micro manche, tonalité fermée, pas de drive avant Fantomine."],
      ["La pédale ne fait rien", "Point MIDI immobile = le MIDI n'arrive pas (routage) ; il clignote = la pédale n'est pas encore assignée : faites le MIDI Learn."],
      ["La pédale agit à l'envers", "PITCH : changez le sens de la pédale. OCTAVE : changez la plage de la whammy. Talon et pointe inversés : décochez MIDI pedals inverted."],
      ["Le levier ne suit plus la pédale", "Vous l'avez touché ou avez chargé un preset : bougez de nouveau la pédale."],
      ["macOS ne charge pas le plugin", "Retirez l'attribut de quarantaine (section 2), puis rescannez."]]
f += [KeepTogether([P("Dépannage", "h2"), table(ts, [48 * mm, W - 48 * mm])])]

tech = [["Format", "VST3 - Windows 64 bits, macOS universel (Apple Silicon + Intel) - NINE HANDS | DSP, Fx | Pitch Shift, entrée MIDI"],
        ["Canaux", "entrée mono ou stéréo (sommée), sortie mono ou stéréo"],
        ["Latence", "aucune sur la guitare directe ; la voix réagit en quelques dizaines de millisecondes"],
        ["Suivi de note", "monophonique, d'environ 33 Hz à 1,4 kHz, analyse toutes les 5 ms"],
        ["Voix", "oscillateur additif sans repliement, 12 harmoniques, formant vocal, vibrato humanisé, lente dérive hétérodyne"],
        ["Pédale de hauteur", "±1 à ±24 demi-tons, UP / DOWN / BIPOLAR, CC 7 ou 14 bits"],
        ["Octave", "−1 / 0 / +1, ou whammy continue (3 plages)"],
        ["MIDI", "MIDI Learn sur 9 commandes + footswitch, aucun CC assigné par défaut, assignations sauvegardées avec le projet"],
        ["Presets", "12 usine (programmes VST3) + 9 utilisateur communs à toutes les instances"],
        ["Bypass", "fondu de 12 ms, lumières éteintes"],
        ["Fenêtre", "Plugin size 60 % / 75 % / 100 %, taille par défaut au choix (60 % au départ), jamais moins de 60 %, jusqu'à 150 % par le coin ; Glow 25 - 100 %"],
        ["Stabilité Windows", "anti-gel v2 : rendu logiciel, caches refaits par le timer, chien de garde du redessin, aucun appel à l'hôte depuis le thread audio"]]
f += [KeepTogether([P("10. Caractéristiques techniques", "h1"), table(tech, [32 * mm, W - 32 * mm], header=False)])]

def deco(c, doc):
    c.saveState()
    c.setFillColor(DARK); c.rect(0, A4[1] - 6 * mm, A4[0], 6 * mm, stroke=0, fill=1)
    c.setFillColor(MINT); c.rect(0, A4[1] - 6.8 * mm, A4[0], 0.8 * mm, stroke=0, fill=1)
    c.setFont("Pop", 7.5); c.setFillColor(GREY)
    c.drawString(18 * mm, 10 * mm, "Fantomine (NINE HANDS | DSP) · v" + VERSION)
    c.drawRightString(A4[0] - 18 * mm, 10 * mm, str(doc.page))
    c.restoreState()

doc = BaseDocTemplate(OUT, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=18 * mm,
                      title="FANTOMINE - Notice v" + VERSION, author="NINE HANDS | DSP")
# ---- Couverture « minimale » (modele 6) : gabarit fixe commun a toutes les notices (mm depuis le HAUT, logo et bandeau depuis le bas) ----
COVER_NAME, COVER_SUB, COVER_LANG = "FANTOMINE", "Voix de thérémine", "FRANÇAIS"
PEDAL_H, PEDAL_MAXW, PEDAL_TOP = 82 * mm, 115 * mm, 84 * mm
LANG_TOP = 18 * mm
NAME_TOP, NAME_PT = 194 * mm, 30
SUB_TOP, SUB_PT = 208 * mm, 10
LOGO_W, LOGO_BOTTOM = 38 * mm, 22 * mm
BAND_H = 3 * mm
def cover_bg(c, doc):
    c.saveState(); c.setFillColor(colors.black); c.rect(0, 0, A4[0], A4[1], stroke=0, fill=1)
    c.setFillColor(MINT); c.rect(0, 0, A4[0], BAND_H, stroke=0, fill=1)
    def line(text, top, font, size, cs, col):
        w = pdfmetrics.stringWidth(text, font, size) + cs * (len(text) - 1)
        t = c.beginText((A4[0] - w) / 2, A4[1] - top - size * 0.8); t.setFont(font, size); t.setCharSpace(cs)
        t.setFillColor(col); t.textOut(text); c.drawText(t)
    line(COVER_LANG, LANG_TOP, "PopM", 8.5, 0, ACC_L)
    ci = Image.open(cover); iw, ih = ci.size
    cw = iw / 1.32; pad = int(cw * 0.16); ch = (ih - pad) / 1.2            # geometrie de fm_cover.png
    k = min(PEDAL_H / ch, PEDAL_MAXW / cw)
    dw, dh = iw * k, ih * k
    y0 = A4[1] - (PEDAL_TOP + (PEDAL_H - ch * k) / 2) + pad * k
    c.drawImage(cover, (A4[0] - dw) / 2, y0 - dh, dw, dh)
    line(COVER_NAME, NAME_TOP - NAME_PT * 0.02, "Title", NAME_PT, NAME_PT * 0.5, colors.white)
    line(COVER_SUB, SUB_TOP, "Pop", SUB_PT, 1.5, colors.HexColor("#BDC4B8"))
    lw, lh = Image.open(LOGO_PNG).size
    c.drawImage(LOGO_PNG, (A4[0] - LOGO_W) / 2, LOGO_BOTTOM, LOGO_W, LOGO_W * lh / lw, mask="auto")
    c.restoreState()
doc.addPageTemplates([PageTemplate(id="cover", frames=[Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="fc")], onPage=cover_bg),
                      PageTemplate(id="p", frames=[Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")], onPage=deco)])
doc.build(f)
print(OUT)
