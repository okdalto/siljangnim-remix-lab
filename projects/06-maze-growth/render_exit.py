"""Continue real recorded growth at original step rate; reveal its measured route afterward."""
from pathlib import Path
import json,ast,math,subprocess
from PIL import Image,ImageDraw
D=Path(__file__).parent;data=json.loads((D/'simulation.json').read_text());adj={ast.literal_eval(k):[tuple(v) for v in ns] for k,ns in data['adjacency'].items()};edges=[(tuple(a),tuple(b),k) for a,b,k in data['growth_edges']];path=[tuple(a) for a in data['exit_path']][::-1];pathorder={tuple(sorted((a,b))):i for i,(a,b) in enumerate(zip(path,path[1:]))};reached=data['arrival_step'];C,R=data['size'];X,Y,S=63,170,66;start=(4,R-1);goal=(4,0)
def pt(a):return X+a[0]*S+S/2,Y+a[1]*S+S/2
p=subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s','720x1280','-r','30','-i','-','-an','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(D/'exit-clean.mp4')],stdin=subprocess.PIPE)
for f in range(180):
 t=f/30;progress=min(reached,reached*.88+t*reached/10);done=progress>=reached;highlight=max(0,(t-1.5)/2.4)*len(pathorder);im=Image.new('RGB',(720,1280),'#11191a');d=ImageDraw.Draw(im)
 for a,ns in adj.items():
  x,y=X+a[0]*S,Y+a[1]*S
  for b,line in [((a[0]+1,a[1]),[(x+S,y),(x+S,y+S)]),((a[0],a[1]+1),[(x,y+S),(x+S,y+S)])]:
   if b not in ns and not (a==start and b==(4,R)):d.line(line,fill='#3c4a4d',width=6)
 d.line([(X,Y+R*S),(X,Y),(X+4*S,Y)],fill='#3c4a4d',width=6);d.line([(X+5*S,Y),(X+C*S,Y),(X+C*S,Y+R*S)],fill='#3c4a4d',width=6)
 gx,gy=pt(goal);d.ellipse((gx-17,Y-32,gx+17,Y+2),fill='#ffe69a')
 for a,b,k in edges:
  u=min(1,max(0,progress-(k-1)))
  if not u:continue
  aa,bb=pt(a),pt(b);end=(aa[0]+(bb[0]-aa[0])*u,aa[1]+(bb[1]-aa[1])*u);order=pathorder.get(tuple(sorted((a,b))),10000);lit=done and order<highlight;color='#a5e89d' if lit else '#496e52' if done else '#8fd898';d.line([aa,end],fill=color,width=10 if lit else 7)
  if u==1:
   xx,yy=end;side=-1 if b[0]%2 else 1;d.polygon([(xx,yy),(xx+side*23,yy-20),(xx+side*24,yy-8),(xx+side*12,yy+1)],fill=color)
 if done:
  for j in range(6):
   angle=j*math.pi/3;xx=gx+13*math.cos(angle);yy=gy+13*math.sin(angle);d.ellipse((xx-9,yy-9,xx+9,yy+9),fill='#f3c2df')
  d.ellipse((gx-7,gy-7,gx+7,gy+7),fill='#ffe69a')
 p.stdin.write(im.tobytes())
p.stdin.close();assert p.wait()==0
print(D/'exit-clean.mp4')
