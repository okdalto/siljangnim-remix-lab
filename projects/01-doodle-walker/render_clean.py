from PIL import Image,ImageDraw
from pathlib import Path
import json,math,subprocess
r=Path(__file__).parent;src=r;data=json.loads((src/'frames.json').read_text())
def creature(d,f,origin,scale=2):
 color='#adeb72'
 def pt(x,y):return(origin[0]+x*scale,origin[1]-y*scale)
 def poly(b,coords):
  x,y,a=b;c=math.cos(a);s=math.sin(a);return[pt(x+u*c-v*s,y+u*s+v*c)for u,v in coords]
 for b in f['legs']:
  ps=poly(b,[(-3,-32),(2,-18),(-2,2),(3,20),(1,32)]);d.line(ps,fill='white',width=5)
  x,y=ps[0];d.ellipse((x-13,y-10,x+12,y+11),outline='white',width=3)
 coords=[(-55,-20),(-39,-23),(-18,-19),(3,-23),(28,-19),(53,-22),(57,-8),(54,17),(33,22),(6,18),(-20,22),(-53,18),(-57,0),(-55,-20)]
 ps=poly(f['body'],coords);d.line(ps,fill='white',width=4)
 for u in [-44,-31,-18,-5,8]:d.line(poly(f['body'],[(u,-12),(u+18,13)]),fill='#dce4de',width=2)
 for e in [(24,8),(41,8)]:
  x,y=poly(f['body'],[e])[0];d.ellipse((x-6,y-6,x+6,y+6),fill='white')
for name,which in [('first','before'),('result','after')]:
 proc=subprocess.Popen(['ffmpeg','-y','-f','rawvideo','-pix_fmt','rgb24','-s','720x1280','-r','30','-i','-','-an','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(r/(name+'-clean.mp4')),'-loglevel','error'],stdin=subprocess.PIPE)
 for k in range(240):
  f=data[which][min(209,k)];im=Image.new('RGB',(720,1280),'#10151c');d=ImageDraw.Draw(im);ground=730;offset=230-max(0,f['body'][0]*2-150);d.line((40,ground,660,ground),fill='#65737c',width=4)
  for n in range(-10,20):
   x=offset+n*220
   if 40<x<660:d.line((x,ground,x,ground+28),fill='#65737c',width=4)
  creature(d,f,(offset,ground));proc.stdin.write(im.tobytes())
 proc.stdin.close();assert proc.wait()==0
