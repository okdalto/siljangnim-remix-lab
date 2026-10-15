"""Actual OSM building contours become Pymunk collision boundaries."""
from pathlib import Path
import json,math,subprocess,collections
import pymunk
from PIL import Image,ImageDraw,ImageFont
D=Path(__file__).resolve().parent;data=json.loads((D/'map.json').read_text());W,H=720,1280
lon0,lat0=126.978,37.56625
scale=620/(.0044*math.cos(math.radians(lat0)))
def pt(p):return (360+(p['lon']-lon0)*math.cos(math.radians(lat0))*scale,550-(p['lat']-lat0)*scale)
buildings=[];roads=[]
for e in data['elements']:
 pts=[pt(p) for p in e['geometry']]
 if 'building' in e['tags'] and len(pts)>3 and all(-100<x<820 and 70<y<1000 for x,y in pts):buildings.append({'id':e['id'],'points':pts,'name':e['tags'].get('name','')})
 elif 'highway' in e['tags']:roads.append(pts)
space=pymunk.Space();space.gravity=(0,180);space.damping=.995
shape_index={};hits=collections.Counter();last_hit={};events=[]
for i,b in enumerate(buildings):
 for a,z in zip(b['points'],b['points'][1:]):
  if math.dist(a,z)<.1:continue
  seg=pymunk.Segment(space.static_body,a,z,2);seg.elasticity=1.03;seg.friction=.04;seg.collision_type=2;space.add(seg);shape_index[id(seg)]=i
for a,b in [((34,160),(686,160)),((34,160),(34,1100)),((686,160),(686,1100)),((34,1100),(686,1100))]:
 s=pymunk.Segment(space.static_body,a,b,8);s.elasticity=.9;space.add(s)
flippers=[]
for x,sign in [(235,1),(485,-1)]:
 b=pymunk.Body(body_type=pymunk.Body.KINEMATIC);b.position=(x,1000)
 s=pymunk.Segment(b,(0,0),(sign*110,0),15);s.elasticity=1.1;s.friction=.1;space.add(b,s);flippers.append((b,s,sign))
time_now=0
ball_contacts=0
def hit(arbiter,sp,data):
 global ball_contacts
 for shape in arbiter.shapes:
  idx=shape_index.get(id(shape))
  if idx is not None:
   hits[idx]+=1;last_hit[idx]=time_now;ball_contacts+=1;events.append({'t':round(time_now,4),'building_id':buildings[idx]['id']})
space.on_collision(1,2,begin=hit)
balls=[];states=[]
for frame in range(420):
 t=frame/30
 if frame in [30,130,230]:
  body=pymunk.Body(1,pymunk.moment_for_circle(1,0,11));body.position=(640,1050);body.velocity=(-210-(frame%3)*30,-930);s=pymunk.Circle(body,11);s.elasticity=1;s.friction=.04;s.collision_type=1;space.add(body,s);balls.append((body,[]))
 for _ in range(8):
  time_now+=1/240
  for b,s,sign in flippers:
   target=sign*(.3-.95*(math.sin(time_now*5+sign)>.2));b.angular_velocity=(target-b.angle)*18
  space.step(1/240)
  for b,trail in balls:
   if b.velocity.length>1250:b.velocity=b.velocity.normalized()*1250
 for b,trail in balls:trail.append(tuple(b.position));del trail[:-24]
 states.append({'t':t,'balls':[{'pos':tuple(b.position),'trail':list(tr)} for b,tr in balls],'flippers':[(tuple(b.local_to_world(s.a)),tuple(b.local_to_world(s.b))) for b,s,_ in flippers],'score':ball_contacts*100,'flash':{i:t-v for i,v in last_hit.items() if t-v<.15}})
def portable_font(size):
 try: return ImageFont.truetype("DejaVuSans.ttf",size)
 except OSError: return ImageFont.load_default(size=size)
f=portable_font(42);small=portable_font(23)
base=Image.new('RGB',(W,H),'#111820');d=ImageDraw.Draw(base)
for road in roads:d.line(road,fill='#263540',width=14,joint='curve')
for i,b in enumerate(buildings):
 color=['#718f96','#7d9c8b','#9a9c83','#7a899e'][i%4]
 d.polygon([(x+5,y+7) for x,y in b['points']],fill='#070d11');d.polygon(b['points'],fill=color);d.line(b['points'],fill='#b0c5bf',width=2)
d.rectangle((0,0,W,159),fill='#111820');d.rectangle((0,1109,W,H),fill='#111820');d.rectangle((0,0,27,H),fill='#111820');d.rectangle((693,0,W,H),fill='#111820')
d.rounded_rectangle((29,155,691,1110),radius=30,outline='#4c6570',width=6)
def center(draw,y,text,font=f,fill='#eef2ed'):
 box=draw.textbbox((0,0),text,font=font);draw.text(((W-box[2])/2,y),text,font=font,fill=fill)
center(d,70,'SEOUL CITY HALL × PINBALL')
center(d,1210,'© OpenStreetMap contributors · ODbL',small,fill='#aab9bf')
proc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pixel_format','rgb24','-video_size','720x1280','-framerate','30','-i','-','-an','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(D/'preview.mp4')],stdin=subprocess.PIPE)
for st in states:
 im=base.copy();d=ImageDraw.Draw(im)
 for i,age in st['flash'].items():d.polygon(buildings[i]['points'],fill='#e9cf79')
 for a,b in st['flippers']:d.line([a,b],fill='#f6c965',width=30);d.ellipse((a[0]-15,a[1]-15,a[0]+15,a[1]+15),fill='#fff0c9')
 for k,ball in enumerate(st['balls']):
  tr=ball['trail']
  for j,p in enumerate(tr):
   r=2+j/len(tr)*5;d.ellipse((p[0]-r,p[1]-r,p[0]+r,p[1]+r),fill=['#807f60','#5a8a80','#946c8b'][k%3])
  x,y=ball['pos'];d.ellipse((x-12,y-12,x+12,y+12),fill=['#fff2a8','#b4ffe2','#ffd3ef'][k%3]);d.ellipse((x-5,y-8,x+2,y-1),fill='white')
 center(d,1135,f"{st['score']:,}")
 proc.stdin.write(im.tobytes())
proc.stdin.close();assert proc.wait()==0
(D/'simulation.json').write_text(json.dumps({'physics':'Pymunk '+pymunk.version,'dt':1/240,'gravity':[0,180],'events':events,'frames':states,'building_count':len(buildings)}))
(D/'provenance.json').write_text(json.dumps({'map':'https://www.openstreetmap.org/copyright','source':data['source'],'map_license':'ODbL 1.0 © OpenStreetMap contributors','physics':'https://github.com/viblo/pymunk MIT','implementation':'Actual building outline collision segments; authored automated flippers and launch impulses; all ball trajectories integrated by Pymunk','limitation':'2D pinball board from building footprints; not a navigable road routing simulation'},indent=2))
subprocess.run(['ffmpeg','-v','error','-y','-i',str(D/'preview.mp4'),'-vf','fps=0.57,scale=270:480,tile=4x2','-frames:v','1',str(D/'contact-sheet.jpg')],check=True)
subprocess.run(['ffmpeg','-v','error','-i',str(D/'preview.mp4'),'-f','null','-'],check=True)
(D/'qa.json').write_text(json.dumps({'decode':'pass','buildings':len(buildings),'building_contacts':ball_contacts,'distinct_buildings_hit':len(hits),'duration':14},indent=2))
print(len(buildings),'buildings',ball_contacts,'collisions',len(hits),'unique')
