from pathlib import Path
from PIL import Image,ImageDraw
import json,math,subprocess
r=Path(__file__).parent;data=json.loads((r/'states.json').read_text())
for name,seconds in [('before',4),('after',7)]:
 d=data[name];proc=subprocess.Popen(['ffmpeg','-y','-f','rawvideo','-pix_fmt','rgb24','-s','720x1280','-r','30','-i','-','-an','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(r/(name+'-clean.mp4')),'-loglevel','error'],stdin=subprocess.PIPE)
 for f in range(seconds*30):
  t=f/30;state=d['states'][min(299,f)];im=Image.new('RGB',(720,1280),'#10151c');dr=ImageDraw.Draw(im)
  q=max(0,min(1,(t-4.3)/1.2));q=q*q*(3-2*q)
  scale=1.25 if name=='before' else .90-.35*q;ox=220 if name=='before' else 10;gy=790
  def point(x,y):return(ox+x*scale,gy-y*scale)
  dr.line((45,gy,650,gy),fill='#52616c',width=3)
  for i,(b,h) in enumerate(zip(state,d['heights'])):
   x,y,a=b;w=h*.13;c=math.cos(a);s=math.sin(a);pts=[point(x+u*c-v*s,y+u*s+v*c)for u,v in[(-w/2,-h/2),(w/2,-h/2),(w/2,h/2),(-w/2,h/2)]]
   # Face marks use exactly the same rigid local-to-world transform as the body.
   def local(u,v):return point(x+u*c-v*s,y+u*s+v*c)
   shadow=[(px+5,py+5)for px,py in pts];dr.polygon(shadow,fill='#25313a')
   dr.polygon(pts,fill='#f3f0e7');dr.line(pts+[pts[0]],fill='#18232c',width=max(1,round(w*scale*.025)))
   # Keep the face ivory; a narrow edge indicates a body that is already tilting.
   if abs(a)>.15:dr.line([local(-w/2,-h/2),local(-w/2,h/2)],fill='#aee976',width=max(1,round(w*scale*.055)))
   dr.line([local(-w*.38,0),local(w*.38,0)],fill='#52616c',width=max(1,round(w*scale*.025)))
   # Three above / two below. The narrow side-view silhouette remains unchanged.
   dots=[(-w*.22,h*.36),(0,h*.25),(w*.22,h*.14),(-w*.22,-h*.16),(w*.22,-h*.35)]
   radius=max(.65,w*.10*scale)
   for u,v in dots:
    px,py=local(u,v);dr.ellipse((px-radius,py-radius,px+radius,py+radius),fill='#17212a')
  proc.stdin.write(im.tobytes())
 proc.stdin.close();assert proc.wait()==0
(r/'concat.txt').write_text("file 'before-clean.mp4'\nfile 'after-clean.mp4'\n")
subprocess.run(['ffmpeg','-y','-f','concat','-safe','0','-i',str(r/'concat.txt'),'-c','copy','-movflags','+faststart',str(r/'preview.mp4'),'-loglevel','error'],check=True)
subprocess.run(['ffmpeg','-y','-i',str(r/'preview.mp4'),'-vf','fps=0.72,scale=180:320,tile=4x2','-frames:v','1',str(r/'contact-sheet.jpg'),'-loglevel','error'],check=True)
