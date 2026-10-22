import fs from 'node:fs';import{rng,build,leaves}from './core.mjs';import{createNoise3D}from './vendor/simplex-noise.mjs';
const r=rng(29),n=createNoise3D(rng(381)),base=Array.from({length:96},()=>[r()*1.8-.9,r()*1.8-.9]);
const frames=Array.from({length:1801},(_,i)=>{let t=i/60*.32;let points=base.map(p=>p.map((v,k)=>.98*Math.tanh(v*1.25+1.15*n(p[0]*.75+k*7,p[1]*.75+k*11,t))));let root=build(points,2,5);return{points,cells:leaves(root,5).map(n=>({lo:n.lo,hi:n.hi}))}});
const curve=Array.from({length:161},(_,i)=>[i/160*6-3,n(i/160*2,0,0)]);
fs.writeFileSync('/tmp/kd-motion2.json',JSON.stringify({frames,curve}));
