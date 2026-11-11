#include "PluginEditor.h"
#include "BinaryData.h"
#include "WigaWindowSize.h"
#include "NineHandsGlow.h"

using namespace juce;
using P = FantomineAudioProcessor;

namespace
{
    const Colour silk (0xffe0dee8), silk2 (0xffc4c0d2);        // serigraphie claire / grise du design
    const Colour mint (0xff7ef0d6), mintCore (0xffb0f6f2);
    const Colour scrText (0xffe2ecec), scrTeal (0xff78beb4), scrEdge (0xff5a8c88), violet (0xffb48cff);
    const Colour barFill (0xff060609), barRim (0xff0e0c14), barEdge (0xff787488), barInk (0xffe8eaf0);
    const Colour menuAccent (0xff7ef0d6);                      // pastille des en-tetes de menu (menthe de la pedale)
    constexpr float arrowW = 34.0f;
    const char* knobIds[6]   = { "glide", "range", "tone", "vibrato", "speed", "blend" };
    const char* knobNames[6] = { "GLIDE", "RANGE", "TONE", "VIBRATO", "SPEED", "BLEND" };
    const char* knobMin[6]   = { "FAST", "\xc2\xb1" "1", "PURE", "0", "SLOW", "DRY" };
    const char* knobMax[6]   = { "SLOW", "\xc2\xb1" "24", "REED", "WIDE", "FAST", "VOICE" };

    Image png (const void* d, int n) { return ImageCache::getFromMemory (d, n); }
    bool flag (P& p, const char* id) { return p.apvts.getRawParameterValue (id)->load() > 0.5f; }
    int choice (P& p, const char* id) { return roundToInt (p.apvts.getRawParameterValue (id)->load()); }

    String noteName (float midi, int& cents)
    {
        static const char* names[] = { "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B" };
        const int n = roundToInt (midi);
        cents = roundToInt ((midi - (float) n) * 100.0f);
        return String (names[((n % 12) + 12) % 12]) + String (n / 12 - 1);
    }

    // texte vectoriel centre sur (x, y) (milieu entre jambage haut et bas, comme l'apercu), rotation en radians
    Path textPath (const String& s, const Typeface::Ptr& face, float em, Point<float> c, float rot = 0.0f, float track = 0.0f)
    {
        const Font font (FontOptions (face).withPointHeight (em));
        float total = 0.0f;
        for (int i = 0; i < s.length(); ++i)
            total += GlyphArrangement::getStringWidth (font, String::charToString (s[i])) + (i > 0 ? track : 0.0f);
        const float base = (font.getAscent() - font.getDescent()) * 0.5f;
        GlyphArrangement ga;
        float x = -total * 0.5f;
        for (int i = 0; i < s.length(); ++i)
        {
            const String ch = String::charToString (s[i]);
            ga.addLineOfText (font, ch, x, base);
            x += GlyphArrangement::getStringWidth (font, ch) + track;
        }
        Path p; ga.createPath (p);
        p.applyTransform (AffineTransform::rotation (rot).translated (c.x, c.y));
        return p;
    }

    std::unique_ptr<Drawable> svg (const char* data, int size)
    {
        return Drawable::createFromSVGString (String::fromUTF8 (data, size));
    }
}

constexpr int FantomineAudioProcessorEditor::knobTarget[6];

//==============================================================================
FantomineAudioProcessorEditor::FantomineAudioProcessorEditor (FantomineAudioProcessor& p)
    : AudioProcessorEditor (&p), proc (p)
{
    background = png (BinaryData::background_png, BinaryData::background_pngSize);
    glowTitle  = png (BinaryData::glow_title_png, BinaryData::glow_title_pngSize);
    titleOn    = png (BinaryData::title_on_png, BinaryData::title_on_pngSize);
    titleOff   = png (BinaryData::title_off_png, BinaryData::title_off_pngSize);
    glowLed    = png (BinaryData::glow_led_png, BinaryData::glow_led_pngSize);
    ledOn      = png (BinaryData::led_on_png, BinaryData::led_on_pngSize);
    fsRefl     = png (BinaryData::fs_refl_png, BinaryData::fs_refl_pngSize);
    octHandle  = png (BinaryData::oct_handle_png, BinaryData::oct_handle_pngSize);
    mediumFace  = Typeface::createSystemTypefaceFor (BinaryData::PoppinsMedium_ttf, BinaryData::PoppinsMedium_ttfSize);
    boldFace    = Typeface::createSystemTypefaceFor (BinaryData::PoppinsBold_ttf, BinaryData::PoppinsBold_ttfSize);
    regularFace = Typeface::createSystemTypefaceFor (BinaryData::PoppinsRegular_ttf, BinaryData::PoppinsRegular_ttfSize);
    menuLnf.f = { regularFace, mediumFace, boldFace };
    logo     = svg (BinaryData::NineHandsLogoWhite_svg, BinaryData::NineHandsLogoWhite_svgSize);
    subtitle = svg (BinaryData::FantomineSubtitle_svg, BinaryData::FantomineSubtitle_svgSize);
    if (subtitle != nullptr) subtitle->replaceColour (Colours::white, silk2);
    buildPrint();
    glow = (float) NineHandsGlow::percent (JucePlugin_Name) / 100.0f;

    // potards nh::Knob (skill potards-nine-hands-dsp) : calques 512 px, repere au-dessus des reflets fixes
    nh::Knob::Layers L;
    L.shadow     = png (BinaryData::knob_shadow_png, BinaryData::knob_shadow_pngSize);
    L.crown      = png (BinaryData::knob_crown_png, BinaryData::knob_crown_pngSize);
    L.cap        = png (BinaryData::knob_cap_png, BinaryData::knob_cap_pngSize);
    L.highlight  = png (BinaryData::knob_highlight_png, BinaryData::knob_highlight_pngSize);
    L.markerOff  = png (BinaryData::knob_marker_off_png, BinaryData::knob_marker_off_pngSize);
    L.markerOn   = png (BinaryData::knob_marker_on_png, BinaryData::knob_marker_on_pngSize);
    L.markerGlow = png (BinaryData::knob_marker_glow_png, BinaryData::knob_marker_glow_pngSize);
    nh::Knob::Style st;
    st.hitRadius = layout::knobR * 1.05f / layout::knobLayer;
    for (int i = 0; i < 6; ++i)
    {
        knobs[(size_t) i] = std::make_unique<nh::Knob> (*proc.apvts.getParameter (knobIds[i]), L, st);
        auto* kn = knobs[(size_t) i].get();
        kn->onRightClick = [this, i] (const MouseEvent&) { showContextMenu (knobTarget[i]); };
        kn->onGestureStart = [this, i]
        {
            if (auto* prm = proc.apvts.getParameter (knobIds[i])) flash (String (knobNames[i]) + "   " + prm->getCurrentValueAsText());
        };
        addAndMakeVisible (*kn);
        lastKnob[(size_t) i] = proc.apvts.getRawParameterValue (knobIds[i])->load();
    }

    // taille : 495 px de haut par defaut (« 60 % ») = taille minimale, proportions bloquees ;
    // ouverture a la taille enregistree pour cette instance, sinon a la taille par defaut choisie dans le menu
    const double aspect = (double) baseW / (double) baseH;
    const int saved = proc.uiHeight.load();
    const int h0 = saved > 0 ? jlimit (heightDefault, heightMax, saved)
                             : sizeHeight (WigaWindowSize::defaultIndex (JucePlugin_Name, numSizes));
    setResizable (true, true);
    setResizeLimits (roundToInt (heightDefault * aspect), heightDefault, roundToInt (heightMax * aspect), heightMax);
    getConstrainer()->setFixedAspectRatio (aspect);
    setOpaque (true);                    // anti-gel : l'hote ne redessine jamais ce qui est derriere la fenetre
    openHeight = h0;
    setSize (roundToInt (h0 * aspect), h0);
    rebuildCaches();

    const bool on = ! flag (proc, "bypass");
    power = titleLevel = on ? 1.0f : 0.0f;
    ledLevel = on ? 0.8f : 0.0f;
    wasOn = on;
    octAnim = (float) choice (proc, "octave");
    lastOctave = choice (proc, "octave"); lastMode = choice (proc, "pedalMode"); lastWRange = choice (proc, "whammyRange");
    lastBypass = ! on; lastHold = flag (proc, "hold"); lastInvert = flag (proc, "invert");
    lastExp = proc.apvts.getRawParameterValue ("expression")->load();
    lastPresetName = proc.getCurrentPresetName();
    presetText = presetLine();
    lastTickMs = Time::getMillisecondCounterHiRes();
    startTimerHz (30);
}

