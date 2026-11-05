/* Mathematical engine. Parameters follow the frozen Econophysics Risk Lab model.
   c is the research notation for the original Python parameter rho; q = 2a. */
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
function groupingGraph(n,size){
 if(!Number.isInteger(n)||n<2||!Number.isInteger(size)||size<1)throw Error('Invalid grouping');
 const groups=[],edges=[];for(let i=0;i<n;i+=size){const g=Array.from({length:Math.min(size,n-i)},(_,j)=>i+j);groups.push(g);for(let j=1;j<g.length;j++)edges.push([g[j-1],g[j]]);}
 return{n,groups,edges,s2:groups.reduce((a,g)=>a+g.length**2,0),s3:groups.reduce((a,g)=>a+g.length**3,0),largest:Math.max(...groups.map(g=>g.length))};
}
function groupSizes(n,edges){
 const parent=Array.from({length:n},(_,i)=>i);const find=i=>{while(parent[i]!==i)i=parent[i];return i;};
 for(const[a,b]of edges){if(a<0||b<0||a>=n||b>=n||a===b)throw Error('Invalid edge');parent[find(a)]=find(b);}
 const groups=new Map();for(let i=0;i<n;i++){const k=find(i);groups.set(k,(groups.get(k)||0)+1);}return[...groups.values()].sort((a,b)=>b-a);
}
function observationLaw(sizes,q,lambda=.02,u=1){
 if(!(q>0&&q<1)||sizes.length>10||!sizes.length||sizes.some(s=>!Number.isInteger(s)||s<1))throw Error('Invalid exact enumeration');
 const n=sizes.reduce((a,s)=>a+s,0);let values=new Map([['0,0',1]]);
 for(const s of sizes){const next=new Map();for(const[key,p]of values){const[r,v]=key.split(',').map(Number);for(const[a,w]of [[-1,q/2],[0,1-q],[1,q/2]]){const k=[r+a*s,v+Math.abs(a)*s].join(',');next.set(k,(next.get(k)||0)+p*w);}}values=next;}
 return[...values].map(([k,p])=>{const[r,v]=k.split(',').map(Number);return{signed:r,active:v,r:r*lambda/n,v:v*u,p};}).sort((a,b)=>a.r-b.r||a.v-b.v);
}
function permutePairs(pairs,seed){const out=pairs.map(p=>p.slice()),rand=rng(seed);for(let i=out.length-1;i>0;i--){const j=Math.floor(rand()*(i+1));[out[i],out[j]]=[out[j],out[i]];}return out;}
function correlation(a,b){
 if(a.length!==b.length||a.length<2)throw Error('Matched series required');const n=a.length,ma=a.reduce((s,x)=>s+x,0)/n,mb=b.reduce((s,x)=>s+x,0)/n;let aa=0,bb=0,ab=0;
 for(let i=0;i<n;i++){const x=a[i]-ma,y=b[i]-mb;aa+=x*x;bb+=y*y;ab+=x*y;}return aa>0&&bb>0?ab/Math.sqrt(aa*bb):null;
}
function pathStats(pairs){
 const n=pairs.length;if(n<2)throw Error('At least two pairs required');const r=pairs.map(p=>p[0]),v=pairs.map(p=>p[1]),a=r.map(Math.abs),mr=r.reduce((s,x)=>s+x,0)/n,mv=v.reduce((s,x)=>s+x,0)/n;
 return{meanV:mv,varR:r.reduce((s,x)=>s+(x-mr)**2,0)/n,varV:v.reduce((s,x)=>s+(x-mv)**2,0)/n,magnitudeACF:correlation(a.slice(1),a.slice(0,-1)),volumeACF:correlation(v.slice(1),v.slice(0,-1))};
}
root.EconoMath={rng,graph,moments,interp,infer,sample,risk,skill,chainLaw,groupingGraph,groupSizes,observationLaw,permutePairs,correlation,pathStats};
if(typeof module!=='undefined')module.exports=root.EconoMath;
})(typeof window==='undefined'?globalThis:window);
