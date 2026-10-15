"""Real input-photo segmentation → textured cell packing, no replacement icon geometry."""
from pathlib import Path
import argparse,json,subprocess,hashlib
import cv2,numpy as np
from PIL import Image,ImageDraw,ImageFont
p=Path(__file__).parent
ap=argparse.ArgumentParser();ap.add_argument('--cols',type=int,default=2);ap.add_argument('--rows',type=int,default=3);ap.add_argument('--board-width',type=int,default=22);ap.add_argument('--sequence',default='0,4,4,1,2,3,5,4,0,1,2,3');ap.add_argument('--simulate-only',action='store_true');args=ap.parse_args()
source=Image.open(p/'assets.png').convert('RGBA');sw,sh=source.size
CELL=22;BW=args.board_width;BH=36;OX=(720-BW*CELL)//2;OY=300
objects=[];segment=[]
for k in range(args.cols*args.rows):
 col=k%args.cols;row=k//args.cols
 tile=np.asarray(source.crop((round(col*sw/args.cols),round(row*sh/args.rows),round((col+1)*sw/args.cols),round((row+1)*sh/args.rows))))
 original_alpha=tile[:,:,3];has_alpha=bool(np.any(original_alpha<250));tile=tile[:,:,:3]
 hsv=cv2.cvtColor(tile,cv2.COLOR_RGB2HSV)
 # Remove white background and pale drop shadows using actual image colours.
 initial=(original_alpha>20) if has_alpha else (((hsv[:,:,1]>25)&(hsv[:,:,2]<254))|(hsv[:,:,2]<205))
 n,labels,stats,cent=cv2.connectedComponentsWithStats(initial.astype(np.uint8),8)
 if n<2:raise RuntimeError(f'No foreground in tile{k}')
 biggest=1+np.argmax(stats[1:,cv2.CC_STAT_AREA]);mask=(labels==biggest).astype(np.uint8)*255
 # Retain nearby detached metal tips only if sufficiently large, while dropping noise.
 for j in range(1,n):
  if stats[j,cv2.CC_STAT_AREA]>stats[biggest,cv2.CC_STAT_AREA]*.08:mask[labels==j]=255
 mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
 if has_alpha:mask=np.minimum(mask,original_alpha)
 ys,xs=np.where(mask>0);x0,x1=max(0,int(xs.min())-2),min(tile.shape[1],int(xs.max())+3);y0,y1=max(0,int(ys.min())-2),min(tile.shape[0],int(ys.max())+3)
 rgba=Image.fromarray(np.dstack([tile,mask]),'RGBA').crop((x0,y0,x1,y1))
 # All objects are large, maintaining photographed aspect ratio.
 scale=240/max(rgba.size);nw=max(12,round(rgba.width*scale));nh=max(12,round(rgba.height*scale));rgba=rgba.resize((nw,nh),Image.Resampling.LANCZOS)
 ww=int(np.ceil(nw/CELL));hh=int(np.ceil(nh/CELL));pad=Image.new('RGBA',(ww*CELL,hh*CELL));pad.paste(rgba,(0,0),rgba)
 a=np.asarray(pad);coverage=(a[:,:,3]/255).reshape(hh,CELL,ww,CELL).transpose(0,2,1,3).mean((2,3));cells=(coverage>.11).astype(np.uint8)
 # Every retained occupied cell stores the ORIGINAL photograph RGBA tile.
 rgba.save(p/f'object-{k}.png');Image.fromarray(mask).save(p/f'mask-{k}.png');objects.append((cells,a.copy()));segment.append({'tile':k,'crop':[x0,y0,x1,y1],'cells':int(cells.sum()),'width_cells':ww,'height_cells':hh,'foreground_pixels':int((mask>0).sum())})
board=np.zeros((BH,BW),np.uint8);texture=np.zeros((BH,BW,CELL,CELL,4),np.uint8);events=[]
seq=[int(v) for v in args.sequence.split(',')]
def candidate(shape,tex):
 for r in range(4):
  s=np.rot90(shape,r);im=np.rot90(tex,r);h,w=s.shape
  for xx in range(BW-w+1):
   yy=0
   def fits(y):return y+h<=BH and not np.any(board[y:y+h,xx:xx+w]*s)
   if not fits(0):continue
   while fits(yy+1):yy+=1
   b=board.copy();b[yy:yy+h,xx:xx+w]|=s
   heights=[BH-np.argmax(c) if np.any(c) else 0 for c in b.T];holes=sum(np.sum(c[np.argmax(c):]==0) if np.any(c) else 0 for c in b.T);lines=int(np.all(b,axis=1).sum());bump=sum(abs(a-b) for a,b in zip(heights,heights[1:]));score=lines*140-holes*6-sum(heights)*.8-max(heights)*.3-bump*.2
   yield score,s,im,xx,yy,r

