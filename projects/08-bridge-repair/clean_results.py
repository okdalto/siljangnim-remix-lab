"""Rerun identical failure and selected repair at 1x for ten-second clean clips."""
import ast,json,math,subprocess
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parent;ROOT=R.parents[1]
source=(R/'run.py').read_text().replace('range(3600)','range(6000)');tree=ast.parse(source)
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='simulate'],type_ignores=[]),str(R/'clean_results.py'),'exec'))
for name,level in [('failure',0),('result',1)]:
 trial=simulate(level,4);(R/(name+'-trajectory.json')).write_text(json.dumps(trial))
 proc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pixel_format','rgb24','-video_size','720x1280','-framerate','30','-i','-','-an','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(R/('clean-'+name+'.mp4'))],stdin=subprocess.PIPE)
 for st in trial['states']:
  im=Image.new('RGB',(720,1280),'#0c1119');d=ImageDraw.Draw(im);nodes=st['nodes']
  for xx in [70,650]:d.line((xx,430,xx,1050),fill='#38485c',width=18);d.rectangle((xx-30,1040,xx+30,1060),fill='#526278')
  d.line((30,1060,690,1060),fill='#38485c',width=5)
  for k,(a,b,kind) in enumerate(trial['edges']):
   if not st['alive'][k]:continue
   stress=min(1,abs(st['forces'][k])/35000);color='#65e1ca' if kind=='repair' else (int(150+105*stress),int(190-125*stress),int(210-135*stress))
   d.line((*nodes[a],*nodes[b]),fill=color,width=9 if kind=='repair' else 7)
  for p in nodes[:18]:d.ellipse((p[0]-5,p[1]-5,p[0]+5,p[1]+5),fill='#d8e4ed')
  x,y=nodes[4];d.rounded_rectangle((x-42,y-90,x+42,y-8),radius=8,fill='#f2ba5a' if st['load']>0 else '#695b45');proc.stdin.write(im.tobytes())
 proc.stdin.close();assert proc.wait()==0
 print(name,len(trial['states'])/30,trial['broken'],flush=True)
