const s=ctx.state,u=ctx.uniforms,gl=ctx.gl,[w,h]=ctx.resolution;
if(s.mode!==u.u_filter){s.out=s.apply(s.rgb,s.n,u.u_filter);s.mode=u.u_filter;s.clock=0;}
if(u.u_reset)s.clock=0;
if(!u.u_pause)s.clock+=Math.min(ctx.dt,.05)*u.u_speed;
const x=u.u_x,y=u.u_y,result=s.pixel(s.rgb,s.n,x,y,u.u_filter),c=s.c;
if(s.canvas.width!==w||s.canvas.height!==h){s.canvas.width=w;s.canvas.height=h;}
c.fillStyle='#0b0b0b';c.fillRect(0,0,w,h);
const scale=Math.min(w/1080,h/1350), ox=(w-1080*scale)/2,oy=(h-1350*scale)/2;
c.save();c.translate(ox,oy);c.scale(scale,scale);
const color=a=>'rgb('+a.map(v=>Math.round(Math.max(0,Math.min(1,v))*255)).join(',')+')';
function grid(rgb,n,X,Y,size){let step=size/n;for(let j=0;j<n;j++)for(let i=0;i<n;i++){c.fillStyle=color(rgb.slice((j*n+i)*3,(j*n+i)*3+3));c.fillRect(X+i*step,Y+j*step,step-.5,step-.5);}}
function text(t,x,y,size=28,color='#fff'){c.fillStyle=color;c.font=`${size}px sans-serif`;c.textAlign='center';c.fillText(t,x,y);}
text('CONVOLUTION',540,80,48);text('Image · 32 × 32',285,160);text(['Identity','Blur','Sharpen','Sobel magnitude','Laplacian magnitude'][u.u_filter]+' · 30 × 30',795,160,26);
grid(s.rgb,32,75,190,420);grid(s.out,30,585,190,420);
c.strokeStyle='#78ffd3';c.lineWidth=4;c.strokeRect(75+x*420/32,190+y*420/32,3*420/32,3*420/32);c.strokeRect(585+x*14,190+y*14,14,14);
text('3 × 3 neighbourhood × filter → one output pixel',540,690,28);
const phase=s.clock%5,active=Math.min(8,Math.floor(phase/.25));
for(let j=0;j<3;j++)for(let i=0;i<3;i++){
 const q=j*3+i,t=result.terms[q],X=130+i*82,Y=760+j*82;
 c.fillStyle=color(t.input);c.fillRect(X,Y,72,72);c.fillStyle='#142a24';c.fillRect(X+290,Y,72,72);
 text(t.weight.toFixed(u.u_filter===1?2:0),X+326,Y+46,25);
 if(q===active&&phase<2.3){c.strokeStyle='#78ffd3';c.strokeRect(X-2,Y-2,76,76);c.strokeRect(X+288,Y-2,76,76);}
}
text('×',390,900,42);text('→',735,900,42);c.fillStyle=color(result.rgb);c.fillRect(805,825,110,110);
text('RGB '+result.rgb.map(v=>Math.round(v*255)).join(' / '),860,980,22);
text('Sum RGB: '+result.sum.map(v=>v.toFixed(3)).join(' / '),540,1080,25);
text(u.u_filter===3?'Sobel combines horizontal + vertical brightness responses.':u.u_filter===4?'Absolute luminance response; display clipped to [0, 1].':'Add weighted values per channel; display clipped to [0, 1].',540,1130,23,'#b9c9c3');
text('Change Filter or select an output pixel in the controls.',540,1220,24,'#b9c9c3');
c.restore();gl.disable(gl.DEPTH_TEST);gl.bindTexture(gl.TEXTURE_2D,s.tex);gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,false);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,s.canvas);gl.useProgram(s.program);ctx.utils.bindTexture(s.program,'u_canvas',s.tex,0);ctx.utils.drawFullscreen(s.program);
ctx.publish('Output pixel',`${x}, ${y}`);ctx.publish('Raw weighted RGB',result.sum.map(v=>v.toFixed(4)).join(', '));