FantomineAudioProcessorEditor::~FantomineAudioProcessorEditor()
{
    PopupMenu::dismissAllActiveMenus();
    stopTimer();
}

//==============================================================================
// Anti-gel v2 (NINE HANDS | DSP) : moteur logiciel sous Windows, caches refaits par le timer seulement,
// chien de garde des redessins, aucun appel a l'hote depuis le thread audio (voir PluginProcessor).
void FantomineAudioProcessorEditor::useSoftwareRenderer()
{
    auto* peer = getPeer();
    if (peer != lastPeer) { lastPeer = peer; repaint(); }
   #if JUCE_WINDOWS
    if (peer != nullptr)
    {
        int sw = peer->getAvailableRenderingEngines().indexOf ("Software Renderer");
        if (sw < 0) sw = 0;
        if (peer->getCurrentRenderingEngine() != sw)
            peer->setCurrentRenderingEngine (sw);
    }
   #endif
}

void FantomineAudioProcessorEditor::parentHierarchyChanged() { useSoftwareRenderer(); }
void FantomineAudioProcessorEditor::visibilityChanged()      { useSoftwareRenderer(); if (isShowing()) repaint(); }

float FantomineAudioProcessorEditor::physicalScale() const
{
    if (forcedScale > 0.0f) return forcedScale;
    return jlimit (1.0f, 4.0f, (float) Component::getApproximateScaleFactorForComponent (this));
}

void FantomineAudioProcessorEditor::askRepaint (Rectangle<float> u)
{
    if (repaintAskedMs <= 0.0) repaintAskedMs = Time::getMillisecondCounterHiRes();
    repaint (u.transformedBy (AffineTransform::scale (k())).getSmallestIntegerContainer().expanded (2));
}

void FantomineAudioProcessorEditor::resized()
{
    // jamais de setSize ici ; taille de l'instance enregistree seulement si elle a ete changee
    if (proc.uiHeight.load() > 0 || (openHeight > 0 && std::abs (getHeight() - openHeight) > 2))
        proc.uiHeight.store (jlimit (heightDefault, heightMax, getHeight()));
    const float s = k();
    for (int i = 0; i < 6; ++i)
        knobs[(size_t) i]->setBounds (Rectangle<float> (layout::knobLayer, layout::knobLayer).withCentre (layout::knobPos[i])
                                          .transformedBy (AffineTransform::scale (s)).toNearestInt());
    resizeSettle = 4;
}

int FantomineAudioProcessorEditor::sizeHeight (int idx)
{
    const int h[numSizes] = { heightDefault, height75, height100 };
    return h[jlimit (0, numSizes - 1, idx)];
}

void FantomineAudioProcessorEditor::setWindowHeight (int h)
{
    h = jlimit (heightDefault, heightMax, h);
    setSize (roundToInt ((double) h * baseW / baseH), h);
}

void FantomineAudioProcessorEditor::rebuildCaches (float sc)
{
    if (sc <= 0.0f) sc = cacheScale > 0.0f ? cacheScale : physicalScale();
    const int w = getWidth(), h = getHeight();
    if (w <= 0 || h <= 0) return;
    if (w == cacheW && h == cacheH && std::abs (sc - cacheScale) < 0.01f && bgScaled.isValid()) return;
    cacheW = w; cacheH = h; cacheScale = sc;
    const int pw = roundToInt ((float) w * sc), ph = roundToInt ((float) h * sc);
    bgScaled = (pw >= background.getWidth()) ? background : background.rescaled (pw, ph, Graphics::highResamplingQuality);
    repaint();
}

void FantomineAudioProcessorEditor::forceRenderScale (float sc)
{
    forcedScale = sc;
    cacheW = 0;
    rebuildCaches (sc);
    for (auto& kn : knobs) kn->setForcedScale (sc);
}

void FantomineAudioProcessorEditor::setGlowPercent (int pc)
{
    NineHandsGlow::setPercent (JucePlugin_Name, pc);
    glow = (float) jlimit (25, 100, pc) / 100.0f;
    for (auto& kn : knobs) kn->setGlow (glow);
    repaint();
}

void FantomineAudioProcessorEditor::settleForCapture()
{
    const bool on = ! flag (proc, "bypass");
    power = titleLevel = on ? 1.0f : 0.0f;
    flickerT = 1.0f;
    ledLevel = on ? (flag (proc, "hold") ? 1.0f : 0.72f + 0.28f * jlimit (0.0f, 1.0f, proc.uiAmp.load() * 1.4f)) : 0.0f;
    octAnim = proc.whammyActive.load() ? jlimit (0.0f, 2.0f, proc.uiOctave.load() + 1.0f) : (float) choice (proc, "octave");
    ampSm = proc.uiAmp.load(); midiSm = proc.uiMidi.load(); expSm = proc.uiExpression.load();
    presetText = presetLine();
    statusAlpha = Time::getMillisecondCounterHiRes() < statusUntil ? 1.0f : 0.0f;
    for (auto& kn : knobs) { kn->setLight (power); kn->setGlow (glow); kn->settle(); }
    repaint();
}

