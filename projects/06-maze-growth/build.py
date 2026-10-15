"""A procedural maze plus an authored branching-growth model. Not botanical AI."""
from pathlib import Path
import random, json, math, subprocess
from PIL import Image, ImageDraw, ImageFont
D=Path(__file__).resolve().parent
W,H=720,1280; C,R=9,14; S=66; X,Y=63,170
rng=random.Random(23); adj={ (x,y):[] for x in range(C) for y in range(R)}
start=(4,R-1); goal=(4,0); stack=[start];seen={start}
while stack:
 a=stack[-1];opts=[b for b in [(a[0]+1,a[1]),(a[0]-1,a[1]),(a[0],a[1]+1),(a[0],a[1]-1)] if b in adj and b not in seen]
 if not opts:stack.pop();continue
 b=rng.choice(opts);adj[a].append(b);adj[b].append(a);seen.add(b);stack.append(b)
# Growth explores only open neighbouring cells. It does not know a shortest path.
front=[start];grown={start};edges=[];arrival={start:0};parents={};step=0;reached=None
while front:
 step+=1;new=[]
 for a in front:
  opts=[b for b in adj[a] if b not in grown]
  opts.sort(key=lambda b:b[1]) # deterministic order only; all open neighbours grow, no path oracle
  for b in opts:
   grown.add(b);parents[b]=a;arrival[b]=step;edges.append((a,b,step));new.append(b)
   if b==goal:reached=step
 front=new
 if reached is not None:break
path=[goal]
while path[-1]!=start:path.append(parents[path[-1]])
pathset={tuple(sorted((a,b))) for a,b in zip(path,path[1:])}
def portable_font(size):
 try: return ImageFont.truetype("DejaVuSans.ttf",size)
 except OSError: return ImageFont.load_default(size=size)
f=portable_font(38);sm=portable_font(34)
def pt(a):return (X+a[0]*S+S/2,Y+a[1]*S+S/2)
def text(draw,y,s,font=f,color='#edf1ef'):
 box=draw.textbbox((0,0),s,font=font);draw.text(((W-box[2])/2,y),s,font=font,fill=color)
proc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pixel_format','rgb24','-video_size','720x1280','-framerate','30','-i','-','-an','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(D/'preview.mp4')],stdin=subprocess.PIPE)
for frame in range(390):
 t=frame/30;progress=max(0,(t-1)/10)*reached;done=progress>=reached
 im=Image.new('RGB',(W,H),'#11191a');d=ImageDraw.Draw(im)
 text(d,70,'BRANCHES THROUGH A MAZE')
 # Thick maze walls are rendered directly from the generated graph.
 for a,ns in adj.items():
  x,y=X+a[0]*S,Y+a[1]*S
  for b,line in [((a[0]+1,a[1]),[(x+S,y),(x+S,y+S)]),((a[0],a[1]+1),[(x,y+S),(x+S,y+S)])]:
   if b not in ns and not (a==start and b==(4,R)):d.line(line,fill='#3c4a4d',width=6)
 d.line([(X,Y+R*S),(X,Y),(X+4*S,Y)],fill='#3c4a4d',width=6);d.line([(X+5*S,Y),(X+C*S,Y),(X+C*S,Y+R*S)],fill='#3c4a4d',width=6)
 gx,gy=pt(goal);d.ellipse((gx-17,Y-32,gx+17,Y+2),fill='#ffe69a')
 for a,b,k in edges:
  u=min(1,max(0,progress-(k-1)))
  if u<=0:continue
  p,q=pt(a),pt(b);end=(p[0]+(q[0]-p[0])*u,p[1]+(q[1]-p[1])*u)
  main=tuple(sorted((a,b))) in pathset
  color=('#a5e89d' if main else '#496e52') if done else '#8fd898'
  d.line([p,end],fill=color,width=9 if main and done else 7);d.ellipse((end[0]-5,end[1]-5,end[0]+5,end[1]+5),fill=color)
  if u==1:
   xx,yy=end;side=-1 if b[0]%2 else 1
   d.polygon([(xx,yy),(xx+side*23,yy-20),(xx+side*24,yy-8),(xx+side*12,yy+1)],fill=color)
   d.line([(xx,yy),(xx+side*20,yy-16)],fill='#c3f4a8' if main and done else '#70af77',width=2)
 if done:
  for a in range(6):
   angle=a*math.pi/3;xx=gx+13*math.cos(angle);yy=gy+13*math.sin(angle)
   d.ellipse((xx-9,yy-9,xx+9,yy+9),fill='#f3c2df')
  d.ellipse((gx-7,gy-7,gx+7,gy+7),fill='#ffe69a')
 text(d,1125,'EXIT REACHED' if done else 'Blocked branches stop.',sm)
 if not done:text(d,1170,'Open passages keep growing.',sm)
 proc.stdin.write(im.tobytes())
proc.stdin.close();assert proc.wait()==0
subprocess.run(['ffmpeg','-v','error','-y','-i',str(D/'preview.mp4'),'-vf','fps=0.62,scale=270:480,tile=4x2','-frames:v','1',str(D/'contact-sheet.jpg')],check=True)
subprocess.run(['ffmpeg','-v','error','-i',str(D/'preview.mp4'),'-f','null','-'],check=True)
(D/'simulation.json').write_text(json.dumps({'seed':23,'size':[C,R],'adjacency':{str(k):v for k,v in adj.items()},'growth_edges':edges,'arrival_step':reached,'visited':len(grown),'exit_path':path},indent=2))
(D/'provenance.json').write_text(json.dumps({'implementation':'Authored local branching growth over an actual DFS maze graph; no globally planned path used during growth','libraries':{'Pillow':'https://github.com/python-pillow/Pillow'},'limitation':'Illustrative discrete branching rules, not a botanical growth model, neural network, or biological prediction','render':'Direct rendering of recorded simulation edges; time compressed','input':'procedurally generated maze seed 23'},indent=2))
(D/'qa.json').write_text(json.dumps({'decode':'pass','reached_exit':goal in grown,'edges_do_not_cross_walls':all(b in adj[a] for a,b,k in edges),'duration':13},indent=2))
print('growth',reached,'steps',len(grown),'cells',flush=True)
