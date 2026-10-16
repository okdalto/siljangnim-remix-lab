const gl=ctx.gl,s=ctx.state,m=ctx.utils.mat4,t=ctx.time,[w,h]=ctx.resolution;
gl.bindFramebuffer(gl.FRAMEBUFFER,null);gl.viewport(0,0,w,h);gl.clearColor(.03,.043,.039,1);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);
const pw=Math.floor(w/2),ah=Math.floor(h*.84),ay=Math.floor(h*.05);
const k=Math.max(0,Math.min(1,(t-5)/5)),ease=k*k*(3-2*k),dist=5.3-3.5*ease,targetY=.25+.85*ease;
const view=m.lookAt([Math.sin(t*.6)*.45*(1-ease*.7),targetY+.12,dist],[0,targetY,0],[0,1,0]);
const character=m.multiply(m.fromTranslation(0,-.34,0),m.multiply(m.fromYRotation(Math.sin(t*.45)*.12),m.fromScaling(.8,.8,.8))),room=m.identity(),proj=m.perspective(49,pw/ah,.1,60);
for(let side=0;side<2;side++){
 const old=side===1;if(old){gl.bindFramebuffer(gl.FRAMEBUFFER,s.target.read().framebuffer);gl.viewport(0,0,192,240);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT)}else gl.viewport(0,ay,pw,ah);
 gl.useProgram(s.p);gl.disable(gl.CULL_FACE);old?gl.disable(gl.DEPTH_TEST):gl.enable(gl.DEPTH_TEST);
 const objects=[...s.room.map(f=>({f,model:room,tex:f.tex})),...s.portrait.map(f=>({f,model:character,tex:s.faceTex}))];
 if(old)objects.sort((a,b)=>m.transformPoint(m.multiply(view,a.model),a.f.centre)[2]-m.transformPoint(m.multiply(view,b.model),b.f.centre)[2]);
 for(const {f,model,tex} of objects){ctx.utils.setUniforms(s.p,{u_mvp:m.multiply(proj,m.multiply(view,model)),u_model:model,u_snap:old?1:0,u_grid:[160,200],u_affine:old?1:0,u_gouraud:old?1:0,u_quant:old?1:0,u_dither:old?1:0,u_texture:1,u_color:f.colour||[1,1,1]});ctx.utils.bindTexture(s.p,'u_tex',tex,0);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,old?gl.NEAREST:gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,old?gl.NEAREST:gl.LINEAR);f.mesh.draw();}
 if(old){gl.bindFramebuffer(gl.FRAMEBUFFER,null);gl.viewport(pw,ay,pw,ah);gl.disable(gl.DEPTH_TEST);gl.useProgram(s.blit);ctx.utils.bindTexture(s.blit,'u_image',s.target.read().texture,0);ctx.utils.drawFullscreen(s.blit)}
}
gl.viewport(0,0,w,h);ctx.publish('Comparison','PSX Style Teen / swickster · same model, camera, laboratory corridor');
