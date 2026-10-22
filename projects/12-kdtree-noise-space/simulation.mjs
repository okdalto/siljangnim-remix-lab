import {rng,build} from './core.mjs';
import {createNoise4D} from './vendor/simplex-noise.mjs';
export function createSimulation(seed=117){
 const rand=rng(seed),noise=createNoise4D(rng(381));
 const base=Array.from({length:1024},()=>Array.from({length:3},()=>rand()*2-1));
 const target=(p,k,t)=>.98*Math.tanh(p[k]*1.25+1.15*noise(p[0]*.75+k*7,p[1]*.75+k*11,p[2]*.75+k*13,t*.24));
 const positions=base.map(p=>p.map((_,k)=>target(p,k,0))),velocities=base.map(()=>[0,0,0]),planes=new Map();
 let time=0;
 return {positions,step(dt,depth=9,damping=1,exact=false){
  dt=Math.max(0,Math.min(dt,1/30));const steps=Math.max(1,Math.ceil(dt*240)),h=dt/steps;
  for(let j=0;j<steps;j++){time+=h;for(let i=0;i<base.length;i++)for(let k=0;k<3;k++){
   velocities[i][k]+=(12*(target(base[i],k,time)-positions[i][k])-2*Math.sqrt(12)*damping*velocities[i][k])*h;
   positions[i][k]+=velocities[i][k]*h;
  }}
  const root=build(positions,3,depth),cells=[];
  function visit(n,lo,hi,path=''){
   if(!n.children){cells.push({lo,hi,path});return}
   const a=n.axis,goal=(n.split-n.lo[a])/(n.hi[a]-n.lo[a]);let q=planes.get(path)||[goal,0];
   for(let j=0;j<steps;j++){q[1]+=(25*(goal-q[0])-10*q[1])*h;q[0]+=q[1]*h}planes.set(path,q);
   const split=lo[a]+(hi[a]-lo[a])*(exact?goal:Math.max(.025,Math.min(.975,q[0])));
   const l=[...hi],r=[...lo];l[a]=r[a]=split;visit(n.children[0],lo,l,path+'0');visit(n.children[1],r,hi,path+'1');
  }
  visit(root,[-1,-1,-1],[1,1,1]);return {root,cells,time};
 }};
}
