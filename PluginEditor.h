#pragma once
#include <juce_gui_basics/juce_gui_basics.h>
#include <juce_audio_processors/juce_audio_processors.h>
#include "PluginProcessor.h"
#include "Layout.h"
#include "NineHandsMenu.h"
#include "NineHandsWindow.h"
#include "NHKnob.h"

//==============================================================================
// FANTOMINE v2 (NINE HANDS | DSP) : pedale double, fond 2350 x 1800 px plein cadre (repere 1175 x 900, Layout.h).
// Le fond contient le boitier, la vitre de l'ecran, la fente du levier, la LED eteinte, le footswitch et les jacks
// (pieces du kit photo). L'editeur dessine par-dessus : potards nh::Knob (composants enfants), neon du titre,
// halos (doses par le reglage Glow du clic droit), LED, levier d'octave, serigraphie vectorielle (Poppins),
// logo NINE HANDS | DSP (SVG officiel), ecran (voix fantome, note, pedale) et pastille presets / ligne d'etat.
//==============================================================================
class FantomineAudioProcessorEditor : public juce::AudioProcessorEditor,
                                      private juce::Timer
{
public:
    explicit FantomineAudioProcessorEditor (FantomineAudioProcessor&);
    ~FantomineAudioProcessorEditor() override;

    void paint (juce::Graphics&) override;
    void resized() override;
    void parentHierarchyChanged() override;

    void mouseDown (const juce::MouseEvent&) override;
    void mouseDrag (const juce::MouseEvent&) override;
    void mouseUp (const juce::MouseEvent&) override;
    void mouseMove (const juce::MouseEvent&) override;
    void mouseExit (const juce::MouseEvent&) override;
    void mouseWheelMove (const juce::MouseEvent&, const juce::MouseWheelDetails&) override;

    static constexpr float baseW = layout::frameW, baseH = layout::frameH;
    static constexpr int numSizes = 3;                   // 60 % (defaut) / 75 % / 100 %
    static constexpr int heightDefault = 495, height75 = 557, height100 = 743, heightMax = 1114;
    static int sizeHeight (int idx);
    void setWindowHeight (int h);

    // outil de rendu (captures) : echelle forcee, etat lumineux immediat
    void forceRenderScale (float sc);
    void settleForCapture();
    void setGlowPercent (int pc);
    void flash (const juce::String& text, double seconds = 2.5);

private:
    void timerCallback() override;
    void visibilityChanged() override;
    void useSoftwareRenderer();
    float physicalScale() const;
    void askRepaint (juce::Rectangle<float> unitsRect);
    void rebuildCaches (float sc = 0.0f);
    float k() const { return (float) getHeight() / baseH; }
    juce::Point<float> toUnits (juce::Point<float> p) const { return p / k(); }

    enum class Hit { none, octave, foot, mode, exp, screen, presetPrev, presetName, presetNext };
    Hit hitAt (juce::Point<float> u) const;

    // zones de l'ecran (unites)
    juce::Rectangle<float> modeArea() const;
    juce::Rectangle<float> expArea() const;

    void setChoice (const char* id, int v);
    void setOctaveFromX (float ux);
    void setExpressionFromY (float uy);
    void stepPreset (int delta);
    juce::String presetLine() const;
    void showPresetMenu();
    void showContextMenu (int focus);
public:
    juce::PopupMenu buildContextMenu (int focus = -1);   // menu clic droit (aussi pour l'outil de controle des menus)
private:
    void buildPrint();

    void drawTitle (juce::Graphics&);
    void drawPrint (juce::Graphics&);
    void drawLights (juce::Graphics&);
    void drawOctave (juce::Graphics&);
    void drawScreen (juce::Graphics&);
    void drawBar (juce::Graphics&);

    FantomineAudioProcessor& proc;
    NineHandsMenu::MenuLnf menuLnf;
    NineHandsWindow::HostLock hostLock;    // fenetre du DAW : jamais sous 60 %, jamais au-dela de 150 %
    juce::Typeface::Ptr mediumFace, boldFace, regularFace;
    std::unique_ptr<juce::Drawable> logo, subtitle;
    juce::Path namePath, printPath;          // noms des potards (clair) ; graduations, min/max, octave, jacks, BYPASS (gris)

    std::array<std::unique_ptr<nh::Knob>, 6> knobs;
    static constexpr int knobTarget[6] = { FantomineAudioProcessor::kGlide, FantomineAudioProcessor::kRange, FantomineAudioProcessor::kTone,
                                           FantomineAudioProcessor::kVibrato, FantomineAudioProcessor::kSpeed, FantomineAudioProcessor::kBlend };

    juce::Image background, bgScaled, glowTitle, titleOn, titleOff, glowLed, ledOn, fsRefl, octHandle;
    int cacheW = 0, cacheH = 0, resizeSettle = 0, openHeight = 0;
    float cacheScale = 0.0f, forcedScale = 0.0f;
    void* lastPeer = nullptr;
    double lastPaintMs = 0.0, repaintAskedMs = 0.0, lastScaleCheckMs = 0.0, lastRendererCheckMs = 0.0, lastGlowReadMs = 0.0, lastTickMs = 0.0;

    // etat affiche
    float glow = 1.0f;                       // reglage Glow (1 = 100 %)
    float power = 1.0f, titleLevel = 1.0f, ledLevel = 1.0f, flickerT = 1.0f, ledPulse = 0.0f;
    float octAnim = 1.0f, footAnim = 0.0f;
    float ampSm = 0.0f, midiSm = 57.0f, expSm = 0.0f, phase = 0.0f, midiBlink = 0.0f;
    bool wasOn = true;
    Hit dragging = Hit::none, hover = Hit::none;
    bool footHeld = false;

    // pastille unique : barre de presets au repos, ligne d'etat pendant les reglages (fondu croise)
    juce::String statusText, presetText;
    double statusUntil = 0.0;
    float statusAlpha = 0.0f;
    std::array<float, 6> lastKnob {};
    int lastOctave = -1, lastMode = -1, lastWRange = -1;
    bool lastBypass = false, lastHold = false, lastInvert = true;
    float lastExp = -1.0f, lastOct = 0.0f;
    juce::String lastPresetName;

    // dernier etat dessine
    float dPower = -1.0f, dTitle = -1.0f, dLed = -1.0f, dOct = -1.0f, dFoot = -1.0f, dStatus = -1.0f, dGlow = -1.0f;
    bool dHold = false, dLearn = false;
    Hit dHover = Hit::none;
    juce::String dStatusText, dPresetText;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (FantomineAudioProcessorEditor)
};
