"""Rerun the same selected rigid-body designs at 1x for ten-second clean clips."""
import ast,json,math,subprocess,sys
from pathlib import Path
import pymunk
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parent;ROOT=R.parents[1]
source=(R/'run.py').read_text().replace('range(600)','range(1200)')
tree=ast.parse(source);exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['simulate','xy']],type_ignores=[]),str(R/'clean_results.py'),'exec'))
xy_world=xy
def xy(points,pose):
 pts=xy_world(points,pose)
 return [(360+.9*(x-360),960+.9*(y-960)) for x,y in pts] if name=='failure' else pts
for name,spread,bias in [('failure',12,0),('result',70,0)]:
 if len(sys.argv)>1 and name!=sys.argv[1]:continue
 trial=simulate(spread,bias);(R/(name+'-trajectory.json')).write_text(json.dumps(trial))
 proc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pixel_format','rgb24','-video_size','720x1280','-framerate','30','-i','-','-an','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(R/('clean-'+name+'.mp4'))],stdin=subprocess.PIPE)
 for st in trial['states']:
  im=Image.new('RGB',(720,1280),'#0c1119');d=ImageDraw.Draw(im);d.rounded_rectangle((50,963,670,982),radius=8,fill='#445162')
  pose=lambda v:[v[0]-(70 if name=='failure' else 0),v[1],v[2]]
  for poly in trial['polygons']:d.polygon(xy(poly,pose(st['chair'])),fill='#d7a76a',outline='#efcd9c',width=3)
  d.polygon(xy([(-55,-55),(55,-55),(55,55),(-55,55)],pose(st['load'])),fill='#65dcca',outline='#c7fff3',width=4)
  if st['load2'] is not None:d.polygon(xy([(-45,-45),(45,-45),(45,45),(-45,45)],pose(st['load2'])),fill='#79b4f0',outline='#dceeff',width=4)
  proc.stdin.write(im.tobytes())
 proc.stdin.close();assert proc.wait()==0
 print(name,len(trial['states'])/30,trial['tilt_degrees'],flush=True)