//==============================================================================
// Serigraphie vectorielle (Poppins), construite une fois en chemins (unites du plugin)
//==============================================================================
void FantomineAudioProcessorEditor::buildPrint()
{
    namePath.clear(); printPath.clear();
    for (int i = 0; i < 6; ++i)
    {
        const auto c = layout::knobPos[i];
        namePath.addPath (textPath (knobNames[i], mediumFace, 21.0f, { c.x, layout::knobLabelY }));
        printPath.addPath (textPath (String::fromUTF8 (knobMin[i]), regularFace, 13.5f, { c.x - layout::knobMinMaxDX, layout::knobMinMaxY }));
        printPath.addPath (textPath (String::fromUTF8 (knobMax[i]), regularFace, 13.5f, { c.x + layout::knobMinMaxDX, layout::knobMinMaxY }));
        for (int t = 0; t < 11; ++t)          // 11 graduations de -135 a +135 degres
        {
            const float a = degreesToRadians (-225.0f + 27.0f * (float) t);
            const Point<float> d (std::cos (a), std::sin (a));
            Path seg; seg.startNewSubPath (c + d * layout::tickR0); seg.lineTo (c + d * layout::tickR1);
            Path stroked;
            PathStrokeType (1.6f, PathStrokeType::curved, PathStrokeType::butt).createStrokedPath (stroked, seg);
            printPath.addPath (stroked);
        }
    }
    namePath.addPath (textPath ("OCTAVE", mediumFace, 18.0f, layout::octLabel));
    printPath.addPath (textPath (String::fromUTF8 ("\xe2\x88\x92" "1"), regularFace, 16.5f, layout::octM1));
    printPath.addPath (textPath ("+1", regularFace, 16.5f, layout::octP1));
    printPath.addPath (textPath ("0", regularFace, 15.0f, layout::octZero));
    printPath.addPath (textPath (String::fromUTF8 ("BYPASS  \xc2\xb7  HOLD"), mediumFace, 15.0f, layout::bypassLabel));
    const float hp = MathConstants<float>::halfPi;
    printPath.addPath (textPath ("OUT", mediumFace, 13.0f, { layout::jackLabelL, layout::jackOutY }, -hp));
    printPath.addPath (textPath ("IN",  mediumFace, 13.0f, { layout::jackLabelR, layout::jackInY }, hp));
    printPath.addPath (textPath ("EXP", mediumFace, 13.0f, { layout::jackLabelR, layout::jackExpY }, hp));
}

//==============================================================================
juce::String FantomineAudioProcessorEditor::presetLine() const
{
    auto n = proc.getCurrentPresetName();
    if (proc.presetDirty.load()) n << " *";
    return n;
}

void FantomineAudioProcessorEditor::flash (const String& t, double seconds)
{
    statusText = t;
    statusUntil = Time::getMillisecondCounterHiRes() + seconds * 1000.0;
}

void FantomineAudioProcessorEditor::setChoice (const char* id, int v)
{
    if (auto* prm = proc.apvts.getParameter (id))
    {
        prm->beginChangeGesture();
        prm->setValueNotifyingHost (prm->convertTo0to1 ((float) v));
        prm->endChangeGesture();
    }
}

Rectangle<float> FantomineAudioProcessorEditor::modeArea() const
{
    const auto s = layout::screen;
    return { s.getX() + 16.0f, s.getY() + 12.0f, 80.0f, 23.0f };
}

Rectangle<float> FantomineAudioProcessorEditor::expArea() const
{
    const auto s = layout::screen;
    return { s.getRight() - 45.0f, s.getY() + 28.0f, 30.0f, s.getHeight() - 39.0f };
}

