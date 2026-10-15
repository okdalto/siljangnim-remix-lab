# 03 · City buildings become a pinball board

OpenStreetMap building footprints around Seoul City Hall become collision segments in Pymunk. Three balls, automatic kinematic flippers, gravity, restitution, and a speed cap create an authored arcade experiment. This is not a traffic model or an energy-conserving physics demonstration.

## Run locally

Python 3.10+ and FFmpeg on your PATH are required. No API key, network request, or image-generation service is used.

```sh
python3 -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
python -m pip install -r requirements.txt
python build.py
```

Run these commands inside this project directory. Open `preview.mp4` (14 seconds, 720×1280 at 30 fps). `simulation.json` contains every trajectory and building collision. `qa.json` reports building count and contacts. The same recorded simulation is used in short 03; title text is English here for portable fonts. No custom font download is required.

## Map data and attribution

© OpenStreetMap contributors. Map data is available under the [Open Data Commons Open Database License (ODbL) 1.0](https://opendatacommons.org/licenses/odbl/1-0/). [OpenStreetMap copyright and attribution](https://www.openstreetmap.org/copyright).

`map.json` is the derived geometry snapshot used by the short. Source: `https://api.openstreetmap.org/api/0.6/map?bbox=126.9758,37.5645,126.9802,37.5680`. The exact fetch timestamp was not recorded. The extraction keeps way IDs, tags and ordered longitude/latitude geometry. It is redistributed as ODbL data, separately from repository source code. Preserve attribution and the ODbL notice when redistributing the map or adapted database. Rendered previews display attribution at the bottom; retain it if you crop/share them.

Dependencies are installed separately: [Pymunk](https://github.com/viblo/pymunk) and [Pillow](https://github.com/python-pillow/Pillow). Their own licenses apply.
