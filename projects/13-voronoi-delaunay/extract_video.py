from pathlib import Path
import cv2,numpy as np,json,sys
import argparse
parser=argparse.ArgumentParser(description='Extract tracked points and silhouette from your own video on a dark background.')
parser.add_argument('video');parser.add_argument('--crop',nargs=4,type=int);parser.add_argument('--floor-cut',type=int,default=546);parser.add_argument('--threshold',type=int,default=18)
args=parser.parse_args();E=Path(__file__).resolve().parent/'data';E.mkdir(exist_ok=True)
crop=args.crop;cap=cv2.VideoCapture(args.video);fps=cap.get(cv2.CAP_PROP_FPS);assert fps>0;rows=[];prev=None;pts=None;frame=0
while True:
 ok,im=cap.read()
 if not ok:break
 im=cv2.resize(im[crop[1]:crop[3],crop[0]:crop[2]] if crop else im,(432,546));gray=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY);mask=(gray>args.threshold).astype('uint8')*255
 mask[args.floor_cut:]=0
 mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8));n,labels,stats,_=cv2.connectedComponentsWithStats(mask)
 if n>1:mask=np.uint8(labels==1+np.argmax(stats[1:,cv2.CC_STAT_AREA]))*255
 edges=cv2.Canny(gray,55,130);edges=cv2.bitwise_and(edges,cv2.dilate(mask,np.ones((3,3),np.uint8)))
 boundary=cv2.morphologyEx(mask,cv2.MORPH_GRADIENT,np.ones((3,3),np.uint8));candidates=cv2.bitwise_or(edges,boundary)
 kept=[]
 if prev is not None and pts is not None and len(pts)>0:
  flow,st,err=cv2.calcOpticalFlowPyrLK(prev,gray,pts.reshape(-1,1,2),None,winSize=(21,21),maxLevel=3)
  for p,valid,e in zip(flow[:,0],st[:,0],err[:,0]):
   x,y=map(int,p)
   if valid and e<35 and 0<=x<432 and 0<=y<546 and mask[y,x]:kept.append(p.tolist())
 # Deterministic edge sampling; replenish spatially separated points, not random flicker.
 yy,xx=np.where(candidates);order=np.lexsort((xx//5,yy//5));occup=np.zeros((546,432),np.uint8)
 for x,y in kept:cv2.circle(occup,(int(x),int(y)),9,255,-1)
 for j in order:
  x,y=int(xx[j]),int(yy[j])
  if len(kept)>=480:break
  if not occup[y,x]:kept.append([x,y]);cv2.circle(occup,(x,y),9,255,-1)
 # Sparse interior samples preserve shading and prevent giant cross-body faces.
 for y in range(8,546,22):
  for x in range(8,432,22):
   if len(kept)<560 and mask[y,x] and not occup[y,x]:kept.append([x,y]);cv2.circle(occup,(x,y),9,255,-1)
 pts=np.array(kept,dtype=np.float32);prev=gray
 contours,_=cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
 outline=cv2.approxPolyDP(max(contours,key=cv2.contourArea),.65,True)[:,0].tolist() if contours else [[0,0],[432,0],[432,546],[0,546]]
 rows.append({'p':np.round(pts,1).tolist(),'outline':outline});frame+=1
(E/'ballet.json').write_text(json.dumps({'fps':fps,'frames':rows,'width':432,'height':546},separators=(',',':')));print('tracked',frame,'frames @',fps,'points',min(len(r['p'])for r in rows),max(len(r['p'])for r in rows))
