const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'..'),M=require('../web/assets/math.js');let checks=0;
function close(a,b,tol=1e-12){assert.ok(Math.abs(a-b)<tol,`${a} != ${b}`);checks++;}
for(const topology of [[[0,1],[1,2],[2,3]],[[0,1],[0,2],[0,3]]]){
 const law=M.observationLaw(M.groupSizes(4,topology),.2);
 assert.equal(law.length,3);checks++;
 for(let i=0;i<3;i++){close(law[i].r,M.chainLaw(.2)[i].r);close(law[i].v,M.chainLaw(.2)[i].v);close(law[i].p,M.chainLaw(.2)[i].p);}
}
const split=M.observationLaw([2,2],.2);close(split.reduce((s,p)=>s+p.p,0),1);
// Two active groups with opposite signs: two independent action assignments.
close(split.find(p=>p.signed===0&&p.active===4).p,2*.1*.1);
for(const sizes of [[4],[2,2],[1,1,1,1]]){
 const law=M.observationLaw(sizes,.2),mom=M.moments(sizes,.2);
 close(law.reduce((s,p)=>s+p.p*p.r,0),0);
 close(law.reduce((s,p)=>s+p.p*p.r*p.r,0),mom.varR);
 close(law.reduce((s,p)=>s+p.p*p.v,0),mom.meanV);
 close(law.reduce((s,p)=>s+p.p*(p.v-mom.meanV)**2,0),mom.varV);
}
const independent=M.moments(M.groupingGraph(128,1).groups.map(g=>g.length),.2),grouped=M.moments(M.groupingGraph(128,16).groups.map(g=>g.length),.2);
close(grouped.meanV,independent.meanV);close(grouped.varR/independent.varR,16);close(grouped.varV/independent.varV,16);
const replay=JSON.parse(fs.readFileSync(path.join(root,'web/assets/data/memory-path.json'))),rows=fs.readFileSync(path.join(root,'results/tables/state_mechanism_v2/path_metrics.csv'),'utf8').trim().split(/\r?\n/).map(s=>s.split(',')),header=rows.shift();
for(const [arm,pairs]of Object.entries(replay.arms)){
 const fixture=Object.fromEntries(header.map((h,i)=>[h,rows.find(r=>r[0]==='0'&&r[1]===arm)[i]])),got=M.pathStats(pairs);
 close(got.meanV,+fixture.mean_volume);close(got.varR,+fixture.return_variance,1e-16);close(got.magnitudeACF,+fixture.magnitude_acf1,1e-11);close(got.volumeACF,+fixture.volume_acf1,1e-11);
 const shuffled=M.permutePairs(pairs,4381);assert.deepEqual([...pairs].sort(),[...shuffled].sort());checks++;
 const after=M.pathStats(shuffled);close(after.meanV,got.meanV);close(after.varR,got.varR,1e-16);
 assert.deepEqual(shuffled,M.permutePairs(pairs,4381));checks++;
}
console.log(JSON.stringify({status:'pass',checks,scope:'Exact laws against independent action probabilities, moment identities, saved Python path correlations and deterministic pair-preserving permutations'}));
