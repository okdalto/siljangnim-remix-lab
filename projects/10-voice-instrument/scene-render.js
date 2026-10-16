const s=ctx.state,c=s.c,gl=ctx.gl;
const index=Math.max(0,Math.min(s.states.length-1,Math.round(ctx.uniforms.u_candidate)));
if(index!==s.selected){s.selected=index;s.updateSound();}
if(s.audio&&s.gain){s.gain.gain.setTargetAtTime(ctx.uniforms.u_sound?.5:0,s.audio.currentTime,.02);}
const [w,h]=ctx.resolution;
if(s.canvas.width!==w||s.canvas.height!==h){s.canvas.width=w;s.canvas.height=h;}
const u=Math.min(w,h), z=s.states[index];
c.fillStyle='#080b0a';c.fillRect(0,0,w,h);
c.textAlign='center';c.fillStyle='#eef4f2';c.font=`bold ${u*.055}px sans-serif`;
c.fillText('VOICE → INSTRUMENT',w/2,h*.20);
c.save();c.translate(w/2,h*.47);
const sc=w*.76/(z[0]*1000);
c.beginPath();
for(let i=0;i<16;i++){const r=Math.sqrt(Math.exp(z[i+1])*100/Math.PI);for(const j of [i,i+1]){const x=(j/16-.5)*z[0]*1000*sc,y=-r*sc;i===0&&j===0?c.moveTo(x,y):c.lineTo(x,y);}}
for(let i=15;i>=0;i--){const r=Math.sqrt(Math.exp(z[i+1])*100/Math.PI);for(const j of [i+1,i])c.lineTo((j/16-.5)*z[0]*1000*sc,r*sc);}
c.closePath();c.fillStyle='#69c9e6';c.fill();c.strokeStyle='#d6f3fb';c.lineWidth=u*.003;c.stroke();c.restore();
c.font=`${u*.033}px sans-serif`;c.fillStyle='#b9c8c8';
c.fillText(`Candidate ${index+1} / ${s.states.length} · ${(z[0]*1000).toFixed(1)} mm`,w/2,h*.73);
c.fillText(s.audio?.state==='running'?(ctx.uniforms.u_sound?'Sound on · change the candidate slider':'Sound muted'):'Click the instrument to enable sound',w/2,h*.81);
c.font=`${u*.025}px sans-serif`;c.fillText('Simulated bore profile · analytic excitation',w/2,h*.88);
gl.bindTexture(gl.TEXTURE_2D,s.tex);gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,false);
gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,s.canvas);
gl.useProgram(s.prog);ctx.utils.bindTexture(s.prog,'u_canvas',s.tex,0);ctx.utils.drawFullscreen(s.prog);
ctx.publish('Candidate',index+1);ctx.publish('Length (mm)',Number((z[0]*1000).toFixed(1)));
