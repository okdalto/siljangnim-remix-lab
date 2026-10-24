const fs=require('fs'),assert=require('assert'),{apply,pixel}=require('./core.cjs'),data=require('./data.json'),expected=require('./expected.json');
let maxError=0;
for(let mode=0;mode<5;mode++){
 const out=apply(data.rgb,data.n,mode);assert.equal(out.length,2700);
 for(let i=0;i<out.length;i++){assert(Number.isFinite(out[i]));maxError=Math.max(maxError,Math.abs(out[i]-expected[mode][i]));}
}
assert(maxError<1e-6);
const uniform=Array(32*32*3).fill(.5);
assert(apply(uniform,32,3).every(v=>v===0));assert(apply(uniform,32,4).every(v=>v===0));
assert(apply(uniform,32,1).every(v=>Math.abs(v-.5)<1e-12));
const a=Array.from({length:5*5*3},(_,i)=>i/75);
assert.deepEqual(pixel(a,5,1,1,0).rgb,a.slice((2*5+2)*3,(2*5+2)*3+3));
const step=Array.from({length:32*32*3},(_,i)=>Math.floor(i/3)%32>=16?1:0);
assert.equal(pixel(step,32,14,8,3).rgb[0],1);assert.equal(pixel(step,32,0,8,3).rgb[0],0);
const scene=require('./scene.json');new (Object.getPrototypeOf(async function(){}).constructor)('ctx',scene.script.setup);new Function('ctx',scene.script.render);
const report={numeric_values_compared:13500,max_error:maxError,constant_and_step_checks:true,scene_syntax:true};fs.writeFileSync(__dirname+'/verification.json',JSON.stringify(report,null,2));console.log(report);
