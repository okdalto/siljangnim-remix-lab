import assert from 'node:assert/strict';
import {createSimulation} from './simulation.mjs';
import './browser/verify.mjs';
const a=createSimulation(),b=createSimulation();let first,last;
for(let f=0;f<240;f++){
 const r=a.step(1/60,9),q=b.step(1/60,9);assert.deepEqual(r.cells,q.cells);
 assert.equal(r.cells.length,512);let volume=0;
 for(const c of r.cells){let v=1;for(let k=0;k<3;k++){assert(Number.isFinite(c.lo[k])&&Number.isFinite(c.hi[k]));assert(c.hi[k]>c.lo[k]);v*=c.hi[k]-c.lo[k]}volume+=v}assert(Math.abs(volume-8)<1e-9);
 if(!first)first=JSON.stringify(r.cells);last=JSON.stringify(r.cells);
}
assert.notEqual(first,last);
const exact=a.step(0,9,1,true);function check(n,cells){if(!n.children){const c=cells.shift();n.lo.forEach((x,k)=>assert(Math.abs(x-c.lo[k])<1e-10));n.hi.forEach((x,k)=>assert(Math.abs(x-c.hi[k])<1e-10));}else n.children.forEach(c=>check(c,cells))}check(exact.root,[...exact.cells]);
for(const d of [2,5,9])assert.equal(a.step(1/60,d).cells.length,2**d);
console.log('240 deterministic animated frames; volume, finite bounds, exact mode and depth controls passed.');
