# 09 · Music → colliding handwritten type

The actual Pymunk trajectories and original extruded MIX lettering from the short. Measured drum-energy rises push three rigid bodies; contacts and springs determine their motion. After eight seconds, stronger springs and angular damping bring them home.

## Run

Python 3.11 or 3.12 recommended. From this folder:

```sh
python -m pip install -r requirements.txt
python run.py
python -m http.server 8080
```

Open http://localhost:8080 and press **Play / restart**. This standalone viewer retains the published Three.js geometry, materials, lighting and measured body transforms. It fetches pinned Three.js 0.180.0 modules from esm.sh, so the browser needs internet access. No Siljangnim backend or credentials are required. `output/metrics.json` is generated locally; run the simulator first.

For a flat debug MP4, install FFmpeg on PATH and run `python run.py --render`. This creates `output/preview.mp4` (720×1280, 30 fps, 12 seconds). The flat debug renderer is not the final 3D presentation. Pillow's built-in font removes the original macOS font dependency. The viewer uses WebGL.

## Input provenance and reproduction

All the bundled music is **original procedural audio**, composed by `make_music.py` using sinusoids, envelopes and seeded noise; it contains no commercial music recording. `assets/music.wav` is the exact authored mix from the short. `assets/drums.wav` is the actual Demucs htdemucs drum separation of that mix, used in the short, not a random beat clock. `assets/features.json` is its measured, normalized librosa RMS cache (plus other stem channels, unused by this solver).

```sh
python make_music.py
python extract_features.py
python -m pip install "vtracer>=0.6,<0.7"
python make_handwriting.py
```

The first regenerates `output/original-mix.wav`. The second remeasures the included separated drums to `output/features.json`. The third redraws the authored strokes and retraces them into `output/handwriting.png` and `output/traced.svg` (requires the optional vtracer package). Generated outputs do not overwrite the published assets. To try new separated drums, use `extract_features.py --audio my-drums.wav`; then deliberately replace `assets/features.json` with the result and rerun the simulation. Audio should last eight seconds; the solver reads a 480-frame 60 Hz feature window. If changing sound, replace `assets/music.wav` with the matching mix for playback.

Re-running Demucs itself is optional: install it separately and run `python -m demucs -n htdemucs output/original-mix.wav`. It downloads model weights; the repository neither vendors the weights nor requires them for the demo. Stem separation may vary by model/runtime version. Re-measure the resulting drums with the extraction command.

The MIX lettering is original hand-authored stroke coordinates, not a font or third-party illustration. `make_handwriting.py` records those coordinates; VTracer generated the supplied trace. No generated-image service or proprietary glyph asset is needed.

## Physics and faithful limits

The solver is the published Pymunk 7.3.1 version: convex hulls of the raster glyphs, gravity (0,420), restitution 0.82, bounded walls, and damped springs. Positive drum RMS changes trigger impulses; letters are not manually animated. Physics runs at 120 Hz, sampled at 30 Hz for replay. The browser replays those states, rather than running a different JavaScript physics model. The output includes every trigger, contact and transform.

Convex hulls fill the empty areas inside each glyph: visual letter cavities are not collision holes. The rendered beveled 3D extrusion has different apparent depth from the 2D collision model. After eight seconds the spring and damping parameters intentionally strengthen; the return is not caused by silence alone. Expected published result: 116 contact callbacks, final rotations less than 0.001 radians.

## Licenses

Original project code, procedural music, authored lettering, derived stems and measured data are released under the repository GPL-3.0 license. There are no third-party song samples. Third-party implementations are dependencies, not relicensed: Pymunk (MIT), Three.js (MIT), Demucs (MIT), VTracer (MIT), librosa (ISC), NumPy (BSD), OpenCV (Apache-2.0), SoundFile (BSD), Pillow (HPND). Consult upstream distribution notices for exact terms; FFmpeg license depends on the installed build. This package does not redistribute Demucs model weights or bundled third-party library source.
