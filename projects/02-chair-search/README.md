# How much can this chair carry? / 짐을 계속 쌓으면 의자는 버틸까?

## Current published experiment: increasing loads

Run `python stack_loads.py`. Pymunk simulates 18 foot-position designs with the **same six falling boxes**, at the same locations and times. Each successive box has mass 15, 30, 45, 60, 75, then 90 simulation units. The seat geometry and chair mass stay unchanged; only leg-foot geometry changes. The boxes are identical in size and their `1x`–`6x` labels describe relative mass, not physical size.

The narrow baseline (spread 40, bias 0) reaches a 0.3 radian tilt at 4.125 s, with the third box present. The selected design (spread 70, bias 25) retains all six for the entire 20 s run. Total box mass is 315 versus chair mass 13.904, over 22 times as much. Selection chooses the narrowest stable design among the tested candidates; it does not establish a global optimum.

Outputs: `stack-metrics.json`, `stack-search.json`, `stack-failure-trajectory.json`, `stack-result-trajectory.json`, and two 20 s MP4s (`stack-failure.mp4`, `stack-result.mp4`). Simulation uses 120 Hz and renders at 30 fps, exactly 1 simulation second per video second. Both cameras are identical. Last frames remain live simulation rather than an artificial freeze.

**Limit:** this rigid 2D model cannot bend or break, and does not represent 3D stability or furniture safety. The result concerns tipping and retention only. It is not a real load rating.

## Setup

Install Python 3.12 and FFmpeg, then `python -m pip install -r requirements.txt`. No keys, model downloads or service connection are needed. Pymunk is MIT-licensed, Pillow is HPND-licensed, and FFmpeg is an external dependency whose license depends on the installed build. Renderer labels use Pillow's bundled font. Recorded numeric results may vary slightly between platforms.

## Previous version

`run.py` and `clean_results.py` preserve the original two-load, 21-design experiment for comparison. They are not the latest Short source. Use `stack_loads.py` for the increasing-load episode.
