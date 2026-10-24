const s=ctx.state,gl=ctx.gl;
s.rgb=DATA.rgb;s.n=DATA.n;s.pixel=pixel;s.kernels=KERNELS;s.mode=-1;s.clock=0;
s.canvas=new OffscreenCanvas(1,1);s.c=s.canvas.getContext('2d');
s.tex=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,s.tex);
for(const [k,v] of [[gl.TEXTURE_MIN_FILTER,gl.LINEAR],[gl.TEXTURE_MAG_FILTER,gl.LINEAR],[gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE],[gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE]])gl.texParameteri(gl.TEXTURE_2D,k,v);
s.program=ctx.utils.createProgram(ctx.utils.FULLSCREEN_VERTEX_SHADER,`#version 300 es
precision highp float;in vec2 v_uv;out vec4 outColor;uniform sampler2D u_canvas;
void main(){outColor=texture(u_canvas,vec2(v_uv.x,1.-v_uv.y));}`);
s.apply=apply;