def texture_image(t):
 arr=t.transpose(0,2,1,3,4).reshape(BH*CELL,BW*CELL,4)
 return Image.fromarray(arr.copy(),'RGBA')
for step,k in enumerate(seq):
 options=list(candidate(*objects[k]));
 if not options:break
 _,s,tex,xx,yy,rotation=max(options,key=lambda q:q[0]);h,w=s.shape;before=texture_image(texture)
 for y,x in zip(*np.where(s)):
  board[yy+y,xx+x]=1;texture[yy+y,xx+x]=tex[y*CELL:(y+1)*CELL,x*CELL:(x+1)*CELL]
 landed=texture_image(texture);full=np.all(board,axis=1);clear=int(full.sum())
 if clear:
  board=np.vstack([np.zeros((clear,BW),np.uint8),board[~full]])
  texture=np.concatenate([np.zeros((clear,BW,CELL,CELL,4),np.uint8),texture[~full]],axis=0)
 after=texture_image(texture);events.append({'kind':k,'shape':s,'rgba':Image.fromarray(tex.copy(),'RGBA'),'x':xx,'y':yy,'rotation':rotation,'before':before,'landed':landed,'after':after,'cleared':clear,'rows':np.where(full)[0].tolist()})
metric={'board':[BW,BH],'sequence':seq,'source_size':[sw,sh],'source_layout':[args.cols,args.rows],'segmentation':segment,'pieces_placed':len(events),'lines_cleared':sum(e['cleared'] for e in events),'events':[{k:(v.tolist() if isinstance(v,np.ndarray) else v) for k,v in e.items() if k not in ['rgba','before','landed','after']} for e in events]};(p/'metrics.json').write_text(json.dumps(metric,indent=2))
if args.simulate_only:
 print('SIMULATION',len(events),sum(e['cleared'] for e in events));raise SystemExit
def portable_font(size):
 try: return ImageFont.truetype("DejaVuSans.ttf",size)
 except OSError: return ImageFont.load_default(size=size)
font=portable_font
proc=subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s','720x1280','-r','30','-i','-','-an','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(p/'preview.mp4')],stdin=subprocess.PIPE)
for f in range(600):
 t=f/30;im=Image.new('RGB',(720,1280),'#151b22');d=ImageDraw.Draw(im);d.text((360,135),'DESK OBJECTS.',font=font(47),fill='white',anchor='mt');d.text((360,195),'TETRIS RULES.',font=font(47),fill='white',anchor='mt')
 if t<1.5:
  show=source.copy();show.thumbnail((600,720));im.paste(show,((720-show.width)//2,340+(720-show.height)//2),show)
 else:
  phase=(t-1.5)/1.0;ix=min(len(events)-1,int(phase));e=events[ix];q=phase-int(phase);settled=q>.88 or phase>=len(events)
  img=e['after'] if settled else e['landed'] if q>.7 else e['before'];im.paste(img,(OX,OY),img)
  if q<=.7 and not settled:
   yy=-e['rgba'].height+(e['y']*CELL+e['rgba'].height)*(q/.7)**2
   piece=e['rgba'];dest=Image.new('RGBA',(BW*CELL,BH*CELL));dest.paste(piece,(e['x']*CELL,round(yy)),piece);im.paste(dest,(OX,OY),dest)
  if .7<q<=.88 and e['cleared']:
   for row in e['rows']:d.rectangle((OX,OY+row*CELL,OX+BW*CELL,OY+(row+1)*CELL),fill='#eef4d0')
  d.rectangle((OX-2,OY-2,OX+BW*CELL+2,OY+BH*CELL+2),outline='#4b5661',width=2)
  clears=sum(e0['cleared'] for e0 in events[:ix+(1 if settled else 0)]);d.text((360,1150),f'{ix+1} objects · {clears} rows cleared',font=font(33),fill='white',anchor='mt')
 proc.stdin.write(im.tobytes())
proc.stdin.close();assert proc.wait()==0
(p/'provenance.json').write_text(json.dumps({'input':'assets.png; generated photo-style sprite sheet, not a real camera photograph','input_sha256':hashlib.sha256((p/'assets.png').read_bytes()).hexdigest(),'segmentation':'original alpha first; actual HSV white-background key fallback + connected components +3px closing; internal holes retained','texture':'actual input RGBA pixels rotate and fall with pieces; per-cell RGBA tiles remain on board and shift after line clears','packing':'actual exhaustive rotation/x search, gravity drop, occupancy collision, complete-row deletion','source_code':'make.py','output':'720x1280,30fps,20s; full 12-object run followed by final board hold'},indent=2))
