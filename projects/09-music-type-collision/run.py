from pathlib import Path
import numpy as np,cv2,json,subprocess,math
import pymunk
from PIL import Image,ImageDraw,ImageFont
import argparse
args=argparse.ArgumentParser();args.add_argument('--render',action='store_true');args=args.parse_args()
root=Path(__file__).resolve().parent;p=root/'output';p.mkdir(exist_ok=True);src=root/'assets';features=json.loads((src/'features.json').read_text());orig=Image.open(src/'handwriting.png').convert('L');colors=['#83b9f1','#f1ef78','#7ee5bb'];space=pymunk.Space();space.gravity=(0,420);space.damping=.96
bodies=[];sprites=[];springs=[];anchors=[(360,360),(360,640),(360,920)];collisions=[]
for k,(x0,x1) in enumerate([(120,370),(410,545),(620,825)]):
 mask=orig.crop((x0,60,x1,320));mask=mask.resize((int(mask.width*.9),234));alpha=Image.eval(mask,lambda x:255-x);sp=Image.new('RGBA',mask.size,colors[k]);sp.putalpha(alpha);sprites.append(sp)
 arr=np.array(alpha);cs,_=cv2.findContours((arr>100).astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE);hull=cv2.convexHull(np.concatenate(cs)).reshape(-1,2);vs=[(float(x-mask.width/2),float(y-mask.height/2)) for x,y in hull];mass=2;body=pymunk.Body(mass,pymunk.moment_for_poly(mass,vs));body.position=anchors[k];shape=pymunk.Poly(body,vs);shape.elasticity=.82;shape.friction=.45;shape.collision_type=1;space.add(body,shape)
 spring=pymunk.DampedSpring(space.static_body,body,anchors[k],(0,0),0,75,9);space.add(spring);springs.append(spring);bodies.append(body)
for a,b in [((40,180),(680,180)),((40,1100),(680,1100)),((40,180),(40,1100)),((680,180),(680,1100))]:
 wall=pymunk.Segment(space.static_body,a,b,8);wall.elasticity=.8;wall.friction=.3;space.add(wall)
clock=[0]
def collision(arb,space,data):collisions.append({'t':clock[0],'impulse':float(arb.total_impulse.length)})
space.on_collision(1,1,post_solve=collision)
font=lambda n:ImageFont.load_default(size=n)
proc=None
if args.render:
 proc=subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s','720x1280','-r','30','-i','-','-an','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(p/'silent.mp4')],stdin=subprocess.PIPE)
impulses=[];states=[];last_fire=-1
for f in range(360):
 t=f/30;clock[0]=t;i=min(479,int(t*60));rise=max(0,features['drums'][i]-features['drums'][max(0,i-3)]) if t<8 else 0
 if rise>.12 and t-last_fire>.16:
  last_fire=t;power=min(1,rise)*14000
  for k,b in enumerate(bodies):b.apply_impulse_at_local_point(((1 if k==0 else -1 if k==2 else (-1 if len(impulses)%2 else 1)*.4)*power,-power*(.65 if k==0 else .95 if k==1 else .4)),(0,0));b.angular_velocity+=(k-1)*rise*3
  impulses.append({'t':t,'rise':rise,'impulse':power})
 for spring in springs:
  spring.stiffness=12 if t<8 else 100;spring.damping=3 if t<8 else 15
 for sub in range(4):
  for b in bodies:b.torque=b.moment*(-b.angular_velocity*(.7 if t<8 else 7)-b.angle*(.5 if t<8 else 24))
  space.step(1/120)
 # Physical angular friction, no manual position/angle animation.
 # torque is applied at each physics substep above.
 im=Image.new('RGB',(720,1280),'#10151b');d=ImageDraw.Draw(im);d.text((360,170),'MUSIC HITS.',font=font(56),fill='white',anchor='mt');d.text((360,240),'TYPE COLLIDES.',font=font(49),fill='white',anchor='mt')
 for k,(b,sp) in enumerate(zip(bodies,sprites)):
  rot=sp.rotate(-math.degrees(b.angle),resample=Image.Resampling.BICUBIC,expand=True);im.paste(rot,(round(b.position.x-rot.width/2),round(b.position.y-rot.height/2)),rot)
 if t>=8:d.text((360,1100),'THE SPRINGS BRING IT BACK.',font=font(29),fill='#aab5be',anchor='mt')
 states.append([{'x':b.position.x,'y':b.position.y,'angle':b.angle} for b in bodies])
 if proc:proc.stdin.write(im.tobytes())
if proc:
 proc.stdin.close();assert proc.wait()==0
 subprocess.run(['ffmpeg','-y','-v','error','-i',str(p/'silent.mp4'),'-i',str(src/'music.wav'),'-af','apad','-t','12','-c:v','copy','-c:a','aac','-movflags','+faststart',str(p/'preview.mp4')],check=True)
(p/'metrics.json').write_text(json.dumps({'beat_impulses':impulses,'letter_contact_frames':len(collisions),'collisions':collisions,'states':states},indent=2));(p/'provenance.json').write_text(json.dumps({'input':'existing authored MIX raster and actual Demucs/librosa features, unchanged','physics':'Pymunk 7.3.1 actual convex-hull rigid body collisions, restitution .82, gravity, damped positional springs, physical angular restoring torque','motion':'Measured drum RMS positive rises trigger impulses until source audio ends at8s; then solver settles naturally','generated_video':False},indent=2))
