'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const E=require('../web/assets/trading-engine.js');
const root=path.resolve(__dirname,'..');
const tableDir=path.join(root,'results/tables/collective_trading_v1');
const checkDir=path.join(root,'results/checks');
fs.mkdirSync(tableDir,{recursive:true});fs.mkdirSync(checkDir,{recursive:true});
let checks=0;
function check(name,fn){fn();checks++;console.log('PASS',name);}
function near(a,b,tolerance=1e-10){assert.ok(Math.abs(a-b)<=tolerance,`${a} != ${b}`);}
function csv(file,rows){const keys=Object.keys(rows[0]);const text=[keys.join(','),...rows.map(row=>keys.map(k=>JSON.stringify(row[k])).join(','))].join('\n')+'\n';fs.writeFileSync(path.join(tableDir,file),text);}
function enumerate(weights,q){let mean=0,second=0;function visit(i,total,p){if(i===weights.length){mean+=p*total;second+=p*total*total;return;}for(const [sign,prob] of [[-1,q/2],[0,1-q],[1,q/2]])visit(i+1,total+weights[i]*sign,p*prob);}visit(0,0,1);return second-mean*mean;}

check('independent weighted action law by exact enumeration',()=>{
 for(const weights of [[1],[1,2,3,4],[.1,.3,.6]])for(const q of [.1,.5,1])near(enumerate(weights,q),q*weights.reduce((s,v)=>s+v*v,0));
});
check('coherent capital block versus independent decisions',()=>{
 const weights=[1,2,3,4];near(enumerate(weights,1),30);near(enumerate([10],1),100);
 const cov=weights.map(()=>weights.map(()=>1));near(E.math.covarianceVariance(cov,weights),100);
});
check('splitting preserves common-parent covariance; RV and cumulative variance differ',()=>{
 const weights=Array(10).fill(10);const common=weights.map(()=>weights.map(()=>1));const independent=weights.map((_,i)=>weights.map((__,j)=>i===j?1:0));
 near(E.math.covarianceVariance(common,weights),10000);near(E.math.covarianceVariance(independent,weights),1000);
 const rvCommon=weights.reduce((s,w)=>s+w*w,0),rvIndependent=weights.reduce((s,w)=>s+w*w,0);near(rvCommon,1000);near(rvIndependent,1000);
});
check('positive-reinforcement scalar control does not impose cycles',()=>{
 let m=.12;let previous=m;let crossings=0;
 for(let t=0;t<400;t++){m=Math.tanh(1.4*m);assert.ok(m>=previous-1e-14);if(m*previous<0)crossings++;previous=m;}
 assert.equal(crossings,0);assert.ok(m>.7);
});
check('configuration validation',()=>{
 for(const o of [{scenario:'unknown'},{mode:'bad'},{steps:0},{steps:1.2},{steps:5001},{memory:-1},{coupling:NaN},{seed:Infinity},{weighting:'bad'},{externalOrders:'no'}])assert.throws(()=>E.create(o));
});
check('deterministic path, snapshot read and mutation isolation',()=>{
 const a=E.create({seed:'repeat'}),b=E.create({seed:'repeat'});
 for(let i=0;i<90;i++){a.snapshot();a.snapshot();const x=a.step(),y=b.step();assert.deepEqual(x,y);x.bars[0].close=-1;x.network.nodes[0].weight=999;}
 assert.deepEqual(a.snapshot(),b.snapshot());
});
check('horizon prefix invariance and completion idempotence',()=>{
 const a=E.simulate({steps:80,seed:11,scenario:'turn'});const b=E.create({steps:230,seed:11,scenario:'turn'});for(let i=0;i<80;i++)b.step();const bb=b.snapshot();
 assert.deepEqual(a.bars,bb.bars);assert.deepEqual(a.events,bb.events);assert.deepEqual(a.network,bb.network);assert.deepEqual(a.metrics,bb.metrics);
 const short=E.create({steps:3});short.step();short.step();const done=short.step();for(let i=0;i<6;i++)assert.deepEqual(short.step(),done);
});
check('reset returns exact initial state and seed streams are isolated',()=>{
 const a=E.create({seed:23,scenario:'split'});const start=a.snapshot();for(let i=0;i<55;i++)a.step();assert.deepEqual(a.reset(),start);
 const x=E.simulate({seed:88,scenario:'buy'});E.simulate({seed:99,scenario:'sell'});assert.deepEqual(E.simulate({seed:88,scenario:'buy'}),x);
});
check('advance messages reveal only current intent and current execution',()=>{
 const e=E.create({scenario:'turn'});
 for(let t=1;t<=180;t++){
  const s=e.step();assert.ok(s.events.every(v=>v.tick<=s.tick));
  if(t<18)assert.ok(!s.events.some(v=>v.type==='intent'));
  if(t<75)assert.ok(!s.events.some(v=>v.id.startsWith('new-seller')));
  for(const event of s.events){assert.deepEqual(Object.keys(event).sort(),['body','id','tick','title','type']);assert.ok(event.title.en&&event.title.zh&&event.body.en&&event.body.zh);}
 }
});
check('capital weights, graph coupling and memory ablations',()=>{
 const base=E.simulate({seed:35,scenario:'turn'}),noCoupling=E.simulate({seed:35,scenario:'turn',coupling:0}),noMemory=E.simulate({seed:35,scenario:'turn',memory:0});
 near(base.network.nodes.reduce((s,n)=>s+n.weight,0),1);assert.ok(base.network.edges.some(x=>x.layer==='cross'));
 assert.ok(!noCoupling.network.edges.some(x=>x.layer==='cross'));assert.notEqual(base.price,noCoupling.price);assert.notEqual(base.price,noMemory.price);
 const equal=E.simulate({seed:35,weighting:'equal'});for(const n of equal.network.nodes)near(n.weight,1/48);
 const endogenous=E.simulate({seed:35,externalOrders:false});assert.ok(endogenous.events.every(x=>!['intent','execution','completion'].includes(x.type)));
});