//==============================================================================
void FantomineAudioProcessorEditor::timerCallback()
{
    const double now = Time::getMillisecondCounterHiRes();
    const float dt = (float) jlimit (0.0, 0.1, (now - lastTickMs) / 1000.0);
    lastTickMs = now;
    if (getPeer() != lastPeer || now - lastRendererCheckMs > 1000.0) { lastRendererCheckMs = now; useSoftwareRenderer(); }
    if (resizeSettle > 0 && --resizeSettle == 0) rebuildCaches();
    else if (resizeSettle == 0 && now - lastScaleCheckMs > 250.0)
    {
        lastScaleCheckMs = now;
        const float sc = physicalScale();
        if (std::abs (sc - cacheScale) > 0.01f) rebuildCaches (sc);
    }
    if (repaintAskedMs > 0.0 && isShowing() && now - repaintAskedMs > 1500.0 && lastPaintMs < repaintAskedMs)
    {
        repaintAskedMs = 0.0; lastPeer = nullptr;
        useSoftwareRenderer(); repaint();
    }
    if (now - lastGlowReadMs > 3000.0 && resizeSettle == 0)
    {
        lastGlowReadMs = now;
        glow = (float) NineHandsGlow::percent (JucePlugin_Name) / 100.0f;     // reglage commun a toutes les fenetres
    }

    // ---- reglages qui changent (souris, automation, MIDI) -> ligne d'etat ; chargement de preset -> barre seulement
    const auto pn = proc.getCurrentPresetName();
    const bool presetLoaded = pn != lastPresetName || (! proc.presetDirty.load() && dPresetText.endsWith (" *"));
    lastPresetName = pn;
    for (int i = 0; i < 6; ++i)
    {
        const float v = proc.apvts.getRawParameterValue (knobIds[i])->load();
        if (std::abs (v - lastKnob[(size_t) i]) > 1.0e-5f && ! presetLoaded)
            if (auto* prm = proc.apvts.getParameter (knobIds[i])) flash (String (knobNames[i]) + "   " + prm->getCurrentValueAsText());
        lastKnob[(size_t) i] = v;
    }
    const int oct = choice (proc, "octave"), mode = choice (proc, "pedalMode"), wr = choice (proc, "whammyRange");
    const bool bypass = flag (proc, "bypass"), hold = flag (proc, "hold"), inv = flag (proc, "invert");
    const float exp = proc.apvts.getRawParameterValue ("expression")->load();
    if (! presetLoaded)
    {
        if (oct != lastOctave) { const char* t[] = { "OCTAVE  -1", "OCTAVE  0", "OCTAVE  +1" }; flash (t[jlimit (0, 2, oct)]); }
        if (mode != lastMode)  { const char* t[] = { "PEDAL  UP", "PEDAL  DOWN", "PEDAL  BIPOLAR" }; flash (t[jlimit (0, 2, mode)]); }
    }
    if (wr != lastWRange) { const char* t[] = { "WHAMMY  -1 > +1 oct", "WHAMMY  0 > +1 oct", "WHAMMY  0 > -1 oct" }; flash (t[jlimit (0, 2, wr)]); }
    if (bypass != lastBypass) flash (bypass ? "BYPASS" : "EFFECT ON", 1.6);
    if (hold != lastHold)     flash (hold ? "HOLD  -  tap to release" : "HOLD released", hold ? 3.0 : 1.6);
    if (inv != lastInvert)    flash (inv ? "MIDI pedal inverted" : "MIDI pedal normal");
    if (std::abs (exp - lastExp) > 0.004f && lastExp >= 0.0f) flash ("EXP   " + String (roundToInt (exp * 100.0f)) + " %");
    lastOctave = oct; lastMode = mode; lastWRange = wr; lastBypass = bypass; lastHold = hold; lastInvert = inv; lastExp = exp;

    const bool whammy = proc.whammyActive.load();
    const float uo = proc.uiOctave.load();
    if (whammy && std::abs (uo - lastOct) > 0.004f)
        flash ("OCTAVE  " + String (uo >= 0 ? "+" : "") + String (uo * 12.0f, 1) + " st");
    lastOct = uo;

    if (const int lt = proc.learnTarget.load(); lt >= 0)
        flash (String::fromUTF8 ("MIDI LEARN  \xc2\xb7  ") + P::getTargetName (lt), 0.25);
    if (const int learned = proc.lastLearned.exchange (-1); learned >= 0)
    {
        const int cc = learned == P::kLearnFootswitch ? proc.footswitchCC.load() : proc.targetCC[(size_t) learned].load();
        flash (String (P::getTargetName (learned)) + " = CC " + String (cc));
    }

    const float st = now < statusUntil ? 1.0f : 0.0f;
    statusAlpha += (st - statusAlpha) * (st > statusAlpha ? 0.45f : 0.30f);      // ~120 ms a l'apparition, ~300 ms au retour
    if (statusAlpha < 0.005f) statusAlpha = 0.0f;
    if (statusAlpha > 0.995f) statusAlpha = 1.0f;
    presetText = presetLine();

    // ---- lumieres : extinction rapide, allumage plus doux, petit scintillement du neon a l'allumage
    const bool on = ! bypass;
    const float target = on ? 1.0f : 0.0f;
    power += (target - power) * jmin (1.0f, dt * (on ? 9.0f : 14.0f));
    if (std::abs (target - power) < 0.003f) power = target;
    if (on && ! wasOn) flickerT = 0.0f;
    wasOn = on;
    flickerT = jmin (1.0f, flickerT + dt);
    float tl = power;
    if (on && flickerT < 0.35f && ((flickerT > 0.04f && flickerT < 0.08f) || (flickerT > 0.15f && flickerT < 0.19f))) tl *= 0.25f;
    titleLevel = tl;
    ledPulse += dt;
    float led = 0.0f;
    if (on)
        led = hold ? 0.55f + 0.45f * (0.5f + 0.5f * std::sin (ledPulse * MathConstants<float>::twoPi * 1.2f))
                   : 0.72f + 0.28f * jlimit (0.0f, 1.0f, proc.uiAmp.load() * 1.4f);
    ledLevel += (led * power - ledLevel) * jmin (1.0f, dt * 20.0f);
    if (ledLevel < 0.003f) ledLevel = 0.0f;
    for (auto& kn : knobs) { kn->setLight (power); kn->setGlow (glow); }

    // levier : 3 positions, ou suivi continu quand une pedale le pilote (whammy)
    const float op = whammy ? jlimit (0.0f, 2.0f, uo + 1.0f) : (float) oct;
    octAnim += (op - octAnim) * jmin (1.0f, dt * (whammy ? 30.0f : 22.0f));
    if (std::abs (op - octAnim) < 0.002f) octAnim = op;
    const float press = proc.footswitchPressed.load() ? 1.0f : 0.0f;
    footAnim += (press - footAnim) * jmin (1.0f, dt * 30.0f);
    if (std::abs (press - footAnim) < 0.01f) footAnim = press;

    // ecran : voix fantome animee quand la pedale est allumee
    ampSm  += (proc.uiAmp.load() - ampSm) * jmin (1.0f, dt * 12.0f);
    midiSm += (proc.uiMidi.load() - midiSm) * jmin (1.0f, dt * 20.0f);
    expSm  += (proc.uiExpression.load() - expSm) * jmin (1.0f, dt * 25.0f);
    phase  += dt * 1.6f;
    if (proc.midiActivity.exchange (0.0f) > 0.0f) midiBlink = 1.0f;
    midiBlink = jmax (0.0f, midiBlink - dt * 4.0f);

    // ---- redessins limites a ce qui change
    auto changed = [] (float& drawn, float v) { if (std::abs (drawn - v) < 0.003f) return false; drawn = v; return true; };
    const bool glowChanged = changed (dGlow, glow);
    if (changed (dTitle, titleLevel) || glowChanged) askRepaint (layout::glowTitle);
    if (changed (dLed, ledLevel) || glowChanged)
    {
        askRepaint (layout::glowLed);
        askRepaint (Rectangle<float> (layout::fsS, layout::fsS).withCentre (layout::fsPos));
    }
    if (changed (dFoot, footAnim)) askRepaint (Rectangle<float> (layout::fsS, layout::fsS).withCentre (layout::fsPos));
    if (changed (dOct, octAnim)) askRepaint (layout::octSlot.getUnion (layout::octHandle.expanded (layout::octTravel + 4.0f, 4.0f)));
    const bool learn = proc.learnTarget.load() >= 0;
    if (power > 0.003f || changed (dPower, power) || hold != dHold || learn != dLearn)
    {
        dHold = hold; dLearn = learn; dPower = power;
        askRepaint (layout::screen.expanded (2.0f));
    }
    if (changed (dStatus, statusAlpha) || statusText != dStatusText || presetText != dPresetText || hover != dHover)
    {
        dStatusText = statusText; dPresetText = presetText; dHover = hover;
        askRepaint (layout::presetRect.expanded (3.0f));
    }
}

//==============================================================================
void FantomineAudioProcessorEditor::paint (Graphics& g)
{
    lastPaintMs = Time::getMillisecondCounterHiRes();
    repaintAskedMs = 0.0;
    g.fillAll (Colour (0xff111112));          // derriere les jacks : le fond de l'image est transparent
    const Image& bg = bgScaled.isValid() ? bgScaled : background;
    g.setImageResamplingQuality (&bg == &background ? Graphics::highResamplingQuality : Graphics::lowResamplingQuality);
    if (bg.isValid()) g.drawImage (bg, getLocalBounds().toFloat());

    g.addTransform (AffineTransform::scale (k()));
    g.setImageResamplingQuality (Graphics::mediumResamplingQuality);
    drawTitle (g);
    drawPrint (g);
    drawLights (g);
    drawOctave (g);
    drawScreen (g);
    drawBar (g);
}

void FantomineAudioProcessorEditor::drawTitle (Graphics& g)
{
    // tube de verre (ombre + biseau) toujours la, halo menthe dose par Glow, tube allume (jamais dose)
    const auto r = layout::glowTitle;
    if (titleOff.isValid()) g.drawImage (titleOff, r);
    if (titleLevel > 0.003f)
    {
        g.setOpacity (jmin (1.0f, titleLevel * glow)); g.drawImage (glowTitle, r);
        g.setOpacity (jmin (1.0f, titleLevel));        g.drawImage (titleOn, r);
        g.setOpacity (1.0f);
    }
    if (subtitle != nullptr)              // coordonnees du viewBox 3000 x 1000 posees dans la boite du logo
        subtitle->draw (g, 1.0f, AffineTransform::scale (layout::brand.getWidth() / 3000.0f).translated (layout::brand.getX(), layout::brand.getY()));
}

