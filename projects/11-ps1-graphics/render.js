const gl=ctx.gl,s=ctx.state,m=ctx.utils.mat4;
const topic=ctx.uniforms.u_topic,variant=ctx.uniforms.u_variant;
const t=ctx.time;const [w,h]=ctx.resolution;const areaH=Math.floor(Math.min(h*.47,w*.85));const areaY=Math.floor(h*.41);
const pixelated=topic===3&&variant===2&&t>ctx.uniforms.u_lowtime;
gl.clearColor(.03,.043,.039,1);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);
if(pixelated){gl.bindFramebuffer(gl.FRAMEBUFFER,s.target.read().framebuffer);gl.viewport(0,0,320,240);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT)}else gl.viewport(0,areaY,w,areaH);
const aspect=w/areaH;
s.camera.update(ctx.mouse,ctx.mousePrev,ctx.mouseDown,ctx.keys,ctx.dt);
const nearPlane=topic===2&&variant===2?.1+4.7*Math.min(1,Math.max(0,(t-ctx.uniforms.u_droptime)/.5)):.1;
const projection=m.perspective(topic===0?50:46,aspect,nearPlane,100);
const view=topic===0?m.lookAt([Math.sin(t*1.4)*1.1,2.8,4.8],[0,0,0],[0,1,0]):m.lookAt([topic===1?Math.sin(t*.6)*.7:0,0,5],[0,0,0],[0,1,0]);
let model=topic===0?m.fromYRotation(Math.sin(t*1.15)*.38):m.multiply(m.fromYRotation(topic===1?.35:Math.sin(t*1.4-.8)*.65),m.fromXRotation(topic===2?0:.25));
if(topic===1)model=m.multiply(model,m.fromScaling(1.55,1.55,1.55));
if(topic===3)model=m.multiply(model,m.fromScaling(3.4,3.4,3.4));
// Orbit controls replace the cinematic camera when the viewer is being dragged.
const vp=m.multiply(projection,ctx.mouseDown?s.camera.getViewMatrix():view);
gl.useProgram(s.p);ctx.utils.setUniforms(s.p,{u_mvp:m.multiply(vp,model),u_model:model,u_snap:topic===1&&variant===1?1:0,u_grid:[96,72],u_affine:topic===0&&variant>0?1:0,u_gouraud:topic===3&&variant>0?1:0,u_quant:topic===3&&variant>0&&t>ctx.uniforms.u_quanttime?1:0,u_dither:topic===3&&variant>0&&t>ctx.uniforms.u_dithertime?1:0,u_texture:topic===0||topic===3&&variant===2?1:0,u_color:[.8,.95,.97]});ctx.utils.bindTexture(s.p,'u_tex',s.texture,0);
gl.enable(gl.DEPTH_TEST);gl.disable(gl.CULL_FACE);
if(topic===0)s.planes[variant===2?1:0].draw();
if(topic===1){ctx.utils.setUniforms(s.p,{u_color:[.47,.69,.76]});s.box.draw()}
if(topic===2){
 let tris=s.triangles.map((tr,i)=>({tr,i,depth:m.transformPoint(model,[0,1,2].map(j=>(tr.positions[j]+tr.positions[j+3]+tr.positions[j+6])/3))[2]}));
 if(variant===1){gl.disable(gl.DEPTH_TEST);tris.sort((a,b)=>a.depth-b.depth)}
 for(const {tr,i} of tris){
  if(variant===2&&t<ctx.uniforms.u_cliptime&&tr.positions.some((_,j)=>j%3===0&&m.transformPoint(m.multiply(view,model),tr.positions.slice(j,j+3))[2]>-nearPlane))continue;
  ctx.utils.setUniforms(s.p,{u_color:i===0?[.35,.75,.83]:[.82,.36,.43]});tr.mesh.draw();
 }
}
if(topic===3){ctx.utils.setUniforms(s.p,{u_color:[.65,.76,.9]});s.spheres[variant===0?1:0].draw()}
if(pixelated){gl.bindFramebuffer(gl.FRAMEBUFFER,null);gl.viewport(0,areaY,w,areaH);gl.disable(gl.DEPTH_TEST);gl.useProgram(s.blit);ctx.utils.bindTexture(s.blit,'u_image',s.target.read().texture,0);ctx.utils.drawFullscreen(s.blit)}
gl.viewport(0,0,w,h);ctx.publish('Demonstration',['Affine UV','Integer vertex coordinates (magnified)','Depth sorting / simplified clipping','Geometry, colour and sampling'][topic]);
