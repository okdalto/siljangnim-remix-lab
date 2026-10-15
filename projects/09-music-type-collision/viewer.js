const THREE=await import('https://esm.sh/three@0.180.0');
const {SVGLoader}=await import('https://esm.sh/three@0.180.0/examples/jsm/loaders/SVGLoader.js');
const svg=await (await fetch('assets/traced.svg')).text();
const canvas=document.createElement('canvas');
const renderer=new THREE.WebGLRenderer({canvas,antialias:true,preserveDrawingBuffer:true});renderer.setSize(720,1280);renderer.setPixelRatio(1);
renderer.setClearColor('#0c1016');renderer.outputColorSpace=THREE.SRGBColorSpace;
const scene=new THREE.Scene();const camera=new THREE.OrthographicCamera(-3.6,3.6,6.4,-6.4,.1,100);camera.position.set(0,0,17);
scene.add(new THREE.HemisphereLight(0xffffff,0x596278,2.2));const key=new THREE.DirectionalLight(0xffffff,3.2);key.position.set(-4,5,8);scene.add(key);const fill=new THREE.DirectionalLight(0x75aaff,2);fill.position.set(5,-2,2);scene.add(fill);
const data=new SVGLoader().parse(svg), root=new THREE.Group();scene.add(root);const meshes=[];
for(const path of data.paths){for(const shape of SVGLoader.createShapes(path)){
 const geo=new THREE.ExtrudeGeometry(shape,{depth:35,bevelEnabled:true,bevelSize:5,bevelThickness:5,bevelSegments:3,steps:1});geo.computeBoundingBox();const bb=geo.boundingBox;const center=bb.getCenter(new THREE.Vector3());geo.translate(-center.x,-center.y,-center.z);geo.scale(.009,-.009,.012);
 const mesh=new THREE.Mesh(geo,new THREE.MeshStandardMaterial({color:[0xf1ff72,0x78f3bf,0x76baf8,0xff87ac][meshes.length%4],roughness:.3,metalness:.12}));mesh.position.set((center.x-475)*.012,(190-center.y)*.012,0);mesh.userData.home=mesh.position.clone();root.add(mesh);meshes.push(mesh);
}}

document.querySelector('#stage').append(canvas);
root.rotation.x=0;meshes.sort((a,b)=>a.userData.home.x-b.userData.home.x);
const physics=(await (await fetch('output/metrics.json')).json()).states;
const audio=document.querySelector('audio');let start=null;
document.querySelector('button').onclick=async()=>{audio.currentTime=0;await audio.play();start=performance.now();};
function draw(now){const t=start===null?0:(now-start)/1000;const sample=Math.min(physics.length-1,Math.floor(t*30));
 for(let k=0;k<meshes.length;k++){const m=meshes[k],b=physics[sample][k];m.position.set((b.x-360)/100,(640-b.y)/100,0);m.rotation.set(.10,.10,-b.angle);m.scale.set(1,1,1.6);}
 renderer.render(scene,camera);requestAnimationFrame(draw);
}requestAnimationFrame(draw);