void FantomineAudioProcessorEditor::drawPrint (Graphics& g)
{
    g.setColour (silk2); g.fillPath (printPath);
    g.setColour (silk);  g.fillPath (namePath);
    if (logo != nullptr)
    {
        const auto vb = logo->getDrawableBounds();
        const float w = layout::logoW, h = w * vb.getHeight() / jmax (1.0f, vb.getWidth());
        logo->drawWithin (g, { layout::logoPos.x - w * 0.5f, layout::logoPos.y - h * 0.5f, w, h }, RectanglePlacement::centred, 0.92f);
    }
}

void FantomineAudioProcessorEditor::drawLights (Graphics& g)
{
    auto layer = [&] (const Image& im, Rectangle<float> r, float level)
    {
        if (level <= 0.003f || ! im.isValid()) return;
        g.setOpacity (jmin (1.0f, level)); g.drawImage (im, r);
        g.setOpacity (1.0f);
    };
    const auto fsR = Rectangle<float> (layout::fsS, layout::fsS).withCentre (layout::fsPos);
    // footswitch enfonce : le chapeau s'assombrit et son ombre interne s'elargit
    if (footAnim > 0.01f)
    {
        const auto c = layout::fsPos; const float r = layout::footR * 0.98f;
        g.setColour (Colours::black.withAlpha (0.22f * footAnim));
        g.fillEllipse (c.x - r, c.y - r, r * 2.0f, r * 2.0f);
        ColourGradient sh (Colours::black.withAlpha (0.0f), c.x, c.y, Colours::black.withAlpha (0.38f * footAnim), c.x + r, c.y, true);
        g.setGradientFill (sh);
        g.fillEllipse (c.x - r, c.y - r, r * 2.0f, r * 2.0f);
    }
    layer (fsRefl, fsR, ledLevel * 0.55f * (0.4f + 0.6f * glow));     // reflet de la LED dans le chrome
    layer (glowLed, layout::glowLed, ledLevel * glow * 0.7f);                 // lumiere portee sur la facade (dosee)
    const float hs = layout::ledS * 0.5f;
    layer (ledOn, { layout::ledPos.x - hs, layout::ledPos.y - hs, hs * 2.0f, hs * 2.0f }, ledLevel);
}

void FantomineAudioProcessorEditor::drawOctave (Graphics& g)
{
    if (! octHandle.isValid()) return;
    const float dx = (octAnim - 1.0f) * layout::octTravel;
    g.setImageResamplingQuality (Graphics::highResamplingQuality);
    g.drawImage (octHandle, layout::octHandle.translated (dx, 0.0f));
    g.setImageResamplingQuality (Graphics::mediumResamplingQuality);
}

void FantomineAudioProcessorEditor::drawScreen (Graphics& g)
{
    const float on = power;
    if (on < 0.01f) return;                       // bypass : ecran eteint, seule la vitre du visuel reste
    const auto s = layout::screen;
    Graphics::ScopedSaveState ss (g);
    Path clip; clip.addRoundedRectangle (s, 10.0f);
    g.reduceClipRegion (clip);

    // trame
    g.setColour (mint.withAlpha (0.045f * on));
    for (float y = s.getY() + 8.0f; y < s.getBottom() - 4.0f; y += 7.5f)
        g.fillRect (Rectangle<float> (s.getX() + 8.0f, y, s.getWidth() - 58.0f, 0.6f));

    // voix fantome : forme d'onde reelle (harmoniques du moteur), trois passes lumineuses
    const auto h = proc.getHarmonicsSnapshot();
    const float x0 = s.getX() + 16.0f, x1 = s.getRight() - 60.0f, cy = s.getY() + s.getHeight() * 0.52f;
    const float cycles = jlimit (1.5f, 5.0f, 1.6f + (midiSm - 36.0f) / 14.0f);
    const float amp = 36.0f * jlimit (0.04f, 1.0f, ampSm * 1.3f);
    double norm = 0.0; for (auto a : h) norm += a; norm = jmax (1e-6, norm);
    Path wave; bool first = true;
    for (float x = x0; x <= x1; x += 1.5f)
    {
        const float t = (x - x0) / (x1 - x0);
        const float th = MathConstants<float>::twoPi * (t * cycles - phase);
        double v = 0.0;
        for (size_t i = 0; i < h.size(); ++i) v += h[i] * std::sin ((double) (i + 1) * th);
        const float y = cy - amp * std::sin (MathConstants<float>::pi * t) * (float) (v / norm) * 1.6f;
        if (first) { wave.startNewSubPath (x, y); first = false; } else wave.lineTo (x, y);
    }
    g.setColour (mint.withAlpha (0.10f * on * glow)); g.strokePath (wave, PathStrokeType (12.0f, PathStrokeType::curved, PathStrokeType::rounded));
    g.setColour (mint.withAlpha (0.24f * on * glow)); g.strokePath (wave, PathStrokeType (6.0f, PathStrokeType::curved, PathStrokeType::rounded));
    g.setColour (mint.withAlpha (0.96f * on));        g.strokePath (wave, PathStrokeType (2.2f, PathStrokeType::curved, PathStrokeType::rounded));

    // sens de la pedale (clic = change)
    const auto ma = modeArea();
    const char* modes[] = { "UP", "DOWN", "BIPOLAR" };
    g.setColour (scrTeal.withAlpha ((hover == Hit::mode ? 1.0f : 0.85f) * on));
    g.drawRoundedRectangle (ma, ma.getHeight() * 0.5f, 1.2f);
    g.setFont (Font (FontOptions (mediumFace).withPointHeight (15.0f)));
    g.setColour (scrText.withAlpha (on));
    g.drawText (modes[jlimit (0, 2, choice (proc, "pedalMode"))], ma.translated (0.0f, 0.5f), Justification::centred);

    // activite MIDI
    g.setColour (mint.withAlpha ((0.35f + 0.65f * midiBlink) * on));
    g.fillEllipse (s.getRight() - 74.0f, s.getY() + 19.0f, 8.0f, 8.0f);

    // pedale d'expression (glisser = la piloter a la souris)
    const auto ea = expArea();
    g.setFont (Font (FontOptions (mediumFace).withPointHeight (13.0f)));
    g.setColour (scrTeal.withAlpha (on));
    g.drawText ("EXP", Rectangle<float> (ea.getX() - 8.0f, s.getY() + 7.0f, ea.getWidth() + 16.0f, 18.0f), Justification::centred);
    g.setColour (scrEdge.withAlpha ((hover == Hit::exp ? 1.0f : 0.85f) * on));
    g.drawRoundedRectangle (ea, 6.0f, 1.2f);
    auto fill = ea.reduced (3.5f);
    fill = fill.withTop (fill.getBottom() - fill.getHeight() * jlimit (0.0f, 1.0f, expSm));
    if (fill.getHeight() > 0.5f)
    {
        ColourGradient eg (mint.withAlpha (0.95f * on), fill.getX(), ea.getY(), mint.withAlpha (0.55f * on), fill.getX(), ea.getBottom(), false);
        g.setGradientFill (eg);
        g.fillRoundedRectangle (fill, 3.5f);
    }

    // note jouee
    if (proc.uiNote.load())
    {
        int cents = 0;
        const auto nn = noteName (midiSm, cents);
        const Font nf (FontOptions (mediumFace).withPointHeight (30.0f));
        g.setFont (nf);
        g.setColour (scrText.withAlpha (on));
        const float ny = s.getBottom() - 22.0f;
        g.drawText (nn, Rectangle<float> (x0, ny - 22.0f, 120.0f, 44.0f), Justification::centredLeft);
        const float nx = x0 + GlyphArrangement::getStringWidth (nf, nn) + 12.0f;
        g.setFont (Font (FontOptions (regularFace).withPointHeight (16.0f)));
        g.setColour (scrTeal.withAlpha (on));
        g.drawText ((cents >= 0 ? "+" : "") + String (cents) + String::fromUTF8 (" \xc2\xa2"),
                    Rectangle<float> (nx, ny - 12.0f + 2.0f, 100.0f, 24.0f), Justification::centredLeft);
    }

    // etiquettes d'etat
    const bool learn = proc.learnTarget.load() >= 0;
    if (learn || flag (proc, "hold"))
    {
        g.setFont (Font (FontOptions (boldFace).withPointHeight (12.5f)));
        g.setColour (violet.withAlpha (on));
        g.drawText (learn ? "LEARN" : "HOLD", Rectangle<float> (ea.getX() - 110.0f, s.getBottom() - 30.0f, 100.0f, 18.0f), Justification::centredRight);
    }
}

