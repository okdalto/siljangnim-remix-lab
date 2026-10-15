"""Actual pitch-edited voice -> rail -> constrained cart -> ballistic landing.
No trained voice model is distributed. --source accepts an authorized recording.
"""
from pathlib import Path
import argparse,json,subprocess
import numpy as np,librosa,soundfile as sf
from scipy.ndimage import gaussian_filter1d
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent

def measure(y,sr):
 f,_,_=librosa.pyin(y,sr=sr,fmin=50,fmax=900,frame_length=1024,hop_length=128)
 ok=np.isfinite(f)
 if ok.sum()<5:raise ValueError('Need pitched voice')
 return np.interp(np.arange(len(f)),np.where(ok)[0],f[ok])
def edit(y,sr,shift):
 # Overlapping fixed-pitch blocks, weighted crossfade; pitch rises progressively.
 size=4096;hop=1024;pad=np.pad(y,(size,size));out=np.zeros(len(pad));weight=np.zeros(len(pad));w=np.hanning(size)
 for pos in range(0,len(pad)-size,hop):
  q=np.clip((pos+size/2-size)/len(y),0,1)
  block=librosa.effects.pitch_shift(pad[pos:pos+size],sr=sr,n_steps=shift*q)
  out[pos:pos+size]+=block*w;weight[pos:pos+size]+=w
 return (out/np.maximum(weight,1e-8))[size:size+len(y)]
def model(pitch,ref):
 x=np.linspace(0,8,400);semi=12*np.log2(pitch/ref)
 z=5-.30*x+.20*np.interp(x/8,np.linspace(0,1,len(semi)),gaussian_filter1d(semi,3))
 # fixed ground level and fixed initial speed; rail constrains cart until its end
 tail=np.polyval(np.polyfit(x[-150:],z[-150:],1),x[-150:]);blend=np.clip(np.arange(150)/45,0,1);blend=blend*blend*(3-2*blend);z[-150:]=z[-150:]*(1-blend)+tail*blend;slope=np.gradient(z,x);arc=np.r_[0,np.cumsum(np.sqrt(1+slope[:-1]**2)*np.diff(x))]
 energy=8**2+2*9.81*(z[0]-z)-2*.015*9.81*arc
 if energy.min()<=0 or z[-1]<=0:return None
 speed=np.sqrt(energy);m=float(slope[-1]);theta=np.arctan(m);vx=speed[-1]*np.cos(theta);vy=speed[-1]*np.sin(theta)
 flight=(vy+np.sqrt(vy*vy+2*9.81*z[-1]))/9.81;distance=vx*flight
 times=np.r_[0,np.cumsum(np.diff(arc)/((speed[1:]+speed[:-1])/2))]
 return dict(x=x.tolist(),z=z.tolist(),times=times.tolist(),vx=float(vx),vy=float(vy),flight=float(flight),distance_m=float(distance),angle_degrees=float(np.degrees(theta)))
def render(run,audio,sr,path,limit):
 W,H=1080,1200;fps=60;duration=12
 font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf',60) if Path('/System/Library/Fonts/Supplemental/Arial Bold.ttf').exists() else ImageFont.load_default(size=60)
 proc=subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(fps),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p',str(path.with_suffix('.silent.mp4'))],stdin=subprocess.PIPE)
 x=np.array(run['x']);z=np.array(run['z']);times=np.array(run['times']);scale=880/(8+limit);ground=980
 xy=lambda a,b:(100+a*scale,ground-b*105)
 for frame in range(duration*fps):
  t=frame/fps;im=Image.new('RGB',(W,H),'#10151b');d=ImageDraw.Draw(im);d.line((70,ground,1010,ground),fill='#35434e',width=5)
  pts=[xy(a,b) for a,b in zip(x,z)];d.line(pts,fill='#87eecc',width=12)
  for i in range(0,len(x),55):d.line((*pts[i],pts[i][0],ground),fill='#35434e',width=4)
  # 1s introduction, true-time ride and flight, then landed result stays readable.
  u=max(0,t-1)
  if u<times[-1]:cx=np.interp(u,times,x);cz=np.interp(u,times,z)
  else:
   f=min(run['flight'],u-times[-1]);cx=8+run['vx']*f;cz=max(0,z[-1]+run['vy']*f-4.905*f*f)
   trace=np.linspace(0,f,70);d.line([xy(8+run['vx']*v,z[-1]+run['vy']*v-4.905*v*v) for v in trace],fill='#83b9f1',width=5)
  px,py=xy(cx,cz);d.rounded_rectangle((px-28,py-46,px+28,py-10),8,fill='white');d.ellipse((px-24,py-14,px-8,py+2),fill='#f68dab');d.ellipse((px+8,py-14,px+24,py+2),fill='#f68dab')
  if u>=times[-1]+run['flight']:d.text((540,55),f"{run['distance_m']:.1f} m",font=font,anchor='mt',fill='white')
  proc.stdin.write(im.tobytes())
 proc.stdin.close();assert proc.wait()==0
 # Separate source audio used by final editor, zero padded clip audio available too.
 padded=np.zeros(sr*duration);padded[:len(audio)]=audio;wav=path.with_suffix('.embedded.wav');sf.write(wav,padded,sr)
 subprocess.run(['ffmpeg','-y','-v','error','-i',str(path.with_suffix('.silent.mp4')),'-i',str(wav),'-c:v','copy','-c:a','aac','-shortest','-movflags','+faststart',str(path)],check=True)
 path.with_suffix('.silent.mp4').unlink()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path);ap.add_argument('--output',type=Path,default=P/'launch-output');ap.add_argument('--render',action='store_true');a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=True);sr=22050
 if a.source:y,_=librosa.load(a.source,sr=sr)
 else:
  t=np.arange(int(1.3*sr))/sr;f=145+12*np.sin(t*5);phase=2*np.pi*np.cumsum(f)/sr;y=(np.sin(phase)+.35*np.sin(2*phase)+.15*np.sin(3*phase))*np.sin(np.pi*t/t[-1])**.5*.3
 pitch=measure(y,sr);ref=float(np.median(pitch));trials=[];runs=[]
 for shift in [0,6,12,18,24,30]:
  edited=y if shift==0 else edit(y,sr,shift);measured=measure(edited,sr);r=model(measured,ref)
  if r:r.update(shift_semitones=shift,pitch_hz=measured.tolist());trials.append({'shift_semitones':shift,'distance_m':r['distance_m'],'angle_degrees':r['angle_degrees']});runs.append((r,edited))
 raw=runs[0];best=max(runs,key=lambda a:a[0]['distance_m']);report={'input':a.source.name if a.source else 'authored harmonic vowel','method':'actual overlapping pitch shifts, remeasured with librosa pYIN; attached cart until open rail end; fixed initial speed 8m/s and gravity 9.81; same pitch-height mapping for all candidates','trials':trials,'original':raw[0],'optimized':best[0]};(a.output/'metrics.json').write_text(json.dumps(report,indent=2));sf.write(a.output/'original.wav',raw[1],sr);sf.write(a.output/'optimized.wav',best[1],sr)
 if a.render:
  limit=max(raw[0]['distance_m'],best[0]['distance_m'])+1
  for name,(run,audio) in [('original',raw),('optimized',best)]:render(run,audio,sr,a.output/f'{name}.mp4',limit)
 print(json.dumps({'trials':trials,'best':best[0]['shift_semitones']}))
if __name__=='__main__':main()
