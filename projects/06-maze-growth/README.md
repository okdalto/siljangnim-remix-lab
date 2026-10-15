# 06 · Branches explore a maze

A seeded depth-first maze generator creates the walls. An authored branching rule expands into all open, unvisited neighbouring cells. Branches stop at dead ends; no route to the exit is supplied to growth. Only after reaching the exit is its successful route reconstructed and highlighted. This is a discrete illustration, not botanical simulation, AI training, or evidence of biological intelligence.

## Run locally

Python 3.10+ and FFmpeg on your PATH are required. No API key, network request, or image-generation service is used.

```sh
python3 -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
python -m pip install -r requirements.txt
python build.py
python render_exit.py
```

Run inside this directory. `preview.mp4` shows the 13-second growth animation. `exit-clean.mp4` recreates the latest six-second continuation used by short 06, beginning at 88% of the recorded growth steps and revealing the path after arrival. `simulation.json` records the actual graph, edges, arrival step and path; `qa.json` verifies growth never crosses a wall. Display time compresses many discrete growth steps; no physical time scale is claimed.

Change `random.Random(23)` in `build.py` to try other mazes. Keep dimensions and start/goal coordinates synchronized if you edit grid size. Titles in this portable rendering are English; geometry and growth are unchanged. Pillow's bundled fallback font is used when DejaVu Sans is unavailable.

[Pillow](https://github.com/python-pillow/Pillow) is installed separately under its own license. Inputs are procedural; no external asset is required.
