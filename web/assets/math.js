/* Mathematical engine. Parameters follow the frozen PC5253 model.
   c is the course notation for the original Python parameter rho; q = 2a. */
(function(root){
'use strict';
function rng(seed){let z=(seed>>>0)||1;return function(){z^=z<<13;z^=z>>>17;z^=z<<5;return(z>>>0)/4294967296;};}
function graph(n,c,seed){
 if(!Number.isInteger(n)||n<2||!Number.isFinite(c)||c<0||c>n-1)throw Error('Invalid ER parameters');
 const rand=rng(seed),parent=Array.from({length:n},(_,i)=>i),edges=[];
 function find(i){while(parent[i]!==i){parent[i]=parent[parent[i]];i=parent[i];}return i;}
 for(let i=0;i<n;i++)for(let j=i+1;j<n;j++)if(rand()<c/(n-1)){edges.push([i,j]);const a=find(i),b=find(j);if(a!==b)parent[a]=b;}
 const groupsMap=new Map();for(let i=0;i<n;i++){const k=find(i);if(!groupsMap.has(k))groupsMap.set(k,[]);groupsMap.get(k).push(i);}
 const groups=[...groupsMap.values()].sort((a,b)=>b.length-a.length||a[0]-b[0]),sizes=groups.map(g=>g.length);
 return{n,c,seed,edges,groups,s2:sizes.reduce((a,s)=>a+s*s,0),s3:sizes.reduce((a,s)=>a+s*s*s,0),largest:sizes[0]};
}
function moments(sizes,q,lambda=.02,u=1){
 const n=sizes.reduce((a,s)=>a+s,0);if(!n||q<=0||q>=1||lambda<=0||u<=0)throw Error('Invalid moment parameters');
 const s2=sizes.reduce((a,s)=>a+s*s,0),s3=sizes.reduce((a,s)=>a+s*s*s,0);
 return{n,s2,s3,meanV:q*u*n,varV:q*(1-q)*u*u*s2,varR:q*(lambda/n)**2*s2,delta:s3/(n*s2)};
}
function interp(curve,x,xkey='rho',ykey='s2'){
 if(!curve.length)throw Error('Empty curve');if(x<=curve[0][xkey])return curve[0][ykey];if(x>=curve.at(-1)[xkey])return curve.at(-1)[ykey];
 let lo=0,hi=curve.length-1;while(hi-lo>1){const m=(lo+hi)>>1;if(curve[m][xkey]<x)lo=m;else hi=m;}
 const a=curve[lo],b=curve[hi];return a[ykey]+(b[ykey]-a[ykey])*(x-a[xkey])/(b[xkey]-a[xkey]);
}
function infer(meanV,varV,varR,curve,n=128,u=1){
 const q=meanV/(u*n);if(!(q>0&&q<1)||varV<=0||varR<0)return{flag:'degenerate'};
 const s2=varV/(q*(1-q)*u*u),lo=curve[0].s2,hi=curve.at(-1).s2;
 return{q,s2,c:interp(curve,s2,'s2','rho'),lambda:Math.sqrt(n*n*u*u*(1-q)*varR/varV),flag:s2<lo?'below':s2>hi?'above':'interior'};
}
function sample(n,c,q,lambda,u,length,seed){
 if(!Number.isInteger(length)||length<2)throw Error('At least two periods are required');
 const rand=rng(seed+101),observations=[];let sr=0,sv=0,srr=0,svv=0;
 for(let t=0;t<length;t++){
  const g=graph(n,c,(seed+Math.imul(t+1,2654435761))>>>0);let signed=0,active=0;
  for(const group of g.groups){const z=rand(),d=z<q/2?-1:z<q?1:0;signed+=group.length*d;active+=group.length*Math.abs(d);}
  const r=lambda/n*signed,v=u*active;sr+=r;sv+=v;srr+=r*r;svv+=v*v;observations.push({r,v});
 }
 return{meanV:sv/length,varV:(svv-sv*sv/length)/(length-1),varR:(srr-sr*sr/length)/(length-1),observations};
}
function risk(flat,weights,eta=1){
 const n=weights.length,total=weights.reduce((a,x)=>a+x,0);
 if(flat.length!==n*n||total<=0||eta<0||eta>1||weights.some(x=>!Number.isFinite(x)||x<0))throw Error('Invalid portfolio');
 const w=weights.map(x=>x/total);let full=0,diagonal=0;
 for(let i=0;i<n;i++){diagonal+=w[i]*w[i]*flat[i*n+i];for(let j=0;j<n;j++)full+=w[i]*w[j]*flat[i*n+j];}
 const counter=diagonal+eta*(full-diagonal);
 return{full,diagonal,counter,fullVol:100*Math.sqrt(Math.max(0,252*full)),diagonalVol:100*Math.sqrt(Math.max(0,252*diagonal)),counterVol:100*Math.sqrt(Math.max(0,252*counter)),collectiveShare:counter?(counter-diagonal)/counter:0,observedCollectiveShare:full?(full-diagonal)/full:0,weights:w};
}
function skill(model,baseline){if(!(baseline>0))throw Error('Positive baseline loss required');return 100*(1-model/baseline);}
function chainLaw(q,lambda=.02,u=1){return[{action:-1,p:q/2,r:-lambda,v:4*u},{action:0,p:1-q,r:0,v:0},{action:1,p:q/2,r:lambda,v:4*u}];}
root.EconoMath={rng,graph,moments,interp,infer,sample,risk,skill,chainLaw};
if(typeof module!=='undefined')module.exports=root.EconoMath;
})(typeof window==='undefined'?globalThis:window);
