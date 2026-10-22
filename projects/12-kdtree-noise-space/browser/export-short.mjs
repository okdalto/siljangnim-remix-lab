import fs from'node:fs';import{rng,build,leaves,nearest}from'./core.mjs';import{createNoise2D,createNoise3D}from'./vendor/simplex-noise.mjs';
const n2=createNoise2D(rng(74)),n3=createNoise3D(rng(75)),r=rng(76),a=[],b=[];
while(a.length<4096){let p=[r()*2-1,r()*2-1],n=n2(...p.map(v=>v*1.8));if(r()<.035+Math.exp(-n*n*25))a.push(p)}
while(b.length<8192){let p=[r()*2-1,r()*2-1,r()*2-1],n=n3(...p.map(v=>v*1.8));if(r()<.045+Math.exp(-n*n*22))b.push(p)}
let rr=rng(29),plain=build(Array.from({length:96},()=>[rr()*1.8-.9,rr()*1.8-.9]),2,7),query=[.28,.17];
function slim(n,noise){let mid=n.lo.map((v,k)=>(v+n.hi[k])/2);return{lo:n.lo,hi:n.hi,id:n.id,depth:n.depth,axis:n.axis,split:n.split,value:noise?noise(...mid.map(v=>v*1.8)):0}}
let t2=build(a,2,9),t3=build(b,3,8),res=nearest(plain,query,4),splits=[];function walk(n){if(n.children){splits.push(slim(n));n.children.forEach(walk)}}walk(plain);
const data={plain:plain.points,query,nearest:res.best,checked:res.checked,pruned:res.pruned.map(n=>slim(n)),splits,points2:a.filter((_,i)=>i%16===0),points3:b.filter((_,i)=>i%32===0),levels2:Array.from({length:10},(_,d)=>leaves(t2,d).map(n=>slim(n,n2))),levels3:Array.from({length:9},(_,d)=>leaves(t3,d).map(n=>slim(n,n3))),field:Array.from({length:80},(_,y)=>Array.from({length:80},(_,x)=>n2((x/79*2-1)*1.8,(y/79*2-1)*1.8)))};
fs.writeFileSync('/tmp/kd-short-data.json',JSON.stringify(data));console.log('exported actual KD/noise results');
