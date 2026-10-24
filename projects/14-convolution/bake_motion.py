"""Sample original CPU animation at 240 Hz; GPU geometry remains live GLSL."""
from pathlib import Path
import sys,json,gzip,numpy as np
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D/'original'));import convolution as c
rate=240;camera=c.CameraRig(.8);rows=[]
for i in range(int(np.ceil(c.DURATION*rate))+1):
 t=float(np.float32(i/rate+.0001));m=c.motion_values(t);pose=camera.sample(t);prep,layer=c.prepared_filter(t,camera)
 row=np.r_[m,c.filter_motion_values(t),c.gather_motion_values(t),c.source_scale_values(t,.8),pose,prep,layer,c.sweep_motion_visibility(t,.8),c.label_opacity(t),np.pad(c.footprint_vertices(t,m,pose).flatten(),(0,72-c.footprint_vertices(t,m,pose).size))]
 rows.append(row)
arr=np.asarray(rows,dtype='<f4');(D/'motion.bin.gz').write_bytes(gzip.compress(arr.tobytes(),mtime=0))
photo=c.load_image(Path(sys.argv[2]) if len(sys.argv)>2 and sys.argv[1]=='--image' else D/'original/assets/dog.jpg',512);rgba=np.concatenate([np.rint(photo*255).astype('uint8'),np.full((512,512,1),255,dtype='uint8')],axis=2)
(D/'photo.bin.gz').write_bytes(gzip.compress(rgba.tobytes(),mtime=0))
(D/'motion-meta.json').write_text(json.dumps({'rate':rate,'stride':arr.shape[1],'frames':len(arr),'duration':c.DURATION,'scanStart':c.SCAN_START,'firstCell':c.FIRST_CELL,'scanFinish':c.SCAN_END,'phaseTiming':c.PHASE_TIMING.tolist(),'introTiming':[c.PIXELIZE_START,c.SPLIT_START],'loopBlendStart':c.LOOP_BLEND_START,'loopBlendDuration':c.LOOP_BLEND_DURATION},indent=2))
(D/'labels.bin.gz').write_bytes(gzip.compress(c.label_atlas().tobytes(),mtime=0))
print(arr.shape)