void FantomineAudioProcessorEditor::drawBar (Graphics& g)
{
    // pastille unique (400 x 38, reference Strong Pickle) : barre de presets au repos, ligne d'etat pendant les reglages
    const auto r = layout::presetRect;
    const bool barHot = hover == Hit::presetPrev || hover == Hit::presetName || hover == Hit::presetNext;
    g.setColour (barRim);
    g.fillRoundedRectangle (r.expanded (1.5f), r.getHeight() * 0.5f + 1.5f);
    g.setColour (barFill);
    g.fillRoundedRectangle (r, r.getHeight() * 0.5f);
    g.setColour (barEdge.brighter (barHot && statusAlpha <= 0.0f ? 0.6f : 0.0f));
    g.drawRoundedRectangle (r.reduced (0.3f), r.getHeight() * 0.5f, 0.6f);
    g.setFont (Font (FontOptions (mediumFace).withPointHeight (layout::presetFont)));
    if (statusAlpha > 0.0f)
    {
        g.setColour (barInk.withAlpha (statusAlpha));
        g.drawFittedText (statusText, r.reduced (r.getHeight() * 0.5f, 0.0f).toNearestInt(), Justification::centred, 1, 0.6f);
    }
    const float a = 1.0f - statusAlpha;
    if (a <= 0.0f) return;
    auto arrow = [&] (Rectangle<float> ar, bool left, bool hot)
    {
        Path p; const auto c = ar.getCentre(); const float sz = 5.5f;
        if (left) p.addTriangle (c.x + sz * 0.6f, c.y - sz, c.x + sz * 0.6f, c.y + sz, c.x - sz * 0.9f, c.y);
        else      p.addTriangle (c.x - sz * 0.6f, c.y - sz, c.x - sz * 0.6f, c.y + sz, c.x + sz * 0.9f, c.y);
        g.setColour (barInk.withAlpha ((hot ? 1.0f : 0.6f) * a));
        g.fillPath (p);
    };
    arrow (r.withWidth (arrowW), true, hover == Hit::presetPrev);
    arrow (r.withTrimmedLeft (r.getWidth() - arrowW), false, hover == Hit::presetNext);
    g.setColour (barInk.withAlpha ((hover == Hit::presetName ? 1.0f : 0.92f) * a));
    g.drawFittedText (presetText, r.reduced (arrowW, 0.0f).toNearestInt(), Justification::centred, 1, 0.7f);
}

//==============================================================================
// Souris
//==============================================================================
FantomineAudioProcessorEditor::Hit FantomineAudioProcessorEditor::hitAt (Point<float> u) const
{
    if (layout::octSlot.expanded (6.0f, 14.0f).contains (u)) return Hit::octave;
    if (u.getDistanceFrom (layout::fsPos) <= layout::fsFlats * 0.62f) return Hit::foot;
    if (modeArea().expanded (4.0f).contains (u)) return Hit::mode;
    if (expArea().expanded (8.0f, 6.0f).contains (u)) return Hit::exp;
    if (layout::screen.contains (u)) return Hit::screen;
    const auto r = layout::presetRect;
    if (r.contains (u))
        return u.x < r.getX() + arrowW ? Hit::presetPrev : (u.x > r.getRight() - arrowW ? Hit::presetNext : Hit::presetName);
    return Hit::none;
}

void FantomineAudioProcessorEditor::mouseMove (const MouseEvent& e)
{
    hover = hitAt (toUnits (e.position));
    setMouseCursor (hover == Hit::none || hover == Hit::screen ? MouseCursor::NormalCursor
                  : hover == Hit::exp ? MouseCursor::UpDownResizeCursor : MouseCursor::PointingHandCursor);
}

void FantomineAudioProcessorEditor::mouseExit (const MouseEvent&) { hover = Hit::none; }

void FantomineAudioProcessorEditor::setOctaveFromX (float ux)
{
    const float c = layout::octHandle.getCentreX();
    const int pos = ux < c - layout::octTravel * 0.5f ? 0 : (ux > c + layout::octTravel * 0.5f ? 2 : 1);
    if (proc.whammyActive.load())
    {
        proc.whammyActive.store (false);          // le levier reprend la main sur la pedale
        if (pos == choice (proc, "octave")) { const char* t[] = { "OCTAVE  -1", "OCTAVE  0", "OCTAVE  +1" }; flash (t[pos]); }
    }
    if (pos != choice (proc, "octave")) setChoice ("octave", pos);
}

void FantomineAudioProcessorEditor::setExpressionFromY (float uy)
{
    const auto ea = expArea().reduced (3.5f);
    const float v = jlimit (0.0f, 1.0f, (ea.getBottom() - uy) / ea.getHeight());
    if (auto* prm = proc.apvts.getParameter ("expression")) prm->setValueNotifyingHost (v);
}

void FantomineAudioProcessorEditor::mouseDown (const MouseEvent& e)
{
    const auto u = toUnits (e.position);
    const auto h = hitAt (u);
    if (e.mods.isPopupMenu())
    {
        // clic droit sur une commande : son MIDI Learn en tete du menu
        showContextMenu (h == Hit::octave ? P::kOctave : h == Hit::foot ? P::kLearnFootswitch
                         : h == Hit::mode ? P::kPedalMode : (h == Hit::exp || h == Hit::screen) ? P::kPitch : -1);
        return;
    }
    if (statusAlpha > 0.0f && layout::presetRect.contains (u))
    {   // la ligne d'etat ne bloque pas : un clic fait revenir la barre de presets
        statusUntil = 0.0;
        return;
    }
    dragging = Hit::none;
    switch (h)
    {
        case Hit::octave: dragging = Hit::octave; setOctaveFromX (u.x); break;
        case Hit::foot:   footHeld = true; proc.footswitchDown(); break;
        case Hit::mode:   setChoice ("pedalMode", (choice (proc, "pedalMode") + 1) % 3); break;
        case Hit::exp:
            dragging = Hit::exp;
            if (auto* prm = proc.apvts.getParameter ("expression")) prm->beginChangeGesture();
            setExpressionFromY (u.y);
            break;
        case Hit::presetPrev: stepPreset (-1); break;
        case Hit::presetNext: stepPreset (1); break;
        case Hit::presetName: showPresetMenu(); break;
        case Hit::screen: case Hit::none: break;
    }
}

