from pathlib import Path
from PIL import Image,ImageDraw
import vtracer
p=Path(__file__).resolve().parent/'output';p.mkdir(exist_ok=True)
im=Image.new('RGB',(1000,400),'white');d=ImageDraw.Draw(im)
# Original hand-authored lettering, deliberately uneven strokes, not a font.
strokes=[[(140,300),(155,85),(245,220),(335,90),(350,300)],[(470,290),(484,90)],[(433,95),(525,80)],[(435,291),(523,301)],[(640,300),(790,80)],[(640,85),(805,300)]]
for s in strokes:d.line(s,fill='black',width=27,joint='curve');[d.ellipse((x-13,y-13,x+13,y+13),fill='black') for x,y in s]
im.save(p/'handwriting.png')
vtracer.convert_image_to_svg_py(str(p/'handwriting.png'),str(p/'traced.svg'),colormode='binary',mode='spline',filter_speckle=4)
