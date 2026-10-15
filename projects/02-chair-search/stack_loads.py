"""Increasing-load chair experiment. Deterministic 120 Hz Pymunk; no strength model."""
import json,math,subprocess
from pathlib import Path
import pymunk
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent
FPS=30
SCHEDULE=[{'time':.5+1.5*i,'mass':15*(i+1),'x':400+6*i,'y':630-65*i,'size':[100,62]} for i in range(6)]
def simulate(spread,bias=0):
 s=pymunk.Space();s.gravity=(0,1100);s.iterations=60
 floor=pymunk.Segment(s.static_body,(-1000,960),(1600,960),8);floor.friction=.9;s.add(floor)
 b=pymunk.Body();b.position=(340,710);s.add(b)
 polys=[[(-110,-12),(110,-12),(110,12),(-110,12)],[(-106,-150),(-88,-150),(-88,0),(-106,0)]]
 for x,end in [(-85,bias-spread),(85,bias+spread)]:polys.append([(x-10,0),(x+10,0),(end+10,235),(end-10,235)])
 for poly in polys:
  sh=pymunk.Poly(b,poly);sh.density=.0008;sh.friction=.9;s.add(sh)
 loads=[];states=[];first_tip=None
 for step in range(2400):
  for item in SCHEDULE:
   if step==round(item['time']*120):
    mass=item['mass'];body=pymunk.Body(mass,pymunk.moment_for_box(mass,item['size']));body.position=(item['x'],item['y']);sh=pymunk.Poly.create_box(body,item['size']);sh.friction=1.;s.add(body,sh);loads.append(body)
  s.step(1/120)
  if abs(b.angle)>.3 and first_tip is None:first_tip={'seconds':step/120,'box_count':len(loads)}
  if step%4==0:states.append({'chair':[b.position.x,b.position.y,b.angle],'loads':[[l.position.x,l.position.y,l.angle] for l in loads]})
 stable=abs(b.angle)<.1 and all(l.position.y<710 for l in loads)
 return {'spread':spread,'bias':bias,'chair_mass':b.mass,'tilt_degrees':math.degrees(b.angle),'stable':stable,'first_tip':first_tip,'retained':sum(l.position.y<710 for l in loads),'polygons':polys,'states':states}
def xy(points,pose):
 x,y,a=pose;c=math.cos(a);sn=math.sin(a)
 return [(x+px*c-py*sn,y+px*sn+py*c) for px,py in points]
def frame(trial,index):
 im=Image.new('RGB',(720,1280),'#0c1119');d=ImageDraw.Draw(im);st=trial['states'][index]
 d.line((30,963,690,963),fill='#445162',width=8)
 for poly in trial['polygons']:d.polygon(xy(poly,st['chair']),fill='#d7a76a',outline='#efcd9c',width=3)
 colors=['#65dcca','#79b4f0','#b4a5e9','#e8c974','#e99783','#e8edf4']
 font=ImageFont.load_default(size=23)
 for i,pose in enumerate(st['loads']):
  d.polygon(xy([(-50,-31),(50,-31),(50,31),(-50,31)],pose),fill=colors[i],outline='#eff5fb',width=2)
  # Label drawn in the body's own coordinate frame, then rotated with it.
  tile=Image.new('RGBA',(100,62));td=ImageDraw.Draw(tile);td.text((50,31),f'{i+1}x',font=font,fill='#15212d',anchor='mm')
  tile=tile.rotate(-math.degrees(pose[2]),resample=Image.Resampling.BICUBIC,expand=True)
  im.paste(tile,(round(pose[0]-tile.width/2),round(pose[1]-tile.height/2)),tile)
 return im
def render(trial,dest):
 p=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pixel_format','rgb24','-video_size','720x1280','-framerate',str(FPS),'-i','-','-an','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(dest)],stdin=subprocess.PIPE)
 for i in range(len(trial['states'])):p.stdin.write(frame(trial,i).tobytes())
 p.stdin.close();assert p.wait()==0

def main():
 trials=[simulate(sp,bias) for sp in [40,70,100,130,160,190] for bias in [-25,0,25]]
 baseline=next(t for t in trials if t['spread']==40 and t['bias']==0)
 winner=min((t for t in trials if t['stable']),key=lambda t:(t['spread'],abs(t['tilt_degrees']),abs(t['bias'])))
 summary=lambda t:{k:v for k,v in t.items() if k not in ['polygons','states']}
 report={'schedule':SCHEDULE,'duration':20,'fps':FPS,'physics_hz':120,'evaluations':len(trials),'baseline':summary(baseline),'winner':summary(winner),'total_load_mass':315,'limitations':'Rigid 2D contact only; no bending, fracture, 3D stability or real-world safety claim.'}
 (R/'stack-metrics.json').write_text(json.dumps(report,indent=2));(R/'stack-search.json').write_text(json.dumps(trials))
 for name,tr in [('failure',baseline),('result',winner)]:
  (R/f'stack-{name}-trajectory.json').write_text(json.dumps(tr));render(tr,R/f'stack-{name}.mp4')
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()
