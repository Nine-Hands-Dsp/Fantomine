#pragma once
#include <juce_gui_basics/juce_gui_basics.h>
#include <juce_audio_processors/juce_audio_processors.h>

// NINE HANDS | DSP : potard anime (skill potards-nine-hands-dsp).
// Ombre, couronne, chapeau et repere tournent ensemble au meme angle, flou de mouvement selon la vitesse,
// reflets fixes (lumiere en haut a gauche a 45 deg), ombre decalee a 45 deg vers le bas a droite.
// Variante Fantomine : le repere (rainure + trait lumineux menthe) est dessine AU-DESSUS des reflets fixes
// (une lumiere emise n'est pas assombrie par le reflet du chapeau) ; trait allume dose par setLight(),
// halo du trait dose par setLight() x setGlow() (reglage Glow du clic droit).
namespace nh
{
class Knob : public juce::Component, private juce::Timer
{
public:
    struct Layers { juce::Image shadow, crown, cap, wear, marker, highlight, markerOff, markerOn, markerGlow; };

    struct Style
    {
        float startAngle = juce::degreesToRadians (-135.0f);
        float endAngle   = juce::degreesToRadians ( 135.0f);
        juce::Point<float> shadowOffset { 0.025f, 0.025f };   // lumiere en haut a gauche a 45 deg -> ombre a 45 deg vers le bas a droite
        float blurMax    = juce::degreesToRadians (40.0f);
        float blurStep   = juce::degreesToRadians (3.0f);
        float blurDecay  = 0.6f;
        float dragPixels = 250.0f;
        float hitRadius  = 0.5f;                               // rayon cliquable / cote du composant
    };

    Knob (juce::RangedAudioParameter& p, Layers l) : Knob (p, std::move (l), Style()) {}
    Knob (juce::RangedAudioParameter& p, Layers l, Style s)
        : param (p), layers (std::move (l)), style (s),
          attachment (p, [this] (float v) { target = param.convertTo0to1 (v); }, nullptr)
    {
        attachment.sendInitialUpdate();
        shown = target;
        lastAngle = angleFor (shown);
        setMouseCursor (juce::MouseCursor::UpDownResizeCursor);
        startTimerHz (30);
    }

    std::function<void (const juce::MouseEvent&)> onRightClick;
    std::function<void()> onGestureStart;

    void setLight (float v) { v = juce::jlimit (0.0f, 1.0f, v); if (v != light) { light = v; markerDirty = true; } }
    void setGlow  (float v) { v = juce::jlimit (0.0f, 1.0f, v); if (v != glow) { glow = v; markerDirty = true; } }
    void setForcedScale (float s) { forcedScale = s; resizeSettle = 1; }
    // rendu immediat (captures) : pas de flou, cache a jour
    void settle() { rebuildCache(); blurSpan = 0.0f; shown = target; lastAngle = angleFor (shown); markerDirty = true; renderNow(); }

    bool hitTest (int x, int y) override
    {
        const auto c = getLocalBounds().toFloat().getCentre();
        return c.getDistanceFrom ({ (float) x, (float) y }) <= style.hitRadius * (float) juce::jmin (getWidth(), getHeight());
    }

    void resized() override { resizeSettle = frame.isValid() ? 3 : 1; }

    void paint (juce::Graphics& g) override
    {
        if (frame.isValid()) g.drawImage (frame, getLocalBounds().toFloat());
    }

    void mouseDown (const juce::MouseEvent& e) override
    {
        if (e.mods.isPopupMenu()) { if (onRightClick) onRightClick (e); return; }
        dragging = true; lastY = e.position.y; attachment.beginGesture();
        if (onGestureStart) onGestureStart();
    }
    void mouseDrag (const juce::MouseEvent& e) override
    {
        if (! dragging) return;
        const auto range = style.dragPixels * (e.mods.isShiftDown() ? 5.0f : 1.0f);
        const auto dy = e.position.y - lastY; lastY = e.position.y;
        setNormalised (target - dy / range, true);
    }
    void mouseUp (const juce::MouseEvent&) override { if (dragging) attachment.endGesture(); dragging = false; }
    void mouseDoubleClick (const juce::MouseEvent& e) override { if (! e.mods.isPopupMenu()) setNormalised (param.getDefaultValue(), false); }
    void mouseWheelMove (const juce::MouseEvent& e, const juce::MouseWheelDetails& w) override
    {
        const float step = (std::abs (w.deltaY) > 1.0e-6f ? w.deltaY : w.deltaX) * (w.isReversed ? -1.0f : 1.0f);
        setNormalised (target + step * (e.mods.isShiftDown() ? 0.01f : 0.05f), false);
    }

private:
    float angleFor (float v) const { return style.startAngle + v * (style.endAngle - style.startAngle); }

    void setNormalised (float v, bool inGesture)
    {
        target = juce::jlimit (0.0f, 1.0f, v);
        const auto plain = param.convertFrom0to1 (target);
        if (inGesture) attachment.setValueAsPartOfGesture (plain);
        else           attachment.setValueAsCompleteGesture (plain);
    }

    float currentScale() const
    {
        if (forcedScale > 0.0f) return forcedScale;
        return juce::jlimit (1.0f, 4.0f, (float) juce::Component::getApproximateScaleFactorForComponent (this));
    }

    juce::AffineTransform place (const juce::Image& img, juce::Point<float> c, float a) const
    {
        return juce::AffineTransform::translation (-img.getWidth() * 0.5f, -img.getHeight() * 0.5f)
                   .scaled (1.0f / scale).rotated (a).translated (c.x, c.y);
    }

