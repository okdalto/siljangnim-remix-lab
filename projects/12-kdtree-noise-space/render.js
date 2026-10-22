const s=ctx.state,gl=ctx.gl,u=ctx.uniforms,m=ctx.utils.mat4;
if(s.seed!==u.u_seed){s.sim=s.createSimulation(u.u_seed);s.seed=u.u_seed;}
const result=s.sim.step(ctx.dt*u.u_speed,u.u_depth,u.u_damping,u.u_exact);
s.camera.update(ctx.mouse,ctx.mousePrev,ctx.mouseDown,ctx.keys,ctx.dt);
const vp=s.camera.getViewProjection(ctx.resolution[0]/ctx.resolution[1]);
gl.enable(gl.DEPTH_TEST);gl.clearColor(.031,.043,.039,1);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);gl.useProgram(s.program);
let count=0;
for(let i=0;i<result.cells.length;i++){
 if(!u.u_all&&i%7===3)continue;
 const c=result.cells[i],pos=c.lo.map((x,k)=>x+c.hi[k]),size=c.lo.map((x,k)=>(c.hi[k]-x)*1.87);
 if(u.u_style===1)size[i%3]*=.12;
 const model=m.multiply(m.fromTranslation(...pos),m.fromScaling(...size));
 const z=(c.lo[2]+c.hi[2]+2)/4;
 ctx.utils.setUniforms(s.program,{u_mvp:m.multiply(vp,model),u_model:model,u_color:[.28+z*.60,.55+z*.36,.51+z*.18]});s.mesh.draw();count++;
}
ctx.publish('Regions',result.cells.length);ctx.publish('Visible',count);ctx.publish('Points',1024);ctx.publish('Boundary',u.u_exact?'Exact median':'Spring display (lags median)');
