from pathlib import Path
import numpy as np, soundfile as sf
p=Path(__file__).resolve().parent/'output';p.mkdir(exist_ok=True); sr=44100; n=sr*8;t=np.arange(n)/sr;rng=np.random.default_rng(40)
dr=np.zeros(n);ba=np.zeros(n);mel=np.zeros(n)
for beat in np.arange(0,8,.5):
 q=t-beat;env=np.exp(-np.maximum(q,0)*18)*(q>=0);dr+=.55*np.sin(2*np.pi*(48*q+3*(1-np.exp(-np.maximum(q,0)*30))))*env
for beat in np.arange(.25,8,.5):
 q=t-beat;dr+=.18*rng.normal(size=n)*np.exp(-np.maximum(q,0)*45)*(q>=0)
for i,beat in enumerate(np.arange(0,8,.5)):
 q=t-beat;f=[55,55,65.4,73.4,55,82.4,73.4,65.4][i%8];ba+=.3*np.sin(2*np.pi*f*q)*np.minimum(np.maximum(q,0)*80,1)*np.exp(-np.maximum(q,0)*5)*(q>=0)
for i,beat in enumerate(np.arange(.25,8,.5)):
 q=t-beat;f=[440,523.25,659.25,783.99][i%4];mel+=.13*(np.sin(2*np.pi*f*q)+.35*np.sin(4*np.pi*f*q))*np.exp(-np.maximum(q,0)*6)*(q>=0)
y=dr+ba+mel;y/=max(1,np.max(abs(y)));sf.write(p/'original-mix.wav',np.stack([y,y],axis=1),sr)
