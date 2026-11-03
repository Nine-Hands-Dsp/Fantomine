# FANTOMINE (Studio Wiga) - notice PDF bilingue (anglais puis francais), illustree avec le rendu reel du plugin.
# Usage : python3 tools/manual.py <fichier PDF de sortie>
# Images : tools/manual_assets/ (captures reprises de la notice v1.3.0, toujours justes : facade, ecran, ligne d'etat ;
# aucune capture de menu). Polices : assets/fonts (Poppins + DejaVuSans pour les fleches).
# Contenu verifie contre PluginEditor.cpp / PluginProcessor.cpp (v1.4.1). Pas d'historique des versions dans le PDF.
import os, sys
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (BaseDocTemplate, PageTemplate, NextPageTemplate, Frame, Paragraph, Spacer, Image as RLImage,
                                Table, TableStyle, PageBreak, CondPageBreak, KeepTogether)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "docs", "Fantomine_Manual_EN-FR_v1.4.1.pdf")
VERSION = "1.4.1"
NAME = "Fantomine"
FONTS = os.path.join(ROOT, "assets", "fonts")
A = os.path.join(ROOT, "tools", "manual_assets")

for n, f in (("Pop", "Poppins-Regular"), ("PopL", "Poppins-Light"), ("PopM", "Poppins-Medium"), ("PopB", "Poppins-Bold"), ("DV", "DejaVuSans")):
    pdfmetrics.registerFont(TTFont(n, os.path.join(FONTS, f + ".ttf")))

ACC = colors.HexColor("#2FA88F"); ACC_L = colors.HexColor("#7FD8C4")       # vert d'eau du neon
DARK = colors.HexColor("#1B1A2A"); GREY = colors.HexColor("#646A78"); LIGHT = colors.HexColor("#E9F4F1")

st = {
    "h1": ParagraphStyle("h1", fontName="PopB", fontSize=20, leading=24, textColor=ACC, spaceAfter=8, spaceBefore=4, keepWithNext=1),
    "h2": ParagraphStyle("h2", fontName="PopM", fontSize=13, leading=17, textColor=DARK, spaceAfter=4, spaceBefore=10, keepWithNext=1),
    "h3": ParagraphStyle("h3", fontName="PopM", fontSize=10.5, leading=14, textColor=ACC, spaceAfter=2, spaceBefore=7, keepWithNext=1),
    "p": ParagraphStyle("p", fontName="Pop", fontSize=9.6, leading=14, textColor=DARK, spaceAfter=5),
    "small": ParagraphStyle("small", fontName="Pop", fontSize=8.2, leading=11.5, textColor=GREY),
    "cap": ParagraphStyle("cap", fontName="Pop", fontSize=8.2, leading=11, textColor=GREY, alignment=TA_CENTER),
    "cell": ParagraphStyle("cell", fontName="Pop", fontSize=8.4, leading=11, textColor=DARK),
    "cellb": ParagraphStyle("cellb", fontName="PopM", fontSize=8.4, leading=11, textColor=DARK),
    "cover": ParagraphStyle("cover", fontName="PopL", fontSize=40, leading=48, textColor=colors.white, alignment=TA_CENTER),
    "coversub": ParagraphStyle("coversub", fontName="Pop", fontSize=12, leading=17, textColor=colors.HexColor("#BDB8C6"), alignment=TA_CENTER),
    "coverlang": ParagraphStyle("coverlang", fontName="PopM", fontSize=8.5, leading=11, textColor=ACC_L),
}
W = A4[0] - 36 * mm

def arrows(t): return t.replace("◀", '<font name="DV">◀</font>').replace("▶", '<font name="DV">▶</font>')
def P(t, s="p"): return Paragraph(arrows(t), st[s])
def img(name, width):
    path = os.path.join(A, name); im = Image.open(path)
    return RLImage(path, width=width, height=width * im.height / im.width)
def table(rows, widths, header=True):
    data = [[P(c, "cellb" if (header and r == 0) else "cell") for c in row] for r, row in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    style = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.HexColor("#D5E2DE")),
             ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
    if header: style += [("BACKGROUND", (0, 0), (-1, 0), LIGHT), ("LINEBELOW", (0, 0), (-1, 0), 0.8, ACC)]
    t.setStyle(TableStyle(style)); return t
def row_of(items, total):  # [(image, caption)] cote a cote
    n = len(items); w = total / n
    cells = [[img(f, w - 4 * mm), P(c, "cap")] if c else [img(f, w - 4 * mm)] for f, c in items]
    t = Table([cells], colWidths=[w] * n)
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("ALIGN", (0, 0), (-1, -1), "CENTER")]))
    return t

# ---------- donnees communes (PluginProcessor.cpp : getFactoryPresets) ----------
PRESETS = [  # nom, glide, range, tone, vib, speed, blend, oct, pedal
    ("Classic Theremin", 35, 12, 35, 30, 45, 75, "0", "UP"), ("Clara (Pure Sine)", 45, 12, 5, 35, 40, 85, "0", "UP"),
    ("Sci-Fi Swoop", 80, 24, 40, 15, 55, 90, "0", "BIP"), ("Ghost Choir +1", 30, 7, 55, 30, 40, 60, "+1", "UP"),
    ("Spectre Bass -1", 25, 12, 45, 10, 35, 65, "−1", "DOWN"), ("Saucer Wobble", 55, 5, 30, 85, 85, 85, "0", "BIP"),
    ("Haunted Lead", 15, 2, 70, 40, 50, 70, "0", "UP"), ("Ondes Blend", 40, 12, 60, 25, 45, 45, "0", "UP"),
    ("Slow Phantom", 100, 24, 20, 25, 30, 100, "0", "DOWN"), ("Tight Tracker", 2, 2, 25, 0, 50, 80, "0", "UP"),
    ("Reed Wraith", 30, 12, 100, 35, 50, 80, "0", "UP"), ("Drone Ghost (Hold)", 60, 12, 30, 20, 35, 70, "−1", "BIP")]

