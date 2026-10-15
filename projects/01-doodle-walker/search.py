import pymunk,math,json,random
from pathlib import Path
r=Path(__file__).parent
DT=1/120

def run(param,save=False):
 s=pymunk.Space();s.gravity=(0,-900);s.iterations=20
 floor=pymunk.Segment(s.static_body,(-10000,0),(10000,0),4);floor.friction=1.8;s.add(floor)
 body=pymunk.Body(4,5*pymunk.moment_for_box(4,(110,40)));body.position=(0,100);poly=pymunk.Poly.create_box(body,(110,40));poly.friction=.6;poly.filter=pymunk.ShapeFilter(group=1);s.add(body,poly)
 legs=[];motors=[]
 for i,x in enumerate([-42,0,42]):
  b=pymunk.Body(.6,pymunk.moment_for_box(.6,(14,64)));b.position=(x,55);sh=pymunk.Poly.create_box(b,(14,64));sh.friction=2;sh.filter=pymunk.ShapeFilter(group=1)
  foot=pymunk.Circle(b,12,(0,-32));foot.friction=2;foot.filter=pymunk.ShapeFilter(group=1)
  s.add(b,sh,foot);p=pymunk.PivotJoint(body,b,(x,85));m=pymunk.SimpleMotor(body,b,0);m.max_force=param['force'];s.add(p,m);legs.append(b);motors.append(m)
 frames=[];start=None
 for step in range(120*7):
  t=step*DT
  if t>=.5:
   for i,m in enumerate(motors):m.rate=param['speed']+param['amp']*math.sin(t*param['freq']+i*param['phase'])
  s.step(DT)
  if step==60:start=body.position.x
  if save and step%4==0:frames.append({'t':t,'body':[*body.position,body.angle],'legs':[[*b.position,b.angle] for b in legs]})
 score=body.position.x-start
 return score,frames
rng=random.Random(51);trials=[]
base={'speed':0,'amp':.8,'freq':4,'phase':0,'force':80000};score,_=run(base);trials.append({'parameters':base,'distance':score})
for i in range(191):
 p={'speed':rng.uniform(-8,0),'amp':rng.uniform(0,6),'freq':rng.uniform(2,8),'phase':rng.uniform(0,6.28),'force':rng.uniform(25000,150000)};score,_=run(p);trials.append({'parameters':p,'distance':score})
best=max(trials,key=lambda q:q['distance']);a,af=run(base,True);b,bf=run(best['parameters'],True)
(r/'metrics.json').write_text(json.dumps({'engine':'pymunk7.3.1','objective':'body horizontal displacement after settling over6.5sec','seed':51,'trials':trials,'baseline':a,'best':b,'improvement':b-a,'best_parameters':best['parameters']},indent=2));(r/'frames.json').write_text(json.dumps({'before':af,'after':bf}));print(a,b,best)
