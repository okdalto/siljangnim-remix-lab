const s=ctx.state,u=ctx.uniforms,gl=ctx.gl,[w,h]=ctx.resolution;
if(s.seek!==u.u_seek){s.clock=u.u_seek;s.seek=u.u_seek;}
if(u.u_reset){s.clock=0;s.first=true;}
if(!u.u_pause){s.clock+=Math.min(ctx.dt,.1)*u.u_speed;if(s.clock>=s.meta.duration){s.clock%=s.meta.duration;s.first=false;}}
const n=Math.min(u.u_quality,Math.max(256,Math.round(Math.min(w,h))));if(n!==s.size)s.resize(n);
if(!s.cached){s.renderScene(.95,false);gl.bindFramebuffer(gl.READ_FRAMEBUFFER,s.main);gl.readBuffer(gl.COLOR_ATTACHMENT0);gl.bindFramebuffer(gl.DRAW_FRAMEBUFFER,s.openingFBO);gl.blitFramebuffer(0,0,n,n,0,0,n,n,gl.COLOR_BUFFER_BIT,gl.NEAREST);s.cached=true;}
if(s.resultMode!==u.u_result)s.updateResult(u.u_result);
s.renderScene(u.u_result?34.9701:s.clock,s.first);
const alpha=u.u_result?0:s.ease((s.clock-s.meta.loopBlendStart)/s.meta.loopBlendDuration);
if(alpha>0){gl.bindFramebuffer(gl.FRAMEBUFFER,s.main);gl.drawBuffers([gl.COLOR_ATTACHMENT0,gl.NONE]);gl.disable(gl.DEPTH_TEST);gl.enable(gl.BLEND);gl.blendFunc(gl.ONE,gl.ONE_MINUS_SRC_ALPHA);const p=s.programs.composite;gl.useProgram(p);s.bind(p,'outlineImage',s.opening,0);s.f(p,'layerOpacity',alpha);s.draw(p);gl.disable(gl.BLEND);}
gl.bindFramebuffer(gl.FRAMEBUFFER,null);gl.viewport(0,0,w,h);gl.disable(gl.DEPTH_TEST);gl.disable(gl.BLEND);const p=s.programs.present;gl.useProgram(p);s.bind(p,'squareImage',s.color,0);s.vec(p,'displaySize',[w,h]);s.draw(p);ctx.publish('Source time',Number(s.clock.toFixed(2)));ctx.publish('Renderer','Original 3D SDF · WebGL2');
