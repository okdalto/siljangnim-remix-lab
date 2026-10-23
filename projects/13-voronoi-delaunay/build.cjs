const fs=require('fs'),path=require('path'),zlib=require('zlib');const base=__dirname,read=p=>fs.readFileSync(path.join(base,p),'utf8');
const packed=p=>zlib.gzipSync(read(p)).toString('base64');
const notices=['D3-LICENSE','DELAUNATOR-LICENSE','ROBUST-PREDICATES-LICENSE','CANNON-LICENSE'].map(n=>'/* '+n+'\n'+read('vendor/'+n)+' */').join('\n');
const setup=`${notices}\n// Third-party notices: see vendor/*LICENSE. d3-delaunay ISC, cannon-es MIT.\nconst d3=(()=>{const exports={};const module={exports};${read('vendor/d3-delaunay.min.js')};return exports;})();\nconst CANNON=(()=>{const exports={};${read('vendor/cannon-es.cjs.js').replace("require('perf_hooks') && require('perf_hooks').performance || {}","globalThis.performance || {}")};return exports;})();\nasync function unpack(b){const a=Uint8Array.from(atob(b),c=>c.charCodeAt(0));return JSON.parse(await new Response(new Blob([a]).stream().pipeThrough(new DecompressionStream('gzip'))).text());}\nconst GEOMETRY=await unpack('${packed('data/geometry.json')}');\nconst BALLET=await unpack('${packed('data/ballet.json')}');\n${read('core.cjs')}\n${read('setup.js')}`;
const num=(value,min,max,step,label,type='float')=>({type,value,min,max,step,label});
const scene={version:2,backend:'webgl2',inputs:['mouse'],script:{setup,render:read('render.js'),cleanup:''},uniforms:{
 u_mode:{...num(0,0,3,1,'Study','int'),widget:'select',options:['Voronoi & Delaunay','Ballet points','3D Voronoi','Wall physics'].map((label,value)=>({label,value}))},
 u_pause:{type:'bool',value:false,label:'Pause'},u_reset:{type:'bool',value:false,widget:'button',label:'Restart'},
 u_count:num(40,4,160,1,'2D point count','int'),u_seed:num(75,1,999,1,'2D seed','int'),
 u_cells:{type:'bool',value:true,label:'Voronoi regions'},u_edges:{type:'bool',value:true,label:'Delaunay edges'},u_points:{type:'bool',value:true,label:'Show points'},u_mix:num(.65,0,1,.01,'Region brightness'),
 u_explode:num(.35,0,1.5,.01,'3D separation'),u_cluster:{type:'bool',value:false,label:'Cluster wall seeds'}
}};
fs.writeFileSync(path.join(base,'scene.json'),JSON.stringify(scene));
fs.writeFileSync(path.join(base,'project.md'),'---\ntitle: Voronoi and Delaunay\nsiljangnim: 2\nbackend: webgl2\nassets: []\n---\n\n# Voronoi and Delaunay\n\nFour runnable studies, all dependencies embedded. No API key or downloads. Select Study; pause/restart or change parameters. 3D cells are precomputed; wall rigid-body dynamics are live. Ballet points come from generated source footage, not live tracking. Full provenance and third-party notices in README.md and vendor/.\n\n## Scene\n\n```json\n'+JSON.stringify(scene)+'\n```\n');
console.log('Built scene.json and project.md');