void FantomineAudioProcessorEditor::mouseDrag (const MouseEvent& e)
{
    const auto u = toUnits (e.position);
    if (dragging == Hit::octave) setOctaveFromX (u.x);
    else if (dragging == Hit::exp) setExpressionFromY (u.y);
}

void FantomineAudioProcessorEditor::mouseUp (const MouseEvent& e)
{
    if (dragging == Hit::exp)
        if (auto* prm = proc.apvts.getParameter ("expression")) prm->endChangeGesture();
    dragging = Hit::none;
    if (footHeld && ! e.mods.isPopupMenu()) proc.footswitchUp();
    footHeld = false;
}

void FantomineAudioProcessorEditor::mouseWheelMove (const MouseEvent& e, const MouseWheelDetails& w)
{
    const auto h = hitAt (toUnits (e.position));
    const float step = (std::abs (w.deltaY) > 1.0e-6f ? w.deltaY : w.deltaX) * (w.isReversed ? -1.0f : 1.0f);
    if (std::abs (step) < 1.0e-6f) return;
    if (h == Hit::octave)
    {
        proc.whammyActive.store (false);
        setChoice ("octave", jlimit (0, 2, choice (proc, "octave") + (step > 0 ? 1 : -1)));
    }
    else if (h == Hit::exp)
        if (auto* prm = proc.apvts.getParameter ("expression"))
            prm->setValueNotifyingHost (jlimit (0.0f, 1.0f, prm->getValue() + step * 0.05f));
}

//==============================================================================
// Presets
//==============================================================================
void FantomineAudioProcessorEditor::stepPreset (int delta)
{
    const int n = proc.getNumPrograms();
    proc.setCurrentProgram ((proc.getCurrentProgram() + delta + n) % n);
    proc.updateHostDisplay (AudioProcessor::ChangeDetails().withProgramChanged (true));
}

void FantomineAudioProcessorEditor::showPresetMenu()
{
    PopupMenu m;
    m.setLookAndFeel (&menuLnf);
    NineHandsMenu::addHeader (m, menuLnf.f, NineHandsMenu::icoPreset, menuAccent, "Presets", presetLine());
    m.addSectionHeader ("Factory presets");
    const auto& fp = P::getFactoryPresets();
    for (int i = 0; i < (int) fp.size(); ++i)
        m.addItem (100 + i, String (i + 1) + ". " + fp[(size_t) i].name, true,
                   proc.getCurrentProgram() == i && proc.getCurrentPresetName() == fp[(size_t) i].name);
    m.addSeparator();
    PopupMenu load, save;
    for (int s = 1; s <= 9; ++s)
    {
        const bool used = proc.isUserSlotUsed (s);
        load.addItem (200 + s, "User " + String (s) + (used ? "  " + proc.getUserSlotName (s) : String ("  (empty)")), used);
        save.addItem (300 + s, "User " + String (s) + (used ? "  " + proc.getUserSlotName (s) + "  (overwrite)" : String()));
    }
    m.addSubMenu ("Load user preset", load);
    m.addSubMenu ("Save user preset", save);
    const auto area = layout::presetRect.transformedBy (AffineTransform::scale (k())).getSmallestIntegerContainer();
    m.showMenuAsync (PopupMenu::Options().withTargetScreenArea (localAreaToGlobal (area)),
        [safe = Component::SafePointer<FantomineAudioProcessorEditor> (this)] (int r)
        {
            if (safe == nullptr || r == 0) return;
            auto& pr = safe->proc;
            if (r >= 100 && r < 200)
            {
                pr.setCurrentProgram (r - 100);
                pr.updateHostDisplay (AudioProcessor::ChangeDetails().withProgramChanged (true));
            }
            else if (r > 200 && r < 300) pr.loadUserPreset (r - 200);
            else if (r > 300 && r < 400) { pr.saveUserPreset (r - 300); safe->flash ("Saved  User " + String (r - 300)); }
        });
}