T = {
"en": dict(
 lang="ENGLISH", sub=["Theremin voice", "VST3 for Windows and macOS"], ver="User manual &nbsp;·&nbsp; version " + VERSION,
 intro_t="1. Introduction",
 intro=["<b>Fantomine</b> turns your guitar into a <b>theremin</b>. It listens to the note you play, then sings it back with a spectral voice that glides from note to note: the unmistakable swoop of 1950s science-fiction films, Hitchcock soundtracks and Good Vibrations.",
        "A real theremin has two antennas, one for pitch and one for volume. Fantomine maps them onto a guitarist's world: the <b>pitch</b> comes from your fretting hand and a MIDI expression pedal bends it continuously, like a hand moving towards the antenna; the <b>volume</b> follows your picking dynamics: play softly and the ghost whispers, dig in and it sings.",
        "Six knobs shape how the voice moves (GLIDE, VIBRATO, SPEED), how far the pedal bends it (RANGE), its timbre (TONE) and its balance with your guitar (BLEND). The OCTAVE lever moves the voice one octave up or down, or sweeps between octaves like a Whammy when driven by a pedal.",
        "<b>Signal path.</b> Guitar (stereo summed to mono) &gt; note tracker &gt; voice (glide, vibrato, tone) &gt; level following your playing &gt; BLEND with the dry guitar, which always runs in parallel without any delay. MIDI expression pedals act on pitch, octave and the knobs.",
        "<b>Character.</b> Never stepped: pitch and octave changes are smoothed, so even a 7-bit pedal glides continuously (14-bit pedals are supported). Human vibrato that fades in on each note and breathes slightly. Monophonic like the real instrument: on a chord it follows the strongest note, usually the lowest."],
 inst_t="2. Installation",
 inst=[("Windows", "Unzip the <b>Fantomine-VST3-Windows</b> artifact and copy the whole <b>Fantomine.vst3</b> folder into <b>C:\\Program Files\\Common Files\\VST3\\</b>. No Visual C++ redistributable is needed."),
       ("macOS", "Unzip <b>Fantomine-VST3-macOS</b> (universal: Apple Silicon and Intel) and copy <b>Fantomine.vst3</b> into <b>~/Library/Audio/Plug-Ins/VST3/</b>. The plugin is signed ad hoc; if macOS refuses to load it, run in Terminal: <b>xattr -dr com.apple.quarantine ~/Library/Audio/Plug-Ins/VST3/Fantomine.vst3</b>"),
       ("Reaper", "Options &gt; Preferences &gt; Plug-ins &gt; VST &gt; <b>Re-scan</b>. Fantomine is listed as <b>Fantomine</b> by <b>Studio Wiga</b> (Fx / Pitch Shift).")],
 reaper_h="Getting the expression pedal into Reaper",
 reaper=["Insert Fantomine on your guitar track, before your amp simulator (Two Notes Genome, for example).",
         "Create a track called <b>Pedals</b>: input <b>MIDI &gt; your controller &gt; All channels</b>, armed, record monitoring on.",
         "In the routing of the Pedals track, add a send to the guitar track with <b>Audio: None</b> and <b>MIDI: All</b>.",
         "Move your pedal: the small MIDI dot on Fantomine's screen blinks. No control is assigned by default: give the pedal to PITCH (or to any other control) with MIDI Learn (section 6)."],
 ov_t="3. Interface overview",
 ov_hdr=["#", "Control", "Role", "#", "Control", "Role"],
 ov=[("1", "Neon title", "Lit when on, dark in bypass"), ("2", "Screen", "Preset, pedal mode, live voice, note, EXP bar"),
     ("3", "GLIDE", "Slide time to each new note"), ("4", "RANGE", "Pitch pedal amount, ±1 to ±24 st"),
     ("5", "TONE", "Pure sine to reedy, vocal timbre"), ("6", "VIBRATO", "Vibrato depth"), ("7", "SPEED", "Vibrato rate, 3 to 9 Hz"),
     ("8", "BLEND", "Guitar / voice mix"), ("9", "OCTAVE lever", "−1, 0, +1 octave; whammy with a pedal"),
     ("10", "LED", "Follows the voice; pulses in HOLD"), ("11", "Status line", "Preset, values, BYPASS, HOLD, MIDI Learn"),
     ("12", "Footswitch", "Click: bypass · hold 0.6 s: HOLD"), ("13", "INPUT", "Decorative (audio comes from the track)"),
     ("14", "EXP", "Decorative (pedals arrive as MIDI)"), ("15", "OUTPUT", "Decorative")],
 ov_note="Drag a knob up or down (or use the wheel); the status line shows its exact value. A double-click resets nothing, on purpose. <b>Right-click any control</b> for its MIDI Learn (section 6); right-click elsewhere for the full menu.",
 ctl_t="4. The controls one by one",
 ctl=[("GLIDE (FAST &gt; SLOW)", "Time the voice takes to reach a new note, from 2 ms (glued to your playing) to about 0.7 s (a lazy, sliding ghost). Exponential: the first half covers the playable region (2 to about 40 ms), the second half the dramatic swoops. Only note changes glide; the pitch pedal and the whammy have their own very short smoothing. Around 11 o'clock is the classic theremin portamento. Default 35 %."),
      ("RANGE (±1 &gt; ±24)", "How many semitones the pitch pedal bends the voice at full travel, in whole steps from 1 to 24. RANGE ±12 with the pedal in UP mode: toe down = one octave above the note you play. No effect on the OCTAVE lever. Default ±12."),
      ("TONE (PURE &gt; REED)", "Fully left: an almost pure sine, like Clara Rockmore's RCA theremin. Turning it adds harmonics with a slight even / odd imbalance (the heterodyne colour of real theremins) and raises a vocal formant around 1.1 kHz, up to a reedy sound close to an oboe or Ondes Martenot. Default 35 %."),
      ("VIBRATO (0 &gt; WIDE)", "Vibrato depth, up to about ±0.65 semitone. Humanised: on each new note it starts at zero and blooms over a third of a second, and its speed and depth drift very slightly. Default 30 %."),
      ("SPEED (SLOW &gt; FAST)", "Vibrato rate, 3 to 9 Hz (shown in Hz). Classical thereminists stay around 5–6 Hz (12 o'clock). Default 45 % (about 4.9 Hz)."),
      ("BLEND (DRY &gt; VOICE)", "Balance between guitar and voice with an equal-power law: loudness stays even across the travel. In between, the guitar gives the attack and the voice the sustain. Default 75 %.")],
 oct_h="OCTAVE lever and whammy",
 oct=["Click left or right of the handle, or drag it: three positions, −1, 0 and +1 octave. The status line confirms the change.",
      "<b>Whammy</b>: assign a MIDI expression pedal to OCTAVE (right-click the lever &gt; MIDI Learn) and the lever slides continuously with your foot, the voice following between octaves without steps. The status line shows the exact transposition (for example <b>OCTAVE +7.0 st</b>). The whammy has its own fast smoothing (15 ms), independent of GLIDE.",
      "Touching the lever with the mouse (or loading a preset) gives control back to the three fixed positions; the next pedal movement takes over again. The whammy and the pitch pedal add up."],
 wr_hdr=["Octave whammy range (right-click menu)", "Heel", "Centre", "Toe"],
 wr=[["Heel -1 oct &gt; centre 0 &gt; toe +1 oct (default)", "−1", "0", "+1"], ["Heel 0 &gt; toe +1 oct", "0", "+0.5", "+1"], ["Heel 0 &gt; toe -1 oct", "0", "−0.5", "−1"]],
 scr_h="The screen",
 scr_hdr=["", "Element", "Role"],
 scr=[["a", "◀ arrow", "Previous factory preset"], ["b", "Preset name", "Click: preset menu. An asterisk * means a knob moved since loading"],
      ["c", "▶ arrow", "Next factory preset"], ["d", "Pedal mode", "UP / DOWN / BIPOLAR, click to cycle (MIDI-learnable: right-click it)"],
      ["e", "MIDI dot", "Blinks on every MIDI controller message"], ["f", "EXP bar", "Pitch pedal position; drag it to test without a pedal (right-click: MIDI Learn of PITCH)"],
      ["g", "Ghost voice", "The real waveform, drawn live"], ["h", "Note", "Note sung by the voice (after pedal, octave and glide), with cents"],
      ["i", "Tags", "HOLD (violet) when the note is frozen, LEARN while MIDI Learn waits"]],
 fs_t="5. Footswitch, LED, bypass and HOLD",
 fs_hdr=["Action", "Result"],
 fs=[["Short press", "Bypass on / off. If HOLD is active, a short press releases HOLD instead."],
     ["Long press (0.6 s)", "HOLD on / off; HOLD also switches the pedal on if it was bypassed."]],
 hold="<b>HOLD</b> freezes the current note and its level: the ghost keeps singing while you stop playing or play something else on top. The pitch pedal, the whammy and the vibrato still act on the frozen note. The LED pulses, the screen shows a violet HOLD tag and the status line reads <b>HOLD - tap to release</b>.",
 led="<b>LED and status line.</b> When active, the LED glows with the voice; in HOLD it pulses; in bypass it is off. The status line shows the preset name, the value of a control while you move it (GLIDE 35 %, SPEED 5.2 Hz, RANGE ±12 st…), BYPASS, HOLD and the MIDI Learn messages.",
 byp="<b>Bypass: everything goes dark.</b> The neon title, the knob pointers, the screen and the LED fade out together; the status line reads BYPASS. Audio is crossfaded in 12 ms, so switching never clicks. Switching back on, the neon flickers briefly before it settles.",
 act="Active", bp="Bypass",
 midi_t="6. MIDI",
 midi_intro="Fantomine reads MIDI Control Change messages on any channel. <b>No CC is assigned by default</b>: every control, PITCH included, is assigned with <b>MIDI Learn</b>. One CC = one function: learning a CC for a control removes it from the others (a pedal learned for the whammy can no longer bend the pitch by accident). Assignments are <b>saved with the project</b>, not with presets.",
 learn_h="MIDI Learn",
 learn=["<b>Right-click a control</b>: a knob (GLIDE, RANGE, TONE, VIBRATO, SPEED, BLEND), the OCTAVE lever, the footswitch, the EXP bar of the screen (PITCH) or the UP / DOWN / BIPOLAR pill (PEDAL MODE). The menu starts with <b>MIDI Learn: &lt;NAME&gt; (none)</b> (or the learnt CC, e.g. <b>(CC 12)</b>), <b>Clear MIDI: &lt;NAME&gt;</b> and, while waiting, <b>Cancel MIDI learn</b>; choosing the same Learn again also cancels.",
        "Move the pedal or press the footswitch: the status line shows <b>MIDI LEARN: move a control for &lt;NAME&gt;</b> (the screen shows a LEARN tag), then <b>&lt;NAME&gt; = CC n</b> for two seconds.",
        "Right-click an empty area &gt; <b>Expression pedals (MIDI)</b>: one entry per control (<b>Learn: PITCH (bend)</b>, <b>OCTAVE (whammy)</b>, VIBRATO, SPEED, BLEND, GLIDE, RANGE, TONE, PEDAL MODE) with its current CC (<i>not assigned</i> until you learn one), each with <b>MIDI Learn</b> and <b>Clear</b>; for PITCH, quick choices CC 11 Expression, CC 4 Foot Controller, CC 7 Volume, CC 1 Modulation and CC 2 Breath. Then <b>Cancel MIDI learn</b> (while waiting), <b>Clear all MIDI assignments</b> (removes every assignment, footswitch included) and <b>Invert pedal direction</b>.",
        "<b>Footswitch (MIDI)</b> sub-menu: <b>MIDI Learn (press the footswitch)</b>, <b>None (use the DAW's MIDI learn)</b> (the default), or CC 64 / CC 80 in one click.",
        "A project saved with an earlier version that still had the former factory assignment (PITCH on CC 11, nothing else) opens with no assignment: learn your pedal again. A project in which you had changed or added an assignment keeps all its assignments as saved."],
 st_caps=["MIDI Learn waiting for a control", "Assignment confirmed (2 s)", "Value while a knob moves"],
 lc_h="Learnable controls",
 lc_hdr=["Control", "Type"],
 lc=[["PITCH (pitch pedal)", "Continuous, ±RANGE; 14-bit accepted (CC 0–31 + LSB on CC n+32)"],
     ["OCTAVE (whammy)", "Continuous: the lever slides between octaves (whammy range)"],
     ["VIBRATO, SPEED, BLEND", "Continuous: the knob follows the pedal"], ["GLIDE, TONE", "Continuous"],
     ["RANGE", "Continuous, whole semitones ±1 to ±24"], ["PEDAL MODE", "Selector, 3 positions: 0–42 UP, 43–85 DOWN, 86–127 BIPOLAR"],
     ["FOOTSWITCH", "Momentary footswitch: ≥ 64 = pressed, &lt; 64 = released; short press = bypass, long press = HOLD"]],
 pd_h="Pitch pedal direction (screen pill or right-click menu)",
 pd_hdr=["Mode", "Heel", "Toe"],
 pd=[["UP (default)", "your note", "+RANGE"], ["DOWN", "your note", "−RANGE"], ["BIPOLAR", "−RANGE (centre = your note)", "+RANGE"]],
 pd_more=["<b>Invert MIDI pedal direction (heel / toe)</b> (right-click menu, also in Expression pedals (MIDI)) is ticked by default and reverses the PITCH and OCTAVE pedals only; untick it if heel and toe are swapped with your pedal.",
          "The first 4 % of travel at the heel (and 4 % around the centre in BIPOLAR) is a dead zone and full travel is reached just before the toe stop: pedals that never send exactly 0 keep the voice in tune.",
          "Even with a standard 7-bit pedal, pitch and whammy are smoothed: no steps. Fantomine does not use Program Change.",
          "Everything is also an automatable DAW parameter: Glide, Range, Tone, Vibrato, Speed, Blend, Octave, Octave Whammy, Whammy Range, Pedal Mode, Expression, MIDI Pedal Invert, Bypass, Hold (Reaper: Param &gt; Learn in the FX window)."],
 win_t="7. Window",
 win=["Fantomine opens at <b>60 %</b>, the same default size as Ring Think and the other Studio Wiga pedals, and the window can never be made smaller than 60 %. Right-click &gt; <b>Plugin size</b>: <b>60 %</b>, <b>75 %</b> or <b>100 %</b> resizes this window, with <b>(default)</b> shown next to the default size you chose.",
      "At the bottom of the same menu, <b>Default size (new windows)</b> chooses the size at which every new Fantomine window opens (a setting shared by all instances and saved on the computer, in Studio Wiga/Fantomine/settings.xml of your user data folder); the open window takes that size at once.",
      "A size chosen in Plugin size for one instance is saved with the project and stays the priority for that instance: it reopens at that size whatever the default. An instance whose size was never chosen (or that you just set with Default size) opens at the default size. You can also drag the bottom-right corner to enlarge the window up to about 150 %; the proportions stay locked, and the next time it opens the window takes back the size chosen in the menu."],
 pre_t="8. Presets",
 pre="12 factory presets and 9 user slots. Click the preset name to open the menu, or use the ◀ ▶ arrows to step through the factory presets; they also appear in the DAW's program list. A preset stores the six knobs, the octave and the pedal mode (MIDI assignments stay with the project).",
 pre_hdr=["#", "Preset", "Glide", "Range", "Tone", "Vib.", "Speed", "Blend", "Oct.", "Pedal"],
 pre_note="Values in % except Range (semitones), Octave and Pedal (pitch pedal mode).",
 char_hdr=["#", "Preset", "Character"],
 char=["The reference: soft portamento, singing vibrato.", "Almost pure sine, slow glide: the concert theremin.",
       "Huge glides, ±2 octaves, bipolar pedal: 1950s sci-fi.", "One octave up, vocal tone: a ghostly soprano.",
       "One octave down, pedal dives: deep spectral bass.", "Fast deep vibrato: flying-saucer warble.",
       "Tight tracking, reedy tone: follows fast lines.", "Guitar and voice half-and-half, Ondes Martenot colour.",
       "Very slow glide, voice only: haunted house.", "Instant glide, no vibrato: the most precise tracking.",
       "Full TONE: nasal, oboe-like.", "Built for HOLD: freeze a low note, play it with the pedal."],
 user="<b>User presets</b>: preset menu &gt; <b>Save to slot</b> &gt; 1 to 9 (occupied slots marked “(replace)”); <b>Load user preset</b> (empty slots greyed). Shared by every project, stored in %APPDATA%\\Studio Wiga\\Fantomine\\UserPresets.xml (Windows) or ~/Library/Application Support/Studio Wiga/Fantomine/UserPresets.xml (macOS).",
 tips_t="9. Tips",
 tips=["In Reaper, put Fantomine <b>before your amp simulator</b> (Two Notes Genome or another): the ghost voice goes through the amp and cab like your guitar, warm and vintage. On a clean channel with BLEND on VOICE you get the purest theremin; a long plate reverb or a tape echo after it is the classic sound.",
       "<b>Tracking</b>: neck pickup, tone slightly rolled off, clean input (put drive after it), one note at a time. A new note is taken from a real attack, a nearby bend / slide / hammer-on, or a stable pitch while the string rings loud; hum and dying tails never replace the note you played.",
       "<b>7-string and low tunings</b>: the tracker follows down to about 33 Hz, so a 7-string tuned to G (G1, 49 Hz) is tracked accurately. On the lowest notes the voice takes a little longer to lock: set OCTAVE +1 to sing in the real theremin register, or use a little more GLIDE so the slide hides the detection time.",
       "<b>Pedal melodies</b>: hold a note (or HOLD), RANGE ±12 in BIPOLAR, play the melody with your foot while watching the note on the screen. BLEND on a pedal = volume pedal for the ghost.",
       "With ARC before it notes ring forever; with Freeze Shimmer after it the frozen voice becomes a pad; with Echoflex, a 1950s B-movie tape echo."],
 ts_h="Troubleshooting",
 ts_hdr=["Problem", "Solution"],
 ts=[["No voice", "Title lit (not bypassed)? BLEND not fully DRY? Enough input level? Play a single clear note."],
     ["The voice jumps an octave", "Weak fundamental: neck pickup, roll off the tone, no drive before Fantomine."],
     ["The pedal does nothing", "Watch the MIDI dot: no blink = MIDI does not reach the plugin (check routing); blink = the pedal is not assigned yet (no CC by default): do the MIDI Learn."],
     ["The pedal moves the wrong way", "PITCH: change the pedal mode. OCTAVE: change the whammy range. Heel and toe swapped: untick Invert MIDI pedal direction."],
     ["The lever no longer follows the pedal", "You touched it or loaded a preset: move the pedal again."],
     ["A preset name ends with *", "A knob moved since loading: save to a user slot to keep it."],
     ["macOS will not load it", "Remove the quarantine flag (section 2), then rescan."]],
 tech_t="10. Technical specifications",
 tech=[["Format", "VST3, Fx / Pitch Shift, MIDI input; Windows 10/11 x64, macOS 10.13+ universal; listed as “Fantomine” by “Studio Wiga”"],
       ["Channels", "Mono or stereo in (summed), mono or stereo out"],
       ["Latency", "None on the dry guitar; the voice reacts within a few tens of milliseconds"],
       ["Tracking", "Monophonic, about 33 Hz (C1) to 1.4 kHz, analysis every 5 ms"],
       ["Voice", "Alias-free additive oscillator, 12 harmonics, vocal formant, humanised vibrato, slow heterodyne drift"],
       ["Pitch pedal", "±1 to ±24 semitones, UP / DOWN / BIPOLAR, 7- or 14-bit CC"], ["Octave", "−1 / 0 / +1, or continuous whammy (3 ranges)"],
       ["MIDI", "MIDI Learn on 9 targets + footswitch, no CC assigned by default; assignments saved with the project"],
       ["Presets", "12 factory, 9 user slots"], ["Bypass", "12 ms crossfade, lights off"],
       ["Window", "60 % / 75 % / 100 % (Plugin size), default size of new windows to choose, enlargeable by the corner up to about 150 %, never smaller than 60 %; proportions locked"],
       ["Stability", "Windows anti-freeze v2: software renderer, caches rebuilt by the timer, redraw watchdog, no host call from the audio thread"],
       ["Version", VERSION]]),
"fr": dict(
 lang="FRANÇAIS", sub=["Voix de thérémine", "VST3 pour Windows et macOS"], ver="Notice d'utilisation &nbsp;·&nbsp; version " + VERSION,
 intro_t="1. Présentation",
 intro=["<b>Fantomine</b> transforme votre guitare en <b>thérémine</b>. Elle écoute la note jouée et la rechante avec une voix spectrale qui glisse d'une note à l'autre : le glissando reconnaissable entre mille des films de science-fiction des années 1950, des musiques de Hitchcock et de Good Vibrations.",
        "Un vrai thérémine a deux antennes, l'une pour la hauteur, l'autre pour le volume. Fantomine les transpose dans le monde du guitariste : la <b>hauteur</b> vient de la main gauche et une pédale d'expression MIDI la courbe en continu, comme une main qui s'approche de l'antenne ; le <b>volume</b> suit la dynamique de la main droite : jouez doucement et le fantôme murmure, attaquez fort et il chante.",
        "Six potards règlent la façon dont la voix bouge (GLIDE, VIBRATO, SPEED), jusqu'où la pédale la courbe (RANGE), son timbre (TONE) et sa place à côté de la guitare (BLEND). Le levier OCTAVE monte ou descend la voix d'une octave, ou balaie entre les octaves comme une Whammy quand une pédale le pilote.",
        "<b>Trajet du signal.</b> Guitare (stéréo sommée en mono) &gt; suivi de note &gt; voix (glide, vibrato, tone) &gt; niveau qui suit votre jeu &gt; BLEND avec la guitare directe, qui passe toujours en parallèle sans aucun retard. Les pédales d'expression MIDI agissent sur la hauteur, l'octave et les potards.",
        "<b>Caractère.</b> Jamais en escalier : hauteur et octave sont lissées, même une pédale 7 bits glisse en continu (pédales 14 bits acceptées). Vibrato humain qui s'installe sur chaque note et respire légèrement. Monophonique comme le vrai instrument : sur un accord, elle suit la note la plus forte, en général la plus grave."],
 inst_t="2. Installation",
 inst=[("Windows", "Décompressez l'artefact <b>Fantomine-VST3-Windows</b> et copiez tout le dossier <b>Fantomine.vst3</b> dans <b>C:\\Program Files\\Common Files\\VST3\\</b>. Aucun redistribuable Visual C++ n'est nécessaire."),
       ("macOS", "Décompressez <b>Fantomine-VST3-macOS</b> (universel : Apple Silicon et Intel) et copiez <b>Fantomine.vst3</b> dans <b>~/Library/Audio/Plug-Ins/VST3/</b>. Le plugin est signé « ad hoc » ; si macOS refuse de le charger, tapez dans le Terminal : <b>xattr -dr com.apple.quarantine ~/Library/Audio/Plug-Ins/VST3/Fantomine.vst3</b>"),
       ("Reaper", "Options &gt; Preferences &gt; Plug-ins &gt; VST &gt; <b>Re-scan</b>. Fantomine apparaît sous le nom <b>Fantomine</b>, fabricant <b>Studio Wiga</b> (Fx / Pitch Shift).")],
 reaper_h="Faire entrer la pédale d'expression dans Reaper",
 reaper=["Insérez Fantomine sur la piste guitare, avant le simulateur d'ampli (Two Notes Genome, par exemple).",
         "Créez une piste <b>Pédales</b> : entrée <b>MIDI &gt; votre contrôleur &gt; All channels</b>, armée, monitoring activé.",
         "Dans le routage de la piste Pédales, ajoutez un envoi vers la piste guitare avec <b>Audio : None</b> et <b>MIDI : All</b>.",
         "Bougez la pédale : le petit point MIDI de l'écran clignote. Aucune commande n'est assignée par défaut : confiez la pédale à PITCH (ou à n'importe quelle autre commande) par MIDI Learn (section 6)."],
 ov_t="3. Vue d'ensemble de l'interface",
 ov_hdr=["#", "Commande", "Rôle", "#", "Commande", "Rôle"],
 ov=[("1", "Titre néon", "Allumé quand actif, éteint en bypass"), ("2", "Écran", "Preset, mode de pédale, voix en direct, note, barre EXP"),
     ("3", "GLIDE", "Temps de glissement vers chaque note"), ("4", "RANGE", "Amplitude de la pédale, ±1 à ±24 dt"),
     ("5", "TONE", "De la sinusoïde pure au timbre d'anche"), ("6", "VIBRATO", "Profondeur du vibrato"), ("7", "SPEED", "Vitesse du vibrato, 3 à 9 Hz"),
     ("8", "BLEND", "Mélange guitare / voix"), ("9", "Levier OCTAVE", "−1, 0, +1 octave ; whammy avec une pédale"),
     ("10", "LED", "Suit la voix ; pulse en HOLD"), ("11", "Ligne d'état", "Preset, valeurs, BYPASS, HOLD, MIDI Learn"),
     ("12", "Footswitch", "Clic : bypass · appui 0,6 s : HOLD"), ("13", "INPUT", "Décoratif (l'audio vient de la piste)"),
     ("14", "EXP", "Décoratif (les pédales arrivent en MIDI)"), ("15", "OUTPUT", "Décoratif")],
 ov_note="Tirez un potard vers le haut ou le bas (ou molette) ; la ligne d'état affiche sa valeur exacte. Le double-clic ne remet rien à zéro, volontairement. <b>Clic droit sur une commande</b> : son MIDI Learn (section 6) ; clic droit ailleurs : le menu complet.",
 ctl_t="4. Les commandes une par une",
 ctl=[("GLIDE (FAST &gt; SLOW)", "Temps que met la voix pour atteindre une nouvelle note, de 2 ms (collée à votre jeu) à environ 0,7 s (un fantôme paresseux qui glisse). Courbe exponentielle : la première moitié couvre la zone jouable (2 à environ 40 ms), la seconde les grands glissandos. Seuls les changements de note glissent ; la pédale de hauteur et la whammy ont leur propre lissage très court. Vers 11 h : le portamento classique du thérémine. Défaut 35 %."),
      ("RANGE (±1 &gt; ±24)", "Nombre de demi-tons dont la pédale de hauteur courbe la voix en fin de course, par pas entiers de 1 à 24. RANGE ±12 avec la pédale en mode UP : pointe enfoncée = une octave au-dessus de la note jouée. Sans effet sur le levier OCTAVE. Défaut ±12."),
      ("TONE (PURE &gt; REED)", "Tout à gauche : une sinusoïde presque pure, comme le thérémine RCA de Clara Rockmore. En tournant, des harmoniques s'ajoutent avec un léger déséquilibre pair / impair (la couleur hétérodyne des vrais thérémines) et un formant vocal monte vers 1,1 kHz, jusqu'à un son d'anche proche du hautbois ou des Ondes Martenot. Défaut 35 %."),
      ("VIBRATO (0 &gt; WIDE)", "Profondeur du vibrato, jusqu'à environ ±0,65 demi-ton. Humanisé : sur chaque nouvelle note il part de zéro et s'épanouit en un tiers de seconde, sa vitesse et sa profondeur dérivent très légèrement. Défaut 30 %."),
      ("SPEED (SLOW &gt; FAST)", "Vitesse du vibrato, 3 à 9 Hz (affichée en Hz). Les thérémistes classiques restent vers 5–6 Hz (midi). Défaut 45 % (environ 4,9 Hz)."),
      ("BLEND (DRY &gt; VOICE)", "Équilibre guitare / voix à puissance constante : le volume perçu reste égal sur toute la course. Entre les deux, la guitare donne l'attaque et la voix le sustain. Défaut 75 %.")],
 oct_h="Levier OCTAVE et whammy",
 oct=["Cliquez à gauche ou à droite de la poignée, ou faites-la glisser : trois positions, −1, 0 et +1 octave. La ligne d'état confirme le changement.",
      "<b>Whammy</b> : affectez une pédale d'expression MIDI à OCTAVE (clic droit sur le levier &gt; MIDI Learn) et le levier glisse en continu avec le pied, la voix suivant entre les octaves sans paliers. La ligne d'état affiche la transposition exacte (par exemple <b>OCTAVE +7.0 st</b>). La whammy a son propre lissage rapide (15 ms), indépendant de GLIDE.",
      "Toucher le levier à la souris (ou charger un preset) rend la main aux trois positions fixes ; le mouvement suivant de la pédale reprend le contrôle. La whammy et la pédale de hauteur s'additionnent."],
 wr_hdr=["Plage de la whammy (menu clic droit)", "Talon", "Centre", "Pointe"],
 wr=[["Heel -1 oct &gt; centre 0 &gt; toe +1 oct (défaut)", "−1", "0", "+1"], ["Heel 0 &gt; toe +1 oct", "0", "+0,5", "+1"], ["Heel 0 &gt; toe -1 oct", "0", "−0,5", "−1"]],
 scr_h="L'écran",
 scr_hdr=["", "Élément", "Rôle"],
 scr=[["a", "Flèche ◀", "Preset usine précédent"], ["b", "Nom du preset", "Clic : menu des presets. Un astérisque * signale un potard bougé depuis le chargement"],
      ["c", "Flèche ▶", "Preset usine suivant"], ["d", "Mode de pédale", "UP / DOWN / BIPOLAR, un clic pour changer (apprenable en MIDI : clic droit dessus)"],
      ["e", "Point MIDI", "Clignote à chaque message de contrôleur MIDI"], ["f", "Barre EXP", "Position de la pédale de hauteur ; à tirer à la souris pour tester sans pédale (clic droit : MIDI Learn de PITCH)"],
      ["g", "Voix fantôme", "La vraie forme d'onde, dessinée en direct"], ["h", "Note", "Note chantée par la voix (après pédale, octave et glide), avec les cents"],
      ["i", "Étiquettes", "HOLD (violet) quand la note est figée, LEARN pendant l'attente d'un MIDI Learn"]],
 fs_t="5. Footswitch, LED, bypass et HOLD",
 fs_hdr=["Action", "Résultat"],
 fs=[["Appui court", "Bypass on / off. Si HOLD est actif, un appui court relâche HOLD."],
     ["Appui long (0,6 s)", "HOLD on / off ; HOLD réactive aussi la pédale si elle était en bypass."]],
 hold="<b>HOLD</b> fige la note en cours et son niveau : le fantôme continue de chanter pendant que vous arrêtez de jouer ou jouez autre chose par-dessus. La pédale de hauteur, la whammy et le vibrato agissent toujours sur la note figée. La LED pulse, l'écran affiche une étiquette HOLD violette et la ligne d'état indique <b>HOLD - tap to release</b>.",
 led="<b>LED et ligne d'état.</b> Pédale active, la LED brille avec la voix ; en HOLD elle pulse ; en bypass elle est éteinte. La ligne d'état affiche le nom du preset, la valeur d'une commande pendant qu'on la bouge (GLIDE 35 %, SPEED 5.2 Hz, RANGE ±12 st…), BYPASS, HOLD et les messages du MIDI Learn.",
 byp="<b>Bypass : tout s'éteint.</b> Le titre néon, les traits des potards, l'écran et la LED s'éteignent ensemble ; la ligne d'état affiche BYPASS. L'audio passe par un fondu de 12 ms, sans clic. Au rallumage, le néon scintille brièvement avant de se stabiliser.",
 act="Active", bp="Bypass",
 midi_t="6. MIDI",
 midi_intro="Fantomine lit les messages MIDI Control Change sur tous les canaux. <b>Aucun CC n'est assigné par défaut</b> : toutes les commandes, PITCH compris, s'affectent par <b>MIDI Learn</b>. Un CC = une fonction : apprendre un CC pour une commande le retire des autres (une pédale apprise pour la whammy ne peut plus courber la hauteur par accident). Les assignations sont <b>sauvegardées avec le projet</b>, pas avec les presets.",
 learn_h="MIDI Learn",
 learn=["<b>Clic droit sur une commande</b> : un potard (GLIDE, RANGE, TONE, VIBRATO, SPEED, BLEND), le levier OCTAVE, le footswitch, la barre EXP de l'écran (PITCH) ou la pastille UP / DOWN / BIPOLAR (PEDAL MODE). Le menu commence par <b>MIDI Learn: &lt;NOM&gt; (none)</b> (ou le CC appris, par ex. <b>(CC 12)</b>), <b>Clear MIDI: &lt;NOM&gt;</b> et, pendant l'attente, <b>Cancel MIDI learn</b> ; choisir de nouveau le même Learn annule aussi.",
        "Bougez la pédale ou appuyez sur le footswitch : la ligne d'état affiche <b>MIDI LEARN: move a control for &lt;NOM&gt;</b> (l'écran affiche une étiquette LEARN), puis <b>&lt;NOM&gt; = CC n</b> pendant deux secondes.",
        "Clic droit sur une zone vide &gt; <b>Expression pedals (MIDI)</b> : une entrée par commande (<b>Learn: PITCH (bend)</b>, <b>OCTAVE (whammy)</b>, VIBRATO, SPEED, BLEND, GLIDE, RANGE, TONE, PEDAL MODE) avec son CC actuel (<i>not assigned</i> tant qu'aucun n'est appris), chacune avec <b>MIDI Learn</b> et <b>Clear</b> ; pour PITCH, des choix rapides CC 11 Expression, CC 4 Foot Controller, CC 7 Volume, CC 1 Modulation et CC 2 Breath. Puis <b>Cancel MIDI learn</b> (pendant l'attente), <b>Clear all MIDI assignments</b> (efface toutes les assignations, footswitch compris) et <b>Invert pedal direction</b>.",
        "Sous-menu <b>Footswitch (MIDI)</b> : <b>MIDI Learn (press the footswitch)</b>, <b>None (use the DAW's MIDI learn)</b> (par défaut), ou CC 64 / CC 80 en un clic.",
        "Un projet enregistré avec une version précédente qui avait encore l'ancienne assignation d'usine (PITCH sur le CC 11, rien d'autre) s'ouvre sans aucune assignation : réapprenez votre pédale. Un projet où vous aviez changé ou ajouté une assignation garde toutes ses assignations telles qu'enregistrées."],
 st_caps=["MIDI Learn en attente d'une commande", "Assignation confirmée (2 s)", "Valeur pendant qu'un potard bouge"],
 lc_h="Commandes apprenables",
 lc_hdr=["Commande", "Type"],
 lc=[["PITCH (pédale de hauteur)", "Continu, ±RANGE ; 14 bits accepté (CC 0–31 + LSB sur le CC n+32)"],
     ["OCTAVE (whammy)", "Continu : le levier glisse entre les octaves (plage de la whammy)"],
     ["VIBRATO, SPEED, BLEND", "Continu : le potard suit la pédale"], ["GLIDE, TONE", "Continu"],
     ["RANGE", "Continu, demi-tons entiers ±1 à ±24"], ["PEDAL MODE", "Sélecteur 3 positions : 0–42 UP, 43–85 DOWN, 86–127 BIPOLAR"],
     ["FOOTSWITCH", "Footswitch momentané : ≥ 64 = appuyé, &lt; 64 = relâché ; appui court = bypass, appui long = HOLD"]],
 pd_h="Sens de la pédale de hauteur (pastille de l'écran ou menu clic droit)",
 pd_hdr=["Mode", "Talon", "Pointe"],
 pd=[["UP (défaut)", "votre note", "+RANGE"], ["DOWN", "votre note", "−RANGE"], ["BIPOLAR", "−RANGE (centre = votre note)", "+RANGE"]],
 pd_more=["<b>Invert MIDI pedal direction (heel / toe)</b> (menu clic droit, aussi dans Expression pedals (MIDI)) est coché par défaut et inverse seulement les pédales PITCH et OCTAVE ; décochez-le si talon et pointe sont inversés avec votre pédale.",
          "Les premiers 4 % de course au talon (et 4 % autour du centre en BIPOLAR) sont une zone morte, et la pleine course est atteinte juste avant la butée : une pédale qui n'envoie jamais 0 pile garde la voix juste.",
          "Même avec une pédale 7 bits standard, hauteur et whammy sont lissées : aucun palier. Fantomine n'utilise pas le Program Change.",
          "Tout est aussi un paramètre automatisable du DAW : Glide, Range, Tone, Vibrato, Speed, Blend, Octave, Octave Whammy, Whammy Range, Pedal Mode, Expression, MIDI Pedal Invert, Bypass, Hold (Reaper : Param &gt; Learn dans la fenêtre FX)."],
 win_t="7. Fenêtre",
 win=["Fantomine s'ouvre à <b>60 %</b>, la même taille par défaut que Ring Think et les autres pédales Studio Wiga, et la fenêtre ne peut jamais être plus petite que 60 %. Clic droit &gt; <b>Plugin size</b> : <b>60 %</b>, <b>75 %</b> ou <b>100 %</b> redimensionne cette fenêtre, et <b>(default)</b> est indiqué à côté de la taille par défaut choisie.",
      "En bas du même menu, <b>Default size (new windows)</b> choisit la taille d'ouverture de toutes les nouvelles fenêtres de Fantomine (réglage commun à toutes les instances, enregistré sur l'ordinateur, dans Studio Wiga/Fantomine/settings.xml du dossier de données de l'utilisateur) ; la fenêtre ouverte prend aussitôt cette taille.",
      "Une taille choisie dans Plugin size pour une instance est sauvegardée avec le projet et reste prioritaire pour cette instance : elle se rouvre à cette taille, quelle que soit la taille par défaut. Une instance dont la taille n'a jamais été choisie (ou que vous venez de régler par Default size) s'ouvre à la taille par défaut. Vous pouvez aussi tirer le coin inférieur droit pour agrandir la fenêtre jusqu'à environ 150 % ; les proportions restent verrouillées, et à l'ouverture suivante la fenêtre reprend la taille choisie dans le menu."],
 pre_t="8. Presets",
 pre="12 presets usine et 9 emplacements utilisateur. Cliquez sur le nom du preset pour ouvrir le menu, ou utilisez les flèches ◀ ▶ pour parcourir les presets usine ; ils apparaissent aussi dans la liste de programmes du DAW. Un preset mémorise les six potards, l'octave et le mode de pédale (les assignations MIDI restent dans le projet).",
 pre_hdr=["N°", "Preset", "Glide", "Range", "Tone", "Vib.", "Speed", "Blend", "Oct.", "Pédale"],
 pre_note="Valeurs en % sauf Range (demi-tons), Octave et Pédale (mode de la pédale de hauteur).",
 char_hdr=["N°", "Preset", "Caractère"],
 char=["La référence : portamento doux, vibrato chantant.", "Sinusoïde presque pure, glide lent : le thérémine de concert.",
       "Glissandos énormes, ±2 octaves, pédale bipolaire : SF des années 50.", "Une octave au-dessus, timbre vocal : une soprano fantôme.",
       "Une octave en dessous, plongées à la pédale : basse spectrale.", "Vibrato rapide et profond : soucoupe volante.",
       "Suivi serré, timbre d'anche : suit les traits rapides.", "Guitare et voix à parts égales, couleur Ondes Martenot.",
       "Glide très lent, voix seule : maison hantée.", "Glide instantané, sans vibrato : le suivi le plus précis.",
       "TONE à fond : nasal, façon hautbois.", "Pensé pour HOLD : figer une note grave et la jouer à la pédale."],
 user="<b>Presets utilisateur</b> : menu des presets &gt; <b>Save to slot</b> &gt; 1 à 9 (emplacements occupés marqués « (replace) ») ; <b>Load user preset</b> (emplacements vides grisés). Partagés par tous les projets, stockés dans %APPDATA%\\Studio Wiga\\Fantomine\\UserPresets.xml (Windows) ou ~/Library/Application Support/Studio Wiga/Fantomine/UserPresets.xml (macOS).",
 tips_t="9. Conseils d'utilisation",
 tips=["Dans Reaper, placez Fantomine <b>avant le simulateur d'ampli</b> (Two Notes Genome ou autre) : la voix fantôme passe par l'ampli et le baffle comme la guitare, chaude et vintage. Sur un canal clair avec BLEND sur VOICE, vous obtenez le thérémine le plus pur ; une longue réverbe à plaque ou un écho à bande après, c'est le son classique.",
       "<b>Suivi de note</b> : micro manche, tonalité un peu fermée, entrée propre (drive après), une note à la fois. Une nouvelle note est prise sur une vraie attaque, un bend / slide / hammer-on proche, ou une hauteur stable tant que la corde sonne fort ; ronflement et fin de note ne remplacent jamais la note jouée.",
       "<b>7 cordes et accordages graves</b> : le suivi descend jusqu'à environ 33 Hz, une 7 cordes accordée en G (Sol1, 49 Hz) est suivie avec précision. Sur les notes les plus graves la voix met un peu plus de temps à accrocher : mettez OCTAVE sur +1 pour chanter dans le vrai registre du thérémine, ou un peu plus de GLIDE pour masquer le temps de détection.",
       "<b>Mélodies à la pédale</b> : tenez une note (ou HOLD), RANGE ±12 en BIPOLAR, jouez la mélodie au pied en regardant la note à l'écran. BLEND sur une pédale = pédale de volume du fantôme.",
       "Avec ARC avant, les notes tiennent indéfiniment ; avec Freeze Shimmer après, la voix figée devient une nappe ; avec Echoflex, l'écho à bande d'un film de série B."],
 ts_h="Dépannage",
 ts_hdr=["Problème", "Solution"],
 ts=[["Pas de voix", "Titre allumé (pas de bypass) ? BLEND pas tout à fait sur DRY ? Niveau d'entrée suffisant ? Jouez une note seule et nette."],
     ["La voix saute d'une octave", "Fondamentale faible : micro manche, tonalité fermée, pas de drive avant Fantomine."],
     ["La pédale ne fait rien", "Regardez le point MIDI : pas de clignotement = le MIDI n'arrive pas (vérifiez le routage) ; clignotement = la pédale n'est pas encore assignée (aucun CC par défaut) : faites le MIDI Learn."],
     ["La pédale agit à l'envers", "PITCH : changez le mode de pédale. OCTAVE : changez la plage de la whammy. Talon et pointe inversés : décochez Invert MIDI pedal direction."],
     ["Le levier ne suit plus la pédale", "Vous l'avez touché ou avez chargé un preset : bougez de nouveau la pédale."],
     ["Le nom du preset finit par *", "Un potard a bougé depuis le chargement : enregistrez dans un emplacement utilisateur."],
     ["macOS ne charge pas le plugin", "Retirez l'attribut de quarantaine (section 2), puis rescannez."]],
 tech_t="10. Caractéristiques techniques",
 tech=[["Format", "VST3, Fx / Pitch Shift, entrée MIDI ; Windows 10/11 x64, macOS 10.13+ universel ; listé « Fantomine », fabricant « Studio Wiga »"],
       ["Canaux", "Entrée mono ou stéréo (sommée), sortie mono ou stéréo"],
       ["Latence", "Aucune sur la guitare directe ; la voix réagit en quelques dizaines de millisecondes"],
       ["Suivi de note", "Monophonique, d'environ 33 Hz (Do1) à 1,4 kHz, analyse toutes les 5 ms"],
       ["Voix", "Oscillateur additif sans repliement, 12 harmoniques, formant vocal, vibrato humanisé, lente dérive hétérodyne"],
       ["Pédale de hauteur", "±1 à ±24 demi-tons, UP / DOWN / BIPOLAR, CC 7 ou 14 bits"], ["Octave", "−1 / 0 / +1, ou whammy continue (3 plages)"],
       ["MIDI", "MIDI Learn sur 9 cibles + footswitch, aucun CC assigné par défaut ; assignations sauvegardées avec le projet"],
       ["Presets", "12 usine, 9 emplacements utilisateur"], ["Bypass", "Fondu de 12 ms, lumières éteintes"],
       ["Fenêtre", "60 % / 75 % / 100 % (Plugin size), taille par défaut des nouvelles fenêtres au choix, agrandissable par le coin jusqu'à environ 150 %, jamais sous 60 % ; proportions verrouillées"],
       ["Stabilité", "Anti-gel v2 sous Windows : rendu logiciel, caches refaits par le timer, chien de garde du redessin, aucun appel à l'hôte depuis le thread audio"],
       ["Version", VERSION]]),
}

