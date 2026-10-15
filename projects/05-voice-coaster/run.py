"""Run the real published rail comparison, or analyze a new pitch JSON."""
import argparse, json
from pathlib import Path
import numpy as np
import physics as p
args=argparse.ArgumentParser();args.add_argument('--pitch');a=args.parse_args()
if a.pitch:p.set_pitch(json.loads(Path(a.pitch).read_text())['pitch_hz'])
results={}
for name,settings in [('raw',(1.7,0,8)),('smoothed',(1.0,.04,16))]:
 r=p.trial(*settings);z,d,v,n,stop,ts=r
 reason='stall' if v[stop] <= np.sqrt(.02)+1e-8 else 'lost contact' if n[stop]<0 else 'finish'
 results[name]={'result':reason,'event_seconds':float(ts[stop]),'event_x':float(p.x[stop]),'normal_acceleration':float(n[stop]),'parameters':settings}
 if reason=='lost contact':
  rows,impacts=p.continue_airborne(r);results[name]['recontacts']=impacts
 if not np.isfinite(np.array([z,d,v,n,ts])).all():raise AssertionError('Non-finite trajectory')
out=p.P/'output';out.mkdir(exist_ok=True);(out/'metrics.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
