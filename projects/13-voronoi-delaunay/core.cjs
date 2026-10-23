// Shared deterministic physics model used by the interactive scene and tests.
function makeWall(C, cells) {
 const world=new C.World({gravity:new C.Vec3(0,0,-9.81)});
 world.solver.iterations=60;world.allowSleep=true;
 Object.assign(world.defaultContactMaterial,{contactEquationStiffness:1e5,contactEquationRelaxation:8,friction:.55,restitution:0});
 world.addBody(new C.Body({mass:0,shape:new C.Plane()}));
 const bodies=cells.map(cell=>{
  const shape=new C.ConvexPolyhedron({vertices:cell.vertices.map(p=>new C.Vec3(...p.map(x=>x*.995))),faces:cell.faces});
  const b=new C.Body({mass:0,shape,position:new C.Vec3(...cell.center),linearDamping:.12,angularDamping:.25,allowSleep:true,sleepSpeedLimit:.08,sleepTimeLimit:1});world.addBody(b);return b;
 });
 const ball=new C.Body({mass:8,shape:new C.Sphere(.32),position:new C.Vec3(.2,-3,1.7)});ball.velocity.set(0,4,0);world.addBody(ball);
 let impact=null,released=false,elapsed=0;
 for(const b of bodies)b.addEventListener('collide',e=>{if(e.body===ball&&impact===null)impact=world.time;});
 return {world,bodies,ball,get impact(){return impact;},get elapsed(){return elapsed;},stepFrame(){
  for(let i=0;i<8;i++){
   if(!released&&ball.position.y>=-.60){released=true;bodies.forEach((b,j)=>{b.type=C.Body.DYNAMIC;b.mass=cells[j].volume*10;b.updateMassProperties();b.updateInertiaWorld(true);b.wakeUp();});world.broadphase.dirty=true;}
   if(impact===null)ball.force.z+=ball.mass*9.81;
   world.step(1/480);
  }
  elapsed+=1/60;
 }};
}
if(typeof module!=='undefined')module.exports={makeWall};
