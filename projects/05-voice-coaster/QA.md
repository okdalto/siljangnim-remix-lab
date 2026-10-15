# Verification

- Ran published fixture with Python 3.12 scientific environment: raw contact loss 3.7663609015s; first recontact 0.5333333333s later; improved track finishes at 3.9397998551s.
- Rendered both full 7-second 1080×1200 60fps comparisons using portable Pillow font; both MP4 files fully decoded with FFmpeg without errors.
- Generated a separate test hum (150±30Hz), extracted pYIN pitch from actual audio, and ran the custom fixture; both configured tracks correctly reported stall for that new input. This test hum is an ignored output, not the original voice.
- Scanned distributable code/data/docs for private absolute paths and service addresses; none found.
- Original source model intentionally preserved, including approximate timing and one-time reattachment limitations described in README.
