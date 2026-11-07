(function(){
'use strict';
const A=window.EconoApp,M=window.EconoMath,D=window.ResearchData,$=id=>document.getElementById(id);
if(!A)return;
const t=(en,zh)=>A.getLanguage()==='zh'?zh:en;
const fmt=(v,n=2)=>Number.isFinite(v)?v.toLocaleString(A.getLanguage()==='zh'?'zh-CN':'en-US',{minimumFractionDigits:n,maximumFractionDigits:n}):'—';
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const C={navy:'#173e60',teal:'#416b73',gray:'#a9b6be',line:'#d4dce2',red:'#92505c',ink:'#242b33'};
const state={networkSeed:20261105,networkGroup:0,history:[],historyKey:'',edges:[[0,1],[1,2],[2,3]],topology:'chain',memory:null,memoryReplication:0,memoryCache:new Map(),memoryPromises:new Map(),memoryPairKey:null,memoryArm:'PersistentActivity',pairs:null,shuffled:false,shuffleSeed:20261105,shuffleCount:0,networkResult:null,identityResult:null,memoryResult:null};
const repo='https://github.com/SAFuDarren/econophysics-risk-lab/blob/main/';
function math(el,tex){if(!el)return;if(window.katex)window.katex.render(tex,el,{displayMode:true,throwOnError:true});else el.textContent=tex;}
function svg(w,h,title){return `<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="${esc(title)}"><title>${esc(title)}</title>`;}
function line(x,y,xx,yy,col=C.line,width=1,extra=''){return `<line x1="${x}" y1="${y}" x2="${xx}" y2="${yy}" stroke="${col}" stroke-width="${width}" ${extra}/>`;}
function txt(x,y,s,anchor='middle',cls=''){return `<text x="${x}" y="${y}" text-anchor="${anchor}" class="${cls}">${esc(s)}</text>`;}
function metric(label,value){return `<div>${esc(label)}<strong>${esc(value)}</strong></div>`;}
const width=(el,min=280)=>Math.max(min,Math.round(el.clientWidth||500));
function physics(){
 const r=A.state.physicsResult;if(!r)return;const size=r.selectedGroup.size,part=r.q*(r.lambda/r.n)**2*size**2,share=r.selectedGroup.share;
 $('physics-er-controls').hidden=r.grouping!=='er';$('new-graph').disabled=r.grouping!=='er';
 $('formula-group-note').textContent=t(`The selected group has ${size} traders. They share one action, contributing ${fmt(100*share,1)}% of this graph’s return variance.`,`所选群体有${size}名交易者，共享一次动作；它贡献当前网络收益方差的${fmt(100*share,1)}%。`);
 $('formula-group-value').innerHTML='<div class="equation" id="group-math"></div><p>'+esc(t('Contribution to conditional return variance: ','对条件收益方差的贡献：'))+'<strong>'+esc(part.toExponential(3))+'</strong></p>';
 math($('group-math'),String.raw`q(\lambda/N)^2\,\underbrace{${size}^{2}}_{s_C^2}=${r.q}\,(0.02/128)^2\,${size**2}`);
}
function network(){
 const n=+$('network-n').value,c=+$('network-c').value,g=M.graph(n,c,state.networkSeed);state.networkGroup=Math.min(state.networkGroup,g.groups.length-1);
 $('network-c-value').value=fmt(c);$('network-stats').innerHTML=metric(t('Largest component','最大连通分量'),g.largest+' / '+n)+metric(t('Connected groups','连通群体数'),fmt(g.groups.length,0))+metric('S₂ / N',fmt(g.s2/n,2));
 A.drawNetwork(g,$('transition-network'),state.networkGroup,null,i=>{state.networkGroup=i;network();});
 const chosen=g.groups[state.networkGroup].length;
 $('network-detail').textContent=t(`Selected group: ${chosen} traders. Move c with this seed fixed to add or remove edges from the same coupled realization.`,`所选群体有${chosen}名交易者。固定随机种子移动c，在同一耦合实现中增加或移除连边。`);
 const e=$('transition-chart'),w=width(e),h=295,L=48,R=w-18,T=28,B=h-48,sx=x=>L+(R-L)*(x-.2)/1.8,sy=y=>B-(B-T)*y;
 const rows=D.phase.filter(r=>r.n===n);let out=svg(w,h,t('Saved finite-size component fraction with a live realization','保存的有限规模连通分量占比与即时单次实现'));
 for(const y of [0,.25,.5,.75,1])out+=line(L,sy(y),R,sy(y))+txt(L-8,sy(y)+4,fmt(y,2),'end');
 for(const x of [.2,.6,1,1.4,1.8,2])out+=txt(sx(x),B+21,fmt(x,1));
 out+=line(sx(1),T,sx(1),B,C.gray,1,'stroke-dasharray="4 4"');
 out+=`<path d="M${rows.map(r=>sx(r.rho)+','+sy(r.largest_fraction_ci_high)).join(' L')} L${[...rows].reverse().map(r=>sx(r.rho)+','+sy(r.largest_fraction_ci_low)).join(' L')} Z" fill="#e1ebef"/>`;
 out+=`<path d="${rows.map((r,i)=>(i?'L':'M')+sx(r.rho)+','+sy(r.largest_fraction_mean)).join(' ')}" fill="none" stroke="${C.teal}" stroke-width="2"/>`;
 for(const r of rows)out+=`<circle cx="${sx(r.rho)}" cy="${sy(r.largest_fraction_mean)}" r="2.5" fill="${C.teal}"/>`;
 out+=`<circle cx="${sx(c)}" cy="${sy(g.largest/n)}" r="5" fill="${C.navy}" stroke="white" stroke-width="1.5"/>`;
 out+=txt(L,14,t('Largest-group fraction','最大群体占比'),'start','axis-title')+txt((L+R)/2,h-5,t('Expected mean degree c','期望平均度c'),'middle','axis-title');
 e.innerHTML=out+'</svg>';
 state.networkResult={n,c,seed:state.networkSeed,largest:g.largest,largestFraction:g.largest/n,s2:g.s2,groups:g.groups.map(g=>g.length),source:D.sources.phase,intervalMeaning:'Saved ensemble intervals; live dot is one separate graph draw.'};
}
function inference(){
 const r=A.state.inferenceResult;if(!r){$('inversion-steps').textContent=t('Draw a nondegenerate window to inspect the inversion.','重采一个非退化窗口后查看反演过程。');return;}
 const e=r.estimate,key=[r.truth.c,r.truth.q,r.mode].join(':');if(key!==state.historyKey){state.history=[];state.historyKey=key;}
 if(r.mode!=='population'&&!state.history.some(v=>v.seed===r.seed))state.history.push({seed:r.seed,c:e.c,q:e.q,lambda:e.lambda,flag:e.flag});
 if(state.history.length>30)state.history.shift();
 $('inversion-steps').innerHTML='<div class="inversion-steps">'+[
  [t('Mean volume → activity','平均成交量 → 活动率'),String.raw`\widehat q=\frac{\overline V}{uN}`,t(`Mean V = ${fmt(r.observed.meanV,2)}; q̂ = ${fmt(e.q,3)}.`,`平均V=${fmt(r.observed.meanV,2)}，q̂=${fmt(e.q,3)}。`)],
  [t('Volume variance → group moment','成交量方差 → 群体矩'),String.raw`\widehat A=\frac{\widehat{\operatorname{Var}}(V)}{\widehat q(1-\widehat q)u^2}`,t(`Estimated E[S₂] = ${fmt(e.s2,1)}.`,`估计E[S₂]=${fmt(e.s2,1)}。`)],
  [t('Finite-ER curve → connectivity','有限ER曲线 → 连接参数'),String.raw`\widehat c=A_N^{-1}(\widehat A)`,t(`The selected setting is c = ${fmt(r.truth.c,2)}; estimate ${fmt(e.c,3)}.`,`所选真值c=${fmt(r.truth.c,2)}，估计为${fmt(e.c,3)}。`)]
 ].map(([label,tex,note],i)=>`<div class="inversion-step"><small>${esc(label)}</small><div class="equation" id="inverse-math-${i}"></div><p>${esc(note)}</p></div>`).join('')+'</div>';
 const formulas=[String.raw`\widehat q=\frac{\overline V}{uN}`,String.raw`\widehat A=\frac{\widehat{\operatorname{Var}}(V)}{\widehat q(1-\widehat q)u^2}`,String.raw`\widehat c=A_N^{-1}(\widehat A)`];formulas.forEach((s,i)=>math($('inverse-math-'+i),s));
 const chart=$('sampling-chart'),w=width(chart),h=140,L=42,R=w-20,sx=x=>L+(R-L)*x/3;
 let out=svg(w,h,t('Connectivity estimates across sampled windows','不同抽样窗口的连接参数估计'));
 out+=line(L,95,R,95)+line(sx(r.truth.c),20,sx(r.truth.c),95,C.teal,1.5,'stroke-dasharray="4 4"');
 for(const x of [0,.5,1,1.5,2,2.5,3])out+=txt(sx(x),119,fmt(x,1));
 state.history.forEach((v,i)=>out+=`<circle cx="${sx(v.c)}" cy="${42+(i%4)*13}" r="4" fill="${C.navy}"><title>${esc('ĉ = '+fmt(v.c,4)+', seed '+v.seed)}</title></circle>`);
 chart.innerHTML=out+txt(L,14,t('Estimated connectivity c','估计连接参数c'),'start','axis-title')+'</svg>';
 $('sampling-detail').textContent=state.history.length?t(`${state.history.length} sampled windows. Mean absolute connectivity error here: ${fmt(state.history.reduce((a,v)=>a+Math.abs(v.c-r.truth.c),0)/state.history.length,4)}. This is your live sample, separate from the ten-study research benchmark.`,`${state.history.length}个抽样窗口，当前连接参数平均绝对误差为${fmt(state.history.reduce((a,v)=>a+Math.abs(v.c-r.truth.c),0)/state.history.length,4)}。这是当前即时抽样结果；十组独立研究的基准见原始结果。`):t('Select a simulated window, then compare five draws. Population moments have no sampling error in this interpolated demonstration.','切换到模拟窗口后，可比较五次抽样。此插值演示中的总体矩没有抽样误差。');
}
function identity(){
 if(A.state.topology!==state.topology){state.topology=A.state.topology;state.edges=state.topology==='chain'?[[0,1],[1,2],[2,3]]:state.topology==='star'?[[0,1],[0,2],[0,3]]:state.topology==='split'?[[0,1],[2,3]]:state.edges;}
 const sizes=M.groupSizes(4,state.edges),law=M.observationLaw(sizes,.2),points=[[60,50],[280,50],[60,190],[280,190]];
 let out=svg(340,240,t('Editable four-trader coordination graph','可编辑的四交易者协调网络'));
 for(const[a,b]of state.edges)out+=line(...points[a],...points[b],C.teal,2.5);
 points.forEach(([x,y],i)=>out+=`<circle cx="${x}" cy="${y}" r="15" fill="${C.navy}"/><text x="${x}" y="${y+5}" text-anchor="middle" fill="white" font-size="15">${i+1}</text>`);
 $('identity-network').innerHTML=out+'</svg>';
 const all=[[0,1],[0,2],[0,3],[1,2],[1,3],[2,3]],has=(a,b)=>state.edges.some(v=>v[0]===a&&v[1]===b);
 $('identity-edges').innerHTML=all.map(([a,b])=>`<button id="edge-${a}-${b}" data-edge="${a},${b}" aria-pressed="${has(a,b)}" aria-label="${esc(t('Toggle edge','切换连边'))} ${a+1}–${b+1}">${a+1}–${b+1}</button>`).join('');
 $('identity-edges').querySelectorAll('button').forEach(el=>el.addEventListener('click',()=>{const[a,b]=el.dataset.edge.split(',').map(Number);state.edges=has(a,b)?state.edges.filter(v=>!(v[0]===a&&v[1]===b)):[...state.edges,[a,b]];A.state.topology=state.topology='custom';identity();$(el.id).focus();}));
 $('identity-sizes').textContent=t('Connected-group sizes: ','连通群体规模：')+'['+sizes.join(', ')+']';
 $('identity-law').innerHTML='<div class="law-row header"><span>'+t('Return r','收益r')+'</span><span>'+t('Volume V','成交量V')+'</span><span>'+t('Probability','概率')+'</span></div>'+law.map(v=>`<div class="law-row"><span>${fmt(v.r,3)}</span><span>${v.v}</span><span class="probability">${fmt(v.p,4)}</span></div>`).join('');
 const same=sizes.length===1;
 $('identity-verdict').innerHTML='<strong>'+esc(same?t('The same law as the four-node chain.','与四节点链具有相同观测分布。'):t('The group-size profile changed. So did the law.','群体规模列表改变，观测分布也改变。'))+'</strong><p>'+esc(same?t('All four traders still share one action. Internal edges do not enter the observation formula; extra observations of this kind cannot distinguish these connected graphs.','四名交易者仍共享一个动作。观测公式中没有内部连边信息，增加同类观测也无法区分这些连通网络。'):t('The network now contains independent groups. Their separate actions produce '+law.length+' distinct outcomes, compared with three for one group of four.','当前网络由独立群体组成，它们分别选择动作，共产生'+law.length+'种不同观测结果；一个四人群体只有三种。'))+'</p>';
 document.querySelectorAll('[data-topology]').forEach(el=>el.setAttribute('aria-pressed',String(el.dataset.topology===state.topology)));
 state.identityResult={edges:state.edges.map(v=>v.slice()),sizes,law,sameAsConnectedFourNodeLaw:same,n:4,q:.2,lambda:.02,u:1};
}
async function loadMemory(rep=state.memoryReplication){
 if(state.memoryCache.has(rep)){const data=state.memoryCache.get(rep);if(rep===state.memoryReplication)state.memory=data;return data;}
 if(!state.memoryPromises.has(rep)){
  const url=rep===0?'assets/data/memory-path.json':`assets/data/memory/path-${String(rep).padStart(2,'0')}.json`;
  const pending=fetch(url).then(r=>{if(!r.ok)throw Error('Path replay could not load');return r.json();}).then(data=>{
   if(data.replication!==rep||data.length!==8192||Object.values(data.arms).some(a=>a.length!==8192))throw Error('Incomplete saved path');
   state.memoryCache.set(rep,data);state.memoryPromises.delete(rep);if(rep===state.memoryReplication)state.memory=data;return data;
  }).catch(error=>{state.memoryPromises.delete(rep);throw error;});state.memoryPromises.set(rep,pending);
 }
 return state.memoryPromises.get(rep);
}
async function changeMemoryPath(rep){
 if(!Number.isInteger(rep)||rep<0||rep>9)throw Error('Invalid saved path');
 state.memoryReplication=rep;state.memory=state.memoryCache.get(rep)||null;state.pairs=null;state.memoryPairKey=null;state.memoryResult=null;state.shuffled=false;state.shuffleCount=0;
 $('memory-path').value=String(rep);return memory();
}
function memoryHeatmap(original,current){
 const e=$('memory-joint'),w=width(e,250),h=270,L=48,R=w-15,T=25,B=h-46,nx=22,ny=18;
 const maxR=Math.max(...original.map(p=>Math.abs(p[0])))||1,maxV=Math.max(...original.map(p=>p[1]))||1,bins=Array(nx*ny).fill(0);
 for(const[r,v]of current){const x=Math.max(0,Math.min(nx-1,Math.floor((r/maxR+1)/2*nx))),y=Math.max(0,Math.min(ny-1,Math.floor(v/maxV*ny)));bins[y*nx+x]++;}
 const max=Math.max(...bins),sx=r=>L+(R-L)*(r/maxR+1)/2,sy=v=>B-(B-T)*v/maxV;
 let out=svg(w,h,t('Joint return-volume count map; every saved observation is retained','收益与成交量联合计数图，保留全部保存观测'));
 bins.forEach((count,i)=>{if(count){const x=i%nx,y=Math.floor(i/nx),opacity=.15+.85*Math.log1p(count)/Math.log1p(max);out+=`<rect x="${L+(R-L)*x/nx}" y="${B-(B-T)*(y+1)/ny}" width="${(R-L)/nx+.1}" height="${(B-T)/ny+.1}" fill="${C.teal}" opacity="${opacity}"><title>${count} ${esc(t('observations','个观测'))}</title></rect>`;}});
 out+=line(L,B,R,B)+line(L,T,L,B);for(const v of [0,maxV/2,maxV])out+=txt(L-7,sy(v)+4,fmt(v,0),'end');
 for(const r of [-maxR,0,maxR])out+=txt(sx(r),B+19,fmt(100*r,2));
 out+=txt(L,14,'V','start','axis-title')+txt((L+R)/2,h-5,t('Return r (%)','收益r (%)'),'middle','axis-title');e.innerHTML=out+'</svg>';
 $('memory-joint-caption').textContent=t('All 8,192 pairs, binned by return and volume. Darker cells contain more observations. Shuffling leaves every cell count unchanged.','全部8,192对观测按收益与成交量分箱，颜色越深，观测越多。整对打乱后，每一格的计数保持不变。');
 return bins;
}
function memoryACF(before,after){
 const e=$('memory-acf'),w=width(e,250),h=270,L=43,R=w-10,T=27,B=h-46,sy=y=>B-(B-T)*(y+.1)/1.1;
 let out=svg(w,h,t('Lag-one magnitude and volume correlation, original and current order','原顺序与当前顺序的一期幅度和成交量相关'));
 for(const y of [0,.25,.5,.75,1])out+=line(L,sy(y),R,sy(y))+txt(L-7,sy(y)+4,fmt(y,2),'end');
 const labels=[t('|r| memory','|r|记忆'),t('V memory','V记忆')],bw=Math.min(24,(R-L)/9);
 ['magnitudeACF','volumeACF'].forEach((key,i)=>{const x=L+(R-L)*(i+.5)/2;[before[key],after[key]].forEach((v,j)=>{if(v===null)return;const xx=x+(j?3:-bw-3),yy=sy(v);out+=`<rect x="${xx}" y="${Math.min(yy,sy(0))}" width="${bw}" height="${Math.max(.8,Math.abs(sy(0)-yy))}" fill="${j?C.navy:C.teal}"/>`;});out+=txt(x,B+20,labels[i]);});
 out+=txt(L,14,t('Lag-one correlation','一期滞后相关'),'start','axis-title');e.innerHTML=out+'</svg>';
}
function memoryTrace(original,current){
 const e=$('memory-trace'),w=width(e),h=265,L=45,R=w-15,start=+$('memory-offset').value,end=start+512;
 $('memory-offset-value').value=start+'–'+(end-1);
 let out=svg(w,h,t('A 512-observation segment in original and current time order','原顺序与当前顺序的512期时间片段'));
 for(let j=0;j<2;j++){
  const top=22+j*122,bottom=top+85,vals=original.slice(start,end).concat(current.slice(start,end)),max=Math.max(...vals.map(p=>j?p[1]:100*Math.abs(p[0])))||1,sx=i=>L+(R-L)*i/511,sy=y=>bottom-(bottom-top)*y/max;
  out+=line(L,bottom,R,bottom)+txt(L-7,top+5,j?'V':'|r| %','end');
  [original,current].forEach((pairs,k)=>{out+=`<path d="${pairs.slice(start,end).map((p,i)=>(i?'L':'M')+sx(i)+','+sy(j?p[1]:100*Math.abs(p[0]))).join(' ')}" fill="none" stroke="${k?C.navy:C.teal}" stroke-width="${k?1.05:1.3}" opacity="${k?.9:.6}"/>`;});
  if(j)for(const i of [0,256,511])out+=txt(sx(i),bottom+20,String(start+i));
 }
 e.innerHTML=out+'</svg>';
}
async function memory(){
 const requestedRep=state.memoryReplication,requestedArm=$('memory-arm').value;
 $('memory-status').textContent=state.memory?t(`Saved simulation replay · path ${state.memoryReplication+1} of 10 · N = 128, c = 1 · 8,192 observations`,`已保存模拟回放 · 第${state.memoryReplication+1}条路径，共10条 · N=128、c=1 · 8,192个观测`):t('Loading the saved research path…','正在加载已保存的研究路径…');
 try{await loadMemory(requestedRep);}catch(e){$('memory-status').innerHTML=esc(t('The saved path could not load. ','保存路径加载失败。'))+'<button class="button secondary" id="memory-retry">'+esc(t('Try again','重试'))+'</button>';$('memory-retry').addEventListener('click',memory);return;}
 if($('memory').closest('[hidden]')||requestedRep!==state.memoryReplication||requestedArm!==$('memory-arm').value)return;
 const arm=$('memory-arm').value,pairKey=state.memoryReplication+'|'+arm;if(state.memoryPairKey!==pairKey||!state.pairs){state.memoryPairKey=pairKey;state.memoryArm=arm;state.pairs=state.memory.arms[arm];state.shuffled=false;state.shuffleCount=0;}
 const original=state.memory.arms[arm],current=state.pairs,before=M.pathStats(original),after=M.pathStats(current);
 $('memory-status').textContent=t(`Saved simulation replay · path ${state.memoryReplication+1} of 10 · N = 128, c = 1 · 8,192 observations`,`已保存模拟回放 · 第${state.memoryReplication+1}条路径，共10条 · N=128、c=1 · 8,192个观测`);
 $('memory-stats').innerHTML=metric(t('Mean V (current)','当前平均V'),fmt(after.meanV,3))+metric(t('Var(r) (current)','当前Var(r)'),after.varR.toExponential(3))+metric(t('Lag-one |r| correlation','|r|一期滞后相关'),fmt(after.magnitudeACF,3));
 const bins=memoryHeatmap(original,current);memoryACF(before,after);memoryTrace(original,current);
 const explanation=arm==='PersistentActivity'?t('Persistent activity can produce memory in both trading volume and return magnitude.','活动率持续变化可使成交量与收益幅度都出现记忆。'):arm==='PersistentImpact'?t('A persistent price response can produce magnitude memory while volume has little memory.','持续变化的价格响应可产生幅度记忆，而成交量的记忆很弱。'):t('The constant model independently redraws networks and actions, giving no population serial memory.','固定模型独立重采网络与动作，总体上没有序列记忆。');
 $('memory-conclusion').innerHTML='<strong>'+esc(state.shuffled?t('Same observations. A different time order.','相同观测，不同时间顺序。'):t('The order carries information.','时间顺序包含信息。'))+'</strong><p>'+esc(explanation+' '+t('Shuffle complete pairs: all single-period empirical joint moments stay fixed, while the correlations across time can change. The project separately evaluates ten independent paths; this replay shows one.','整对打乱会保留全部单期经验联合矩，而跨时间的相关可以改变。项目研究另对十条独立路径进行汇总，这里回放其中一条。'))+'</p>';
 state.memoryResult={arm,replication:state.memoryReplication,length:8192,shuffled:state.shuffled,shuffleCount:state.shuffleCount,shuffleSeed:state.shuffleSeed,before,after,jointBinCounts:bins,source:state.memory.source,sourceSha256:state.memory.source_sha256};
 document.dispatchEvent(new CustomEvent('memorychange'));
}
function risk(){
 const result=A.state.riskResult;if(!result){$('risk-matrix').innerHTML='';$('risk-pair-detail').textContent='';return;}
 const a=$('risk-pair-a'),b=$('risk-pair-b');if(!a.options.length){for(const e of [a,b])e.innerHTML=D.assets.map((v,i)=>`<option value="${i}">${esc(v)}</option>`).join('');b.value='1';}
 const i=+a.value,j=+b.value,n=D.assets.length,cov=D.risk.find(r=>r.date===result.date).cov[result.lookback],wts=result.weights,contribution=(i===j?1:2*result.eta)*wts[i]*wts[j]*cov[i*n+j],corr=cov[i*n+j]/Math.sqrt(cov[i*n+i]*cov[j*n+j]);
 $('risk-pair-detail').textContent=t(`${D.assets[i]} / ${D.assets[j]}: correlation ${fmt(corr,3)}. ${i===j?'Diagonal':'Paired cross'} contribution to daily portfolio variance: ${contribution.toExponential(3)} at η = ${fmt(result.eta,2)}.`,`${D.assets[i]} / ${D.assets[j]}：相关系数${fmt(corr,3)}，在η=${fmt(result.eta,2)}时，${i===j?'对角项':'成对交叉项'}对组合日方差的贡献为${contribution.toExponential(3)}。`);
 const e=$('risk-matrix'),w=width(e,260),h=w,L=40,R=w-10,T=33,B=h-37,cell=Math.min((R-L)/n,(B-T)/n);let out=svg(w,h,t('Historical correlation matrix; select a pair to read its variance contribution','历史相关矩阵，选择行业对查看方差贡献'));
 for(let y=0;y<n;y++)for(let x=0;x<n;x++){const value=cov[y*n+x]/Math.sqrt(cov[y*n+y]*cov[x*n+x]),selected=(y===i&&x===j)||(y===j&&x===i);out+=`<rect data-pair="${y},${x}" x="${L+x*cell}" y="${T+y*cell}" width="${cell-1}" height="${cell-1}" fill="${value<0?C.red:C.navy}" fill-opacity="${.08+.92*Math.abs(value)}" stroke="${selected?C.teal:'none'}" stroke-width="${selected?3:0}"><title>${esc(D.assets[y]+' / '+D.assets[x]+': '+fmt(value,3))}</title></rect>`;}
 for(let k=0;k<n;k++){out+=txt(L-5,T+(k+.7)*cell,D.assets[k],'end')+txt(L+(k+.5)*cell,T+n*cell+18,D.assets[k]);}
 out+=txt(L,15,t('Correlation, same historical window','同一历史窗口的相关系数'),'start','axis-title');e.innerHTML=out+'</svg>';
 e.querySelectorAll('[data-pair]').forEach(el=>el.addEventListener('click',()=>{const[x,y]=el.dataset.pair.split(',');a.value=x;b.value=y;risk();}));
}
function render(name){
 if(name==='network')network();if(name==='memory')memory();
}
function exportExperiment(k,status){
 let result,scope,sources;
 if(k==='mechanism'){result=A.state.physicsResult;scope='Conditional model calculation or one-period model simulation';sources=['src/econophysics/model.py'];}
 if(k==='network'){result=state.networkResult;scope='Live structural graph draw and saved ensemble comparison';sources=[D.sources.phase];}
 if(k==='inference'){result={...A.state.inferenceResult,sampledWindows:state.history};scope='Finite-ER curve interpolation or live model-window simulation';sources=[D.sources.curve,'results/tables/depth_study_v1/summary_metrics.csv'];}
 if(k==='identity'){result=state.identityResult;scope='Exact enumeration of the complete one-period observation law';sources=['docs/theory/FOUNDATIONS.md'];}
 if(k==='memory'){result=state.memoryResult?{...state.memoryResult,currentPairs:state.pairs}:null;scope='Replay of one saved controlled-simulation path, with whole-pair permutation';sources=['scripts/run_state_mechanism_v2.py','results/tables/state_mechanism_v2/summary.csv'];}
 if(k==='risk'){result=A.state.riskResult;scope='Matched-window historical covariance calculation';sources=[D.sources.risk];}
 if(!result){status.textContent=t('Complete a valid experiment first.','请先完成一个有效实验。');return;}
 const record={experiment:k,recordedAt:new Date().toISOString(),scope,result,sources:sources.map(s=>repo+s)},url=URL.createObjectURL(new Blob([JSON.stringify(record,null,2)],{type:'application/json'})),a=document.createElement('a');a.href=url;a.download='econophysics-'+k+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),2000);status.textContent=t('Experiment record saved, including settings and sources.','已保存含参数设置与来源的实验记录。');
}
function researchMap(){
 if(!$('research-map-detail'))return;
 const entries=[
  {title:['From shared action to exact moments','从共同动作到精确矩'],text:['We derive how group sizes enter return and volume moments, then check those identities by exact small-system enumeration.','推导群体规模如何进入收益与成交量的矩，并以小系统精确枚举核验这些关系。'],work:['Analytical moments · exact checks · simulation implementation','矩关系推导、精确核验与模型实现'],figure:'F01',caption:['Original finite-ER group realizations, N = 48','原有限ER群体实现，N=48'],lab:'mechanism',math:'mechanism',code:'src/econophysics/model.py',data:'results/tables/foundation_v2/moment_checks.csv'},
  {title:['The finite-network transition','有限网络的结构过渡'],text:['The experiment compares three system sizes and the distribution of connected groups as connectivity changes.','在三种系统规模下比较连接参数变化时的连通群体分布。'],work:['1,080 graph draws · N = 128, 256, 512 · 40 draws per setting','1,080次网络抽样，N=128、256、512，每个条件40次'],figure:'F03',caption:['Saved ensemble results; the laboratory adds a live single-graph comparison','保存的整体抽样结果；实验室另提供即时单张网络对照'],lab:'network',math:'mechanism',code:'src/econophysics/model.py',data:D.sources.phase},
  {title:['Recover parameters, locate the information limit','恢复参数，找到信息边界'],text:['Moment inversion and radial-basis regression are compared in known-truth simulations. A characteristic-function argument shows why internal edges can remain indistinguishable.','在已知真值模拟中比较矩反演与径向基回归，并用特征函数说明内部连边为何仍可能无法区分。'],work:['Ten independent recovery studies · unseen connectivity settings · scale controls','十组独立恢复研究、未见连接参数与价格尺度对照'],figure:'D01',caption:['Parameter-recovery results across the independent studies','独立研究中的参数恢复结果'],lab:'inference',math:'inverse',code:'src/econophysics/physics_inference.py',data:'results/tables/depth_study_v1/summary_metrics.csv'},
  {title:['Separate joint structure from temporal memory','区分联合结构与时间记忆'],text:['Controlled activity and price-response states isolate different memory channels. Whole-pair shuffling holds the empirical joint observations fixed.','通过活动率与价格响应的受控状态变化区分记忆来源，整对打乱保持经验联合观测不变。'],work:['Four experimental arms · ten paths each · 8,192 periods per path','四组实验，每组十条路径，每条8,192期'],figure:'V01',caption:['The project’s controlled temporal-state experiment','项目中的受控时间状态实验'],lab:'memory',math:'memory',code:'scripts/run_state_mechanism_v2.py',data:'results/tables/state_mechanism_v2/summary.csv'},
  {title:['Confront the model with observations and risk','把模型带到市场检验与风险分析中'],text:['Bitcoin data test a necessary moment restriction. Forecast comparisons and matched-window ETF diagnostics evaluate separate practical questions.','用比特币数据检验必要矩约束，再用预测对照与同窗口ETF诊断分别回答实际问题。'],work:['183 held-out forecast dates · nine sector ETFs · 63 strategy subsets','183个留出预测日期、九只行业ETF、63种策略子集'],figure:'D01',caption:['Open the findings for the market tests and matched risk comparisons','市场检验与同条件风险对照见发现页'],lab:'risk',math:'covariance',code:'web/assets/math.js',data:'results/tables/forecast_v1/test_predictions.csv'}
 ];
 let selected=0;const draw=()=>{const e=entries[selected];document.querySelectorAll('[data-map]').forEach(b=>{b.setAttribute('aria-selected',String(+b.dataset.map===selected));b.tabIndex=+b.dataset.map===selected?0:-1;});$('research-map-detail').setAttribute('aria-labelledby','map-tab-'+selected);const picture=e.figure==='V01'?'assets/figures/V01.svg':'assets/figures/'+e.figure+'.svg';$('research-map-detail').innerHTML='<h3>'+esc(t(...e.title))+'</h3><p>'+esc(t(...e.text))+'</p><p class="map-work">'+esc(t(...e.work))+'</p><div class="map-links"><a href="lab.html#'+e.lab+'">'+esc(t('Open experiment','打开实验'))+'</a><a href="methods.html#'+e.math+'">'+esc(t('Read mathematics','阅读数学'))+'</a><a href="'+repo+e.code+'">'+esc(t('Code','代码'))+'</a><a href="'+repo+e.data+'">'+esc(t('Source results','原始结果'))+'</a></div>'+(selected===4?'<p class="small"><a href="findings.html#forecast">'+esc(t('Inspect every forecast date','查看每个预测日期'))+'</a> · <a href="findings.html#applications">'+esc(t('Risk and strategy findings','风险与策略发现'))+'</a></p>':'<figure class="research-figure"><a class="figure-open" href="'+picture+'" target="_blank"><img src="'+picture+'" loading="lazy" alt="'+esc(t(...e.caption))+'"></a><figcaption>'+esc(t(...e.caption))+'</figcaption></figure>');};
 document.querySelectorAll('[data-map]').forEach((b,i)=>{b.addEventListener('click',()=>{selected=i;draw();});b.addEventListener('keydown',e=>{if(['ArrowDown','ArrowUp','ArrowRight','ArrowLeft','Home','End'].includes(e.key)){e.preventDefault();selected=e.key==='Home'?0:e.key==='End'?entries.length-1:(selected+(['ArrowDown','ArrowRight'].includes(e.key)?1:-1)+entries.length)%entries.length;draw();document.querySelector('[data-map="'+selected+'"]').focus();}});});document.addEventListener('languagechange',draw);draw();
}
researchMap();
if(!$('physics-network'))return;
window.LabModules={render,physics,inference,identity,risk,memory,loadMemory,changeMemoryPath,exportExperiment,state};
document.querySelectorAll('[data-save-experiment]').forEach(button=>button.addEventListener('click',()=>{
 const experiment=button.closest('[data-lab-experiment]');
 window.LabModules.exportExperiment(experiment.id,experiment.querySelector('[data-export-status]'));
}));
$('physics-layout').addEventListener('change',()=>{A.state.actions=null;A.state.selectedGroup=0;$('one-action-result').textContent='';A.renderPhysics();});
['network-n','network-c'].forEach(id=>$(id).addEventListener('input',()=>{state.networkGroup=0;network();}));$('network-redraw').addEventListener('click',()=>{state.networkSeed++;state.networkGroup=0;network();});
$('infer-batch').addEventListener('click',async()=>{const b=$('infer-batch');b.disabled=true;if($('infer-mode').value==='population')$('infer-mode').value='256';state.history=[];try{for(let i=0;i<5;i++){A.state.inferSeed++;A.renderInference();await new Promise(requestAnimationFrame);}}finally{b.disabled=false;}});
document.querySelectorAll('[data-predict]').forEach(box=>box.querySelectorAll('[data-choice]').forEach(b=>b.addEventListener('click',()=>{box.querySelectorAll('[data-choice]').forEach(v=>v.setAttribute('aria-pressed',String(v===b)));const group=box.dataset.predict==='groups',correct=b.dataset.choice==='correct';box.querySelector('.prediction-feedback').textContent=group?t((correct?'Yes. ':'')+'S₂ changes from 128 to 2,048. At fixed q, return and volume variances are sixteen times larger; mean volume stays q × 128.',(correct?'是的。':'')+'S₂从128变为2,048。固定q时，收益与成交量方差变为16倍，平均成交量仍是q×128。'):t((correct?'Yes. ':'')+'Every (r, V) pair stays intact. The empirical joint distribution is unchanged; neighboring pairs change, so time correlations can change.',(correct?'是的。':'')+'每对(r,V)保持完整，经验联合分布不变；相邻观测的组合改变，因此时间相关可以改变。');if(group){$('physics-layout').value='groups';A.state.actions=null;A.state.selectedGroup=0;A.renderPhysics();}})));
$('memory-arm').addEventListener('change',memory);$('memory-offset').addEventListener('input',()=>{if(state.memory&&state.pairs)memoryTrace(state.memory.arms[state.memoryArm],state.pairs);});
$('memory-path').addEventListener('change',()=>changeMemoryPath(+$('memory-path').value));
$('memory-shuffle').addEventListener('click',async()=>{
 const button=$('memory-shuffle'),rep=state.memoryReplication,arm=$('memory-arm').value;button.disabled=true;
 try{const data=await loadMemory(rep);if(rep!==state.memoryReplication||arm!==$('memory-arm').value)return;
  const key=rep+'|'+arm;if(state.memoryPairKey!==key||!state.pairs)state.shuffleCount=0;
  state.memoryPairKey=key;state.memoryArm=arm;state.shuffleCount++;state.shuffleSeed++;
  state.pairs=arm==='PersistentActivity'&&state.shuffleCount===1?data.arms.ShuffledActivity:M.permutePairs(data.arms[arm],state.shuffleSeed);state.shuffled=true;await memory();
 }catch(e){$('memory-status').textContent=t('The saved path could not load; select a path to retry.','保存路径未能加载，请重新选择路径。');}finally{button.disabled=false;}
});
$('memory-reset').addEventListener('click',async()=>{
 const rep=state.memoryReplication,arm=$('memory-arm').value;
 try{const data=await loadMemory(rep);if(rep!==state.memoryReplication||arm!==$('memory-arm').value)return;state.memoryArm=arm;state.memoryPairKey=rep+'|'+arm;state.pairs=data.arms[arm];state.shuffled=false;state.shuffleCount=0;await memory();}
 catch(e){$('memory-status').textContent=t('The saved path could not load; select a path to retry.','保存路径未能加载，请重新选择路径。');}
});
['risk-pair-a','risk-pair-b'].forEach(id=>$(id).addEventListener('change',risk));
A.redraw();
})();
