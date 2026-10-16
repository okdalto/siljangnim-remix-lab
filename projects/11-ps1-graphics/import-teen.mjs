import fs from 'node:fs';
import {FBXLoader} from 'three/addons/loaders/FBXLoader.js';
import {TextureLoader,Texture,Box3,Vector3,Quaternion} from 'three';
TextureLoader.prototype.load=function(){return new Texture()};
globalThis.window={URL:globalThis.URL};
const dir=new URL('./assets/PSXStyleTeen/',import.meta.url);const buf=fs.readFileSync(new URL('PS1Teen1.fbx',dir));
const root=new FBXLoader().parse(buf.buffer.slice(buf.byteOffset,buf.byteOffset+buf.byteLength),'');root.updateMatrixWorld(true);
for(const name of ['arm_stretchr','arm_stretchl']){const bone=root.getObjectByName(name);const wp=bone.getWorldPosition(new Vector3());const q=bone.getWorldQuaternion(new Quaternion());const dq=new Quaternion().setFromAxisAngle(new Vector3(0,0,1),wp.x>0?-.58:.58);q.premultiply(dq);bone.quaternion.copy(bone.parent.getWorldQuaternion(new Quaternion()).invert().multiply(q));root.updateMatrixWorld(true);}root.traverse(o=>{if(o.isSkinnedMesh)o.skeleton.update()});
const out=[];root.traverse(o=>{if(!o.isMesh)return;const g=o.geometry.clone();if(o.isSkinnedMesh){const a=g.attributes.position,v=new Vector3();for(let i=0;i<a.count;i++){v.fromBufferAttribute(a,i);o.applyBoneTransform(i,v);a.setXYZ(i,v.x,v.y,v.z)}}g.applyMatrix4(o.matrixWorld);g.computeBoundingBox(); console.log(o.name,g.attributes.position.count,g.boundingBox);const a=g.index?g.toNonIndexed():g;out.push({name:o.name,positions:Array.from(a.attributes.position.array),normals:Array.from(a.attributes.normal.array),uv:Array.from(a.attributes.uv.array)});});fs.writeFileSync(new URL('mesh.json',dir),JSON.stringify(out));
