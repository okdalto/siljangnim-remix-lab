// STATES and WAVES are inserted by build_scene.py; no fetch, token or asset download.
const canvas=new OffscreenCanvas(1,1), c=canvas.getContext('2d'), gl=ctx.gl;
const tex=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,tex);
for(const [k,v] of [[gl.TEXTURE_MIN_FILTER,gl.LINEAR],[gl.TEXTURE_MAG_FILTER,gl.LINEAR],[gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE],[gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE]]) gl.texParameteri(gl.TEXTURE_2D,k,v);
const fs=`#version 300 es
precision highp float;in vec2 v_uv;out vec4 outColor;uniform sampler2D u_canvas;void main(){outColor=texture(u_canvas,vec2(v_uv.x,1.-v_uv.y));}`;
const s=ctx.state;Object.assign(s,{canvas,c,tex,states:STATES,waves:WAVES,prog:ctx.utils.createProgram(ctx.utils.FULLSCREEN_VERTEX_SHADER,fs),selected:-1,audio:null});
s.updateSound=()=>{
  if(!s.audio)return;
  const ac=s.audio,t=ac.currentTime, coefficients=s.waves[s.selected];
  // Short crossfade between oscillators prevents clicks when switching geometry.
  if(s.osc){s.gain.gain.cancelScheduledValues(t);s.gain.gain.setTargetAtTime(0,t,.015);s.osc.stop(t+.12);}
  const osc=ac.createOscillator(), gain=ac.createGain();
  osc.setPeriodicWave(ac.createPeriodicWave(new Float32Array(coefficients[0]),new Float32Array(coefficients[1]),{disableNormalization:true}));
  osc.frequency.value=80.8533319339;osc.connect(gain);gain.connect(ac.destination);
  osc.onended=()=>{osc.disconnect();gain.disconnect();};
  gain.gain.value=0;gain.gain.setTargetAtTime(ctx.uniforms.u_sound?.5:0,t,.02);osc.start();
  s.osc=osc;s.gain=gain;
};
s.unlock=()=>{if(!s.audio){s.audio=new AudioContext();s.updateSound();}s.audio.resume().catch(()=>{});};
window.addEventListener('pointerdown',s.unlock);
