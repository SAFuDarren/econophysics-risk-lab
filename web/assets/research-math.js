/* Small-system exact sums and deterministic transformations of saved observations. */
(function(root){
'use strict';
const M=root.EconoMath||(typeof require==='function'?require('./math.js'):null);
function choose(n,k){if(k<0||k>n)return 0;let value=1;for(let j=1;j<=Math.min(k,n-k);j++)value=value*(n-j+1)/j;return value;}
function components(n,edges){
 const parent=Array.from({length:n},(_,i)=>i),find=i=>{while(parent[i]!==i)i=parent[i];return i;};
 for(const[a,b]of edges)parent[find(a)]=find(b);
 const groups=new Map();for(let i=0;i<n;i++){const r=find(i);if(!groups.has(r))groups.set(r,[]);groups.get(r).push(i);}
 return[...groups.values()].sort((a,b)=>b.length-a.length||a[0]-b[0]);
}
function rootedProbabilities(n,p){
 if(!Number.isInteger(n)||n<1||n>32||!Number.isFinite(p)||p<0||p>1)throw Error('Invalid finite-graph parameters');
 const connected=Array(n+1).fill(0);connected[1]=1;
 for(let s=2;s<=n;s++){let outside=0;for(let k=1;k<s;k++)outside+=choose(s-1,k-1)*connected[k]*(1-p)**(k*(s-k));connected[s]=1-outside;}
 const probabilities=Array.from({length:n},(_,i)=>{const k=i+1;return choose(n-1,k-1)*connected[k]*(1-p)**(k*(n-k));});
 return{n,p,connected,probabilities,expectedS2:n*probabilities.reduce((s,value,i)=>s+(i+1)*value,0)};
}
function enumerateGraphs(n,p=.5){
 if(!Number.isInteger(n)||n<1||n>5||p<0||p>1)throw Error('Full graph enumeration is limited to N ≤ 5');
 const possible=[];for(let a=0;a<n;a++)for(let b=a+1;b<n;b++)possible.push([a,b]);
 const records=[];for(let mask=0;mask<2**possible.length;mask++){
  const edges=possible.filter((_,i)=>(mask>>i)&1),groups=components(n,edges),rootSize=groups.find(g=>g.includes(0)).length;
  records.push({mask,edges,groups,sizes:groups.map(g=>g.length),rootSize,weight:p**edges.length*(1-p)**(possible.length-edges.length)});
 }return records;
}
function graphAtlas(){
 const graphs=enumerateGraphs(4),classes=new Map();for(const graph of graphs){const key=graph.sizes.join('+');if(!classes.has(key))classes.set(key,[]);classes.get(key).push(graph.mask);}
 return{graphs,classes:[...classes].map(([profile,masks])=>({profile,masks})).sort((a,b)=>a.profile.split('+').length-b.profile.split('+').length||b.profile.localeCompare(a.profile))};
}
function permuteVolume(pairs,seed){const shuffled=M.permutePairs(pairs,seed);return pairs.map((p,i)=>[p[0],shuffled[i][1]]);}
function sameMultiset(a,b){if(a.length!==b.length)return false;const key=v=>Array.isArray(v)?v.join(','):String(v),aa=a.map(key).sort(),bb=b.map(key).sort();return aa.every((v,i)=>v===bb[i]);}
function observationSummary(pairs){
 const statistics=M.pathStats(pairs);return{...statistics,absVolumeCorrelation:M.correlation(pairs.map(p=>Math.abs(p[0])),pairs.map(p=>p[1]))};
}
function recoveryRows(rows,method,split,scale){return rows.filter(r=>r.method===method&&r.test_split===split&&Number(r.lambda_multiplier)===Number(scale)).sort((a,b)=>Number(a.replication)-Number(b.replication));}
function recoveryMean(rows,method,split,scale){const found=recoveryRows(rows,method,split,scale);if(!found.length)throw Error('Saved comparison unavailable');return found.reduce((s,r)=>s+Number(r.mae),0)/found.length;}
const api={choose,components,rootedProbabilities,enumerateGraphs,graphAtlas,permuteVolume,sameMultiset,observationSummary,recoveryRows,recoveryMean};
root.EconoResearch=api;if(typeof module!=='undefined')module.exports=api;
})(typeof window==='undefined'?globalThis:window);