//==============================================================================
// Menu clic droit (design d'Octopus, NineHandsMenu.h), toujours ouvert a l'endroit du clic
//==============================================================================
void FantomineAudioProcessorEditor::showContextMenu (int focus)
{
    using namespace NineHandsMenu;
    PopupMenu menu;
    menu.setLookAndFeel (&menuLnf);
    auto ccOf = [this] (int t) { return t == P::kLearnFootswitch ? proc.footswitchCC.load() : proc.targetCC[(size_t) t].load(); };
    auto ccText = [] (int cc) { return cc >= 0 ? "CC " + String (cc) : String ("not assigned"); };
    const int lt = proc.learnTarget.load();

    if (focus >= 0)
    {
        const String name = String (P::getTargetName (focus)).toLowerCase();
        const String title = name.substring (0, 1).toUpperCase() + name.substring (1);
        const int ico = focus == P::kLearnFootswitch ? icoPedal : focus == P::kOctave ? icoSwitch
                      : (focus == P::kPitch || focus == P::kPedalMode) ? icoMidi : icoKnob;
        addHeader (menu, menuLnf.f, ico, menuAccent, focus == P::kPitch ? String ("Pitch pedal") : title, "MIDI: " + ccText (ccOf (focus)));
        const int learnId = focus == P::kLearnFootswitch ? 30 : 1000 + focus * 10;
        const int clearId = focus == P::kLearnFootswitch ? 31 : 1001 + focus * 10;
        menu.addItem (learnId, "MIDI Learn: " + title, true, lt == focus);
        menu.addItem (clearId, "Clear MIDI: " + title, ccOf (focus) >= 0);
        if (lt >= 0) menu.addItem (1200, "Cancel MIDI learn");
        menu.addSeparator();
    }
    else
        addHeader (menu, menuLnf.f, icoPedal, menuAccent, "Fantomine", "Theremin voice  v" + String (JucePlugin_VersionString));

    PopupMenu sizes, defSizes;
    {
        const char* names[numSizes] = { "60 %", "75 %", "100 %" };
        const int def = WigaWindowSize::defaultIndex (JucePlugin_Name, numSizes);
        for (int i = 0; i < numSizes; ++i)
        {
            sizes.addItem (1 + i, String (names[i]) + (i == def ? "  (default)" : ""), true, std::abs (getHeight() - sizeHeight (i)) <= 2);
            defSizes.addItem (20 + i, names[i], true, i == def);
        }
        sizes.addSeparator();
        sizes.addSubMenu ("Default size (new windows)", defSizes);
    }
    menu.addSubMenu ("Plugin size", sizes);
    PopupMenu glowM;
    {
        const int now = roundToInt (glow * 100.0f);
        for (int i = 0; i < NineHandsGlow::numSteps; ++i)
        {
            const int pc = NineHandsGlow::steps[i];
            glowM.addItem (60 + i, "Glow " + String (pc) + " %" + (pc == 100 ? "  (default)" : ""), true, now == pc);
        }
    }
    menu.addSubMenu ("Glow (halo of the lights)", glowM);
    menu.addSeparator();

    PopupMenu factory, load, save;
    const auto& fp = P::getFactoryPresets();
    for (int i = 0; i < (int) fp.size(); ++i)
        factory.addItem (100 + i, String (i + 1) + ". " + fp[(size_t) i].name, true,
                         proc.getCurrentProgram() == i && proc.getCurrentPresetName() == fp[(size_t) i].name);
    for (int s = 1; s <= 9; ++s)
    {
        const bool used = proc.isUserSlotUsed (s);
        load.addItem (200 + s, "User " + String (s) + (used ? "  " + proc.getUserSlotName (s) : String ("  (empty)")), used);
        save.addItem (300 + s, "User " + String (s) + (used ? "  " + proc.getUserSlotName (s) + "  (overwrite)" : String()));
    }
    menu.addSubMenu ("Factory presets", factory);
    menu.addSubMenu ("Load user preset", load);
    menu.addSubMenu ("Save user preset", save);
    menu.addSeparator();

    // reglages de jeu
    PopupMenu settings, mode, wrange;
    const int pm = choice (proc, "pedalMode");
    mode.addItem (21, "UP: heel = played note, toe = + Range", true, pm == 0);
    mode.addItem (22, "DOWN: heel = played note, toe = - Range", true, pm == 1);
    mode.addItem (23, "BIPOLAR: centre = played note", true, pm == 2);
    settings.addSubMenu ("Pitch pedal direction", mode);
    const int wr = choice (proc, "whammyRange");
    wrange.addItem (41, "Heel -1 oct  >  centre 0  >  toe +1 oct", true, wr == 0);
    wrange.addItem (42, "Heel 0  >  toe +1 oct", true, wr == 1);
    wrange.addItem (43, "Heel 0  >  toe -1 oct", true, wr == 2);
    settings.addSubMenu ("Octave whammy range", wrange);
    menu.addSubMenu ("Settings", settings);

    // MIDI : MIDI Learn de chaque commande (aucun CC par defaut), sens des pedales, footswitch
    PopupMenu midi, foot;
    midi.addSectionHeader ("MIDI Learn");
    for (int t = 0; t < P::kNumTargets; ++t)
    {
        const String label = t == P::kPitch ? "PITCH (bend)" : t == P::kOctave ? "OCTAVE (whammy)" : String (P::getTargetName (t));
        midi.addItem (1000 + t * 10, "Learn: " + label + "  (" + ccText (ccOf (t)) + ")", true, lt == t);
    }
    const int fcc = proc.footswitchCC.load();
    foot.addItem (30, "MIDI Learn (press the footswitch)", true, lt == P::kLearnFootswitch);
    foot.addItem (31, "Clear MIDI: footswitch", fcc >= 0);
    foot.addItem (32, "CC 64", true, fcc == 64);
    foot.addItem (33, "CC 80", true, fcc == 80);
    midi.addSubMenu ("Footswitch  (" + ccText (fcc) + ")", foot, true, nullptr, lt == P::kLearnFootswitch);
    midi.addSeparator();
    if (lt >= 0) midi.addItem (1200, "Cancel MIDI learn");
    midi.addItem (1201, "Clear all MIDI assignments");
    midi.addSeparator();
    midi.addItem (50, "MIDI pedals inverted (heel / toe)", true, flag (proc, "invert"));
    menu.addSubMenu ("MIDI", midi);
    menu.addSeparator();
    menu.addItem (999, "Fantomine v" + String (JucePlugin_VersionString) + "  NINE HANDS | DSP", false);

    menu.showMenuAsync (PopupMenu::Options().withMousePosition(),       // toujours la ou l'on clique
        [safe = Component::SafePointer<FantomineAudioProcessorEditor> (this)] (int r)
        {
            if (safe == nullptr || r == 0) return;
            auto& ed = *safe;
            auto& pr = ed.proc;
            if      (r >= 1 && r < 1 + numSizes) ed.setWindowHeight (sizeHeight (r - 1));
            else if (r >= 20 && r < 20 + numSizes)
            {
                WigaWindowSize::setDefaultIndex (JucePlugin_Name, r - 20);
                ed.setWindowHeight (sizeHeight (r - 20));
            }
            else if (r >= 60 && r < 60 + NineHandsGlow::numSteps)
            {
                ed.setGlowPercent (NineHandsGlow::steps[r - 60]);
                ed.flash ("Glow  " + String (NineHandsGlow::steps[r - 60]) + " %");
            }
            else if (r >= 100 && r < 200)
            {
                pr.setCurrentProgram (r - 100);
                pr.updateHostDisplay (AudioProcessor::ChangeDetails().withProgramChanged (true));
            }
            else if (r > 200 && r < 300) pr.loadUserPreset (r - 200);
            else if (r > 300 && r < 400) { pr.saveUserPreset (r - 300); ed.flash ("Saved  User " + String (r - 300)); }
            else if (r >= 21 && r <= 23) ed.setChoice ("pedalMode", r - 21);
            else if (r >= 41 && r <= 43) ed.setChoice ("whammyRange", r - 41);
            else if (r == 30) pr.learnTarget.store (pr.learnTarget.load() == P::kLearnFootswitch ? -1 : P::kLearnFootswitch);
            else if (r == 31) { pr.footswitchCC.store (-1); ed.flash ("FOOTSWITCH  MIDI cleared"); }
            else if (r == 32) pr.assignCC (P::kLearnFootswitch, 64);
            else if (r == 33) pr.assignCC (P::kLearnFootswitch, 80);
            else if (r == 50)
            {
                if (auto* prm = pr.apvts.getParameter ("invert"))
                    prm->setValueNotifyingHost (prm->getValue() < 0.5f ? 1.0f : 0.0f);
            }
            else if (r == 1200) pr.learnTarget.store (-1);
            else if (r == 1201)
            {
                pr.learnTarget.store (-1); pr.resetMidiMap();
                if (auto* prm = pr.apvts.getParameter ("expression")) prm->setValueNotifyingHost (0.0f);
                ed.flash ("All MIDI cleared");
            }
            else if (r >= 1000 && r < 1000 + P::kNumTargets * 10)
            {
                const int t = (r - 1000) / 10, kk = (r - 1000) % 10;
                if (kk == 0) pr.learnTarget.store (pr.learnTarget.load() == t ? -1 : t);       // re-cliquer annule
                else
                {
                    pr.targetCC[(size_t) t].store (-1);
                    if (t == P::kPitch)
                        if (auto* prm = pr.apvts.getParameter ("expression")) prm->setValueNotifyingHost (0.0f);
                    ed.flash (String (P::getTargetName (t)) + "  MIDI cleared");
                }
            }
        });
}
