import json,math,subprocess
from pathlib import Path
import pymunk
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent
FONT=None
def simulate(spread,bias):
 s=pymunk.Space();s.gravity=(0,1100);s.iterations=30;s.damping=.995
 floor=pymunk.Segment(s.static_body,(-1000,960),(1600,960),8);floor.friction=.9;s.add(floor)
 b=pymunk.Body();b.position=(340,710);s.add(b)
 polys=[[(-110,-12),(110,-12),(110,12),(-110,12)],[(-106,-150),(-88,-150),(-88,0),(-106,0)]]
 for x,end in [(-85,bias-spread),(85,bias+spread)]:polys.append([(x-10,0),(x+10,0),(end+10,235),(end-10,235)])
 for poly in polys:
  sh=pymunk.Poly(b,poly);sh.density=.0008;sh.friction=.9;sh.elasticity=.02;s.add(sh)
 load=pymunk.Body(30,pymunk.moment_for_box(30,(110,110)));load.position=(420,480);sh=pymunk.Poly.create_box(load,(110,110));sh.friction=.85;sh.elasticity=.03;s.add(load,sh)
 states=[];load2=None
 for step in range(600):
  if step==300:
   load2=pymunk.Body(20,pymunk.moment_for_box(20,(90,90)));load2.position=(305,430);sh2=pymunk.Poly.create_box(load2,(90,90));sh2.friction=.85;s.add(load2,sh2)
  s.step(1/120)
  if step%4==0:states.append({'chair':[b.position.x,b.position.y,b.angle],'load':[load.position.x,load.position.y,load.angle],'load2':None if load2 is None else [load2.position.x,load2.position.y,load2.angle]})
 angle=abs(b.angle);score=angle*100+max(0,load.position.y-720)*.2+max(0,load2.position.y-720)*.2+spread*.001
 return {'spread':spread,'bias':bias,'score':score,'tilt_degrees':math.degrees(angle),'load_y':load.position.y,'load2_y':load2.position.y,'stable':angle<.1 and load.position.y<720 and load2.position.y<720,'polygons':polys,'states':states}
trials=[simulate(spread,bias) for spread in [12,40,70,100,130,160,190] for bias in [-25,0,25]]
initial=trials[1];best=min(trials,key=lambda t:t['score']);(R/'search.json').write_text(json.dumps(trials));(R/'metrics.json').write_text(json.dumps({'initial':{k:v for k,v in initial.items() if k not in ['states','polygons']},'best':{k:v for k,v in best.items() if k not in ['states','polygons']},'evaluations':len(trials)},indent=2));print((R/'metrics.json').read_text())
def xy(points,pose):
 x,y,a=pose;c=math.cos(a);s=math.sin(a);return [(x+px*c-py*s,y+px*s+py*c) for px,py in points]
def draw(trial,frame,title,sub):
 im=Image.new('RGB',(720,1280),'#0c1119');d=ImageDraw.Draw(im)
 d.multiline_text((360,190),title,font=ImageFont.load_default(size=48),fill='white',anchor='ma',align='center',spacing=12)
 d.rounded_rectangle((50,963,670,982),radius=8,fill='#445162');st=trial['states'][min(frame,149)]
 for p in trial['polygons']:d.polygon(xy(p,st['chair']),fill='#d7a76a',outline='#efcd9c',width=3)
 d.polygon(xy([(-55,-55),(55,-55),(55,55),(-55,55)],st['load']),fill='#65dcca',outline='#c7fff3',width=4)
 if st['load2'] is not None:d.polygon(xy([(-45,-45),(45,-45),(45,45),(-45,45)],st['load2']),fill='#79b4f0',outline='#dceeff',width=4)
 d.text((360,1080),f"TILT: {abs(math.degrees(st['chair'][2])):.0f}°",font=ImageFont.load_default(size=44),fill='#e6eaf0',anchor='mm')
 return im
out=subprocess.Popen(['ffmpeg','-y','-f','rawvideo','-pix_fmt','rgb24','-s','720x1280','-r','30','-i','-','-an','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(R/'preview.mp4'),'-loglevel','error'],stdin=subprocess.PIPE)
for f in range(390):
 t=f/30
 if t<5:im=draw(initial,f,'SAME CHAIR.\nSAME LOAD.','The narrow base tips over.')
 elif t<7:
  i=min(20,int((t-5)/2*21));tr=trials[i];im=draw(tr,149,f'TEST {i+1:02d} / 21','Search foot position and leg angle')
 else:im=draw(best,int((t-7)*30),'CHANGE ONLY\nTHE LEGS.','The load stays on the seat.')
 out.stdin.write(im.tobytes())
out.stdin.close();assert out.wait()==0
