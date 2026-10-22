const s=ctx.state,gl=ctx.gl;
s.createSimulation=createSimulation;s.sim=createSimulation();s.seed=117;
s.camera=ctx.utils.createOrbitCamera({distance:10,theta:.65,phi:1.05,target:[0,0,0],fov:42,autoRotate:.08});
s.mesh=ctx.utils.createMesh(ctx.utils.geometry.box());
s.program=ctx.utils.createProgram(`#version 300 es
precision highp float;layout(location=0) in vec3 a_position;layout(location=1) in vec3 a_normal;
uniform mat4 u_mvp;uniform mat4 u_model;out vec3 normal;void main(){normal=a_normal;gl_Position=u_mvp*vec4(a_position,1.);}`,`#version 300 es
precision highp float;in vec3 normal;uniform vec3 u_color;out vec4 outColor;
void main(){float light=.38+.62*max(dot(normalize(normal),normalize(vec3(1.,2.,3.))),0.);outColor=vec4(u_color*light,1.);}`);
