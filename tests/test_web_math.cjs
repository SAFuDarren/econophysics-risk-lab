const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.resolve(__dirname,'..'),M=require('../web/assets/math.js'),sandbox={window:{}};
vm.createContext(sandbox);vm.runInContext(fs.readFileSync(path.join(root,'web/assets/data/research-data.js'),'utf8'),sandbox);
const D=sandbox.window.ResearchData;let checks=0;
function close(a,b,tol=3e-9){checks++;assert.ok(Math.abs(a-b)<=tol*Math.max(1,Math.abs(a),Math.abs(b)),`${a} != ${b}`);}
const fixed=M.moments(Array(10).fill(10),.2);close(fixed.meanV,20);close(fixed.varV,160);close(fixed.s2,1000);
for(const c of [.4,.65,1,1.35,1.6])for(const q of [.1,.2,.4]){
 const s2=M.interp(D.curve,c),r=M.infer(q*128,q*(1-q)*s2,q*(.02/128)**2*s2,D.curve);
 close(r.c,c);close(r.q,q);close(r.lambda,.02);
}
const fixtures=JSON.parse(fs.readFileSync(path.join(root,'results/checks/risk_lab_v1/browser_fixtures.json')));
for(const f of fixtures.risk_cases){
 const flat=D.risk.find(r=>r.date===f.date).cov[f.lookback],got=M.risk(flat,f.weights,f.eta),e=f.expected;
 close(got.full,e.variance_full_observed);close(got.diagonal,e.variance_self);close(got.counter,e.variance_counterfactual);
 close(got.fullVol,e.annual_vol_observed_pct);close(got.diagonalVol,e.annual_vol_diagonal_pct);close(got.counterVol,e.annual_vol_counterfactual_pct);close(got.collectiveShare,e.collective_share);
}
for(const c of [.2,1,2.4]){
 const g=M.graph(128,c,20261027);assert.equal(new Set(g.groups.flat()).size,128);checks++;
 close(g.s2,g.groups.reduce((a,g)=>a+g.length*g.length,0));
 assert.deepEqual(g,M.graph(128,c,20261027));checks++;
 const sample=M.sample(128,c,.2,.02,1,256,20261028);assert.ok(sample.varV>0&&sample.varR>=0);checks++;
}
assert.throws(()=>M.risk(Array(81).fill(0),Array(9).fill(0)));checks++;
assert.throws(()=>M.risk(Array(81).fill(0),[-1,...Array(8).fill(1)]));checks++;
assert.equal(M.infer(0,1,1,D.curve).flag,'degenerate');checks++;
const dates=D.forecast.dates;assert.equal(dates.length,183);assert.equal(dates[0],'2026-04-01');assert.equal(dates.at(-1),'2026-09-30');checks+=3;
for(const p of M.chainLaw(.2))assert.ok(p.p>=0);close(M.chainLaw(.2).reduce((a,r)=>a+r.p,0),1);
close(M.skill(D.forecast.losses['HAR+All'],D.forecast.losses.Persistence),31.20400030806677);
console.log(JSON.stringify({status:'pass',checks,scope:'New interface engine against Python risk fixtures, frozen moments, complete date coverage and edge cases'}));
