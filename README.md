# Fantomine — NINE HANDS | DSP

Pédale VST3 (Windows / macOS) qui transforme la guitare en **voix de thérémine** :
le plugin suit la note jouée, une voix fantôme glisse vers elle, et une pédale
d'expression MIDI courbe la hauteur en continu, comme une main près de l'antenne.

<p align="center">
  <a href="https://github.com/Nine-Hands-Dsp/Fantomine/releases/latest/download/Fantomine-VST3-Windows.zip"><img alt="Télécharger pour Windows" src="https://img.shields.io/badge/%E2%AC%87%20T%C3%A9l%C3%A9charger-Windows-0078D6?style=for-the-badge"></a>
  <a href="https://github.com/Nine-Hands-Dsp/Fantomine/releases/latest/download/Fantomine-VST3-macOS.zip"><img alt="Télécharger pour macOS" src="https://img.shields.io/badge/%E2%AC%87%20T%C3%A9l%C3%A9charger-macOS-111111?style=for-the-badge&logo=apple&logoColor=white"></a>
  <br>
  <a href="https://github.com/Nine-Hands-Dsp/Fantomine/releases/latest/download/Fantomine-Notice.pdf"><img alt="Télécharger la notice (PDF)" src="https://img.shields.io/badge/%F0%9F%93%96%20Notice-PDF-7EF0D6?style=for-the-badge"></a>
  <br>
  <a href="https://github.com/Nine-Hands-Dsp/Fantomine/releases/latest"><img alt="Dernière version" src="https://img.shields.io/github/v/release/Nine-Hands-Dsp/Fantomine?label=derni%C3%A8re%20version&color=7EF0D6"></a>
</p>

Notice complète en français : [docs/Fantomine_Notice_FR_v2.0.0.pdf](docs/Fantomine_Notice_FR_v2.0.0.pdf)

## Installation

- **Windows** : copier `Fantomine.vst3` dans `C:\Program Files\Common Files\VST3\`
- **macOS** (universel) : copier `Fantomine.vst3` dans `~/Library/Audio/Plug-Ins/VST3/`, puis
  `xattr -cr ~/Library/Audio/Plug-Ins/VST3/Fantomine.vst3`
- **Reaper** : Préférences > Plug-ins > VST > Re-scan. Nom affiché : **Fantomine (NINE HANDS | DSP)**.

## Contrôles

| Contrôle | Rôle |
|---|---|
| GLIDE | vitesse du glissando entre les notes (2 ms → 700 ms) |
| RANGE | amplitude de la pédale de hauteur, ±1 à ±24 demi-tons |
| TONE | timbre : sinus pur → anche nasale (formant « voix ») |
| VIBRATO | profondeur du vibrato humanisé |
| SPEED | vitesse du vibrato, 3 à 9 Hz |
| BLEND | dosage guitare / voix (puissance constante) |
| OCTAVE | voix à -1, 0 ou +1 octave, ou en continu par pédale (façon Whammy) |
| Footswitch | clic = bypass · appui long (0,6 s) = HOLD (fige la note) |
| Écran | sens de la pédale (UP / DOWN / BIPOLAR, clic pour changer), barre EXP (pédale à la souris), voix en direct, note jouée |
| Barre de presets | ◀ ▶ = preset précédent / suivant, clic sur le nom = menu ; la ligne d'état y affiche les valeurs pendant les réglages |

- Aucun CC MIDI par défaut : clic droit sur une commande > **MIDI Learn** (9 commandes + footswitch, 14 bits accepté pour PITCH), pédales d'expression inversées par défaut.
- Clic droit : **Plugin size** (60 % par défaut, 75 %, 100 %, taille par défaut des nouvelles fenêtres), **Glow** (halo des lumières 25 à 100 %), presets usine et utilisateur, Settings, MIDI.
- Suivi de note jusqu'à ~33 Hz : 7 cordes accordée en Sol et plus bas.

## Versions

- **v2.0.0** : pédale entièrement redessinée au format double 2350 × 1800 (pédale plein cadre), titre néon vectoriel, potards animés (calques qui tournent ensemble, flou de mouvement, repère lumineux), footswitch, LED et jacks du kit photo, sérigraphie vectorielle Poppins, logo NINE HANDS | DSP officiel, barre de presets / ligne d'état unique sous la LED, réglage Glow, menus au style Octopus ouverts là où l'on clique, notice en français.
- v1.4.1 : plus aucun CC MIDI assigné par défaut (tout passe par le MIDI Learn)
- v1.4.0 : taille par défaut des nouvelles fenêtres au choix
- v1.3.x : MIDI Learn sur chaque commande, pédales d'expression inversées par défaut
- v1.2.x : anti-gel v2, menu de taille en %

## Fabrication

- `tools/make_art.py` (fond 2350 × 1800, sprites, `tools/layout.json`), `tools/make_knob.py` (calques des potards),
  `tools/make_layers.py` (néon, halos, `Layout.h`), `tools/render` (captures du vrai plugin), `tools/manual.py` (notice).
- Build GitHub Actions (`.github/workflows/build.yml`) : Windows et macOS universel, publiés dans les Releases.
