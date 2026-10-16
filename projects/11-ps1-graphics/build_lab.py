from pathlib import Path
import json,base64
B=Path(__file__).resolve().parent;A=B/'assets/PSXStyleTeen';d=json.loads((A/'mesh.json').read_text())[0];p=d['positions'];n=d['normals'];uv=d['uv'];faces=[]
for i in range(0,len(p),9):
 pp=[[p[i+j]*.0068,p[i+j+1]*.0068-1.7,p[i+j+2]*.0068] for j in (0,3,6)]
 faces.append(dict(positions=sum(pp,[]),normals=n[i:i+9],uvs=uv[i//3*2:i//3*2+6],centre=[sum(v[k] for v in pp)/3 for k in range(3)]))
setup=(B/'setup.js').read_text().replace('createPingPong(320,240','createPingPong(192,240')
setup+='\nconst photo=new Image();photo.src="data:image/png;base64,'+base64.b64encode((A/'PS1Teen_Diffuse.png').read_bytes()).decode()+'";await photo.decode();\n'
setup+='const faceTex=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,faceTex);gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,true);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,photo);gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,false);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.NEAREST);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.NEAREST);ctx.state.faceTex=faceTex;\n'
setup+='ctx.state.portrait='+json.dumps(faces,separators=(',',':'))+'.map(f=>({...f,mesh:ctx.utils.createMesh(f)}));\n'
setup+=(B/'lab_setup.js').read_text()
for name,render in [('teen','lab_render.js'),('intro','lab_intro_render.js'),('portrait','lab_portrait_render.js')]:
 scene=dict(version=2,backend='webgl2',script=dict(setup=setup,render=(B/render).read_text(),cleanup=''),inputs=['mouse'],timeline=dict(duration=12,loop=True),uniforms={})
 target=B/'output';target.mkdir(exist_ok=True)
 (target/f'lab-{name}.json').write_text(json.dumps(scene,indent=2))
 (target/f'lab-{name}.md').write_text('---\ntitle: PS1 laboratory '+name+'\nsiljangnim: 2\nbackend: webgl2\nassets: []\n---\n\n# Laboratory comparison\n\nPSX Style Teen by swickster: https://swickster.itch.io/psx-style-teen\n\n## Scene\n\n```json\n'+json.dumps(scene,indent=2)+'\n```\n')
 print(target/f'lab-{name}.md')
