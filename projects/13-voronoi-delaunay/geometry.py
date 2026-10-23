import numpy as np,json
from scipy.spatial import HalfspaceIntersection,ConvexHull
from pathlib import Path
E=Path(__file__).resolve().parent / 'data'
rng=np.random.default_rng(17)
def cells(points,lo,hi):
 out=[]
 for i,p in enumerate(points):
  hs=[]
  for j,q in enumerate(points):
   if i!=j:hs.append([*(q-p),-(q@q-p@p)/2])
  for k in range(3):
   a=np.eye(3)[k];hs.extend([[*a,-hi[k]],[*(-a),lo[k]]])
  vs=HalfspaceIntersection(np.array(hs),p).intersections;h=ConvexHull(vs);center=vs.mean(axis=0);faces=[]
  for tri,eq in zip(h.simplices,h.equations):
   a,b,c=vs[tri];ids=tri.tolist()
   if np.dot(np.cross(b-a,c-a),eq[:3])<0:ids.reverse()
   faces.append(ids)
  out.append(dict(seed=p.tolist(),center=center.tolist(),vertices=(vs-center).tolist(),faces=faces,volume=h.volume))
 assert abs(sum(c['volume']for c in out)-np.prod(np.array(hi)-lo))<1e-7
 return out
cube=cells(rng.uniform(-.95,.95,(36,3)),[-1]*3,[1]*3)
lo=np.array([-2,-.24,.08]);hi=np.array([2,.24,3.08]);pts=rng.uniform(lo+.01,hi-.01,(64,3));cluster=pts.copy();cluster[:36]=np.clip(rng.normal([.2,0,1.7],[.4,.10,.42],(36,3)),lo+.015,hi-.015)
D=dict(cube=cube,uniform=cells(pts,lo,hi),cluster=cells(cluster,lo,hi));(E/'geometry.json').write_text(json.dumps(D));print({k:len(v)for k,v in D.items()})
