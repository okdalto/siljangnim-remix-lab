# 07 · Desk objects meet row-clearing rules

The included transparent sprite sheet supplies the actual pixels. Original alpha produces object silhouettes with holes, occupied 22-pixel cells approximate collision, and an exhaustive rotation/column search chooses a placement. Full rows remove both occupancy and the corresponding texture tiles. This is a Tetris-inspired authored packing demo, not an official Tetris product.

## Run locally

Python 3.10+ and FFmpeg on your PATH are required. No API key, network request, or image-generation service is used.

```sh
python3 -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
python -m pip install -r requirements.txt
python make.py
# Fast simulation without encoding video:
python make.py --simulate-only
```

Run inside this directory. Open `preview.mp4` (15 seconds, 720×1280 at 30 fps). `metrics.json` records each placement, rotation and cleared row. `object-*.png` and `mask-*.png` are derived from the original RGBA sprite sheet. The default selected sequence places 12 objects and clears 7 rows, matching short 07. It does not prove the heuristic handles arbitrary sequences.

Experiment with `--board-width 24 --sequence 0,1,2,3,4,5,0,1,2,3,4,5`. `--cols` and `--rows` describe the sprite-sheet layout (default 2×3), not board dimensions. Very narrow boards may have no legal placements; use `--simulate-only` to inspect such cases first.

## Asset provenance

`assets.png` is the original generated photo-style RGBA sprite sheet used in the short. It is not a camera photograph. Its alpha is preserved without flattening. No generation API or original request/configuration files are included or needed. See `ASSET_PROVENANCE.json` for the SHA-256 fingerprint. This asset is not an upstream open-source project's artwork; repository code licensing should not be read as a claim about copyright protection or third-party model/service terms for generated output.

Dependencies are installed separately: [NumPy](https://github.com/numpy/numpy), [OpenCV](https://github.com/opencv/opencv), and [Pillow](https://github.com/python-pillow/Pillow), each under its own license. Small visible gaps can remain because cell collision is coarser than RGBA texture.
