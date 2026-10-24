"""Project the shader's box envelopes and audit camera margins across a loop."""
from pathlib import Path
import argparse
import json
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import convolution as scene
from camera_framing import margins
from camera_framing import BASIS


def audit(samples=901):
    rig=scene.CameraRig()
    records=[]
    for t in np.linspace(0,scene.DURATION,samples):
        pose=rig.sample(float(t))
        bounds=scene.framing_subject(float(t))
        margin=margins(pose,bounds)*720
        records.append({'time':round(float(t),4),'margins_px':np.round(margin,3).tolist(),
                        'min_px':round(float(margin.min()),3),
                        'horizontal_imbalance_px':round(float(abs(margin[0]-margin[2])),3)})
    worst=min(records,key=lambda r:r['min_px'])
    view=np.c_[rig.poses[:,:3]@BASIS.T,np.log(rig.poses[:,3])]
    jerk=np.linalg.norm(np.diff(view,3,axis=0)/(rig.times[1]-rig.times[0])**3,axis=1)
    return {'logical_square_px':720,'portrait_size':[720,1280],
            'scope':'actual working boxes during convolution; visible context elsewhere; output during final shot',
            'margin_order':['left','bottom','right','top'],
            'minimum_margin_px':43.2,
            'filter_reveal_minimum_px':12.,
            'worst_after_filter_reveal':min((r for r in records if r['time']>=3.6),key=lambda r:r['min_px']),
            'sample_count':samples,'clipped_samples':sum(r['min_px']<-.01 for r in records),
            'max_horizontal_imbalance_px':max(r['horizontal_imbalance_px'] for r in records),
            'camera_jerk_p99':round(float(np.percentile(jerk,99)),3),
            'camera_jerk_max':round(float(jerk.max()),3),
            'worst':worst,'samples':records}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=Path('framing_audit.json'))
    parser.add_argument('--samples',type=int,default=901)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    report=audit(args.samples)
    if args.check:
        assert report['clipped_samples']==0
        assert report['worst']['min_px']>=12.
        assert report['worst_after_filter_reveal']['min_px']>=43.19
        assert report['camera_jerk_max']<5000
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='samples'},indent=2))
