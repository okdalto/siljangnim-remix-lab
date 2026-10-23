const s=ctx.state,gl=ctx.gl;
s.D=d3.Delaunay;s.data=GEOMETRY;s.ballet=BALLET;s.makeWall=cells=>makeWall(CANNON,cells);
s.clock=0;s.mode=-1;s.seed=-1;s.count=-1;s.accumulator=0;
s.canvas=new OffscreenCanvas(1,1);s.c=s.canvas.getContext('2d');s.tex=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,s.tex);
for(const [k,v] of [[gl.TEXTURE_MIN_FILTER,gl.LINEAR],[gl.TEXTURE_MAG_FILTER,gl.LINEAR],[gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE],[gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE]])gl.texParameteri(gl.TEXTURE_2D,k,v);
s.screen=ctx.utils.createProgram(ctx.utils.FULLSCREEN_VERTEX_SHADER,`#version 300 es
precision highp float;in vec2 v_uv;out vec4 outColor;uniform sampler2D u_canvas;void main(){outColor=texture(u_canvas,vec2(v_uv.x,1.-v_uv.y));}`);
s.program=ctx.utils.createProgram(`#version 300 es
precision highp float;layout(location=0)in vec3 a_position;layout(location=1)in vec3 a_normal;uniform mat4 u_mvp;uniform mat4 u_model;out vec3 normal;void main(){normal=mat3(u_model)*a_normal;gl_Position=u_mvp*vec4(a_position,1.);}`,`#version 300 es
precision highp float;in vec3 normal;uniform vec3 u_color;out vec4 outColor;void main(){float light=.32+.68*max(dot(normalize(normal),normalize(vec3(1.,2.,3.))),0.);outColor=vec4(u_color*light,1.);}`);
s.meshes={};
for(const key of ['cube','uniform','cluster'])s.meshes[key]=s.data[key].map(cell=>{
 const positions=[],normals=[];
 for(const face of cell.faces)for(let j=1;j<face.length-1;j++){
  const ps=[face[0],face[j],face[j+1]].map(i=>cell.vertices[i]);
  const a=ps[1].map((v,k)=>v-ps[0][k]),b=ps[2].map((v,k)=>v-ps[0][k]);
  const n=[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]],len=Math.hypot(...n);
  for(const p of ps){positions.push(...p);normals.push(...n.map(v=>v/len));}
 }
 return ctx.utils.createMesh({positions:new Float32Array(positions),normals:new Float32Array(normals)});
});
s.sphere=ctx.utils.createMesh(ctx.utils.geometry.sphere(24));s.floor=ctx.utils.createMesh(ctx.utils.geometry.box());
s.camera=ctx.utils.createOrbitCamera({distance:8,theta:.5,phi:1.15,target:[0,0,0],fov:45});
s.palette=[[.4,.78,.73],[.77,.86,.5],[.5,.65,.82],[.88,.72,.46],[.65,.7,.85]];
s.model=(p,q,scale=1)=>{const [x,y,z,w]=q;return new Float32Array([
 (1-2*y*y-2*z*z)*scale,(2*x*y+2*w*z)*scale,(2*x*z-2*w*y)*scale,0,
 (2*x*y-2*w*z)*scale,(1-2*x*x-2*z*z)*scale,(2*y*z+2*w*x)*scale,0,
 (2*x*z+2*w*y)*scale,(2*y*z-2*w*x)*scale,(1-2*x*x-2*y*y)*scale,0,...p,1]);};
s.draw2d=(w,h,u)=>{
 const c=s.c;if(s.canvas.width!==w||s.canvas.height!==h){s.canvas.width=w;s.canvas.height=h;}
 c.fillStyle='#080b0a';c.fillRect(0,0,w,h);const size=Math.min(w*.86,h*.82),ox=(w-size)/2,oy=(h-size)/2;
 const sx=u.u_mode===1?size*s.ballet.width/s.ballet.height:size;
 c.save();c.translate(ox+(size-sx)/2,oy);c.scale(sx,size);
 let points,clip=null;
 if(u.u_mode===1){const f=s.ballet.frames[Math.floor(s.clock*s.ballet.fps)%s.ballet.frames.length];points=f.p.map(p=>[p[0]/s.ballet.width,p[1]/s.ballet.height]);clip=f.outline;}
 else{
  if(s.seed!==u.u_seed||s.count!==u.u_count){let r=u.u_seed>>>0;const rand=()=>((r=(Math.imul(r,1664525)+1013904223)>>>0)/4294967296);s.points=Array.from({length:u.u_count},()=>[.08+.84*rand(),.08+.84*rand()]);s.seed=u.u_seed;s.count=u.u_count;}
  points=s.points.map((p,i)=>[p[0]+.035*Math.sin(s.clock*.65+i*1.3),p[1]+.035*Math.cos(s.clock*.53+i*.8)]);
 }
 const d=s.D.from(points),v=d.voronoi([0,0,1,1]);
 const path=()=>{c.beginPath();clip.forEach((p,i)=>{const x=p[0]/s.ballet.width,y=p[1]/s.ballet.height;i?c.lineTo(x,y):c.moveTo(x,y);});c.closePath();};
 if(clip){path();c.save();c.clip();}
 if(u.u_mode===0&&u.u_cells){for(let i=0;i<points.length;i++){c.beginPath();v.renderCell(i,c);const rgb=s.palette[i%s.palette.length];c.fillStyle=`rgb(${rgb.map(x=>Math.round(x*255)).join(',')})`;c.globalAlpha=u.u_mix;c.fill();}c.globalAlpha=1;c.beginPath();v.render(c);c.lineWidth=.002;c.strokeStyle='#1b2b2b';c.stroke();}
 if(u.u_edges){c.beginPath();d.render(c);c.lineWidth=u.u_mode===1?.0013:.0025;c.strokeStyle='#fff';c.stroke();}
 if(u.u_points){c.fillStyle='#fff';for(const p of points){c.beginPath();c.arc(...p,u.u_mode===1?.002:.005,0,Math.PI*2);c.fill();}}
 if(clip){c.restore();path();c.lineWidth=.0013;c.strokeStyle='#fff';c.stroke();}
 c.restore();ctx.publish('Points',points.length);ctx.publish('Triangles',d.triangles.length/3);
};
