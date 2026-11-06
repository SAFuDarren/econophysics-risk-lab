const assert=require('node:assert/strict');
const A=require('../web/assets/trading-account.js');
const near=(a,b,tol=1e-7)=>assert.ok(Math.abs(a-b)<=tol*Math.max(1,Math.abs(a),Math.abs(b)),`${a} != ${b}`);
function identity(a){const s=a.snapshot();near(s.equity,s.cash+s.quantity*s.lastPrice);near(s.equity-s.initialCash,s.realizedPnl+s.unrealizedPnl);near(s.realizedPnl,s.trades.reduce((sum,t)=>sum+t.realizedPnl,0));assert.ok(s.totalFees>=0&&Number.isFinite(s.maxDrawdownPct));}
let checks=0;
for(const side of ['buy','short']){
 const a=A.create({feeBps:0,slippageBps:0});a.mark(100,0);assert.ok(a.trade({side,fraction:1,price:100,tick:0}).ok);identity(a);near(a.snapshot().quantity,side==='buy'?1000:-1000);a.mark(side==='buy'?110:90,1);near(a.snapshot().equity,110000);assert.ok(a.close({price:side==='buy'?110:90,tick:1}).ok);identity(a);near(a.snapshot().realizedPnl,10000);near(a.snapshot().quantity,0);checks+=8;
}
for(const side of ['buy','short']){
 const a=A.create();a.mark(100,0);assert.ok(a.trade({side,fraction:1,price:100,tick:0}).ok);assert.ok(a.snapshot().grossExposure<=1+1e-12);identity(a);assert.equal(a.trade({side,fraction:1,price:100,tick:0}).ok,false);let s=a.snapshot();const before=s.equity;
 assert.ok(a.trade({side:side==='buy'?'sell':'cover',fraction:.5,price:100,tick:1}).ok);identity(a);assert.ok(a.snapshot().equity<before);assert.ok(a.close({price:100,tick:2}).ok);s=a.snapshot();identity(a);assert.ok(s.realizedPnl<0&&s.totalFees>0);near(s.cash,s.equity);checks+=9;
}
{
 const a=A.create();a.mark(100,0);a.trade({side:'buy',fraction:.5,price:100,tick:0});assert.equal(a.trade({side:'short',fraction:.5,price:100,tick:1}).ok,false);assert.equal(a.trade({side:'cover',fraction:1,price:100,tick:1}).ok,false);assert.equal(a.trade({side:'buy',fraction:2,price:100,tick:2}).ok,false);assert.equal(a.trade({side:'buy',fraction:.5,price:NaN,tick:2}).ok,false);assert.equal(a.trade({side:'buy',fraction:.5,price:100,tick:0}).ok,false);identity(a);checks+=6;
}
{
 const a=A.create({feeBps:0,slippageBps:0});a.mark(100,0);a.trade({side:'short',fraction:1,price:100,tick:0});a.mark(180,1);assert.equal(a.snapshot().quantity,0);assert.equal(a.snapshot().liquidated,true);near(a.snapshot().equity,20000);identity(a);assert.equal(a.snapshot().trades.at(-1).forced,true);checks+=5;
}
{
 const a=A.create();a.mark(100,0);a.trade({side:'short',fraction:1,price:100,tick:0});a.mark(400,1);assert.ok(a.snapshot().insolvent);assert.equal(a.snapshot().quantity,0);assert.equal(a.trade({side:'buy',fraction:1,price:400,tick:2}).ok,false);identity(a);checks+=4;
}
{
 const a=A.create();a.mark(100,0);const before=JSON.stringify(a.snapshot());const r=a.review({bars:[{tick:0,open:100,close:100}]});assert.equal(JSON.stringify(a.snapshot()),before);assert.equal(r.score,50);assert.equal(r.metrics.returnPct,0);assert.ok(r.benchmark.passiveReturnPct<0);assert.equal(r.notes.length,1);checks+=5;
}
{
 const a=A.create();a.mark(100,0);a.trade({side:'buy',fraction:1,price:100,tick:0});a.mark(110,1);const bars=[{tick:0,open:100,close:100},{tick:1,open:100,close:110}];near(a.review({bars}).benchmark.passiveReturnPct,a.snapshot().returnPct);a.close({price:110,tick:1});near(a.review({bars,done:true}).benchmark.passiveReturnPct,a.snapshot().returnPct);identity(a);checks+=3;
}
{
 let seed=887;const u=()=>{seed=(1664525*seed+1013904223)>>>0;return seed/4294967296;};
 for(let run=0;run<60;run++){
  const a=A.create();let p=100;for(let t=0;t<90;t++){p*=Math.exp((u()-.5)*.08);a.mark(p,t);const side=['buy','sell','short','cover','close'][Math.floor(u()*5)];a.trade({side,fraction:[.25,.5,1][Math.floor(u()*3)],price:p,tick:t});identity(a);assert.ok(Number.isFinite(a.review({bars:[]}).score));checks+=2;}if(a.snapshot().quantity)a.close({price:p,tick:90});identity(a);
 }
}
console.log(JSON.stringify({status:'pass',checks,scope:'long/short identity, costs, partial close, limits, liquidation, loss, review purity and randomized accounting paths'},null,2));
