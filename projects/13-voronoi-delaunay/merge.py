import numpy as np,json
from pathlib import Path
E=Path(__file__).resolve().parent / 'data';d=json.loads((E/'geometry.json').read_text())
for cells in d.values():
 for c in cells:
  vs=np.array(c['vertices']);groups={}
  for face in c['faces']:
   v=vs[face];n=np.cross(v[1]-v[0],v[2]-v[0]);n/=np.linalg.norm(n);key=tuple(np.round([*n,-n@v[0]],7));groups.setdefault(key,set()).update(face)
  faces=[]
  for key,ids in groups.items():
   ids=list(ids);v=vs[ids];center=v.mean(0);n=np.array(key[:3]);u=v[0]-center;u/=np.linalg.norm(u);w=np.cross(n,u);angle=np.arctan2((v-center)@w,(v-center)@u);faces.append([ids[i]for i in np.argsort(angle)])
  c['faces']=faces
(E/'geometry.json').write_text(json.dumps(d));print('merged coplanar facets')