def section(lang):
    t = T[lang]; f = []
    def bl(items): return [P("&bull;&nbsp;&nbsp;" + i) for i in items]
    # couverture
    f.append(NextPageTemplate("p"))
    f.append(Spacer(1, 2 * mm)); f.append(P(t["lang"], "coverlang")); f.append(Spacer(1, 4 * mm))
    f.append(img("cover_cutout.png", W * 0.80)); f.append(Spacer(1, 6 * mm))
    f.append(P("F A N T O M I N E", "cover")); f.append(Spacer(1, 2 * mm))
    for s in t["sub"]: f.append(P(s, "coversub"))
    f.append(P(t["ver"], "coversub")); f.append(Spacer(1, 9 * mm))
    f.append(img("logo_studio_wiga_blanc.png", 52 * mm)); f.append(PageBreak())
    # 1-2
    f.append(P(t["intro_t"], "h1")); f += [P(x) for x in t["intro"]]
    f.append(P(t["inst_t"], "h1"))
    for h, x in t["inst"]: f.append(P(h, "h3")); f.append(P(x))
    f.append(P(t["reaper_h"], "h2")); f += bl(t["reaper"])
    f.append(PageBreak())
    # 3
    f.append(P(t["ov_t"], "h1")); f.append(img("overview_annotated.png", W * 0.86)); f.append(Spacer(1, 4 * mm))
    half = (len(t["ov"]) + 1) // 2
    rows = [t["ov_hdr"]]
    for i in range(half):
        a = list(t["ov"][i]); b = list(t["ov"][i + half]) if i + half < len(t["ov"]) else ["", "", ""]
        rows.append(a + b)
    cw = [8 * mm, 25 * mm, (W - 66 * mm) / 2] * 2
    f.append(table(rows, cw)); f.append(Spacer(1, 3 * mm)); f.append(P(t["ov_note"]))
    f.append(PageBreak())
    # 4
    f.append(P(t["ctl_t"], "h1")); f.append(img("knobs.png", W)); f.append(Spacer(1, 2 * mm))
    for h, x in t["ctl"]: f.append(P(h, "h3")); f.append(P(x))
    f.append(CondPageBreak(90 * mm))
    f.append(P(t["oct_h"], "h2"))
    f.append(row_of([("octave_m1.png", ""), ("octave_0.png", ""), ("octave_p1.png", "")], W))
    f += [P(x) for x in t["oct"]]
    f.append(KeepTogether([table([t["wr_hdr"]] + t["wr"], [W - 66 * mm, 22 * mm, 22 * mm, 22 * mm])]))
    f.append(CondPageBreak(110 * mm))
    f.append(P(t["scr_h"], "h2")); f.append(img("screen_annotated.png", W * 0.62)); f.append(Spacer(1, 2 * mm))
    f.append(table([t["scr_hdr"]] + t["scr"], [8 * mm, 32 * mm, W - 40 * mm]))
    f.append(PageBreak())
    # 5
    f.append(P(t["fs_t"], "h1")); f.append(table([t["fs_hdr"]] + t["fs"], [40 * mm, W - 40 * mm])); f.append(Spacer(1, 3 * mm))
    f.append(P(t["hold"])); f.append(row_of([("screen_hold.png", ""), ("status_hold.png", "")], W))
    f.append(P(t["led"])); f.append(P(t["byp"]))
    f.append(row_of([("title_active.png", t["act"]), ("title_bypass.png", t["bp"])], W * 0.86))
    f.append(row_of([("foot_active.png", t["act"]), ("foot_bypass.png", t["bp"])], W * 0.62))
    f.append(PageBreak())
    # 6
    f.append(P(t["midi_t"], "h1")); f.append(P(t["midi_intro"]))
    f.append(P(t["learn_h"], "h2")); f += bl(t["learn"])
    f.append(row_of([("status_learn.png", t["st_caps"][0]), ("status_assigned.png", t["st_caps"][1]), ("status_value.png", t["st_caps"][2])], W))
    f.append(P(t["lc_h"], "h2")); f.append(table([t["lc_hdr"]] + t["lc"], [48 * mm, W - 48 * mm]))
    f.append(KeepTogether([P(t["pd_h"], "h2"), table([t["pd_hdr"]] + t["pd"], [40 * mm, (W - 40 * mm) * 0.6, (W - 40 * mm) * 0.4])]))
    f.append(Spacer(1, 2 * mm)); f += bl(t["pd_more"])
    # 7
    f.append(CondPageBreak(60 * mm))
    f.append(P(t["win_t"], "h1")); f += [P(x) for x in t["win"]]
    f.append(PageBreak())
    # 8
    f.append(P(t["pre_t"], "h1")); f.append(P(t["pre"]))
    rows = [t["pre_hdr"]]
    for i, (n, g, r, to, v, s, b, o, pd) in enumerate(PRESETS):
        rows.append([f"{i + 1:02d}", n, str(g), f"±{r}", str(to), str(v), str(s), str(b), o, pd])
    cw = [10 * mm, 38 * mm] + [(W - 48 * mm - 16 * mm) / 7] * 7 + [16 * mm]
    f.append(table(rows, cw)); f.append(P(t["pre_note"], "small")); f.append(Spacer(1, 3 * mm))
    f.append(table([t["char_hdr"]] + [[f"{i + 1:02d}", PRESETS[i][0], c] for i, c in enumerate(t["char"])], [10 * mm, 38 * mm, W - 48 * mm]))
    f.append(Spacer(1, 3 * mm)); f.append(P(t["user"]))
    f.append(PageBreak())
    # 9-10
    f.append(P(t["tips_t"], "h1")); f += bl(t["tips"])
    f.append(KeepTogether([P(t["ts_h"], "h2"), table([t["ts_hdr"]] + t["ts"], [48 * mm, W - 48 * mm])]))
    f.append(CondPageBreak(95 * mm))
    f.append(KeepTogether([P(t["tech_t"], "h1"), table(t["tech"], [32 * mm, W - 32 * mm], header=False)]))
    # pas d'historique des versions dans la notice (demande de l'utilisateur)
    f.append(PageBreak())
    return f

