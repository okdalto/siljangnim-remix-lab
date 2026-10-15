"""Extract pitch from your own recording; never requires a hosted voice service."""
import argparse, json
from pathlib import Path
import librosa, numpy as np
p=argparse.ArgumentParser();p.add_argument('audio');p.add_argument('--output',default='output/my-pitch.json');a=p.parse_args()
y,sr=librosa.load(a.audio,sr=22050)
f0,voiced,prob=librosa.pyin(y,fmin=55,fmax=350,sr=sr,frame_length=1024,hop_length=128)
ok=np.isfinite(f0)
if ok.sum()<2: raise SystemExit('Not enough voiced frames in the 55–350 Hz range. Try a lower voice or hum.')
f0=np.interp(np.arange(len(f0)),np.where(ok)[0],f0[ok]);out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps({'pitch_hz':f0.tolist(),'voiced_fraction':float(ok.mean())},indent=2));print(out)
