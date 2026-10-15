from physics import *
from PIL import Image,ImageDraw,ImageFont
import subprocess
plan=None
P = P/'output'; P.mkdir(exist_ok=True)
font=lambda n:ImageFont.load_default(size=n)
def word(s,i,w,default):
 try:
  c=s['captions'][i]
  return next((a['start'] for a in c.get('words',[]) if w.lower() in a['word'].lower()),c['start'])
 except:return default
def smooth(q):q=np.clip(q,0,1);return q*q*(3-2*q)
qa={}
for name,r in [('result-fail',raw),('result-pass',good)]:
 shot=next((s for s in (plan['shots'] if isinstance(plan,dict) else plan) if s['id']==name),{}) if plan else {};dur=shot.get('seconds',7);fail=name.endswith('fail');z,slope,v,n,stop,ts=r
 begin=0.0 if fail else 1.0
 release=begin+ts[stop]
 proc=subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s','1080x1200','-r','60','-i','-','-an','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(P/(name+'-clean.mp4'))],stdin=subprocess.PIPE)
 for f in range(int(np.ceil(dur*60))):
  t=f/60;im=Image.new('RGB',(1080,1200),'#10151b');dr=ImageDraw.Draw(im)
  # Zoom into the actual release region before it happens; same feature remains visible.
  zoom=smooth((t-.4)/max(.1,release-.6)) if fail else 0
  scale=82+zoom*65;center=5*(1-zoom)+(x[stop]+.45)*zoom
  follow=0
  if fail and t>release+.45:
   dt=t-release;bx=np.interp(dt,ballistic[:,0],ballistic[:,1]);ball=np.interp(dt,ballistic[:,0],ballistic[:,2]);follow=max(0,640-ball*scale-860);center=max(center,bx-1)
  def screen(xx,zz):return (540+(xx-center)*scale,640-zz*scale-follow)
  coords=[screen(xx,zz) for xx,zz in zip(x,z)]
  for j in range(0,500,35):a=coords[j];dr.line((a[0],a[1]+10,a[0],1100),fill='#26313b',width=4)
  if not fail:
   old=[screen(xx,zz) for xx,zz in zip(x,raw[0])];dr.line(old,fill='#35434e',width=4)
  dr.line(coords,fill='#f68dab' if fail else '#87eecc',width=11)
  elapsed=max(0,t-begin);idx=min(stop,np.searchsorted(ts,elapsed));cx,cz=x[idx],z[idx]
  if fail and t>release:
   # Render the measured arc at one simulation second per screen second.
   dt=t-release;cx=np.interp(dt,ballistic[:,0],ballistic[:,1]);cz=np.interp(dt,ballistic[:,0],ballistic[:,2])
   trace=[screen(row[1],row[2]) for row in ballistic[::4] if row[0]<=min(dt,impacts[0]['seconds_after_loss'] if impacts else dt)];
   if len(trace)>1:dr.line(trace,fill='#f4f5f6',width=6)
   a=screen(x[stop],z[stop]);dr.ellipse((a[0]-22,a[1]-22,a[0]+22,a[1]+22),outline='#f68dab',width=5)
   if t>release+.20:dr.text((540,300),'CONTACT LOST.',font=font(64),fill='#f68dab',anchor='mm')
  px,py=screen(cx,cz)
  # Resting cart body with visible wheels above the contact point; no enclosing wheels.
  dr.rounded_rectangle((px-39,py-65,px+39,py-23),radius=12,fill='#f4f5f6');dr.ellipse((px-31,py-27,px-9,py-5),fill='#83b9f1');dr.ellipse((px+9,py-27,px+31,py-5),fill='#83b9f1')
  if not fail:
   ex,ey=screen(10,z[-1]);dr.line((ex,ey-10,ex,ey-150),fill='white',width=6)
   for iy in range(3):
    for ix in range(3):dr.rectangle((ex+ix*17,ey-150+iy*17,ex+(ix+1)*17,ey-133+iy*17),fill='white' if (ix+iy)%2==0 else '#35434e')
   if t>=release:dr.text((540,300),'MADE IT.',font=font(64),fill='#87eecc',anchor='mm')
  proc.stdin.write(im.tobytes())
 proc.stdin.close();assert proc.wait()==0
 qa[name]={'duration':dur,'release_or_finish_cue':release,'contact_index':stop,'contact_x':float(x[stop]),'normal_at_event':float(n[stop]),'end_state':'lost contact then inelastic recontact' if fail else 'finish'}
(P/'result-physics.json').write_text(json.dumps({'runs':qa,'recontact_events':impacts,'input':'same published numeric pitch fixture for both rails','model':'energy-derived speed, curvature contact test, ballistic continuation, inelastic rail recontact conserving tangential velocity','presentation':'fixed 1 simulation second per screen second; pass has 1 second lead-in; camera zoom only; raw sigma 8 removes tiny numerical wiggles while preserving the pitch crest'},indent=2))
