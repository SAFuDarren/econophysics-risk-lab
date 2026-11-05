const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'..'),M=require('../web/assets/math.js'),R=require('../web/assets/research-math.js');let checks=0;
function close(a,b,tol=1e-12){assert.ok(Math.abs(a-b)<=tol,`${a} != ${b}`);checks++;}
const fixture=JSON.parse(fs.readFileSync(path.join(__dirname,'fixtures/finite_graph_recurrence.json')));
for(const f of fixture.cases){
 const got=R.rootedProbabilities(f.n,f.p),graphs=R.enumerateGraphs(f.n,f.p),sums=Array(f.n).fill(0);
 for(const g of graphs)sums[g.rootSize-1]+=g.weight;
 for(let k=0;k<f.n;k++){close(got.probabilities[k],f.root_probabilities[k]);close(sums[k],f.root_probabilities[k]);}
 close(got.expectedS2,f.expected_s2);close(graphs.reduce((s,g)=>s+g.weight,0),1);assert.equal(f.exact_probability_sum,'1');checks++;
}
assert.throws(()=>R.enumerateGraphs(6,.5));checks++;
const atlas=R.graphAtlas();assert.equal(atlas.graphs.length,64);checks++;
assert.deepEqual(Object.fromEntries(atlas.classes.map(c=>[c.profile,c.masks.length])),{'4':38,'3+1':16,'2+2':3,'2+1+1':6,'1+1+1+1':1});checks++;
for(const group of atlas.classes){const first=M.observationLaw(atlas.graphs[group.masks[0]].sizes,.2);for(const mask of group.masks){assert.deepEqual(M.observationLaw(atlas.graphs[mask].sizes,.2),first);checks++;}}
const d=JSON.parse(fs.readFileSync(path.join(root,'web/assets/data/research-depth.json')));
close(R.recoveryMean(d.recovery,'RBF_joint','test',1),.027013,1e-6);close(R.recoveryMean(d.recovery,'RBF_joint','test',2),.258133,1e-6);
for(const method of ['Moment_volume','RBF_shape_joint','RBF_volume'])for(const split of ['test','unseen'])for(const scale of [.5,2])close(R.recoveryMean(d.recovery,method,split,scale),R.recoveryMean(d.recovery,method,split,1),1e-12);
for(let rep=0;rep<10;rep++){
 const filename=rep===0?'memory-path.json':`memory/path-${String(rep).padStart(2,'0')}.json`,data=JSON.parse(fs.readFileSync(path.join(root,'web/assets/data',filename)));
 for(const[arm,pairs]of Object.entries(data.arms)){
  const stats=M.pathStats(pairs),expected=d.memory.paths.find(r=>+r.replication===rep&&r.arm===arm);close(stats.magnitudeACF,+expected.magnitude_acf1,1e-11);close(stats.volumeACF,+expected.volume_acf1,1e-11);
 }
 const pairs=data.arms.PersistentActivity,v=R.permuteVolume(pairs,20261105),joint=M.permutePairs(pairs,20261105);
 assert.deepEqual(v.map(p=>p[0]),pairs.map(p=>p[0]));assert.ok(R.sameMultiset(v.map(p=>p[1]),pairs.map(p=>p[1])));assert.ok(!R.sameMultiset(v,pairs));assert.ok(R.sameMultiset(joint,pairs));checks+=4;
 close(R.observationSummary(pairs).absVolumeCorrelation,R.observationSummary(joint).absVolumeCorrelation,1e-12);
}
console.log(JSON.stringify({status:'pass',checks,scope:'Independent exact-rational graph fixtures, complete graph equivalence classes, saved scale controls, ten-path Python correlations and distinct permutation invariants'}));