    void timerCallback() override
    {
        if (++scaleTick >= 8)
        {
            scaleTick = 0;
            if (std::abs (currentScale() - scale) > 0.01f && resizeSettle == 0) resizeSettle = 1;
        }
        if (resizeSettle > 0 && --resizeSettle == 0) { rebuildCache(); dirty = true; }

        shown = target;
        const auto a = angleFor (shown);
        const auto v = a - lastAngle;
        lastAngle = a;
        if (std::abs (v) > 1.0e-5f) blurDir = v > 0.0f ? 1.0f : -1.0f;
        blurSpan = juce::jmax (juce::jmin (std::abs (v), style.blurMax), blurSpan * style.blurDecay);
        if (blurSpan < 0.002f) blurSpan = 0.0f;

        const bool changed = dirty || markerDirty || std::abs (a - drawnAngle) > 1.0e-4f || blurSpan != drawnSpan;
        if (changed && stack.isValid()) renderNow();
    }

    void renderNow()
    {
        if (! stack.isValid()) return;
        if (markerDirty) rebuildMarker();
        const auto a = angleFor (shown);
        renderFrame (a);
        drawnAngle = a; drawnSpan = blurSpan; dirty = false;
        repaint();
    }

    void renderFrame (float a)
    {
        const int w = juce::roundToInt (getWidth() * scale), h = juce::roundToInt (getHeight() * scale);
        if (w <= 0 || h <= 0) return;
        if (frame.getWidth() != w || frame.getHeight() != h)
        {
            frame   = juce::Image (juce::Image::ARGB, w, h, true);
            scratch = juce::Image (juce::Image::ARGB, w, h, true);
        }
        frame.clear (frame.getBounds());
        juce::Graphics g (frame);
        g.addTransform (juce::AffineTransform::scale (scale));
        g.setImageResamplingQuality (juce::Graphics::highResamplingQuality);
        const auto b = getLocalBounds().toFloat();
        const auto d = juce::jmin (b.getWidth(), b.getHeight());
        const auto c = b.getCentre();
        if (shadowCache.isValid()) drawBlurred (g, shadowCache, c + style.shadowOffset * d, a, false);
        drawBlurred (g, stack, c, a, true);
        if (highlightCache.isValid()) g.drawImage (highlightCache, b.withSizeKeepingCentre (d, d));
        if (markerStack.isValid()) drawBlurred (g, markerStack, c, a, true);
    }

    void drawBlurred (juce::Graphics& g, const juce::Image& img, juce::Point<float> c, float a, bool blur)
    {
        if (! blur || blurSpan <= 0.0f) { g.drawImageTransformed (img, place (img, c, a), false); return; }
        const int n = juce::jlimit (4, 16, (int) std::ceil (blurSpan / style.blurStep) + 1);
        scratch.clear (scratch.getBounds());
        {
            juce::Graphics gs (scratch);
            gs.addTransform (juce::AffineTransform::scale (scale));
            gs.setImageResamplingQuality (juce::Graphics::highResamplingQuality);
            for (int k = 0; k < n; ++k)
            {
                const auto t = (float) k / (float) (n - 1);
                gs.setOpacity (1.0f / (float) (k + 1)); // moyenne progressive exacte
                gs.drawImageTransformed (img, place (img, c, a - blurDir * blurSpan * t), false);
            }
        }
        g.drawImage (scratch, getLocalBounds().toFloat());
    }

    juce::Image fit (const juce::Image& src) const
    {
        if (src.isNull() || cachePx <= 0) return {};
        juce::Image out (juce::Image::ARGB, cachePx, cachePx, true);
        juce::Graphics g (out);
        g.setImageResamplingQuality (juce::Graphics::highResamplingQuality);
        g.drawImage (src, juce::Rectangle<float> (0.0f, 0.0f, (float) cachePx, (float) cachePx), juce::RectanglePlacement::centred);
        return out;
    }

    void rebuildMarker()
    {
        markerDirty = false;
        if (cachePx <= 0) return;
        markerStack = juce::Image (juce::Image::ARGB, cachePx, cachePx, true);
        juce::Graphics g (markerStack);
        if (offCache.isValid()) g.drawImageAt (offCache, 0, 0);
        if (light > 0.002f && onCache.isValid())   { g.setOpacity (light); g.drawImageAt (onCache, 0, 0); }
        if (light * glow > 0.002f && glowCache.isValid()) { g.setOpacity (light * glow); g.drawImageAt (glowCache, 0, 0); }
    }

    void rebuildCache()
    {
        scale = currentScale();
        cachePx = juce::roundToInt (juce::jmin (getWidth(), getHeight()) * scale);
        if (cachePx <= 0) return;
        shadowCache = fit (layers.shadow);
        highlightCache = fit (layers.highlight);
        offCache = fit (layers.markerOff); onCache = fit (layers.markerOn); glowCache = fit (layers.markerGlow);
        stack = juce::Image (juce::Image::ARGB, cachePx, cachePx, true);
        juce::Graphics g (stack);
        for (auto* l : { &layers.crown, &layers.cap, &layers.wear, &layers.marker })
            if (l->isValid()) g.drawImageAt (fit (*l), 0, 0);
        rebuildMarker();
    }

    juce::RangedAudioParameter& param;
    Layers layers;
    Style style;
    juce::ParameterAttachment attachment;
    juce::Image stack, shadowCache, highlightCache, offCache, onCache, glowCache, markerStack, frame, scratch;
    float scale = 1.0f, forcedScale = 0.0f, target = 0.0f, shown = 0.0f, lastAngle = 0.0f;
    float blurSpan = 0.0f, blurDir = 1.0f, lastY = 0.0f;
    float drawnAngle = 1.0e9f, drawnSpan = -1.0f;
    float light = 1.0f, glow = 1.0f;
    int resizeSettle = 0, scaleTick = 0, cachePx = 0;
    bool dragging = false, dirty = true, markerDirty = true;
};
} // namespace nh
