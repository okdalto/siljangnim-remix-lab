"""Remeasure the included separated drums, or your own isolated drum recording."""
from pathlib import Path
import argparse,json,librosa,numpy as np
p=argparse.ArgumentParser();p.add_argument('--audio',default=str(Path(__file__).resolve().parent/'assets/drums.wav'));p.add_argument('--output',default='output/features.json');a=p.parse_args()
y,sr=librosa.load(a.audio,sr=22050);rms=librosa.feature.rms(y=y,hop_length=256)[0];times=librosa.frames_to_time(np.arange(len(rms)),sr=sr,hop_length=256)
vals=np.interp(np.arange(480)/60,times,rms);vals/=max(np.percentile(vals,95),1e-6)
out=Path(a.output);out.parent.mkdir(exist_ok=True,parents=True);out.write_text(json.dumps({'drums':np.minimum(vals,1.4).round(5).tolist(),'fps':60}));print(out)
