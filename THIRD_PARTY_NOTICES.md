# Third-party software and inputs

The project-authored Python/JavaScript code is GPL-3.0-or-later (root LICENSE). Libraries are installed separately, not relicensed by this repository:

- Pymunk — https://github.com/viblo/pymunk — MIT.
- NumPy — https://github.com/numpy/numpy — BSD-3-Clause.
- SciPy — https://github.com/scipy/scipy — BSD-3-Clause.
- librosa — https://github.com/librosa/librosa — ISC.
- SoundFile — https://github.com/bastibe/python-soundfile — BSD-3-Clause; libsndfile has separate LGPL terms.
- Pillow — https://github.com/python-pillow/Pillow — HPND/PIL license; bundled font resources retain their notices.
- OpenCV — https://github.com/opencv/opencv — Apache-2.0; opencv-python package notices apply to its distribution.
- Three.js — https://github.com/mrdoob/three.js — MIT. Episode09's browser viewer loads its pinned upstream modules. It requires network access for these modules.
- FFmpeg/ffprobe — https://ffmpeg.org — external prerequisite, binaries not distributed here; terms depend on the installed build.

## Data and artwork

Episode03 includes an OpenStreetMap-derived geometry snapshot. © OpenStreetMap contributors; ODbL1.0. See projects/03-city-pinball/README.md for the original endpoint and attribution. Map data is separate from the source code license. Do not remove its attribution.

Episode07's assets.png is a generated photo-style sprite sheet, not a camera photograph. Its source hash and generation provenance are in that project's ASSET_PROVENANCE.json. No third-party product logo is intended. The code license does not assert ownership of generated visual elements; source-provider terms are not invented or replaced here.

Episode05 includes numeric pitch measurements for reproduction, not commercial TTS voice recordings. Users can analyze their own audio. Episode09's input provenance and procedural music sources are documented in its folder. No George narration audio is distributed.

Siljangnim: https://github.com/okdalto/siljangnim. These are the standalone experiments used to produce the Shorts, not a distribution of the entire Siljangnim application.

## 10 · Voice to instrument

The original voice-analysis pipeline used Praat/Parselmouth (GPL-3.0) and FEniCSx/DOLFINx (LGPL-3.0). These packages are not bundled. The portable implementation uses NumPy and SciPy (BSD). Authored spectral measurements, geometry search states and analytic synthesized tube audio are included under the repository license. The commercial Brian reference and George narration are not distributed. `samples/short-final-tube.wav` is the original FEM-synthesized tube output, not a voice-provider recording. Browser and Python fixed-pitch examples are computed from an analytic glottal pulse.

## 11 · PS1 graphics

Four educational scenes and procedural laboratory textures are project-authored. The optional character is [PSX Style Teen by swickster](https://swickster.itch.io/psx-style-teen). The author states: “Free to use in commercial projects. Credit is appreciated!” Original FBX, diffuse texture, derived mesh buffers and character-embedded scenes are not distributed; users acquire the asset directly. The importer uses separately installed Three.js 0.185.0 (MIT). Commercial narration and production caches are excluded.
