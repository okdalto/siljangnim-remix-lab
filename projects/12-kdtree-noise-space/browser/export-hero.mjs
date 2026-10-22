import fs from 'node:fs';
import {rng,build} from './core.mjs';
import {createNoise4D} from './vendor/simplex-noise.mjs';
const rand=rng(117),noise=createNoise4D(rng(381)),fps=60,seconds=6.5,dt=1/240;
const base=Array.from({length:1024},()=>Array.from({length:3},()=>rand()*2-1));
function target(p,k,time){return .98*Math.tanh(p[k]*1.25+1.15*noise(p[0]*.75+k*7,p[1]*.75+k*11,p[2]*.75+k*13,time*.24))}
const positions=base.map(p=>p.map((_,k)=>target(p,k,-3))),velocities=base.map(()=>[0,0,0]),planes=new Map();
const mass=1,stiffness=12,damping=2*Math.sqrt(mass*stiffness);
function integrate(x,v,goal,h,k=stiffness,c=damping){const a=(k*(goal-x)-c*v)/mass;v+=a*h;return[x+v*h,v]}
function partition(node,lo,hi,path='',out=[]){
 if(!node.children){out.push({lo,hi});return out}
 const axis=node.axis,goal=(node.split-node.lo[axis])/(node.hi[axis]-node.lo[axis]);
 let q=planes.get(path)||[goal,0];for(let j=0;j<4;j++)q=integrate(...q,goal,dt,25,10);planes.set(path,q);
 const split=lo[axis]+(hi[axis]-lo[axis])*Math.max(.025,Math.min(.975,q[0]));const a=[...hi],b=[...lo];a[axis]=b[axis]=split;
 partition(node.children[0],lo,a,path+'0',out);partition(node.children[1],b,hi,path+'1',out);return out;
}
const frames=[];
for(let frame=-180;frame<=seconds*fps;frame++){
 for(let j=0;j<4;j++){let t=frame/fps+j*dt;for(let i=0;i<base.length;i++)for(let k=0;k<3;k++){const q=integrate(positions[i][k],velocities[i][k],target(base[i],k,t),dt);positions[i][k]=q[0];velocities[i][k]=q[1]}}
 const root=build(positions.map(p=>[...p]),3,9);const cells=partition(root,[-1,-1,-1],[1,1,1]);
 const volume=cells.reduce((s,n)=>s+n.hi.reduce((v,x,k)=>v*(x-n.lo[k]),1),0);
 if(Math.abs(volume-8)>1e-9)throw Error('Partition volume mismatch');
 if(frame>=0)frames.push(cells);
}
fs.writeFileSync('/tmp/kd-hero.json',JSON.stringify({frames,fps,seconds,seed:117,pointCount:base.length,depth:9,physics:{mass,stiffness,damping,substeps:4,noiseRate:.24,warmupSeconds:3,planeStiffness:25,planeDamping:10},field:'Noise targets drive damped point masses; KD-tree rebuilt each frame; displayed split ratios also follow critically damped springs to suppress median-order jumps. Shared hierarchical split planes preserve a valid partition, with deliberate visual lag relative to exact median splits.'}));
console.log('Verified',frames.length,'spring frames; partition volume=8');
