# 05 · Voice → roller coaster

The actual pitch-to-rail and point-cart experiment featured in the published short. The raw crest loses contact; smoothing and a gentle descent let the cart finish. This is **not** the later proposed “find the sound that launches furthest” experiment.

## Run

Python 3.11 or 3.12 recommended. From this folder:

```sh
python -m pip install -r requirements.txt
python run.py
python render.py
```

`run.py` produces `output/metrics.json` quickly. `render.py` requires FFmpeg on PATH and renders the two published comparison tracks to `output/result-fail-clean.mp4` and `output/result-pass-clean.mp4` at 1080×1200, 60 fps. It uses the numeric published pitch fixture. No private server, API key, paid voice service, font download or GPU is required.

## Try your own voice

```sh
python extract_pitch.py my-voice.wav --output output/my-pitch.json
python run.py --pitch output/my-pitch.json
```

pYIN measures pitch between 55 and 350 Hz from the actual supplied recording. Gaps in voiced estimates are linearly interpolated, then pitch is smoothed, resampled to 500 points and normalized into a 10-unit track. A flat pitch or unvoiced input is rejected. The custom-input command computes metrics; the supplied video renderer deliberately reproduces the published fixture. Custom recordings need not produce a finish with the fixed comparison parameters.

## Model and limitations

The cart rests **on top** of a rail. Its speed is approximated from gravitational energy minus friction; the normal acceleration test detects loss of contact. After release, the cart follows gravity; on its first subsequent rail crossing it reattaches inelastically, retaining tangential momentum. This is the final revised solver used in the video, including that recontact fix.

The raw parameters are amplitude 1.7, descent 0, smoothing 8. Comparison parameters are amplitude 1.0, descent 0.04, smoothing 16. Initial speed is 1.1, gravity 9.81, friction coefficient 0.015. Geometry is sampled in 500 points. The published time estimate sums horizontal `dx / speed`, rather than a full constrained dynamics integrator. Recontact is a simplified one-time constraint (not repeated lift-off). This preserves the video experiment, with its limitations, rather than silently replacing the model. It is not a safety model of a real captured-wheel coaster.

For the published fixture: raw contact loss at x≈4.72946, t≈3.76636; recontact ≈0.53333 seconds later. The smoothed rail reaches x=10 at t≈3.93980. The pass video adds one second before departure. Camera zoom does not change simulation time.

## Assets and licensing

`assets/published-pitch.json` contains measured numeric pitch values and selected settings used for the short. The original hosted George narration/voice recording is intentionally not redistributed: voice-provider redistribution terms were not established here. You can supply your own authorized recording; there is no synthetic audio pretending to be the published voice.

Adapted project code and numeric experiment data are released under the repository GPL-3.0 license. Dependencies are installed separately: NumPy/SciPy (BSD), librosa (ISC), SoundFile (BSD), Pillow (HPND); see the upstream projects for their full licenses. FFmpeg is a separate system executable with license conditions depending on its build.
