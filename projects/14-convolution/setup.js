const s=ctx.state,gl=ctx.gl;
s.meta=META;s.motion=new Float32Array(await unpack(MOTION));s.clock=0;s.seek=-1;s.first=true;
s.ease=x=>{x=Math.max(0,Math.min(1,x));return x*x*x*(x*(x*6-15)+10);};
s.programs={};for(const [name,frag] of Object.entries(SHADERS))s.programs[name]=ctx.utils.createProgram(VERT,frag);
s.lineProgram=ctx.utils.createProgram(LINEVERT,LINEFRAG);
s.vao=gl.createVertexArray();gl.bindVertexArray(s.vao);const vb=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,vb);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,3,-1,-1,3]),gl.STATIC_DRAW);gl.enableVertexAttribArray(0);gl.vertexAttribPointer(0,2,gl.FLOAT,false,0,0);
s.lineVAO=gl.createVertexArray();gl.bindVertexArray(s.lineVAO);s.lineBuffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,s.lineBuffer);gl.bufferData(gl.ARRAY_BUFFER,72*4,gl.DYNAMIC_DRAW);gl.enableVertexAttribArray(0);gl.vertexAttribPointer(0,3,gl.FLOAT,false,0,0);gl.bindVertexArray(null);
s.locations=new Map();s.loc=(p,n)=>{let map=s.locations.get(p);if(!map){map={};s.locations.set(p,map);}if(!(n in map))map[n]=gl.getUniformLocation(p,n);return map[n];};
s.f=(p,n,v)=>gl.uniform1f(s.loc(p,n),v);s.i=(p,n,v)=>gl.uniform1i(s.loc(p,n),v);s.vec=(p,n,v)=>gl['uniform'+v.length+'fv'](s.loc(p,n),v);
s.array=(p,n,v)=>gl.uniform1fv(s.loc(p,n+'[0]'),v);
s.texture=(w,h,internal,format,type,data,filter=gl.LINEAR)=>{const t=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,t);gl.texImage2D(gl.TEXTURE_2D,0,internal,w,h,0,format,type,data);for(const k of [gl.TEXTURE_MIN_FILTER,gl.TEXTURE_MAG_FILTER])gl.texParameteri(gl.TEXTURE_2D,k,filter);for(const k of [gl.TEXTURE_WRAP_S,gl.TEXTURE_WRAP_T])gl.texParameteri(gl.TEXTURE_2D,k,gl.CLAMP_TO_EDGE);return t;};
s.bind=(p,n,t,unit)=>{gl.activeTexture(gl.TEXTURE0+unit);gl.bindTexture(gl.TEXTURE_2D,t);s.i(p,n,unit);};
s.draw=p=>{gl.useProgram(p);gl.bindVertexArray(s.vao);gl.drawArrays(gl.TRIANGLES,0,3);gl.bindVertexArray(null);};
const rgba=new Uint8Array(32*32*4),padded=new Uint8Array(32*32*4),out=apply(DATA.rgb,32,3);
for(let y=0;y<32;y++)for(let x=0;x<32;x++){let k=(y*32+x)*4,src=((31-y)*32+x)*3;rgba.set(DATA.rgb.slice(src,src+3).map(v=>Math.round(v*255)),k);rgba[k+3]=255;padded[k+3]=255;if(x>0&&x<31&&y>0&&y<31){const v=out[((30-y)*30+x-1)*3];padded.set([Math.round(v*255),Math.round(v*255),Math.round(v*255)],k);}}
s.source=s.texture(32,32,gl.RGBA8,gl.RGBA,gl.UNSIGNED_BYTE,rgba);
s.photo=s.texture(512,512,gl.RGBA8,gl.RGBA,gl.UNSIGNED_BYTE,new Uint8Array(await unpack(PHOTO)));
// Keep Sobel float precision, as in the desktop renderer.
const resultFloat=new Float32Array(32*32*4);for(let y=1;y<31;y++)for(let x=1;x<31;x++){let i=(y*32+x)*4,v=out[((30-y)*30+x-1)*3];resultFloat.set([v,v,v,1],i);}
s.result=s.texture(32,32,gl.RGBA32F,gl.RGBA,gl.FLOAT,resultFloat,gl.NEAREST);
s.label=s.texture(256,128,gl.R8,gl.RED,gl.UNSIGNED_BYTE,new Uint8Array(await unpack(LABELS)));
s.resultMode=0;s.resultFloat=resultFloat;s.apply=apply;s.rgb=DATA.rgb;
s.updateResult=mode=>{const out=s.apply(s.rgb,32,[3,1,2,4][mode]);s.resultFloat.fill(0);for(let y=1;y<31;y++)for(let x=1;x<31;x++){let i=(y*32+x)*4,j=((30-y)*30+x-1)*3;s.resultFloat.set([out[j],out[j+1],out[j+2],1],i);}gl.bindTexture(gl.TEXTURE_2D,s.result);gl.texSubImage2D(gl.TEXTURE_2D,0,0,0,32,32,gl.RGBA,gl.FLOAT,s.resultFloat);s.resultMode=mode;};
s.size=0;s.cached=false;
s.target=(attachments,depth)=>{const f=gl.createFramebuffer();gl.bindFramebuffer(gl.FRAMEBUFFER,f);attachments.forEach((t,i)=>gl.framebufferTexture2D(gl.FRAMEBUFFER,gl.COLOR_ATTACHMENT0+i,gl.TEXTURE_2D,t,0));if(depth)gl.framebufferTexture2D(gl.FRAMEBUFFER,gl.DEPTH_ATTACHMENT,gl.TEXTURE_2D,depth,0);gl.drawBuffers(attachments.map((_,i)=>gl.COLOR_ATTACHMENT0+i));if(gl.checkFramebufferStatus(gl.FRAMEBUFFER)!==gl.FRAMEBUFFER_COMPLETE)throw Error('Incomplete convolution framebuffer');return f;};
s.resize=n=>{for(const t of s.targets||[])gl.deleteTexture(t);for(const f of s.fbos||[])gl.deleteFramebuffer(f);s.size=n;s.color=s.texture(n,n,gl.RGBA8,gl.RGBA,gl.UNSIGNED_BYTE,null);s.surface=s.texture(n,n,gl.RGBA16F,gl.RGBA,gl.FLOAT,null);s.depth=s.texture(n,n,gl.DEPTH_COMPONENT24,gl.DEPTH_COMPONENT,gl.UNSIGNED_INT,null,gl.NEAREST);s.lines=s.texture(n,n,gl.RGBA8,gl.RGBA,gl.UNSIGNED_BYTE,null);s.opening=s.texture(n,n,gl.RGBA8,gl.RGBA,gl.UNSIGNED_BYTE,null);s.main=s.target([s.color,s.surface],s.depth);s.lineFBO=s.target([s.lines],s.depth);s.openingFBO=s.target([s.opening]);s.targets=[s.color,s.surface,s.depth,s.lines,s.opening];s.fbos=[s.main,s.lineFBO,s.openingFBO];s.cached=false;};
s.phaseCount=20;const p=s.programs.scene;for(let j=0;j<gl.getProgramParameter(p,gl.ACTIVE_UNIFORMS);j++){const a=gl.getActiveUniform(p,j);if(a.name==='phaseTiming[0]')s.phaseCount=a.size;}
s.renderScene=(time,first)=>{
 const frame=Math.min(META.frames-1,Math.max(0,Math.round(time*META.rate))),t=frame/META.rate+.0001,row=s.motion.subarray(frame*META.stride,(frame+1)*META.stride);let at=0;const take=n=>{const v=row.subarray(at,at+n);at+=n;return v;};
 const motion=take(26),filter=take(81),gather=take(28),scales=take(9),pose=take(4),prepared=take(4),layer=take(1)[0],visibility=take(1)[0],label=take(1)[0],vertices=take(72);
 gl.bindFramebuffer(gl.FRAMEBUFFER,s.main);gl.drawBuffers([gl.COLOR_ATTACHMENT0,gl.COLOR_ATTACHMENT1]);gl.viewport(0,0,s.size,s.size);gl.disable(gl.BLEND);gl.enable(gl.DEPTH_TEST);gl.depthFunc(gl.ALWAYS);gl.depthMask(true);gl.clear(gl.DEPTH_BUFFER_BIT);gl.useProgram(p);
 s.f(p,'timeline',t);s.f(p,'introOpacity',first?s.ease(t/.85):1);s.vec(p,'introTiming',META.introTiming);s.i(p,'gridSize',32);s.array(p,'motion',motion);s.array(p,'filterMotion',filter);s.array(p,'gatherMotion',gather);s.array(p,'sourceScale',scales);s.i(p,'sourceChanging',scales.some(v=>Math.abs(v-1)>.001)?1:0);s.array(p,'phaseTiming',META.phaseTiming.slice(0,s.phaseCount));s.vec(p,'cameraPose',pose);s.vec(p,'preparedFilter',prepared);s.f(p,'preparedLayer',layer);s.f(p,'labelOpacity',label);s.f(p,'motionVisibility',visibility);for(const n of ['scanStart','firstCell','scanFinish'])s.f(p,n,META[n]);s.bind(p,'sourceImage',s.source,0);s.bind(p,'photoImage',s.photo,1);s.bind(p,'resultImage',s.result,2);s.bind(p,'labelAtlas',s.label,3);s.draw(p);
 if(t>=META.introTiming[0]){
 gl.bindFramebuffer(gl.FRAMEBUFFER,s.lineFBO);gl.clearColor(0,0,0,0);gl.clear(gl.COLOR_BUFFER_BIT);gl.depthMask(false);gl.disable(gl.DEPTH_TEST);gl.enable(gl.BLEND);gl.blendFuncSeparate(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA,gl.ONE,gl.ONE_MINUS_SRC_ALPHA);
 const b=s.programs.box_outline;gl.useProgram(b);s.bind(b,'surfaceImage',s.surface,0);s.f(b,'opacity',.72*s.ease((t-META.introTiming[0])/1.2));s.draw(b);
 gl.enable(gl.DEPTH_TEST);gl.depthFunc(gl.LEQUAL);gl.useProgram(s.lineProgram);s.f(s.lineProgram,'opacity',.85*s.ease((t-META.introTiming[1]-1.2)/.45)*(1-s.ease((t-META.scanFinish)/.6)));gl.bindVertexArray(s.lineVAO);gl.bindBuffer(gl.ARRAY_BUFFER,s.lineBuffer);gl.bufferSubData(gl.ARRAY_BUFFER,0,vertices);gl.drawArrays(gl.LINES,0,24);gl.bindVertexArray(null);
 gl.disable(gl.DEPTH_TEST);gl.bindFramebuffer(gl.FRAMEBUFFER,s.main);gl.drawBuffers([gl.COLOR_ATTACHMENT0,gl.NONE]);gl.blendFunc(gl.ONE,gl.ONE_MINUS_SRC_ALPHA);const c=s.programs.composite;gl.useProgram(c);s.bind(c,'outlineImage',s.lines,0);s.f(c,'layerOpacity',1);s.draw(c);gl.disable(gl.BLEND);gl.depthMask(true);
 }
};
