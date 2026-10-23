const fs=require('fs'),vm=require('vm');const box={};vm.runInNewContext(fs.readFileSync(require('path').join(__dirname,'vendor/d3-delaunay.min.js'),'utf8'),box);const D=box.d3.Delaunay,E=require('path').join(__dirname,'data');
const base=[[.15,.18],[.48,.13],[.84,.24],[.24,.48],[.59,.46],[.88,.64],[.13,.83],[.49,.86],[.75,.87]];
function geom(p){const d=D.from(p),v=d.voronoi([0,0,1,1]);let edges=[];for(let i=0;i<p.length;i++)for(const j of d.neighbors(i))if(i<j)edges.push([i,j]);return{p,tri:Array.from(d.triangles),cells:p.map((_,i)=>Array.from(v.cellPolygon(i)||[])),edges}}
let seed=75;function rand(){seed=(Math.imul(seed,1664525)+1013904223)|0;return(seed>>>0)/4294967296}const dense=Array.from({length:160},()=>[.04+rand()*.92,.04+rand()*.92]);
const frames=Array.from({length:720},(_,f)=>{let t=f/60;return geom(dense.map((p,i)=>[Math.max(.02,Math.min(.98,p[0]+.055*Math.sin(t*.65+i*1.3))),Math.max(.02,Math.min(.98,p[1]+.055*Math.cos(t*.53+i*.8)))]))});
const moving=Array.from({length:360},(_,f)=>{let a=Math.min(1,Math.max(0,(f/60-1.9)/3.2));a=a*a*(3-2*a);return geom([[.18,.22],[.79,.20],[.77+.13*a,.75+.15*a],[.20,.77]])});
fs.writeFileSync(E+'/two-d.json',JSON.stringify({base:geom(base),frames,moving}));console.log('d3 geometry exported');
