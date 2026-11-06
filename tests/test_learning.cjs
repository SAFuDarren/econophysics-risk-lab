'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const R=path.resolve(__dirname,'..'),M=require('../web/assets/learning-math.js'),content=JSON.parse(fs.readFileSync(path.join(R,'docs/learning/lessons.json'))),demo=JSON.parse(fs.readFileSync(path.join(R,'docs/learning/calibration-demo.json'))),katex=require('../web/assets/vendor/katex/katex.min.js');
function close(a,b){assert.ok(Math.abs(a-b)<1e-9,`${a} != ${b}`);}
let formulas=0;
for(const l of content.lessons){assert.equal(l.self_test.options.length,3);assert.ok(l.self_test.correct>=0&&l.self_test.correct<3);for(const t of [l.title,l.question,l.intuition,l.project_connection,l.misconception,l.self_test.question,l.self_test.explanation])for(const lang of ['en','zh'])assert.ok(t[lang]);for(const s of [l.formula.latex,...l.symbols.map(x=>x.symbol)]){assert.equal(/[\u0000-\u001f]/.test(s),false,l.id);katex.renderToString(s,{throwOnError:true,strict:'ignore'});formulas++;}}
for(const quantity of [10,20,80,160]){const thin=M.bookFill(quantity,20),deep=M.bookFill(quantity,80);close(thin.rows.reduce((s,r)=>s+r.fill,0),quantity);assert.ok(deep.vwap<=thin.vwap+1e-10);assert.ok(thin.rows.every(r=>r.fill>=0&&r.fill<=r.depth));}close(M.bookFill(80,20).vwap,100.05);
for(const concentrated of [false,true])for(const rho of [0,.2,.5,1]){const z=M.varianceRisk(concentrated,rho);let v=0;z.weights.forEach((a,i)=>z.weights.forEach((b,j)=>v+=a*b*(i===j?1:rho)));close(z.variance,v);close(z.weights.reduce((a,b)=>a+b),1);}
// Enumerate all independent block-sign assignments rather than reusing the displayed formula.
for(const L of [1,2,4,8]){const blocks=8/L,paths=2**blocks;let erv=0,esum=0,esum2=0;for(let k=0;k<paths;k++){const returns=Array.from({length:8},(_,t)=>(k>>Math.floor(t/L))&1?1:-1),sum=returns.reduce((s,x)=>s+x,0);erv+=returns.reduce((s,x)=>s+x*x,0)/paths;esum+=sum/paths;esum2+=sum*sum/paths;}const z=M.memoryRisk(L);close(z.rv,erv);close(z.cumulative,esum2-esum*esum);}
for(const p of [0,.1,.5,.9,1]){const z=M.mixtureMoments(p);close(z.variance,z.within+z.between);close(z.second,5);}
for(const n of [1,2,5,10,20]){const z=M.fragmentationMoments(n);close(z.rawBaseline,n*(100/n)**2);close(z.flowSecond/z.rawBaseline,z.rawEnergyG);}
const ci=M.calibrationInterval(demo.calibration_scores,demo.evaluation_ratios,.9);assert.equal(ci.k,59);assert.equal(ci.covered,121);assert.equal(ci.total,128);assert.equal(M.calibrationInterval([1,2,3,4],[1],.9).high,Infinity);
for(const f of [()=>M.mixtureMoments(-1),()=>M.varianceRisk(false,2),()=>M.memoryRisk(3),()=>M.bookFill(0,20)])assert.throws(f,RangeError);
console.log(JSON.stringify({status:'pass',lessons:content.lessons.length,katex_strings:formulas,teaching_models:7,controlled_calibration_cases:ci.total}));