def deco(c, doc):
    c.saveState()
    c.setFillColor(ACC); c.rect(0, A4[1] - 4.5 * mm, A4[0], 4.5 * mm, stroke=0, fill=1)
    c.setFont("Pop", 7.5); c.setFillColor(GREY)
    c.drawString(18 * mm, 10 * mm, NAME + " (Studio Wiga) · v" + VERSION)
    c.drawRightString(A4[0] - 18 * mm, 10 * mm, str(doc.page))
    c.restoreState()

def cover_bg(c, doc):
    c.saveState(); c.setFillColor(colors.black); c.rect(0, 0, A4[0], A4[1], stroke=0, fill=1)
    c.setFillColor(ACC); c.rect(0, A4[1] - 3 * mm, A4[0], 3 * mm, stroke=0, fill=1); c.restoreState()

doc = BaseDocTemplate(OUT, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=18 * mm,
                      title="Fantomine - User manual / Notice v" + VERSION, author="Studio Wiga")
doc.addPageTemplates([PageTemplate(id="cover", frames=[Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="fc")], onPage=cover_bg),
                      PageTemplate(id="p", frames=[Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")], onPage=deco)])
en = section("en"); fr = section("fr")
en[-1:] = [NextPageTemplate("cover"), PageBreak()]
doc.build(en + fr[:-1])
print(OUT)
