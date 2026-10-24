// GPL-3.0-or-later. All filters operate on RGB, valid stride 1.
const KERNELS=[[0,0,0,0,1,0,0,0,0],Array(9).fill(1/9),[0,-1,0,-1,5,-1,0,-1,0],[-1,0,1,-2,0,2,-1,0,1],[-1,-1,-1,-1,8,-1,-1,-1,-1]];
const GY=[-1,-2,-1,0,0,0,1,2,1], LUMA=[.2126,.7152,.0722];
function pixel(rgb,n,x,y,mode){
 const k=KERNELS[mode],a=[0,0,0],b=[0,0,0],terms=[];
 for(let j=0;j<3;j++)for(let i=0;i<3;i++){
  const input=rgb.slice(((y+j)*n+x+i)*3,((y+j)*n+x+i)*3+3),q=j*3+i;
  terms.push({input,weight:k[q],weighted:input.map(v=>v*k[q])});
  for(let c=0;c<3;c++){a[c]+=input[c]*k[q];b[c]+=input[c]*GY[q];}
 }
 const dot=v=>v.reduce((s,a,i)=>s+a*LUMA[i],0),clamp=x=>Math.max(0,Math.min(1,x));
 const value=mode===3?Math.hypot(dot(a),dot(b))/4:Math.abs(dot(a));
 return {rgb:mode>=3?[clamp(value),clamp(value),clamp(value)]:a.map(clamp),sum:a,gy:b,terms};
}
function apply(rgb,n,mode){const out=[];for(let y=0;y<n-2;y++)for(let x=0;x<n-2;x++)out.push(...pixel(rgb,n,x,y,mode).rgb);return out;}
if(typeof module!=='undefined')module.exports={KERNELS,pixel,apply};
