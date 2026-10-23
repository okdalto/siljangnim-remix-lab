const fs=require('fs');const C=require('./vendor/cannon-es.cjs.js');const E=require('path').join(__dirname,'data');const data=JSON.parse(fs.readFileSync(E+'/geometry.json'));
for(const key of ['uniform','cluster']){
const world=new C.World({gravity:new C.Vec3(0,0,-9.81)});world.solver.iterations=60;world.allowSleep=true;world.defaultContactMaterial.contactEquationStiffness=1e5;world.defaultContactMaterial.contactEquationRelaxation=8;world.defaultContactMaterial.friction=.55;world.defaultContactMaterial.restitution=0;
const ground=new C.Body({mass:0,shape:new C.Plane()});world.addBody(ground);
const bodies=data[key].map(cell=>{const shape=new C.ConvexPolyhedron({vertices:cell.vertices.map(p=>new C.Vec3(...p.map(x=>x*.995))),faces:cell.faces});const b=new C.Body({mass:0,shape,position:new C.Vec3(...cell.center),linearDamping:.12,angularDamping:.25,allowSleep:true,sleepSpeedLimit:.08,sleepTimeLimit:1});world.addBody(b);return b});
const ball=new C.Body({mass:8,shape:new C.Sphere(.32),position:new C.Vec3(.2,-3,1.7)});ball.velocity.set(0,4,0);ball.collisionResponse=true;world.addBody(ball);let impact=null;
for(const b of bodies)b.addEventListener('collide',e=>{if(e.body===ball&&impact===null)impact=world.time});
const frames=[];let released=false;
for(let f=0;f<540;f++){
 // Hold the incoming projectile level until collision; wall pieces have support until first contact.
 
 for(let j=0;j<8;j++){
  // Release before contact is solved, so no static-wall impulse or velocity reset.
  if(!released&&ball.position.y>=-.60){released=true;bodies.forEach((b,i)=>{b.type=C.Body.DYNAMIC;b.mass=data[key][i].volume*10;b.updateMassProperties();b.updateInertiaWorld(true);b.wakeUp()});world.broadphase.dirty=true;}
  if(impact===null)ball.force.z+=ball.mass*9.81;
  world.step(1/480);
 }

 const trans=bodies.map(b=>[...b.position.toArray(),...b.quaternion.toArray()]);if(!trans.flat().every(Number.isFinite))throw Error('nonfinite');frames.push({pieces:trans,ball:ball.position.toArray()});
}
if(impact===null)throw Error('no impact');fs.writeFileSync(E+'/'+key+'-physics.json',JSON.stringify({fps:60,impact,frames,model:'Prefractured convex pieces, supports removed at projectile contact; no material stress fracture. Identical impact and density; seed positions change.'}));console.log(key,impact,frames.length);
}
