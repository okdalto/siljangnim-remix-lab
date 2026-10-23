const s=ctx.state,gl=ctx.gl,u=ctx.uniforms,m=ctx.utils.mat4;const [w,h]=ctx.resolution;
if(u.u_mode!==s.mode||u.u_reset){s.clock=0;s.accumulator=0;s.mode=u.u_mode;s.wallKey=u.u_cluster?'cluster':'uniform';s.wall=s.makeWall(s.data[s.wallKey]);}
if(!u.u_pause)s.clock+=Math.min(ctx.dt,.05);
if(u.u_mode<2){
 gl.disable(gl.DEPTH_TEST);s.draw2d(w,h,u);gl.bindTexture(gl.TEXTURE_2D,s.tex);gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,false);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,s.canvas);gl.useProgram(s.screen);ctx.utils.bindTexture(s.screen,'u_canvas',s.tex,0);ctx.utils.drawFullscreen(s.screen);
}else{
 s.camera.update(ctx.mouse,ctx.mousePrev,ctx.mouseDown,ctx.keys,ctx.dt);
 const vp=s.camera.getViewProjection(w/h);gl.enable(gl.DEPTH_TEST);gl.clearColor(.031,.043,.039,1);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);gl.useProgram(s.program);
 // Source geometry is z-up; transform to the viewer's y-up coordinate system.
 const orient=m.fromXRotation(-Math.PI/2);
 const draw=(mesh,model,color)=>{model=m.multiply(orient,model);ctx.utils.setUniforms(s.program,{u_model:model,u_mvp:m.multiply(vp,model),u_color:color});mesh.draw();};
 if(u.u_mode===2){
  s.data.cube.forEach((cell,i)=>draw(s.meshes.cube[i],s.model(cell.center.map(x=>x*(1+u.u_explode)),[0,0,0,1],.98),s.palette[i%s.palette.length]));
  ctx.publish('Model','3D Voronoi · precomputed SciPy cells');ctx.publish('Cells',36);
 }else{
  const key=u.u_cluster?'cluster':'uniform';if(key!==s.wallKey){s.wallKey=key;s.wall=s.makeWall(s.data[key]);s.accumulator=0;}
  if(!u.u_pause){s.accumulator+=Math.min(ctx.dt,.05);while(s.accumulator>=1/60&&s.wall.elapsed<9){s.wall.stepFrame();s.accumulator-=1/60;}}
  s.wall.bodies.forEach((b,i)=>{const p=b.position.toArray();p[2]-=1.3;draw(s.meshes[key][i],s.model(p,b.quaternion.toArray(),.995),s.palette[i%s.palette.length]);});
  const bp=s.wall.ball.position.toArray();bp[2]-=1.3;draw(s.sphere,s.model(bp,[0,0,0,1],.32),[.95,.87,.52]);
  draw(s.floor,m.multiply(m.fromTranslation(0,0,-1.38),m.fromScaling(12,12,.1)),[.06,.08,.075]);
  ctx.publish('Model','Live cannon-es · pre-cut pieces, supports removed');ctx.publish('Simulation seconds',Math.round(s.wall.elapsed*100)/100);ctx.publish('Impact',s.wall.impact??'Approaching');
 }
}
