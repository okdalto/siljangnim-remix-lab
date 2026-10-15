# Verification

- Ran Pymunk 7.3.1 simulation and compared every generated metric to the published experiment's JSON: exact match, including 116 contacts and all 360 frames of body positions/angles.
- Re-extracted librosa RMS from the included Demucs drum stem: exact match of all 480 original drum feature values.
- Regenerated music using make_music.py and compared decoded audio samples: exact equality to the published authored mix.
- Scanned distributable code/data/docs for private absolute paths and service addresses; none found.
- The standalone WebGL viewer adapts the original Three.js final scene (same extrusion, scale, colors, lights and physics transforms), removing only the Siljangnim framebuffer wrapper. Browser loading requires access to esm.sh.
