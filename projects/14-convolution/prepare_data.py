"""Rebuild embedded input/reference outputs from the attributed dog photo.
Optional argument: your own photo; -- build.cjs afterwards.
"""
from pathlib import Path
import json,sys,numpy as np
D=Path(__file__).resolve().parent
sys.path.insert(0,str(D/'original'))
import convolution as c
x=c.load_image(Path(sys.argv[1]) if len(sys.argv)>1 else D/'original/assets/dog.jpg')[::-1].copy()
(D/'data.json').write_text(json.dumps({'n':32,'rgb':x.flatten().tolist()}))
w=np.lib.stride_tricks.sliding_window_view(x,(3,3),axis=(0,1))
ks=[[[0,0,0],[0,1,0],[0,0,0]],np.ones((3,3))/9,[[0,-1,0],[-1,5,-1],[0,-1,0]],None,[[-1,-1,-1],[-1,8,-1],[-1,-1,-1]]]
out=[]
for i,k in enumerate(ks):
 if i==3:y=np.repeat(c.sobel(x)[1][...,None],3,axis=2)
 else:
  y=np.einsum('xycij,ij->xyc',w,np.array(k))
  if i==4:y=np.repeat(np.abs(y@np.array([.2126,.7152,.0722]))[...,None],3,axis=2)
 out.append(np.clip(y,0,1).flatten().tolist())
(D/'expected.json').write_text(json.dumps(out))
