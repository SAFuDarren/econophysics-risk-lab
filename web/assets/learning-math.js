(function(root,factory){'use strict';const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.LearningMath=api;}(typeof globalThis!=='undefined'?globalThis:this,function(){
'use strict';
function bookFill(quantity,depth){
 if(!(quantity>0&&quantity<=160&&depth>0))throw new RangeError('Invalid teaching-book input');
 let remaining=quantity,cost=0,levels=0;const rows=[];
 for(let i=0;i<8;i++){const price=100.02+.02*i,fill=Math.min(remaining,depth);cost+=price*fill;remaining-=fill;if(fill>0)levels++;rows.push({price,fill,depth});}
 if(remaining>1e-8)throw new RangeError('Insufficient displayed quantity');
 const vwap=cost/quantity;return {quantity,depth,rows,levels,vwap,slippage:(vwap-100.02)/100.02*10000};
}
function varianceRisk(concentrated,rho){
 if(!Number.isFinite(rho)||rho<0||rho>1)throw new RangeError('Correlation outside the teaching model');
 const weights=concentrated?[.4,...Array(19).fill(.6/19)]:Array(20).fill(.05),h=weights.reduce((s,x)=>s+x*x,0);
 return {weights,h,variance:rho+(1-rho)*h,multiplier:(rho+(1-rho)*h)/h};
}
function memoryRisk(length){if(![1,2,4,8].includes(length))throw new RangeError('Block length');return {rv:8,cumulative:8*length};}
function mixtureMoments(p){if(!Number.isFinite(p)||p<0||p>1)throw new RangeError('Probability');const mean=4*p-2,within=1,between=16*p*(1-p);return {mean,within,between,variance:within+between,second:within+between+mean*mean};}
function fragmentationMoments(children){if(![1,2,5,10,20].includes(children))throw new RangeError('Child count');return {quantity:100,rawBaseline:10000/children,groupedBaseline:10000,flowSecond:10000,rawEnergyG:children};}
function calibrationInterval(scores,ratios,nominal){
 if(!scores.length||scores.some(x=>!Number.isFinite(x)||x<0)||ratios.some(x=>!Number.isFinite(x)||x<=0)||!(nominal>0&&nominal<1))throw new RangeError('Invalid calibration inputs');
 const sorted=[...scores].sort((a,b)=>a-b),k=Math.ceil((sorted.length+1)*nominal),q=k>sorted.length?Infinity:sorted[k-1],low=Math.exp(-q),high=Math.exp(q);
 return {k,q,low,high,covered:ratios.filter(x=>x>=low&&x<=high).length,total:ratios.length};
}
return Object.freeze({bookFill,varianceRisk,memoryRisk,mixtureMoments,fragmentationMoments,calibrationInterval});
}));
