const assert=require('node:assert/strict'),fs=require('fs'),path=require('path'),vm=require('vm');
const C=require('./vendor/cannon-es.cjs.js'),{makeWall}=require('./core.cjs');
const data=JSON.parse(fs.readFileSync(path.join(__dirname,'data/geometry.json')));
const box={};vm.runInNewContext(fs.readFileSync(path.join(__dirname,'vendor/d3-delaunay.min.js'),'utf8'),box);const D=box.d3.Delaunay;
let queries=0;
for(let frame=0;frame<90;frame++){
 const p=Array.from({length:40},(_,i)=>[.5+.42*Math.sin(i*12.7+frame*.006),.5+.42*Math.cos(i*9.1+frame*.008)]),d=D.from(p),v=d.voronoi([0,0,1,1]);
 let area=0;for(let i=0;i<p.length;i++){const c=v.cellPolygon(i);let a=0;for(let j=1;j<c.length;j++)a+=c[j-1][0]*c[j][1]-c[j][0]*c[j-1][1];area+=Math.abs(a)/2;for(const q of c){const dist=(q[0]-p[i][0])**2+(q[1]-p[i][1])**2;assert(p.every(r=>dist<=(q[0]-r[0])**2+(q[1]-r[1])**2+1e-8));}}
 assert(Math.abs(area-1)<1e-8);
 for(let j=0;j<20;j++){const q=[j/19,((j*7)%19)/19],idx=d.find(...q),ds=p.map(r=>(r[0]-q[0])**2+(r[1]-q[1])**2);assert(ds[idx]<=Math.min(...ds)+1e-10);queries++;}
}
const walls={};for(const key of ['uniform','cluster']){
 const sim=makeWall(C,data[key]);let maxZ=-Infinity;
 for(let f=0;f<540;f++){sim.stepFrame();for(const b of sim.bodies){assert([...b.position.toArray(),...b.quaternion.toArray()].every(Number.isFinite));maxZ=Math.max(maxZ,b.position.z);}}
 assert(sim.impact!==null);assert(maxZ<3.5);assert(sim.bodies.every(b=>b.velocity.length()<.02));
 walls[key]={impact:sim.impact,maxCenterHeight:maxZ,finalMaxSpeed:Math.max(...sim.bodies.map(b=>b.velocity.length()))};
 assert(Math.abs(data[key].reduce((a,c)=>a+c.volume,0)-5.76)<1e-7);
}
assert(Math.abs(data.cube.reduce((a,c)=>a+c.volume,0)-8)<1e-7);
const ballet=JSON.parse(fs.readFileSync(path.join(__dirname,'data/ballet.json')));assert.equal(ballet.frames.length,193);for(const f of ballet.frames){assert(f.outline.length>3);assert(f.p.flat().every(Number.isFinite));}
const result={nearestQueries:queries,animatedPartitions:90,cubeVolume:8,wallVolume:5.76,wallFrames:540,walls,balletFrames:193};console.log(JSON.stringify(result,null,2));fs.writeFileSync(path.join(__dirname,'verification.json'),JSON.stringify(result,null,2)+'\n');
