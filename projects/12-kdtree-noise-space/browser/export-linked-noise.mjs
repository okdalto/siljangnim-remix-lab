import fs from 'node:fs';import{rng,build,leaves}from './core.mjs';import{createNoise3D}from './vendor/simplex-noise.mjs';
const r=rng(29),n=createNoise3D(rng(381)),base=Array.from({length:96},()=>[r()*1.8-.9,r()*1.8-.9]);
const mass=1,stiffness=12,damping=2*Math.sqrt(12),dt=1/240,rate=.42;
let displacement=.32*n(-3*rate,0,0),velocity=0;const frames=[];
for(let i=-180;i<=1200;i++){
 for(let sub=0;sub<4;sub++){
  const target=.32*n((i/60+sub*dt)*rate,0,0);
  const acceleration=(stiffness*(target-displacement)-damping*velocity)/mass;
  velocity+=acceleration*dt;displacement+=velocity*dt;
 }
 if(i<0)continue;
 const t=i/60*rate,value=n(t,0,0),points=base.map(p=>[p[0]*.65+displacement,p[1]*.85]),root=build(points,2,5);
 frames.push({value,displacement,velocity,points,split:root.split,curve:Array.from({length:121},(_,j)=>n(t+(j/120-.5)*3,0,0)),cells:leaves(root,5).map(n=>({lo:n.lo,hi:n.hi}))});
}
const zero=build(base.map(p=>[p[0]*.65,p[1]*.85]),2,5).split;
for(const f of frames){
 if(Math.abs(f.split-zero-f.displacement)>1e-10)throw Error('Spring boundary check failed');
 const area=f.cells.reduce((s,c)=>s+(c.hi[0]-c.lo[0])*(c.hi[1]-c.lo[1]),0);if(Math.abs(area-4)>1e-9)throw Error('Partition area mismatch');
}
fs.writeFileSync('/tmp/kd-linked-noise.json',JSON.stringify({base,frames,featured:24,physics:{mass,stiffness,damping,substeps:4,warmupSeconds:3},description:'Displayed curve is the raw Noise target; point displacement follows a critically damped mass. KD-tree rebuilt from those points. Since all x positions share the same spring displacement, split planes inherit smooth motion exactly without extra visual lag.',verified:frames.length}));
console.log('Verified 1201 frames: spring-driven points, exact KD boundary displacement, partition area=4');
