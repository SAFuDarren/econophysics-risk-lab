(function(){
'use strict';
const A=window.EconoApp,M=window.EconoMath,R=window.EconoResearch,$=id=>document.getElementById(id),L=window.LabModules;
if(!A||!R)return;
const t=(en,zh)=>A.getLanguage()==='zh'?zh:en,esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=(x,n=3)=>Number.isFinite(Number(x))?Number(x).toLocaleString(A.getLanguage()==='zh'?'zh-CN':'en-US',{minimumFractionDigits:n,maximumFractionDigits:n}):'—';
const C={navy:'#173e60',teal:'#416b73',gray:'#a9b6be',line:'#d4dce2',gold:'#9d7841',red:'#92505c',ink:'#242b33'},palette=[C.navy,C.teal,C.gold,C.red];
const state={data:null,pending:null,views:{network:'explore',inference:'explore',identity:'explore',memory:'explore',risk:'explore'},records:{},renderToken:{},rootK:1,atlasMask:41,atlasProfile:'4',atlasOutcome:0,operatorSeed:20261105,marketStep:4};
const sources={recurrence:['docs/theory/DEPTH_ADDENDUM.md','web/assets/research-math.js'],scale:['results/tables/depth_study_v1/run_metrics.csv'],atlas:['docs/theory/FOUNDATIONS.md','web/assets/research-math.js'],memory:['results/tables/state_mechanism_v2/path_metrics.csv','results/tables/state_mechanism_v2/summary.csv','data/snapshots/state-mechanism-series.csv.gz'],tails:['results/tables/tail_increment_v1/synthetic_truth.csv','results/tables/tail_increment_v1/synthetic_ccdf.csv'],market:['results/tables/real_market_v1/market_metrics.csv','results/tables/real_market_v1/joint_constraint_sensitivity.csv']};
const repo='https://github.com/SAFuDarren/econophysics-risk-lab/blob/main/';
function math(el,tex){if(window.katex)katex.render(tex,el,{displayMode:true,throwOnError:true});else el.textContent=tex;}
function svg(w,h,title){return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} ${h}" role="img" aria-label="${esc(title)}"><title>${esc(title)}</title>`;}
function line(x,y,xx,yy,color=C.line,width=1,more=''){return `<line x1="${x}" y1="${y}" x2="${xx}" y2="${yy}" stroke="${color}" stroke-width="${width}" ${more}/>`;}
function text(x,y,s,anchor='middle',cls=''){return `<text x="${x}" y="${y}" text-anchor="${anchor}" class="${cls}">${esc(s)}</text>`;}
function metric(label,value,note=''){return `<div>${esc(label)}<strong>${esc(value)}</strong>${note?'<small>'+esc(note)+'</small>':''}</div>`;}
const width=(el,min=250)=>Math.max(min,Math.round(el.clientWidth||500));
function download(value,name,type){const url=URL.createObjectURL(new Blob([value],{type})),a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),2000);}
function status(name,message){const holder=$('research-'+name)||$('market-workbench');if(!holder)return;let el=holder.querySelector('.deep-status');if(!el){el=document.createElement('p');el.className='deep-status';el.setAttribute('aria-live','polite');holder.prepend(el);}el.textContent=message;}
async function data(){
 if(state.data)return state.data;
 if(!state.pending)state.pending=fetch('assets/data/research-depth.json').then(response=>{if(!response.ok)throw Error('Saved research payload unavailable');return response.json();}).then(d=>{if(d.version!==2||d.recovery.length!==300||d.tails.truth.length!==6)throw Error('Incomplete saved research payload');state.data=d;return d;}).catch(error=>{state.pending=null;throw error;});
 return state.pending;
}
function graphPicture(graph,w=260,h=190,root=false){
 const n=graph.groups.reduce((s,g)=>s+g.length,0),radius=Math.min(w,h)*.35,points=Array.from({length:n},(_,i)=>[w/2+radius*Math.cos(-Math.PI/2+i*2*Math.PI/n),h/2+radius*Math.sin(-Math.PI/2+i*2*Math.PI/n)]),groups=graph.groups,nodeGroup={};groups.forEach((g,j)=>g.forEach(i=>nodeGroup[i]=j));
 let out=svg(w,h,t('A labelled coordination graph','有标号协调网络'));
 for(const[a,b]of graph.edges)out+=line(...points[a],...points[b],root?(groups[nodeGroup[a]].includes(0)?C.teal:C.gray):C.gray,w<150?1.3:2);
 points.forEach(([x,y],i)=>{const active=groups[nodeGroup[i]].includes(0),r=w<150?4.3:10;if(root&&i===0)out+=`<circle cx="${x}" cy="${y}" r="${r+5}" fill="none" stroke="${C.teal}" stroke-width="1.5"/>`;out+=`<circle cx="${x}" cy="${y}" r="${r}" fill="${root?(active?C.navy:C.gray):palette[nodeGroup[i]%4]}"/>`;if(w>=150)out+=`<text x="${x}" y="${y+4}" text-anchor="middle" style="fill:white;font-size:12px">${i+1}</text>`;});return out+'</svg>';
}
function recurrence(){
 const n=+$('recurrence-n').value,p=+$('recurrence-p').value,k=state.rootK=Math.min(state.rootK,n),result=R.rootedProbabilities(n,p),graphs=R.enumerateGraphs(n,p),empirical=Array(n).fill(0);
 for(const graph of graphs)empirical[graph.rootSize-1]+=graph.weight;
 const error=Math.max(...empirical.map((value,i)=>Math.abs(value-result.probabilities[i]))),prob=result.probabilities[k-1],count=graphs.filter(g=>g.rootSize===k).length;
 $('recurrence-p-value').value=fmt(p,2);$('recurrence-readout').innerHTML=metric(t('Enumerated graphs','枚举网络数'),fmt(graphs.length,0))+metric(t('Probability sum','概率之和'),fmt(result.probabilities.reduce((s,x)=>s+x,0),6))+metric(t('Expected S₂','期望S₂'),fmt(result.expectedS2,3));
 $('recurrence-sizes').innerHTML=Array.from({length:n},(_,i)=>`<button data-root-size="${i+1}" aria-pressed="${i+1===k}">k = ${i+1}</button>`).join('');
 $('recurrence-sizes').querySelectorAll('button').forEach(button=>button.addEventListener('click',()=>{state.rootK=+button.dataset.rootSize;recurrence();$('recurrence-sizes').querySelector('[data-root-size="'+state.rootK+'"]').focus();}));
 const example=graphs.filter(g=>g.rootSize===k).sort((a,b)=>b.weight-a.weight||a.mask-b.mask)[0];$('recurrence-graph').innerHTML=graphPicture(example,300,205,true);
 $('recurrence-graph-note').textContent=t(`A representative of the ${count} graphs whose node 1 lies in a group of size ${k}. Their total probability is ${fmt(prob,6)}. Here c = (N−1)p = ${fmt((n-1)*p,2)}.`,`${count}张“节点1所在群体规模为${k}”的网络之一；这些网络的概率之和为${fmt(prob,6)}，对应c=(N−1)p=${fmt((n-1)*p,2)}。`);
 const e=$('recurrence-probabilities'),w=width(e),h=260,Lm=37,rr=w-12,T=25,B=h-47,sx=i=>Lm+(rr-Lm)*(i+.5)/n,sy=value=>B-(B-T)*value,bw=Math.min(34,(rr-Lm)/n*.55);let out=svg(w,h,t('Rooted component probabilities: recurrence bars and exact enumeration points','根节点群体概率：递推柱形与精确枚举点'));
 for(const y of [0,.25,.5,.75,1])out+=line(Lm,sy(y),rr,sy(y))+text(Lm-6,sy(y)+4,fmt(y,2),'end');
 result.probabilities.forEach((value,i)=>{out+=`<rect x="${sx(i)-bw/2}" y="${sy(value)}" width="${bw}" height="${B-sy(value)}" fill="${i+1===k?C.teal:'#d6e2e6'}"/><circle cx="${sx(i)}" cy="${sy(empirical[i])}" r="4" fill="${C.navy}"/><text x="${sx(i)}" y="${B+22}">${i+1}</text>`;});
 e.innerHTML=out+text(Lm,13,'π(N, k)','start','axis-title')+text((Lm+rr)/2,h-4,t('Root group size k','根节点群体规模k'),'middle','axis-title')+'</svg>';
 math($('recurrence-formula'),String.raw`\begin{aligned}\pi_{${n},${k}}&=\binom{${n-1}}{${k-1}}\,C_{${k}}(${fmt(p,2)})\,(1-${fmt(p,2)})^{${k*(n-k)}}\\&=${fmt(prob,6)}\end{aligned}`);
 const factors=[[R.choose(n-1,k-1),t('Choose the other members','选择其余成员')],[result.connected[k],t('Require internal connectedness','要求内部连通')],[(1-p)**(k*(n-k)),t('Forbid every outside link','禁止全部对外连边')]];
 $('recurrence-factors').innerHTML=factors.map(([v,label])=>'<div><strong>'+esc(fmt(v,6))+'</strong><span>'+esc(label)+'</span></div>').join('');
 state.records.network={scope:'Exact small-system enumeration and analytical recurrence evaluated in the browser',n,p,k,probabilities:result.probabilities,enumeratedProbabilities:empirical,maximumNumericalDiscrepancy:error,expectedS2:result.expectedS2,graphs:graphs.length,selectedEventGraphCount:count,sources:sources.recurrence};
}
const methodNames={RBF_return:['Return RBF','收益RBF'],RBF_joint:['Price–volume RBF','量价RBF'],RBF_volume:['Volume RBF','成交量RBF'],RBF_shape_joint:['Invariant RBF','尺度不变RBF'],Moment_volume:['Moment inversion','矩反演']};
const methods=Object.keys(methodNames);
function scales(){
 const rows=state.data.recovery,split=$('scale-split').value,b=+$('scale-value').value,selected=$('scale-method').value,base=R.recoveryMean(rows,selected,split,1),current=R.recoveryMean(rows,selected,split,b),diff=100*(current/base-1),means=methods.map(method=>({method,base:R.recoveryMean(rows,method,split,1),current:R.recoveryMean(rows,method,split,b)}));
 $('scale-readout').innerHTML=metric(t('Reference MAE, b = 1','参照MAE，b=1'),fmt(base,5))+metric(t('Selected-scale MAE','所选尺度MAE'),fmt(current,5))+metric(t('Change in error','误差变化'),(diff>0?'+':'')+fmt(diff,2)+'%',t('Connectivity c is the recovery target','恢复目标为连接参数c'));
 const globalMax=Math.ceil(Math.max(...rows.filter(r=>r.test_split===split).map(r=>+r.mae))*1.08*10)/10||.1;
 const e=$('scale-comparison'),w=width(e),h=335,Lm=w<430?102:137,rr=w-18,sx=x=>Lm+(rr-Lm)*x/globalMax;let out=svg(w,h,t('Paired method errors under a fixed scale control','固定尺度对照下的成对方法误差'));
 for(let i=0;i<=4;i++){const x=globalMax*i/4;out+=line(sx(x),25,sx(x),280)+text(sx(x),303,fmt(x,2));}
 means.forEach((row,i)=>{const y=45+i*50;out+=text(Lm-10,y+4,t(...methodNames[row.method]),'end')+line(sx(row.base),y,sx(row.current),y,C.gray,2)+`<circle cx="${sx(row.base)}" cy="${y}" r="5" fill="${C.teal}"/><circle cx="${sx(row.current)}" cy="${y}" r="${row.method===selected?6:4}" fill="${C.navy}"><title>${esc(fmt(row.current,6))}</title></circle>`;});
 e.innerHTML=out+text((Lm+rr)/2,h-5,t('Connectivity mean absolute error','连接参数平均绝对误差'),'middle','axis-title')+'</svg>';
 const ref=R.recoveryRows(rows,selected,split,1),now=R.recoveryRows(rows,selected,split,b),chart=$('scale-repetitions'),ww=width(chart),hh=355,left=54,right=ww-18,xx=value=>left+(right-left)*value/globalMax;let pair=svg(ww,hh,t('All ten independent studies, paired by scale','十组独立研究的尺度配对'));
 for(let i=0;i<=4;i++){const v=globalMax*i/4;pair+=line(xx(v),25,xx(v),300)+text(xx(v),322,fmt(v,2));}
 ref.forEach((r,i)=>{const y=40+i*27,other=now.find(row=>row.replication===r.replication);pair+=text(left-10,y+4,String(+r.replication+1),'end')+line(xx(+r.mae),y,xx(+other.mae),y,C.gray,1.5)+`<circle cx="${xx(+r.mae)}" cy="${y}" r="4" fill="${C.teal}"/><circle cx="${xx(+other.mae)}" cy="${y}" r="4" fill="${C.navy}"/>`;});
 chart.innerHTML=pair+text(left,14,t('Study','研究组'),'end','axis-title')+text((left+right)/2,hh-4,t('Connectivity mean absolute error','连接参数平均绝对误差'),'middle','axis-title')+'</svg>';
 $('scale-interpretation').textContent=t('These controls isolate uniform positive return rescaling within a window. The original-scale and transformed results are paired observations from the same ten studies. Compare both the change in error and the original-scale accuracy.','该对照针对窗口内收益的统一正尺度变换。原尺度与变换结果来自相同十组研究的配对观测，应同时比较误差变化与原尺度精度。');
 state.records.inference={scope:'Replay of saved paired scale controls; no new fitting',target:'Connectivity c',split,scale:b,method:selected,referenceMAE:base,selectedMAE:current,errorChangePercent:diff,methodMeans:means,referenceStudies:ref,selectedStudies:now,sources:sources.scale};
}
const atlas=R.graphAtlas();
function graphAtlas(){
 const category=atlas.classes.find(c=>c.profile===state.atlasProfile);if(!category.masks.includes(state.atlasMask))state.atlasMask=category.masks[0];
 const chosen=atlas.graphs.find(g=>g.mask===state.atlasMask),law=M.observationLaw(chosen.sizes,.2);state.atlasOutcome=Math.min(state.atlasOutcome,law.length-1);
 $('atlas-profiles').innerHTML=atlas.classes.map(c=>`<button data-profile="${c.profile}" aria-pressed="${c.profile===state.atlasProfile}">[${c.profile.split('+').join(', ')}]<small>${c.masks.length} ${esc(t('graphs','种网络'))}</small></button>`).join('');
 $('atlas-profiles').querySelectorAll('button').forEach(button=>button.addEventListener('click',()=>{state.atlasProfile=button.dataset.profile;graphAtlas();$('atlas-profiles').querySelector('[data-profile="'+state.atlasProfile+'"]').focus();}));
 $('atlas-readout').innerHTML=metric(t('Graphs in this class','此类网络数量'),String(category.masks.length)+' / 64')+metric(t('Group-size profile','群体规模列表'),'['+chosen.sizes.join(', ')+']')+metric(t('Distinct observations','不同观测结果'),String(law.length));
 $('graph-atlas').innerHTML=category.masks.map(mask=>{const graph=atlas.graphs[mask];return `<button data-graph-mask="${mask}" aria-pressed="${mask===state.atlasMask}" aria-label="${esc(t('Select labelled graph','选择有标号网络'))} ${mask+1}">${graphPicture(graph,105,66)}<span>${mask+1}</span></button>`;}).join('');
 $('graph-atlas').querySelectorAll('button').forEach(button=>button.addEventListener('click',()=>{state.atlasMask=+button.dataset.graphMask;graphAtlas();$('graph-atlas').querySelector('[data-graph-mask="'+state.atlasMask+'"]').focus({preventScroll:true});}));
 $('atlas-selected').innerHTML=graphPicture(chosen,280,175);
 const chart=$('atlas-law'),w=width(chart),h=260,Lm=35,rr=w-20,T=22,B=h-65,sx=r=>Lm+(rr-Lm)*(100*r+2)/4,sy=v=>B-(B-T)*v/4;let out=svg(w,h,t('Complete one-period law; symbol size encodes probability','完整单期观测分布；符号大小表示概率'));
 for(const v of [0,2,4])out+=line(Lm,sy(v),rr,sy(v))+text(Lm-7,sy(v)+4,String(v),'end');
 for(const value of [-2,-1,0,1,2])out+=text(sx(value/100),B+30,String(value));
 for(const[index,point]of law.entries())out+=`<circle data-outcome="${index}" cx="${sx(point.r)}" cy="${sy(point.v)}" r="${Math.max(2,18*Math.sqrt(point.p))}" fill="${C.teal}" fill-opacity=".65" stroke="${index===state.atlasOutcome?C.navy:'white'}" stroke-width="${index===state.atlasOutcome?2:.5}"><title>${esc('r='+fmt(point.r,3)+', V='+point.v+', P='+fmt(point.p,5))}</title></circle>`;
 chart.innerHTML=out+text(Lm,13,'V','start','axis-title')+text((Lm+rr)/2,h-4,t('Return r (%)','收益r (%)'),'middle','axis-title')+'</svg>';
 $('atlas-outcome').innerHTML=law.map((point,i)=>`<option value="${i}">r = ${fmt(point.r,3)}, V = ${point.v}</option>`).join('');$('atlas-outcome').value=String(state.atlasOutcome);$('atlas-probability').textContent=t('Probability: ','概率：')+fmt(law[state.atlasOutcome].p,5)+' · '+t('Symbol size encodes probability.','符号大小表示概率。');
 chart.querySelectorAll('[data-outcome]').forEach(point=>point.addEventListener('click',()=>{state.atlasOutcome=+point.dataset.outcome;graphAtlas();}));
 $('atlas-conclusion').innerHTML='<strong>'+esc(t('A whole class shares this observation law.','整个类别共享这一观测分布。'))+'</strong><p>'+esc(t(`The ${category.masks.length} graphs in this class have the same connected-group sizes. Under the fixed group-action model, all their one-period (r, V) probabilities coincide. The atlas is a complete four-node enumeration. It compares laws conditional on each fixed graph. ER parameter recovery instead averages over independently redrawn graphs in the specified family.`,`此类${category.masks.length}种网络的连通群体规模相同，因此在固定群体动作模型下，全部单期(r,V)概率一致。该图谱完整枚举四节点情况，比较的是给定网络的条件观测分布；ER参数恢复则在指定图族中对独立重采的网络取平均。`))+'</p>';
 state.records.identity={scope:'Complete enumeration of four-node labelled simple graphs',totalGraphs:64,classProfile:chosen.sizes,classGraphCount:category.masks.length,mask:chosen.mask,edges:chosen.edges,law,q:.2,n:4,lambda:.02,u:1,sources:sources.atlas};
}
const armNames={Constant:['Constant','固定参数'],PersistentActivity:['Activity state','活动状态'],ShuffledActivity:['Shuffled pairs','整对打乱'],PersistentImpact:['Response state','响应状态']};
function syncMemorySelectors(){
 if(!$('research-path'))return;$('research-path').value=String(L.state.memoryReplication);$('research-arm').value=$('memory-arm').value;
 for(const select of [$('research-path'),$('research-arm')])for(const option of select.options)if(option.dataset.enLabel)option.textContent=select.id==='research-arm'?t(...armNames[option.value]):A.getLanguage()==='zh'?option.dataset.zhLabel:option.dataset.enLabel;
}
function density(pairs,reference,w,h,title){
 const nx=18,ny=14,Lm=30,rr=w-8,T=18,B=h-34,maxR=Math.max(...reference.map(p=>Math.abs(p[0])))||1,maxV=Math.max(...reference.map(p=>p[1]))||1,bins=Array(nx*ny).fill(0);
 for(const[r,v]of pairs){const x=Math.max(0,Math.min(nx-1,Math.floor((r/maxR+1)*nx/2))),y=Math.max(0,Math.min(ny-1,Math.floor(v/maxV*ny)));bins[y*nx+x]++;}
 const maximum=Math.max(...bins);let out=svg(w,h,title);
 bins.forEach((count,index)=>{if(count)out+=`<rect x="${Lm+(rr-Lm)*(index%nx)/nx}" y="${B-(B-T)*(Math.floor(index/nx)+1)/ny}" width="${(rr-Lm)/nx+.1}" height="${(B-T)/ny+.1}" fill="${C.teal}" opacity="${.12+.88*Math.log1p(count)/Math.log1p(maximum)}"/>`;});
 out+=line(Lm,B,rr,B)+text(Lm,12,'V','start')+text((Lm+rr)/2,h-4,t('Return r','收益r'))+text(Lm-4,B+3,'0','end')+text(Lm-4,T+5,fmt(maxV,0),'end')+text(Lm,B+17,'−')+text((Lm+rr)/2,B+17,'0')+text(rr,B+17,'+');return out+'</svg>';
}
function repetitions(){
 syncMemorySelectors();const metricKey=$('repeat-metric').value,rows=state.data.memory.paths,summary=state.data.memory.summary,arms=Object.keys(armNames),rep=L.state.memoryReplication;
 const chart=$('repeat-chart'),w=width(chart),h=300,Lm=w<440?95:118,rr=w-16,T=30,B=250,lower=-.1,upper=1,sx=x=>Lm+(rr-Lm)*(x-lower)/(upper-lower);let out=svg(w,h,t('Ten independent paths and their saved summary intervals','十条独立路径及保存的汇总区间'));
 for(const x of [0,.25,.5,.75,1])out+=line(sx(x),T,sx(x),B)+text(sx(x),274,fmt(x,2));
 for(const[arm,i]of arms.map((v,i)=>[v,i])){
  const y=55+i*57,row=summary.find(r=>r.arm===arm&&r.metric===metricKey);out+=text(Lm-10,y+4,t(...armNames[arm]),'end');
  const measures=rows.filter(r=>r.arm===arm);for(const record of measures){const active=+record.replication===rep,yy=y+((+record.replication%5)-2)*4;out+=`<circle data-rep="${record.replication}" cx="${sx(+record[metricKey])}" cy="${yy}" r="${active?5:3}" fill="${active?C.navy:'#a9b6be'}" stroke="${active?'white':'none'}" stroke-width="1"><title>${esc(t('Path','路径')+' '+(+record.replication+1)+': '+fmt(record[metricKey],4))}</title></circle>`;}
  out+=line(sx(+row.ci_low),y,sx(+row.ci_high),y,C.teal,2.5)+`<rect x="${sx(+row.estimate)-3}" y="${y-3}" width="6" height="6" fill="${C.teal}"/>`;
 }
 chart.innerHTML=out+text((Lm+rr)/2,h-4,t('Lag-one correlation','一期滞后相关'),'middle','axis-title')+'</svg>';
 chart.querySelectorAll('[data-rep]').forEach(point=>point.addEventListener('click',()=>L.changeMemoryPath(+point.dataset.rep)));
 const chosenArm=$('memory-arm').value,summaryRow=summary.find(row=>row.arm===chosenArm&&row.metric===metricKey),pathRow=rows.find(row=>row.arm===chosenArm&&+row.replication===rep);$('repeat-summary-reading').textContent=t(`Selected path: ${fmt(pathRow[metricKey],3)}. Ten-path mean: ${fmt(summaryRow.estimate,3)}, with saved approximate 95% interval [${fmt(summaryRow.ci_low,3)}, ${fmt(summaryRow.ci_high,3)}].`,`当前路径：${fmt(pathRow[metricKey],3)}；十条路径均值：${fmt(summaryRow.estimate,3)}，保存的近似95%区间为[${fmt(summaryRow.ci_low,3)}, ${fmt(summaryRow.ci_high,3)}]。`);
 const original=L.state.memory.arms[$('memory-arm').value],onlyV=R.permuteVolume(original,state.operatorSeed),whole=M.permutePairs(original,state.operatorSeed),all=[original,onlyV,whole],labels=[t('Original observations','原始观测'),t('Permute V only','仅置换V'),t('Permute whole pairs','整对置换')],summaries=all.map(R.observationSummary);
 const sameMarginals=all.map(pairs=>R.sameMultiset(original.map(p=>p[0]),pairs.map(p=>p[0]))&&R.sameMultiset(original.map(p=>p[1]),pairs.map(p=>p[1]))),sameJoint=all.map(pairs=>R.sameMultiset(original,pairs));
 $('operator-comparison').innerHTML=all.map((pairs,i)=>`<section><h5>${esc(labels[i])}</h5><div id="operator-density-${i}" class="chart"></div><div class="operator-result"><p>${esc(t('Marginals: ','边际分布：'))}<strong class="same-yes">${esc(sameMarginals[i]?t('preserved','保留'):t('changed','改变'))}</strong></p><p>${esc(t('Joint pairs: ','联合观测对：'))}<strong class="${sameJoint[i]?'same-yes':'same-no'}">${esc(sameJoint[i]?t('preserved','保留'):t('changed','改变'))}</strong></p><p>Corr(|r|, V): <strong>${fmt(summaries[i].absVolumeCorrelation,3)}</strong></p><p>${esc(t('Lag-one |r|: ','|r|一期相关：'))}<strong>${fmt(summaries[i].magnitudeACF,3)}</strong></p><p>${esc(t('Lag-one V: ','V一期相关：'))}<strong>${fmt(summaries[i].volumeACF,3)}</strong></p></div></section>`).join('');
 all.forEach((pairs,i)=>{const e=$('operator-density-'+i);e.innerHTML=density(pairs,original,width(e,145),190,labels[i]);});
 $('operator-reading').textContent=t(`Path ${rep+1}, ${t(...armNames[$('memory-arm').value])}; all 8,192 observations are used. A shared seeded permutation controls the two transformations.`,`路径${rep+1}，${t(...armNames[$('memory-arm').value])}；使用全部8,192个观测。两种变换使用同一组固定种子置换。`);
 state.records.memory={scope:'Saved ten-path summaries and browser transformations of one saved path',replication:rep,arm:$('memory-arm').value,metric:metricKey,selectedSummaries:summary.filter(r=>r.metric===metricKey),allPathMetrics:rows,permutationSeed:state.operatorSeed,comparison:summaries,preservedMarginals:sameMarginals,preservedJointPairs:sameJoint,sources:sources.memory};
}
function tails(){
 const law=$('tail-law').value,level=+$('tail-level').value,index=+$('tail-threshold').value,all=state.data.tails,ref=all.truth.find(r=>r.truth==='Gaussian'),selected=all.truth.find(r=>r.truth===law),referenceCurve=all.ccdf.filter(r=>r.truth==='Gaussian'),currentCurve=all.ccdf.filter(r=>r.truth===law),threshold=+currentCurve[index].loss_threshold_sigma;
 $('tail-threshold-value').value=fmt(threshold,1)+' σ';
 $('tail-readout').innerHTML=metric(t('Gaussian exceedance','高斯超限频率'),fmt(100*+referenceCurve[index].exceedance_probability,3)+'%')+metric(t('Selected exceedance','所选分布超限频率'),fmt(100*+currentCurve[index].exceedance_probability,3)+'%')+metric(t('Common portfolio σ','共同组合σ'),fmt(selected.portfolio_sigma,6),t('Original fixed covariance experiment','原固定协方差实验'));
 const chart=$('tail-ccdf'),w=width(chart),h=330,Lm=48,rr=w-18,T=27,B=h-53,sx=x=>Lm+(rr-Lm)*x/8,sy=y=>B-(B-T)*(Math.log10(y)+5)/5;let out=svg(w,h,t('Saved empirical loss exceedance frequencies at matched covariance','协方差匹配后的保存经验损失超限频率'));
 for(const value of [1,.1,.01,.001,.0001,.00001])out+=line(Lm,sy(value),rr,sy(value))+text(Lm-7,sy(value)+4,['1','10⁻¹','10⁻²','10⁻³','10⁻⁴','10⁻⁵'][-Math.round(Math.log10(value))],'end');
 for(const x of [0,2,4,6,8])out+=text(sx(x),B+23,String(x));
 out+=line(Lm,sy(1-level),rr,sy(1-level),C.gold,1,'stroke-dasharray="3 4"')+`<text x="${rr}" y="${sy(1-level)-7}" text-anchor="end" style="fill:${C.gold};font-size:12px">1 − α = ${fmt(100*(1-level),0)}%</text>`;
 for(const[curve,color]of [[referenceCurve,C.teal],[currentCurve,C.navy]]){
  let path='',pen=false;for(const point of curve){const probability=+point.exceedance_probability;if(probability>0){path+=(pen?' L':' M')+sx(+point.loss_threshold_sigma)+','+sy(probability);pen=true;}else pen=false;}
  out+=`<path d="${path}" fill="none" stroke="${color}" stroke-width="2" ${color===C.teal?'stroke-dasharray="5 3"':''}/>`;const value=+curve[index].exceedance_probability;
  if(value>0)out+=`<circle cx="${sx(threshold)}" cy="${sy(value)}" r="4.5" fill="${color}" stroke="white"/>`;
  else out+=`<path d="M${sx(threshold)-5},${B-7} L${sx(threshold)+5},${B-7} L${sx(threshold)},${B}Z" fill="${color}"/>`;
 }
 out+=line(sx(threshold),T,sx(threshold),B,C.gray,1,'stroke-dasharray="4 4"');chart.innerHTML=out+text(Lm,14,t('Exceedance frequency (log scale)','超限频率（对数刻度）'),'start','axis-title')+text((Lm+rr)/2,h-5,t('Loss threshold / portfolio σ','损失阈值 / 组合σ'),'middle','axis-title')+'</svg>';
 const zero=+referenceCurve[index].exceedance_probability===0||+currentCurve[index].exceedance_probability===0;
 $('tail-zero-note').textContent=zero?t('A lower-edge triangle denotes zero observed exceedances in 50,000 saved scenarios. It does not assign a zero population probability.','下边界三角表示50,000个保存场景中未观察到超限，不表示总体概率为0。'):t('The curves replay saved empirical frequencies. Each distribution has 50,000 scenarios, with the original covariance matching retained.','曲线回放保存的经验频率。每种分布有50,000个场景，并保留原实验的协方差匹配。');
 const suffix=level===.95?'05':'01',values=[{name:'VaR '+fmt(level*100,0)+'%',ref:-Number(ref['q'+suffix]),current:-Number(selected['q'+suffix])},{name:'ES '+fmt(level*100,0)+'%',ref:-Number(ref['es'+suffix]),current:-Number(selected['es'+suffix])}];
 const e=$('tail-metrics'),ww=width(e),hh=300,left=43,right=ww-18,top=25,bottom=hh-48,max=Math.ceil(Math.max(...all.truth.flatMap(r=>[-Number(r['q'+suffix]),-Number(r['es'+suffix])]))*1.12),yy=v=>bottom-(bottom-top)*v/max,bw=Math.min(35,(right-left)/8);let bars=svg(ww,hh,t('Value at risk and expected shortfall at the same confidence level','相同置信水平下的VaR与ES'));
 for(let i=0;i<=4;i++){const y=max*i/4;bars+=line(left,yy(y),right,yy(y))+text(left-7,yy(y)+4,fmt(y,1),'end');}
 values.forEach((row,i)=>{const x=left+(right-left)*(i+.5)/2;for(const[value,offset,color]of [[row.ref,-bw-2,C.teal],[row.current,2,C.navy]])bars+=`<rect x="${x+offset}" y="${yy(value)}" width="${bw}" height="${bottom-yy(value)}" fill="${color}"><title>${esc(row.name+': '+fmt(value,6))}</title></rect>`;bars+=text(x,bottom+24,row.name);});
 e.innerHTML=bars+text(left,14,t('Loss / portfolio σ','损失 / 组合σ'),'start','axis-title')+'</svg>';
 $('tail-value-reading').innerHTML=values.map(row=>'<p><strong>'+esc(row.name)+'</strong> · '+esc(t('Gaussian ','高斯 '))+fmt(row.ref,3)+' σ · '+esc(t('selected ','所选 '))+fmt(row.current,3)+' σ</p>').join('');
 state.records.risk={scope:'Replay of fixed-portfolio covariance-matched synthetic distributions',distribution:law,alpha:level,thresholdSigma:threshold,referenceExceedance:+referenceCurve[index].exceedance_probability,selectedExceedance:+currentCurve[index].exceedance_probability,reference:ref,selected,tailMetrics:values,referenceCurve,currentCurve,sources:sources.tails};
}
const marketStepNames=[['First moments','一二阶矩'],['Volume variance','成交量方差'],['Joint and third moments','联合与三阶矩'],['Cancel the scales','消去尺度'],['Read the bound','读出界限']];
function market(){
 const select=$('market-case'),block=$('market-block').value,records=state.data.market.sensitivity,primary=state.data.market.metrics.find(r=>r.metric==='delta'&&r.day_block_length===block),cases=[{key:'primary',label:t('BTC 2025 H2 — primary evaluation','BTC 2025下半年：主要检验'),delta:+primary.estimate,ci:[+primary.ci_low,+primary.ci_high]},...records.map((r,i)=>({key:String(i),label:r.case==='calendar_month'?r.period:t(r.case==='leave_max_day_volume'?'H2, exclude highest-volume day':r.case==='leave_max_day_realized_variance'?'H2, exclude highest-variance day':'H2, exclude largest-return day',r.case==='leave_max_day_volume'?'下半年：剔除最高成交量日':r.case==='leave_max_day_realized_variance'?'下半年：剔除最高实现方差日':'下半年：剔除最大收益幅度日'),delta:+r.delta,source:r}))];
 const previous=select.value||'primary';select.innerHTML=cases.map(row=>`<option value="${row.key}">${esc(row.label)}</option>`).join('');select.value=cases.some(r=>r.key===previous)?previous:'primary';const selected=cases.find(r=>r.key===select.value);$('market-block').disabled=selected.key!=='primary';
 $('market-readout').innerHTML=metric(t('Selected estimate Δ','所选估计Δ'),fmt(selected.delta,3))+metric(t('All finite N: model envelope','所有有限N的模型包络'),'0 < Δ ≤ 1')+metric(t('Saved comparison cases','保存的对照条件'),String(cases.length));
 const chart=$('market-restriction'),w=width(chart),h=210,Lm=40,rr=w-18,lo=Math.floor(Math.min(...cases.map(r=>r.delta),+primary.ci_low)-1),hi=2,sx=x=>Lm+(rr-Lm)*(x-lo)/(hi-lo),y=100;let out=svg(w,h,t('Observed Delta against the fixed-model positive envelope','观测Delta与固定模型正值包络的对照'));
 out+=`<rect x="${sx(0)}" y="38" width="${sx(1)-sx(0)}" height="99" fill="#dfebef"/>`+line(Lm,y,rr,y)+line(sx(0),33,sx(0),141,C.teal,1,'stroke-dasharray="4 4"');
 for(let x=Math.ceil(lo/4)*4;x<=0;x+=4)out+=text(sx(x),165,String(x));out+=text(sx(1),165,'1');
 if(selected.ci)out+=line(sx(selected.ci[0]),y,sx(selected.ci[1]),y,C.navy,3)+line(sx(selected.ci[0]),y-7,sx(selected.ci[0]),y+7,C.navy,1.5)+line(sx(selected.ci[1]),y-7,sx(selected.ci[1]),y+7,C.navy,1.5);
 out+=`<circle cx="${sx(selected.delta)}" cy="${y}" r="6" fill="${C.navy}"/>`+text(sx(selected.delta),y-19,fmt(selected.delta,3),'middle','data-label')+text((sx(0)+sx(1))/2,25,'(0, 1]');
 chart.innerHTML=out+text((Lm+rr)/2,h-8,'Δ','middle','axis-title')+'</svg>';
 $('market-interval-note').textContent=selected.ci?t(`Saved approximate 95% interval [${fmt(selected.ci[0],3)}, ${fmt(selected.ci[1],3)}], using ${block}-day circular date blocks on 184 H2 dates. The shaded region is the envelope over finite N; a specified N has lower bound 1/N.`,`保存的近似95%区间为[${fmt(selected.ci[0],3)}, ${fmt(selected.ci[1],3)}]，以184个下半年日期作${block}日循环日期块。阴影为有限N的允许范围包络；给定N时下界为1/N。`):t('This saved case provides a point estimate. The H2 interval applies to the primary H2 evaluation. For a specified finite N, the model lower bound is 1/N.','此保存条件提供点估计。下半年的区间对应主要下半年检验；给定有限N时，模型下界为1/N。');
 $('market-steps').innerHTML=marketStepNames.map((name,i)=>`<button data-market-step="${i}" aria-pressed="${i===state.marketStep}">${esc(t(...name))}</button>`).join('');
 $('market-steps').querySelectorAll('button').forEach(button=>button.addEventListener('click',()=>{state.marketStep=+button.dataset.marketStep;market();$('market-steps').querySelector('[data-market-step="'+state.marketStep+'"]').focus();}));
 const formulas=[String.raw`\begin{aligned}\mathbb E[V]&=quN\\\operatorname{Var}(r)&=q(\lambda/N)^2A\end{aligned}`,String.raw`\operatorname{Var}(V)=q(1-q)u^2A`,String.raw`\begin{aligned}\operatorname{Cov}(r^2,V)&=uq(1-q)(\lambda/N)^2B\\ \kappa_3(V)&=u^3q(1-q)(1-2q)B\end{aligned}`,String.raw`\begin{aligned}\Delta&=\frac{u\{(1-q)-(1-2q)\}B/A}{quN}\\&=\frac{B}{NA}\end{aligned}`,String.raw`\begin{gathered}1\leq s_C\leq N\\\Longrightarrow\quad\frac1N\leq\frac{\mathbb E[S_3]}{N\mathbb E[S_2]}\leq1\end{gathered}`];
 const readings=[['Let A = E[S₂] and B = E[S₃]. The fixed parameters q, λ, N and u enter the observable moments.','记A=E[S₂]、B=E[S₃]。固定参数q、λ、N和u进入可观测矩。'],['The shared-action activity variance q(1−q) multiplies the squared-size group moment.','共同动作的活动方差q(1−q)乘在群体规模平方矩前。'],['The same cubic-size moment B appears in the joint moment and the volume third cumulant. Here κ₃(V) is the centered third moment of volume.','联合矩与成交量三阶累积量中出现相同的群体规模三次矩B，其中κ₃(V)就是成交量的三阶中心矩。'],['Divide by the two variances, subtract, and normalize by mean volume: q, λ and u cancel.','分别除以两个方差，作差，再用平均成交量归一化，q、λ和u消去。'],['Every group size lies between one and N. Thus the moment ratio must be positive and at most one.','每个群体规模介于1与N之间，因此该矩比值必须为正，且不超过1。']];
 math($('market-step-formula'),formulas[state.marketStep]);$('market-step-reading').textContent=t(...readings[state.marketStep]);
 const allChart=$('market-case-chart'),ww=width(allChart),hh=cases.length*26+50,left=ww<500?143:260,right=ww-20,xx=value=>left+(right-left)*(value-lo)/(hi-lo);let plot=svg(ww,hh,t('All saved monthly and exclusion checks','全部保存月份与剔除检验'));
 plot+=line(xx(0),15,xx(0),hh-30,C.teal,1,'stroke-dasharray="4 4"');cases.forEach((row,i)=>{const yy=25+i*26,label=row.key==='primary'?t('H2 primary','下半年主要检验'):row.source.case==='calendar_month'?row.label:t(row.source.case==='leave_max_day_volume'?'Exclude top volume':row.source.case==='leave_max_day_realized_variance'?'Exclude top variance':'Exclude largest return',row.source.case==='leave_max_day_volume'?'剔除最高成交量日':row.source.case==='leave_max_day_realized_variance'?'剔除最高方差日':'剔除最大幅度日');plot+=text(left-10,yy+4,label,'end')+`<circle cx="${xx(row.delta)}" cy="${yy}" r="${row.key===selected.key?5:3}" fill="${row.key===selected.key?C.navy:C.gray}"/>`;});allChart.innerHTML=plot+'</svg>';
 state.records.market={scope:'Saved BTC fixed-interface compatibility checks',case:selected,dayBlockLength:selected.ci?+block:null,step:state.marketStep,allCases:cases,sources:sources.market};
}
async function renderDepth(name){
 if(!state.views[name]||state.views[name]!=='research'||$(name).closest('[hidden]'))return;
 const token=state.renderToken[name]=(state.renderToken[name]||0)+1,requestedRep=name==='memory'?L.state.memoryReplication:null,requestedArm=name==='memory'?$('memory-arm').value:null;
 if(name==='network'){recurrence();return;}if(name==='identity'){graphAtlas();return;}
 status(name,t('Loading saved research results…','正在加载保存的研究结果…'));state.records[name]=null;
 try{
  if(name==='memory')await Promise.all([data(),L.loadMemory()]);else await data();
  if(state.renderToken[name]!==token||state.views[name]!=='research'||$(name).closest('[hidden]'))return;
  if(name==='memory'&&(requestedRep!==L.state.memoryReplication||requestedArm!==$('memory-arm').value||L.state.memory?.replication!==requestedRep))return;
  status(name,'');if(name==='inference')scales();if(name==='memory')repetitions();if(name==='risk')tails();
 }catch(error){status(name,t('Saved results could not load. Reopen Research detail to retry.','保存结果未能加载，请重新打开“深入研究”重试。'));}
}
function synchronizeURL(name){
 const url=new URL(location.href);url.hash=name;if(state.views[name]==='research')url.searchParams.set('view','research');else url.searchParams.delete('view');
 if(url.href!==location.href)history.replaceState(null,'',url);
}
function switchView(name,view,updateURL=true){
 if(!Object.hasOwn(state.views,name)||!['explore','research'].includes(view))return;
 state.views[name]=view;$('explore-'+name).hidden=view!=='explore';$('research-'+name).hidden=view!=='research';
 document.querySelectorAll('[data-depth-view][data-experiment="'+name+'"]').forEach(button=>{const active=button.dataset.depthView===view;button.setAttribute('aria-selected',String(active));button.tabIndex=active?0:-1;});
 if(updateURL)synchronizeURL(name);if(view==='research')renderDepth(name);
}
function exportResearch(name,status){
 const result=state.records[name];if(!result){status.textContent=t('Wait for the selected research result to load.','请等待所选研究结果加载完成。');return;}
 download(JSON.stringify({experiment:name,view:'research',recordedAt:new Date().toISOString(),...result,sources:result.sources.map(path=>repo+path)},null,2),'econophysics-'+name+'-research.json','application/json');
 status.textContent=t('Research comparison saved with its settings and source evidence.','已保存包含设置与原始依据的研究对照。');
}
document.querySelectorAll('[data-export-svg]').forEach(button=>button.addEventListener('click',()=>{
 const target=$(button.dataset.exportSvg),original=target?.querySelector('svg');if(!original)return;
 const clone=original.cloneNode(true),namespace='http://www.w3.org/2000/svg';clone.setAttribute('xmlns',namespace);const style=document.createElementNS(namespace,'style');style.textContent='text{font-family:Arial,sans-serif;font-size:12px;fill:#58636d}.axis-title{font-size:13px;fill:#242b33}.data-label{font-size:15px;fill:#173e60}';clone.prepend(style);
 const metadata=document.createElementNS(namespace,'metadata');metadata.textContent=JSON.stringify({project:'Econophysics Risk Lab',figure:button.dataset.exportSvg,recordedAt:new Date().toISOString(),evidence:state.records[button.closest('[data-lab-experiment]')?.id]||state.records.market});clone.append(metadata);
 download(new XMLSerializer().serializeToString(clone),'econophysics-'+button.dataset.exportSvg+'.svg','image/svg+xml;charset=utf-8');
}));
window.ResearchWorkbench={state,switchView,renderDepth,recurrence,scales,graphAtlas,repetitions,tails,market,data};
if($('market-workbench')){
 const draw=async()=>{try{await data();status('market','');market();}catch(error){status('market',t('Saved market results could not load; reload to retry.','保存的市场结果未能加载，请刷新重试。'));}};
 ['market-case','market-block'].forEach(id=>$(id).addEventListener('change',draw));document.addEventListener('languagechange',draw);
 $('market-case-chart').closest('details').addEventListener('toggle',event=>{if(event.target.open&&state.data)market();});
 if(window.ResizeObserver){let prior=0;new ResizeObserver(entries=>{const now=entries[0].contentRect.width;if(Math.abs(now-prior)>1){prior=now;if(state.data)market();}}).observe($('market-workbench'));}
 draw();
}
if(!L||!$('research-network'))return;
$('recurrence-n').value='5';$('scale-value').value='2';$('scale-method').value='RBF_joint';$('tail-law').value='Herding-rho1.0-q0.05-k0.75';$('tail-level').value='0.99';
// Reuse the existing path and mechanism choices in the repeated-study view.
const memoryControls=$('research-memory').querySelector('.depth-controls');
for(const[from,to,en,zh]of [['memory-path','research-path','Independent path','独立路径'],['memory-arm','research-arm','Mechanism','机制']]){
 const holder=document.createElement('div'),label=document.createElement('label'),select=$(from).cloneNode(true);select.id=to;label.htmlFor=to;label.innerHTML='<span data-en>'+en+'</span><span data-zh hidden>'+zh+'</span>';holder.append(label,select);memoryControls.prepend(holder);
 label.querySelector('[data-en]').hidden=A.getLanguage()!=='en';label.querySelector('[data-zh]').hidden=A.getLanguage()!=='zh';
}
syncMemorySelectors();
$('research-path').addEventListener('change',()=>L.changeMemoryPath(+$('research-path').value));
$('research-arm').addEventListener('change',()=>{$('memory-arm').value=$('research-arm').value;L.memory();});
for(const id of ['recurrence-n','recurrence-p'])$(id).addEventListener('input',recurrence);
for(const id of ['scale-split','scale-value','scale-method'])$(id).addEventListener('change',()=>{if(state.data)scales();});
for(const id of ['tail-law','tail-level'])$(id).addEventListener('change',()=>{if(state.data)tails();});$('tail-threshold').addEventListener('input',()=>{if(state.data)tails();});
$('repeat-metric').addEventListener('change',()=>{if(state.data&&L.state.memory)repetitions();});
$('operator-reshuffle').addEventListener('click',()=>{state.operatorSeed++;if(state.data&&L.state.memory)repetitions();});
$('repeat-open-path').addEventListener('click',()=>switchView('memory','explore'));
$('atlas-outcome').addEventListener('change',()=>{state.atlasOutcome=+$('atlas-outcome').value;graphAtlas();});
$('atlas-to-editor').addEventListener('click',()=>{const graph=atlas.graphs[state.atlasMask];A.state.topology=L.state.topology='custom';L.state.edges=graph.edges.map(edge=>edge.slice());switchView('identity','explore');L.identity();});
document.querySelectorAll('[data-depth-view]').forEach(button=>{
 button.addEventListener('click',()=>switchView(button.dataset.experiment,button.dataset.depthView));
 button.addEventListener('keydown',event=>{if(['ArrowLeft','ArrowRight','Home','End'].includes(event.key)){event.preventDefault();const view=event.key==='Home'?'explore':event.key==='End'?'research':button.dataset.depthView==='explore'?'research':'explore';switchView(button.dataset.experiment,view);$('view-'+button.dataset.experiment+'-'+view).focus();}});
});
const originalRender=L.render;L.render=name=>{originalRender(name);if(Object.hasOwn(state.views,name))switchView(name,state.views[name],false);};
const originalExport=L.exportExperiment;
L.exportExperiment=(name,status)=>state.views[name]==='research'?exportResearch(name,status):originalExport(name,status);
document.addEventListener('memorychange',()=>{
 syncMemorySelectors();
 if(state.views.memory==='research')renderDepth('memory');
});
const initialURL=new URL(location.href);
const initialExperiment=$(initialURL.hash.slice(1))?.closest('[data-lab-experiment]')?.id||'mechanism';
if(initialURL.searchParams.get('view')==='research'&&Object.hasOwn(state.views,initialExperiment)){
 switchView(initialExperiment,'research',false);
}
if(window.ResizeObserver){
 let prior=0;
 new ResizeObserver(entries=>{
  const now=entries[0].contentRect.width;
  if(Math.abs(now-prior)<=1)return;
  prior=now;
  for(const name of Object.keys(state.views))renderDepth(name);
 }).observe(document.querySelector('.experiment-content'));
}
})();
