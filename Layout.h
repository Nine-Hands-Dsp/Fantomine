// généré par tools/make_layers.py (d'après tools/layout.json) - ne pas modifier à la main
// repère du plugin : 1175 x 900 unités (background.png 2350 x 1800 / 2)
#pragma once
#include <juce_graphics/juce_graphics.h>
namespace layout
{
    constexpr float frameW = 1175.0f, frameH = 900.0f;
    const juce::Rectangle<float> box { 26.16f, 0.00f, 1122.69f, 900.00f };   // boîtier (notice)
    constexpr float boxR = 29.56f;
    // ordre : glide, range, tone, vibrato, speed, blend
    const juce::Point<float> knobPos[6] = { { 144.59f, 418.23f }, { 318.34f, 418.23f }, { 492.09f, 418.23f }, { 686.63f, 418.23f }, { 861.12f, 418.23f }, { 1034.87f, 418.23f } };
    constexpr float knobR = 63.86f, knobLayer = 166.82f;   // calques 512 px, potard de rayon 196 px
    constexpr float knobLabelY = 313.30f, knobMinMaxY = 497.29f, knobMinMaxDX = 59.40f;
    constexpr float tickR0 = 72.77f, tickR1 = 80.19f;
    constexpr float sepX = 589.36f, sepY0 = 339.16f, sepY1 = 494.33f;
    const juce::Rectangle<float> screen { 616.09f, 71.67f, 463.33f, 158.87f };
    const juce::Point<float> ledPos { 589.73f, 578.20f }; constexpr float ledS = 32.50f, ledR = 13.00f;
    const juce::Rectangle<float> glowLed { 499.73f, 488.20f, 180.00f, 180.00f };
    const juce::Point<float> fsPos { 590.84f, 790.64f }; constexpr float footR = 42.43f, fsS = 212.80f, fsFlats = 112.00f;
    const juce::Rectangle<float> brand { 60.30f, 74.85f, 499.40f, 166.47f };   // viewBox 3000 x 1000 du logo Fantomine
    const juce::Rectangle<float> glowTitle { 0.30f, 14.85f, 619.40f, 286.47f };
    const juce::Rectangle<float> presetRect { 387.50f, 629.88f, 400.00f, 38.00f };
    constexpr float presetFont = 23.0f;
    const juce::Point<float> octLabel { 215.87f, 729.31f }, octM1 { 84.44f, 779.56f }, octP1 { 347.30f, 779.56f }, octZero { 215.13f, 821.67f };
    const juce::Rectangle<float> octHandle { 172.06f, 742.61f, 90.59f, 80.54f };   // levier en position 0
    const juce::Rectangle<float> octSlot { 119.34f, 761.82f, 193.80f, 44.33f };
    constexpr float octTravel = 66.83f;
    const juce::Point<float> bypassLabel { 590.84f, 710.98f };
    const juce::Point<float> logoPos { 590.84f, 873.32f }; constexpr float logoW = 172.26f;
    constexpr float jackOutY = 318.47f, jackInY = 318.47f, jackExpY = 457.39f;
    constexpr float jackLabelL = 42.16f, jackLabelR = 1132.84f;
}
