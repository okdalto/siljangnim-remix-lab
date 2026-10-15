"""The published short's latest point-cart/contact/recontact model.
An educational approximation, not a real captured-wheel rollercoaster model.
"""
from pathlib import Path
import json
import numpy as np
from scipy.ndimage import gaussian_filter1d
P = Path(__file__).resolve().parent
m = json.loads((P/'assets/published-pitch.json').read_text())
def set_pitch(values):
 global pitch, x, h
 pitch = gaussian_filter1d(np.asarray(values, dtype=float), 2)
 x = np.linspace(0,10,500)
 h = np.interp(np.linspace(0,1,500), np.linspace(0,1,len(pitch)), pitch)
 if np.ptp(h) < 1e-6: raise ValueError('Pitch must vary to make a track')
 h = (h-h.min())/np.ptp(h); h -= h[0]
set_pitch(m['pitch_hz'])
def trial(amp,down,sigma):
 z=gaussian_filter1d(h,sigma)*amp-down*x;d=np.gradient(z,x);cur=np.gradient(d,x)/(1+d*d)**1.5;arc=np.r_[0,np.cumsum(np.sqrt(1+d[:-1]**2)*np.diff(x))];v2=1.1**2+2*9.81*(z[0]-z)-2*.015*9.81*arc;n=9.81/np.sqrt(1+d*d)+np.maximum(v2,0)*cur;bad=np.where((v2<=0)|(n<0))[0];stop=int(bad[0]) if len(bad) else 499;speed=np.sqrt(np.maximum(v2,.02));ts=np.r_[0,np.cumsum(np.diff(x)/np.maximum(speed[:-1],.1))];return z,d,speed,n,stop,ts
raw=trial(1.7,0,8);o=m['optimized'];good=trial(o['amplitude'],o['descent_m_per_m'],o['smoothing_samples'])
def continue_airborne(r,duration=12):
 z,slope,v,n,stop,ts=r;dt=1/240;xx=x[stop];zz=z[stop];vx=v[stop]/np.sqrt(1+slope[stop]**2);vz=vx*slope[stop];rows=[];impacts=[];attached=False
 for step in range(int(duration/dt)):
  tm=step*dt;rows.append((tm,xx,zz))
  if attached:
   sl=float(np.interp(xx,x,slope));speed=np.hypot(vx,vz);speed=max(0,speed+(-9.81*sl/np.sqrt(1+sl*sl)-.015*9.81)*dt);vx=speed/np.sqrt(1+sl*sl);vz=vx*sl
   xx+=vx*dt;zz=float(np.interp(xx,x,z))
  else:
   prev=zz-float(np.interp(xx,x,z));xx+=vx*dt;zz+=vz*dt-.5*9.81*dt*dt;vz-=9.81*dt;surface=float(np.interp(xx,x,z))
   if 0<xx<10 and prev>=0 and zz<=surface:
    # Inelastic recontact, tangent momentum retained; no fabricated passage through rail.
    sl=float(np.interp(xx,x,slope));tx=1/np.sqrt(1+sl*sl);tz=sl*tx;vt=max(0,vx*tx+vz*tz);vx=vt*tx;vz=vt*tz;zz=surface;attached=True;impacts.append({'seconds_after_loss':tm,'x':xx})
 return np.array(rows),impacts
ballistic,impacts=continue_airborne(raw)
