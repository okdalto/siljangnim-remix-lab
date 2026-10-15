import json,math,subprocess
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent;FONT=None
def simulate(repair,weak_node=4):
 x=np.array([[70+i*72.5,650+r*70] for r in range(2) for i in range(9)]+[[70,430],[650,430]],float);v=np.zeros_like(x);start=x.copy();edges=[]
 for r in range(2):
  for i in range(8):edges.append((r*9+i,r*9+i+1,'deck'))
 for i in range(9):edges.append((i,i+9,'post'))
 for i in range(8):
  if i not in [3,4]:edges.append((i,i+10,'brace'))
 if repair>=1:edges.extend([(18,weak_node,'repair'),(19,weak_node,'repair')])
 if repair>=2:edges.extend([(18,weak_node-1,'repair'),(19,weak_node+1,'repair')])
 n=len(edges);a=np.array([e[0] for e in edges]);b=np.array([e[1] for e in edges]);rest=np.linalg.norm(x[b]-x[a],axis=1);alive=np.ones(n,bool);fixed=[0,8,9,17,18,19];events=[];states=[];dt=1/600;maxdef=0
 for step in range(3600):
  t=step*dt;delta=x[b]-x[a];length=np.maximum(.001,np.linalg.norm(delta,axis=1));unit=delta/length[:,None];speed=np.sum((v[b]-v[a])*unit,axis=1);force=6500*(length-rest)+65*speed
  force*=alive
  # Break by computed axial force, never scripted time.
  for k in np.flatnonzero(alive & (np.abs(force)>35000)):
   alive[k]=False;events.append({'time':t,'bar':int(k),'nodes':[int(a[k]),int(b[k])],'force':float(force[k])})
  force*=alive;f=np.zeros_like(x);f[:,1]=8*150
  load=min(1,max(0,(t-.6)/.35))*30000;f[4,1]+=load
  np.add.at(f,a,unit*force[:,None]);np.add.at(f,b,-unit*force[:,None]);v+=f/8*dt;v*=.997;x+=v*dt
  x[fixed]=start[fixed];v[fixed]=0
  mask=x[:,1]>1050;x[mask,1]=1050;v[mask,1]*=-.1
  maxdef=max(maxdef,float(x[4,1]-650))
  if step%20==0:states.append({'nodes':x.round(3).tolist(),'alive':alive.tolist(),'load':float(load),'forces':force.round(1).tolist()})
 return {'repair_level':repair,'edges':edges,'states':states,'events':events,'max_deflection':maxdef,'final_deflection':float(x[4,1]-650),'broken':len(events)}
initial=simulate(0)
first=initial['events'][0]
pre=initial['states'][max(0,int(first['time']*30)-1)]
weak=int(np.argmax(np.array(pre['nodes'])[1:8,1]))+1
trials=[initial]+[simulate(i,weak) for i in [1,2]]
safe=[t for t in trials[1:] if t['broken']==0]
best=min(safe,key=lambda t:t['repair_level'])
(R/'simulations.json').write_text(json.dumps(trials))
metrics={'feedback':{'first_failed_bar':first,'most_deflected_deck_node_before_failure':weak},'selected_repair':best['repair_level'],'added_members':best['repair_level']*2,'initial_broken':initial['broken'],'repaired_broken':best['broken'],'initial_deflection':initial['max_deflection'],'repaired_deflection':best['max_deflection'],'same_downward_load':30000,'capacity_unchanged':35000}
(R/'metrics.json').write_text(json.dumps(metrics,indent=2));print(metrics,flush=True)
def draw(trial,frame,title,diagnose=False):
 im=Image.new('RGB',(720,1280),'#0c1119');d=ImageDraw.Draw(im)
 d.multiline_text((360,190),title,font=ImageFont.load_default(size=48),fill='white',anchor='ma',align='center',spacing=12)
 st=trial['states'][min(frame,179)];nodes=st['nodes']
 for xx in [70,650]:
  d.line((xx,430,xx,1050),fill='#38485c',width=18)
  d.rectangle((xx-30,1040,xx+30,1060),fill='#526278')
 d.line((30,1060,690,1060),fill='#38485c',width=5)
 for k,(a,b,kind) in enumerate(trial['edges']):
  if not st['alive'][k]:continue
  stress=min(1,abs(st['forces'][k])/35000)
  color='#65e1ca' if kind=='repair' else (int(150+105*stress),int(190-125*stress),int(210-135*stress))
  d.line((*nodes[a],*nodes[b]),fill=color,width=9 if kind=='repair' else 7)
 for p in nodes[:18]:d.ellipse((p[0]-5,p[1]-5,p[0]+5,p[1]+5),fill='#d8e4ed')
 x,y=nodes[4];fill='#f2ba5a' if st['load']>0 else '#695b45';d.rounded_rectangle((x-42,y-90,x+42,y-8),radius=8,fill=fill)
 if diagnose:
  for anchor in [18,19]:d.line((*nodes[anchor],*nodes[weak]),fill='#65e1ca',width=9)
  d.ellipse((nodes[weak][0]-18,nodes[weak][1]-18,nodes[weak][0]+18,nodes[weak][1]+18),outline='white',width=4)
  caption='Route the load to the supports'
 else:caption=f"{sum(not a for a in st['alive'])} BROKEN BARS"
 d.text((360,1130),caption,font=ImageFont.load_default(size=36 if diagnose else 44),fill='#eff6fa',anchor='mm')
 return im
out=subprocess.Popen(['ffmpeg','-y','-f','rawvideo','-pix_fmt','rgb24','-s','720x1280','-r','30','-i','-','-an','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(R/'preview.mp4'),'-loglevel','error'],stdin=subprocess.PIPE)
for f in range(360):
 t=f/30
 if t<4:im=draw(initial,f,'LOAD IT.\nFIND THE FAILURE.')
 elif t<6:im=draw(initial,int(first['time']*30)-1,'ADD A NEW\nLOAD PATH.',True)
 else:im=draw(best,int((t-6)*30),'SAME LOAD.\nTWO NEW BRACES.')
 out.stdin.write(im.tobytes())
out.stdin.close();assert out.wait()==0
