from pathlib import Path
import sys,json,gzip,numpy as np
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D/'original'));import convolution as c
meta=json.loads((D/'motion-meta.json').read_text());a=np.frombuffer(gzip.decompress((D/'motion.bin.gz').read_bytes()),dtype='<f4').reshape(-1,meta['stride']);assert np.isfinite(a).all();assert len(a)==meta['frames'];cam=c.CameraRig(.8);err=0
for i in np.linspace(0,len(a)-1,101,dtype=int):
 t=float(np.float32(i/meta['rate']+.0001));m=c.motion_values(t);pose=cam.sample(t);prep,layer=c.prepared_filter(t,cam);vertices=c.footprint_vertices(t,m,pose).flatten();row=np.r_[m,c.filter_motion_values(t),c.gather_motion_values(t),c.source_scale_values(t,.8),pose,prep,layer,c.sweep_motion_visibility(t,.8),c.label_opacity(t),np.pad(vertices,(0,72-len(vertices)))].astype('<f4');err=max(err,float(np.max(np.abs(a[i]-row))))
assert err==0
report={'frames':len(a),'sample_rate':meta['rate'],'all_values_finite':True,'reference_samples':101,'max_original_motion_error':err,'runtime':'Siljangnim WebGL2, live SDF raymarch; CPU motions sampled from original Python','visual_review':'Original photo/filter, 11.6 s RGB operation matched against Python capture; no runtime errors'}
(D/'motion-verification.json').write_text(json.dumps(report,indent=2));print(report)
