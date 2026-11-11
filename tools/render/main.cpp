// Captures PNG de la fenetre reelle de Fantomine (meme code que le plugin), pour l'apercu, le README et la notice.
#include "PluginProcessor.h"
#include "PluginEditor.h"
#include "BinaryData.h"
using namespace juce;

int main (int argc, char** argv)
{
    ScopedJuceInitialiser_GUI init;
    const String out = argc > 1 ? argv[1] : ".";
    File (out).createDirectory();
    FantomineAudioProcessor proc;
    proc.setPlayConfigDetails (2, 2, 48000.0, 256);
    proc.prepareToPlay (48000.0, 256);
    std::unique_ptr<AudioProcessorEditor> ed (proc.createEditor());
    auto* fe = static_cast<FantomineAudioProcessorEditor*> (ed.get());
    std::printf ("taille par defaut : %d x %d\n", ed->getWidth(), ed->getHeight());

    auto pump = [] (int n) { for (int i = 0; i < n; ++i) MessageManager::getInstance()->runDispatchLoopUntil (35); };
    auto set = [&] (const char* id, float v) { if (auto* p = proc.apvts.getParameter (id)) p->setValueNotifyingHost (p->convertTo0to1 (v)); };
    double ph = 0.0;
    auto play = [&] (int blocks, double hz)        // note de guitare tenue (La2 par defaut)
    {
        AudioBuffer<float> b (2, 256); MidiBuffer m;
        for (int k = 0; k < blocks; ++k)
        {
            for (int i = 0; i < 256; ++i)
            {
                double x = 0; for (int h = 1; h < 8; ++h) x += std::sin (MathConstants<double>::twoPi * h * ph) / (h * 1.5);
                b.setSample (0, i, (float) (0.3 * x)); b.setSample (1, i, (float) (0.3 * x));
                ph += hz / 48000.0; ph -= std::floor (ph);
            }
            proc.processBlock (b, m);
        }
    };
    auto save = [&] (const String& name, float scale, Rectangle<int> area = {})
    {
        if (area.isEmpty()) area = ed->getLocalBounds();
        auto img = ed->createComponentSnapshot (area, true, scale);
        File f (out + "/" + name + ".png"); f.deleteFile();
        FileOutputStream os (f); PNGImageFormat().writeImageToStream (img, os);
        std::printf ("%s (%d x %d)\n", f.getFullPathName().toRawUTF8(), img.getWidth(), img.getHeight());
    };
    auto state = [&] (int preset, bool on, int glowPc, const String& status)
    {
        proc.setCurrentProgram (preset);
        set ("bypass", on ? 0.f : 1.f);
        fe->setGlowPercent (glowPc);
        play (400, 110.0); pump (6);
        fe->flash (status, status.isNotEmpty() ? 60.0 : 0.0);
        fe->settleForCapture();
        pump (2);
        fe->settleForCapture();
    };

    // fenetre par defaut (495 px, « 60 % »), rendue en 2x
    fe->forceRenderScale (2.0f);
    pump (6);
    state (0, true, 100, {});
    save ("fm_default", 2.0f);

    // rendu exact de la pedale (2350 x 1800)
    fe->setWindowHeight (900);
    fe->forceRenderScale (2.0f);
    pump (8);
    const float ex = 1800.0f / (float) ed->getHeight();
    state (0, true, 100, {});                         save ("fm_exact_on", ex);
    state (0, false, 100, {});                        save ("fm_exact_bypass", ex);
    state (0, true, 100, "GLIDE   35 %");             save ("fm_exact_status", ex);
    state (0, true, 25, {});                          save ("fm_glow_25", ex);
    state (0, true, 50, {});                          save ("fm_glow_50", ex);
    state (0, true, 75, {});                          save ("fm_glow_75", ex);
    fe->setGlowPercent (100);
    set ("hold", 1.f); state (0, true, 100, {});      save ("fm_exact_hold", ex); set ("hold", 0.f);
    set ("octave", 2.f); state (0, true, 100, {});    save ("fm_exact_oct_up", ex); set ("octave", 1.f);

    // GIF potard : rotation lente puis rapide (GLIDE), images toutes les 33 ms
    {
        state (0, true, 100, {});
        const auto zone = Rectangle<float> (300.0f, 280.0f, 380.0f, 240.0f)
                              .transformedBy (AffineTransform::scale ((float) ed->getHeight() / 900.0f)).toNearestInt();
        int fr = 0;
        auto frame = [&] { save ("gif/k" + String (fr++).paddedLeft ('0', 3), 1.0f, zone); };
        File (out + "/gif").createDirectory();
        auto sweep = [&] (const char* id, float a, float b, int n)
        {
            for (int i = 0; i <= n; ++i)
            {
                auto* p = proc.apvts.getParameter (id);
                p->setValueNotifyingHost (a + (b - a) * (float) i / (float) n);
                MessageManager::getInstance()->runDispatchLoopUntil (34);
                frame();
            }
        };
        sweep ("range", 0.5f, 0.0f, 30);
        sweep ("range", 0.0f, 1.0f, 8);
        for (int i = 0; i < 6; ++i) { MessageManager::getInstance()->runDispatchLoopUntil (34); frame(); }
        sweep ("tone", 0.35f, 1.0f, 4);
        sweep ("tone", 1.0f, 0.0f, 3);
        for (int i = 0; i < 8; ++i) { MessageManager::getInstance()->runDispatchLoopUntil (34); frame(); }
    }

    // grande resolution : fenetre a 150 % rendue en 2x (ecran Retina / 4K)
    fe->setWindowHeight (FantomineAudioProcessorEditor::heightMax);
    fe->forceRenderScale (2.0f);
    pump (8);
    state (0, true, 100, {});                         save ("fm_hires_on", 2.0f);

    // menus clic droit (design Octopus, NineHandsMenu.h) : rendu hors ecran avec le meme LookAndFeel que le plugin
    {
        NineHandsMenu::MenuLnf lnf;
        lnf.f = { Typeface::createSystemTypefaceFor (BinaryData::PoppinsRegular_ttf, BinaryData::PoppinsRegular_ttfSize),
                  Typeface::createSystemTypefaceFor (BinaryData::PoppinsMedium_ttf, BinaryData::PoppinsMedium_ttfSize),
                  Typeface::createSystemTypefaceFor (BinaryData::PoppinsBold_ttf, BinaryData::PoppinsBold_ttfSize) };
        struct It { String text; bool sep = false, sub = false, ticked = false, active = true; };
        auto render = [&] (const String& name, const String& title, const String& subtitle, int ico, const std::vector<It>& items, int hiIndex)
        {
            NineHandsMenu::Header hd (lnf.f, ico, Colour (0xff7ef0d6), title, subtitle);
            int w = 0, h = 0; hd.getIdealSize (w, h);
            const int border = lnf.getPopupMenuBorderSize();
            int totalH = border * 2 + h + 11, maxW = w;
            for (auto& it : items) { int iw, ih; lnf.getIdealPopupMenuItemSize (it.text, it.sep, 0, iw, ih); totalH += ih; maxW = jmax (maxW, iw + (it.sub ? 20 : 0)); }
            maxW += border * 2;
            Image img (Image::ARGB, maxW * 2, totalH * 2, true);
            Graphics g (img); g.addTransform (AffineTransform::scale (2.0f));
            lnf.drawPopupMenuBackground (g, maxW, totalH);
            int y = border;
            hd.setSize (maxW - border * 2, h);
            { Graphics::ScopedSaveState ss (g); g.setOrigin (border, y); hd.paint (g); }
            y += h;
            lnf.drawPopupMenuItem (g, { border, y, maxW - border * 2, 11 }, true, true, false, false, false, {}, {}, nullptr, nullptr); y += 11;
            for (size_t i = 0; i < items.size(); ++i)
            {
                const auto& it = items[i]; int iw, ih; lnf.getIdealPopupMenuItemSize (it.text, it.sep, 0, iw, ih);
                lnf.drawPopupMenuItem (g, { border, y, maxW - border * 2, ih }, it.sep, it.active, (int) i == hiIndex, it.ticked, it.sub, it.text, {}, nullptr, nullptr);
                y += ih;
            }
            File f (out + "/" + name + ".png"); f.deleteFile();
            FileOutputStream os (f); PNGImageFormat().writeImageToStream (img, os);
            std::printf ("%s\n", f.getFullPathName().toRawUTF8());
        };
        const String v (JucePlugin_VersionString);
        render ("fm_menu", "Fantomine", "Theremin voice  v" + v, NineHandsMenu::icoPedal,
                { { "Plugin size", false, true }, { "Glow (halo of the lights)", false, true }, { "", true },
                  { "Factory presets", false, true }, { "Load user preset", false, true }, { "Save user preset", false, true }, { "", true },
                  { "Settings", false, true }, { "MIDI", false, true }, { "", true },
                  { "Fantomine v" + v + "  NINE HANDS | DSP", false, false, false, false } }, 1);
        std::vector<It> g;
        for (int pc : { 25, 50, 75, 100 })
            g.push_back ({ "Glow " + String (pc) + " %" + (pc == 100 ? "  (default)" : ""), false, false, pc == 100 });
        render ("fm_menu_glow", "Glow", "Halo of the lights", NineHandsMenu::icoGlow, g, 1);
        render ("fm_menu_knob", "Glide", "MIDI: not assigned", NineHandsMenu::icoKnob,
                { { "MIDI Learn: Glide" }, { "Clear MIDI: Glide", false, false, false, false }, { "", true },
                  { "Plugin size", false, true }, { "Glow (halo of the lights)", false, true }, { "", true },
                  { "Factory presets", false, true }, { "MIDI", false, true } }, 0);
        render ("fm_menu_midi", "MIDI", "MIDI Learn only, no default CC", NineHandsMenu::icoMidi,
                { { "Learn: PITCH (bend)  (not assigned)" }, { "Learn: OCTAVE (whammy)  (not assigned)" }, { "Learn: VIBRATO  (not assigned)" },
                  { "Footswitch  (not assigned)", false, true }, { "", true }, { "Clear all MIDI assignments" }, { "", true },
                  { "MIDI pedals inverted (heel / toe)", false, false, true } }, 0);
    }
    ed.reset();
    return 0;
}