const all=[];
const ablations=[{id:'full',coupling:.55,memory:.75,weighting:'heterogeneous'},
 {id:'no_cross_layer',coupling:0,memory:.75,weighting:'heterogeneous'},
 {id:'no_memory',coupling:.55,memory:0,weighting:'heterogeneous'},
 {id:'equal_weights',coupling:.55,memory:.75,weighting:'equal'},
 {id:'no_announced_program',coupling:.55,memory:.75,weighting:'heterogeneous',externalOrders:false}];
const seeds=Array.from({length:32},(_,i)=>101+i*37);
check('all fixed-seed scenarios and ablations satisfy finite/flow/OHLC/chronology bounds',()=>{
 for(const scenario of ['buy','sell','split','turn'])for(const mode of ['guided','experiment'])for(const seed of seeds){
  const variants=scenario==='turn'&&mode==='experiment'?ablations:[ablations[0]];
  for(const variant of variants){
   const s=E.simulate(Object.assign({scenario,mode,seed,steps:180},variant));assert.equal(s.bars.length,180);
   let rv=0,net=0,meanCoherence=0;const phases={forming:0,holding:0,fragmenting:0,mixed:0};let previous=100;let maxPrice=100,maxDrawdown=0;
   for(const b of s.bars){
    for(const k of ['open','high','low','close','volume','flow','pressure'])assert.ok(Number.isFinite(b[k]),k);
    assert.ok(b.low>0&&b.low<=Math.min(b.open,b.close)&&b.high>=Math.max(b.open,b.close));assert.ok(b.volume>=0);assert.ok(Math.abs(b.flow)<=b.volume+1e-9);assert.ok(Math.abs(b.pressure)<=1+1e-12);
    near(previous,b.open);const r=Math.log(b.close/b.open);rv+=r*r;net+=r;previous=b.close;phases[b.phase]++;maxPrice=Math.max(maxPrice,b.close);maxDrawdown=Math.max(maxDrawdown,1-b.close/maxPrice);
   }
   assert.ok(s.events.every(e=>e.tick<=180));for(const k of ['pressure','coherence','liquidity','fastAlignment','slowAlignment'])assert.ok(Number.isFinite(s.metrics[k]));
   assert.ok(s.metrics.coherence>=0&&s.metrics.coherence<=1);assert.ok(s.metrics.liquidity>=.35&&s.metrics.liquidity<=1.8);
   all.push({scenario,mode,variant:variant.id,seed,total_log_return:net,return_pct:100*(s.price/100-1),realized_variance:rv,max_drawdown_pct:100*maxDrawdown,
    forming_ticks:phases.forming,holding_ticks:phases.holding,fragmenting_ticks:phases.fragmenting,mixed_ticks:phases.mixed,final_coherence:s.metrics.coherence});
  }
 }
});
csv('simulation_runs.csv',all);
const summary=[];
for(const scenario of ['buy','sell','split','turn'])for(const mode of ['guided','experiment'])for(const variant of ablations){
 const rows=all.filter(x=>x.scenario===scenario&&x.mode===mode&&x.variant===variant.id);if(!rows.length)continue;
 for(const metric of ['return_pct','realized_variance','max_drawdown_pct','fragmenting_ticks','final_coherence']){
  const values=rows.map(x=>x[metric]);const mean=values.reduce((a,b)=>a+b,0)/values.length;const sd=Math.sqrt(values.reduce((s,v)=>s+(v-mean)**2,0)/(values.length-1));const half=2.039513446*Math.sqrt(sd*sd/values.length);
  summary.push({scenario,mode,variant:variant.id,metric,seeds:values.length,mean,sd,mean_ci_low:mean-half,mean_ci_high:mean+half,interval:'Approximate 95% t interval over 32 independent synthetic seeds'});
 }
}
csv('simulation_summary.csv',summary);
const paired=[];
for(const variant of ablations.slice(1))for(const metric of ['return_pct','realized_variance','max_drawdown_pct','fragmenting_ticks']){
 const full=all.filter(x=>x.scenario==='turn'&&x.mode==='experiment'&&x.variant==='full');const control=all.filter(x=>x.scenario==='turn'&&x.mode==='experiment'&&x.variant===variant.id);
 const diffs=full.map((a,i)=>{assert.equal(a.seed,control[i].seed);return a[metric]-control[i][metric];});const mean=diffs.reduce((s,x)=>s+x,0)/diffs.length;const sd=Math.sqrt(diffs.reduce((s,x)=>s+(x-mean)**2,0)/(diffs.length-1));const half=2.039513446*sd/Math.sqrt(diffs.length);
 paired.push({scenario:'turn',mode:'experiment',control:variant.id,metric,seeds:diffs.length,full_minus_control:mean,paired_sd:sd,mean_ci_low:mean-half,mean_ci_high:mean+half,scope:'Descriptive synthetic-seed contrast; no market effect or familywise significance claim'});
}
csv('simulation_paired_ablations.csv',paired);
const demo=[];
for(const scenario of ['buy','sell','split','turn']){
 const s=E.simulate({scenario,mode:'guided',seed:5253});
 for(const b of s.bars)demo.push(Object.assign({scenario,seed:5253},b));
}
csv('guided_demo_paths.csv',demo);
const results={status:'pass',version:E.version,checks,independent_seeds:32,synthetic_runs:all.length,seed_unit:'Independent full simulator run; paired ablations reuse innovation streams',
  control_laws:{independent_weights_variance:30,coherent_block_variance:100,split_parent_cumulative_variance:10000,independent_children_cumulative_variance:1000,squared_flow_sum_both:1000},
  causal_event_messages:true,prefix_invariance:true,completed_path_stable:true,parameters_fitted_to_market:false,
  automatic_periodic_cycle_claim:false,real_market_predictive_claim:false};
fs.writeFileSync(path.join(checkDir,'collective_trading_engine_v1.json'),JSON.stringify(results,null,2)+'\n');
console.log(JSON.stringify(results,null,2));
