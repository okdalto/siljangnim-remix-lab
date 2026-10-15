import pymunk,math,json
from pathlib import Path
r=Path(__file__).parent

def run(ratio=1.35,n=8,gap=.25,direct=False,record=False):
 s=pymunk.Space();s.gravity=(0,-980);s.iterations=60
 floor=pymunk.Segment(s.static_body,(-500,0),(10000,0),2);floor.friction=.8;s.add(floor)
 hs=[50*ratio**i for i in range(n)]
 if direct:hs=[hs[0],hs[-1]]
 bodies=[];x=100;prev=None
 for i,h in enumerate(hs):
  w=h*.13
  if prev is not None:x+=prev*.13/2+prev*gap+w/2
  mass=(h/50)**2
  b=pymunk.Body(mass,pymunk.moment_for_box(mass,(w,h)));b.position=(x,h/2+2.1);sh=pymunk.Poly.create_box(b,(w,h));sh.friction=.28;sh.elasticity=0;s.add(b,sh);bodies.append(b);prev=h
 frames=[]
 for k in range(120*10):
  if k==30:bodies[0].angular_velocity=-3
  s.step(1/120)
  if record and k%4==0:frames.append([[b.position.x,b.position.y,b.angle]for b in bodies])
 fallen=[abs(b.angle)>math.pi/3 for b in bodies]
 return {'ratio':ratio,'n':n,'gap':gap,'direct':direct,'heights':hs,'fallen':fallen,'count':sum(fallen),'states':frames}
trials=[]
for ratio in [1.3,1.35,1.4]:
 for gap in [.20,.25,.3,.35,.4,.45,.5,.55]:
  a=run(ratio,8,gap);trials.append({k:v for k,v in a.items()if k!='states'})
good=[x for x in trials if x['count']==8];print([(x['ratio'],x['gap'],x['count'])for x in trials]);print('GOOD',len(good))
if good:
 best=next(x for x in good if x['ratio']==1.35 and x['gap']==.35);after=run(best['ratio'],8,best['gap'],record=True);before=run(best['ratio'],8,best['gap'],direct=True,record=True)
 (r/'states.json').write_text(json.dumps({'before':before,'after':after}));(r/'metrics.json').write_text(json.dumps({'trials':trials,'selected':{k:v for k,v in best.items() if k!='states'},'before_fallen':before['fallen'],'after_fallen':after['fallen'],'height_gain':after['heights'][-1]/after['heights'][0]},indent=2));print('SELECTED',best['ratio'],best['gap'],before['fallen'],after['fallen'])
