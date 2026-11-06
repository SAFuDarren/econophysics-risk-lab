/* Conditional mechanism diagnostics. No unobserved investor identities are inferred. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.TradingDebrief=api;}(typeof globalThis!=='undefined'?globalThis:this,function(){
 'use strict';const mean=a=>a.reduce((s,x)=>s+x,0)/a.length,variance=a=>Math.max(0,mean(a.map(x=>x*x))-mean(a)**2);
 function analyze(snapshot){
  if(snapshot?.source!=='history')return null;
  const bars=snapshot.bars.filter(b=>b.tick<=snapshot.tick),map=new Map(bars.map(b=>[b.tick,b]));
  if(bars.some(b=>!Number.isFinite(b.flowBase)||!Number.isFinite(b.squaredSizeBase)))throw new Error('Executed-size baseline is missing');
  const returns=new Map();for(const b of bars){const p=map.get(b.tick-1);if(p)returns.set(b.tick,Math.log(b.close/p.close));}
  const calibration=bars.filter(b=>b.tick>=-29&&b.tick<=0&&returns.has(b.tick));if(calibration.length!==30)throw new Error('Thirty pre-play response observations are required');
  const f=calibration.map(b=>b.flowBase),r=calibration.map(b=>returns.get(b.tick)),mf=mean(f),mr=mean(r),vf=variance(f),cov=mean(f.map((x,i)=>x*r[i]))-mf*mr;
  const beta=Math.max(0,vf>1e-18?cov/vf:0),alpha=mr-beta*mf,eta2=mean(r.map((y,i)=>(y-alpha-beta*f[i])**2));
  const points=[];
  for(let tick=0;tick<=snapshot.tick;tick++){
   const slow=bars.filter(b=>b.tick>=tick-14&&b.tick<=tick),fast=slow.slice(-3),flows=slow.map(b=>b.flowBase);if(slow.length!==15||fast.length!==3)throw new Error('Insufficient trailing observations');
   const bSlow=mean(slow.map(b=>b.squaredSizeBase)),bFast=mean(fast.map(b=>b.squaredSizeBase)),meanFlow=mean(flows),varFlow=variance(flows),g=bSlow>0?varFlow/bSlow:null;
   const meanEnergy=(alpha+beta*meanFlow)**2,flowEnergy=beta*beta*bFast*g,independentFlowEnergy=beta*beta*bFast,residualEnergy=eta2;
   const h=meanEnergy+flowEnergy+residualEnergy,h1=meanEnergy+independentFlowEnergy+residualEnergy,direct=meanEnergy+beta*beta*varFlow+residualEnergy,cancel=meanEnergy+beta*beta*bSlow*g+residualEnergy;
   const base=map.get(tick),next=returns.get(tick+1),observed=mean(slow.map(b=>returns.get(b.tick)**2));
   points.push({tick,time:base.time+60000,forecastTick:tick+1,largeBuyQuote:fast.reduce((s,b)=>s+b.largeBuyQuote,0),largeSellQuote:fast.reduce((s,b)=>s+b.largeSellQuote,0),pressure:fast.reduce((s,b)=>s+b.flowBase,0)/fast.reduce((s,b)=>s+b.volume,0),bFast,bSlow,meanFlow,varFlow,g,meanEnergy,flowEnergy,residualEnergy,independentFlowEnergy,modelSecondMoment:h,independentSecondMoment:h1,directSecondMoment:direct,cancellationSecondMoment:cancel,modelRmsPct:100*Math.sqrt(h),independentRmsPct:100*Math.sqrt(h1),observedTrailingRmsPct:100*Math.sqrt(observed),nextAbsReturnPct:next===undefined?null:100*Math.abs(next)});
  }
  return {version:'1.0.0',information:'Uses executed aggregate-size squares in addition to macro OHLC/flow. It is not macro-only inversion.',calibration:{firstTick:-29,lastTick:0,observations:30,alpha,beta,residualSecondMoment:eta2,betaConstraint:'nonnegative',updatedDuringPlay:false},windows:{activity:3,amplification:15,realizedRms:15},points};
 }
 return Object.freeze({version:'1.0.0',analyze});
}));
