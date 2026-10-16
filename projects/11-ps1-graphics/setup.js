const gl=ctx.gl;
const vs=`#version 300 es
precision highp float;
layout(location=0) in vec3 a_position;
layout(location=1) in vec3 a_normal;
layout(location=2) in vec2 a_uv;
uniform mat4 u_mvp;
uniform mat4 u_model;
uniform float u_snap;
uniform vec2 u_grid;
uniform float u_gouraud;
out vec2 v_uv;
out vec3 v_affine;
out vec3 v_normal;
out float v_light;
void main(){
 vec4 clip=u_mvp*vec4(a_position,1.);
 if(u_snap>0.5)clip.xy=floor((clip.xy/clip.w*.5+.5)*u_grid)/u_grid*2.*clip.w-clip.w;
 gl_Position=clip;
 v_uv=a_uv;v_affine=vec3(a_uv*clip.w,clip.w);
 v_normal=mat3(u_model)*a_normal;
 v_light=.22+.78*max(0.,dot(normalize(v_normal),normalize(vec3(-.6,.9,1.))));
}`;
const fs=`#version 300 es
precision highp float;
in vec2 v_uv;in vec3 v_affine;in vec3 v_normal;in float v_light;
out vec4 outColor;
uniform float u_affine;uniform float u_gouraud;uniform float u_quant;uniform float u_dither;uniform float u_texture;uniform vec3 u_color;uniform sampler2D u_tex;
void main(){
 vec2 uv=mix(v_uv,v_affine.xy/v_affine.z,u_affine);
 vec3 c=u_color;
 if(u_texture>.5)c*=texture(u_tex,uv).rgb;
 float light=mix(.22+.78*max(0.,dot(normalize(v_normal),normalize(vec3(-.6,.9,1.)))),v_light,u_gouraud);
 c*=light;
 if(u_quant>.5){
 int x=int(gl_FragCoord.x)%4,y=int(gl_FragCoord.y)%4;
 float d[16]=float[16](-4.,0.,-3.,1.,2.,-2.,3.,-1.,-3.,1.,-4.,0.,3.,-1.,2.,-2.);
 c=floor(clamp(c*255.+d[y*4+x]*u_dither,0.,255.)/8.)/31.;
 }
 outColor=vec4(c,1.);
}`;
ctx.state.p=ctx.utils.createProgram(vs,fs);
ctx.state.camera=ctx.utils.createOrbitCamera({distance:5,theta:0,phi:1.1,target:[0,0,0],fov:46});
function grid(n){let p=[],normal=[],uv=[],ind=[];for(let j=0;j<=n;j++)for(let i=0;i<=n;i++){p.push((i/n-.5)*4,0,(j/n-.5)*4);normal.push(0,1,0);uv.push(i/n,j/n)}for(let j=0;j<n;j++)for(let i=0;i<n;i++){const a=j*(n+1)+i;ind.push(a,a+1,a+n+1,a+1,a+n+2,a+n+1)}return ctx.utils.createMesh({positions:p,normals:normal,uvs:uv,indices:ind})}
ctx.state.planes=[grid(1),grid(12)];
ctx.state.box=ctx.utils.createMesh(ctx.utils.geometry.box());
ctx.state.spheres=[ctx.utils.createMesh(ctx.utils.geometry.sphere(8)),ctx.utils.createMesh(ctx.utils.geometry.sphere(48))];
ctx.state.triangles=[[-1.5,-1,.9,1.2,-1,-.9,-.4,1.5,0],[-1.2,1,-.7,1.5,1,.7,.4,-1.5,0]].map(positions=>({positions,mesh:ctx.utils.createMesh({positions,normals:[0,0,1,0,0,1,0,0,1],uvs:[0,0,1,0,.5,1]})}));
const c=document.createElement('canvas');c.width=c.height=64;const g=c.getContext('2d');for(let y=0;y<8;y++)for(let x=0;x<8;x++){g.fillStyle=(x+y)%2?'#447d86':'#d8e5e7';g.fillRect(x*8,y*8,8,8)}
const texture=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,texture);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,c);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.NEAREST);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.NEAREST);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);ctx.state.texture=texture;
ctx.state.target=ctx.utils.createPingPong(320,240,{depth:true,filter:gl.NEAREST});
ctx.state.blit=ctx.utils.createProgram(ctx.utils.FULLSCREEN_VERTEX_SHADER,`#version 300 es\nprecision highp float;in vec2 v_uv;out vec4 outColor;uniform sampler2D u_image;void main(){outColor=texture(u_image,v_uv);}`);
