/* Pure numeric cross-language audit. No browser automation or DOM execution. */
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname,'..');
const payload = fs.readFileSync(path.join(root,'apps/risk_lab_v1/data.json'),'utf8');
const code = fs.readFileSync(path.join(root,'apps/risk_lab_v1/src/app.js'),'utf8');
if(code.split(';init();').length!==2)throw new Error('Cannot isolate numeric functions');
const sandbox = {document:{getElementById:()=>({textContent:payload})},window:{}};
vm.createContext(sandbox);vm.runInContext(code.replace(';init();',';'),sandbox);
const lab=sandbox.window.MarketLab, checks=[];
const check=(name,pass)=>checks.push({name,pass:Boolean(pass)});
const close=(a,b)=>Array.isArray(a)?a.length===b.length&&a.every((v,i)=>close(v,b[i])):Math.abs(a-b)<=2e-9*Math.max(1,Math.abs(a),Math.abs(b));
const fixtures=JSON.parse(fs.readFileSync(path.join(root,'results/checks/risk_lab_v1/browser_fixtures.json'),'utf8'));
for(const f of fixtures.risk_cases){
 const flat=lab.data.risk.find(s=>s.date===f.date).cov[f.lookback];
 const got=lab.riskCalc(flat,f.weights,f.eta);
 check('Python/JS risk fixture '+f.date,Object.keys(got).every(k=>close(got[k],f.expected[k])));
 const diagonal=lab.riskCalc(flat,f.weights,0);
 check('Eta zero preserves marginal risk '+f.date,close(diagonal.annual_vol_diagonal_pct,diagonal.annual_vol_counterfactual_pct)&&Math.abs(diagonal.collective_share)<1e-12);
}
let zeroRejected=false;try{lab.riskCalc(lab.data.risk[0].cov['63'],Array(9).fill(0));}catch(e){zeroRejected=true;}
check('Zero portfolio rejected',zeroRejected);
check('Default training screen agrees with Python',lab.screen(.8).mask===47);
for(let i=50;i<=95;i++){
 const r=lab.screen(i/100);
 check('Valid greedy training representatives '+i,r.mask>0&&r.mask<64&&r.decisions.length===6);
}
for(let mask=1;mask<64;mask++)for(const cost of [0,5,10,25])for(const period of ['historical_test','confirmation']){
 const s=lab.data.subsets[mask],m=lab.metric(s,cost,period,'capital'),r=lab.metric(s,cost,period,'risk');
 check('Browser risk scale '+mask+'/'+cost+'/'+period,close(r.cumulative_pnl_pct,m.cumulative_pnl_pct*s.scale)&&close(r.mean_daily_turnover,m.mean_daily_turnover*s.scale)&&Object.values(r).every(Number.isFinite));
}
const g1=lab.modelGraph(20261027,.7),g2=lab.modelGraph(20261027,1.5),g3=lab.modelGraph(20261027,1.5);
check('Deterministic seeded ER graph',JSON.stringify(g2)===JSON.stringify(g3));
const edges=new Set(g2.edges.map(e=>e.join('-')));
check('Nested edge uniforms preserve lower-rho edges',g1.edges.every(e=>edges.has(e.join('-'))));
check('Cluster partition covers each of 128 nodes once',new Set(g2.groups.flat()).size===128&&g2.groups.flat().length===128);
check('S2 uses entire cluster squared sum',g2.s2===g2.groups.reduce((s,g)=>s+g.length*g.length,0));
check('Equal-loadings covariance example preserves q lambda squared',close(.2*(.02/128)**2*g2.s2,.05*(.04/128)**2*g2.s2));
check('Live graph extreme range finite',[.2,1,2.4].every(rho=>{const g=lab.modelGraph(20261027,rho);return g.s2>=128&&g.s2<=128**2&&Number.isFinite(g.chi);}));
const report={status:checks.every(r=>r.pass)?'pass':'fail',checks:checks.length,failures:checks.filter(r=>!r.pass),scope:'Pure numeric JavaScript/Python agreement; browser behavior checked separately',details:checks};
fs.writeFileSync(path.join(root,'results/checks/risk_lab_v1/javascript_audit.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({status:report.status,checks:report.checks,failures:report.failures},null,2));
if(report.status!=='pass')process.exitCode=1;
