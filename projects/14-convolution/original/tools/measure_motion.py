"""Measure projected motion using the same spring samples and camera as the renderer."""
import json
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import convolution as scene

RIGHT=np.cross(-np.array([13.,10.,18.]),[0,1,0]);RIGHT/=np.linalg.norm(RIGHT)
FORWARD=-np.array([13.,10.,18.]);FORWARD/=np.linalg.norm(FORWARD)
UP=np.cross(RIGHT,FORWARD)
MACRO=np.array([-3.9,3.9,1.75])


def mix(a,b,t):return np.asarray(a)*(1-t)+np.asarray(b)*t


def destination(index):
 x,y=scene.scan_cell(index)
 return np.array([6.5+(x-15.5)*.18,(y-15.5)*.18,0.])


def delivery(start,end,t):return mix(start,end,t)+np.array([0,.9,.65])*np.sin(t*np.pi)


RIG=None

def camera(t,m):
 pose=RIG.sample(t) if RIG is not None else scene.camera_target(t,m)
 return pose[:3],float(pose[3])


def project(point,t,m):
 focus,framing=camera(t,m)
 q=point-focus
 return np.array([.5+np.dot(q,RIGHT)/(2*framing),.5-np.dot(q,UP)/(2*framing)])*840


def voxel(m,order=0,channel=0):
 x,y=scene.scan_cell(int(m[24]));center=np.array([(x-15.5)*.18,(y-15.5)*.18,0])
 j,i=divmod(order,3);tap=np.array([i-1,1-j,0.])
 home=center+[0,0,(1-channel)*.95]+tap*.18
 staged=MACRO+[0,0,(1-channel)*.95]+tap*.18
 reduced=MACRO
 return mix(mix(home,staged,m[15+order]),reduced,m[1])


def measure(label,start,duration,point):
 times=np.linspace(start,start+duration,1201)
 positions=np.array([project(point(m:=scene.motion_values(float(t))),t,m) for t in times])
 speed=np.linalg.norm(np.diff(positions,axis=0),axis=1)/(times[1]-times[0])
 return {'stage':label,'duration_s':round(float(duration),3),'peak_px_s':round(float(speed.max()),1),
         'travel_px':round(float(np.linalg.norm(np.diff(positions,axis=0),axis=1).sum()),1)}


def measure_current(use_lag=True):
 global RIG
 RIG=scene.CameraRig() if use_lag else None
 p=scene.PHASE_TIMING;s=scene.SCAN_START
 rows=[measure('RGB separation',scene.SPLIT_START,p[15],lambda m:np.array([-2.88,2.88,.95*m[0]]))]
 pops=[measure('voxel pop',s+i*p[1],p[0],lambda m,i=i:voxel(m,i)) for i in range(9)]
 rows.append({'stage':'voxel pop (median of 9)','duration_s':float(p[0]),
              'peak_px_s':round(float(np.median([v['peak_px_s'] for v in pops])),1),
              'travel_px':round(float(np.median([v['travel_px'] for v in pops])),1)})
 rows += [measure('27 products gather',s+p[4],p[5],lambda m:voxel(m,2)),
          measure('result delivery',s+p[8],p[9],lambda m:delivery(MACRO,destination(int(m[24])),m[3]))]
 return rows


if __name__=='__main__':
 old=(scene.SCAN_START,scene.FIRST_CELL,scene.CELL_TIME,scene.SCAN_END,scene.PHASE_TIMING)
 after=measure_current()
 scene.SCAN_START,scene.FIRST_CELL,scene.CELL_TIME=5.4,6.8,.055
 scene.SCAN_END=scene.SCAN_START+2*scene.FIRST_CELL+898*scene.CELL_TIME
 scene.PHASE_TIMING=np.array([.75,.1,1.7,1.1,2.9,.85,3.5,.65,4.3,.8,5.35,1.45,.85,4.25,1.55,2.,4.,.8,4.15,2.],dtype=np.float32)
 before=measure_current(use_lag=False)
 scene.SCAN_START,scene.FIRST_CELL,scene.CELL_TIME,scene.SCAN_END,scene.PHASE_TIMING=old
 report={'canvas_px':840,'method':'1201 time samples per stage, renderer spring and camera projection',
         'before':before,'after':after}
 output=scene.ROOT/'motion_metrics.json'
 output.write_text(json.dumps(report,indent=2)+'\n')
 print(f'{"Stage":28s} {"Before px/s":>12s} {"After px/s":>12s}')
 for a,b in zip(before,after): print(f'{a["stage"]:28s} {a["peak_px_s"]:12.1f} {b["peak_px_s"]:12.1f}')
 print(output)
