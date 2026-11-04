(function(){
'use strict';
const M=window.EconoMath,D=window.ResearchData,$=id=>document.getElementById(id);
const colors={navy:'#173e60',teal:'#416b73',gray:'#a9b6be',line:'#d4dce2',ink:'#242b33',blue:'#2675a0',gold:'#9d7841',red:'#92505c'};
let language='en';try{language=localStorage.getItem('econo-language')==='zh'?'zh':'en';}catch(e){}
const state={grouping:'independent',lab:'mechanism',seed:20261027,actionSeed:15,selectedGroup:0,actions:null,topology:'chain',inferSeed:20261028,forecastIndex:0,visible:new Set(['HAR','HAR+All'])};
const t=(en,zh)=>language==='zh'?zh:en;
const fmt=(x,d=2)=>Number.isFinite(x)?x.toLocaleString(language==='zh'?'zh-CN':'en-US',{minimumFractionDigits:d,maximumFractionDigits:d}):'—';
const esc=s=>String(s).replace(/[&<>"']/g,x=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[x]));
const stat=(label,value)=>`<div>${esc(label)}<strong>${esc(value)}</strong></div>`;
function applyLanguage(){
 document.documentElement.lang=language==='zh'?'zh-CN':'en';
 document.querySelectorAll('[data-en]').forEach(e=>e.hidden=language!=='en');document.querySelectorAll('[data-zh]').forEach(e=>e.hidden=language!=='zh');
 document.querySelectorAll('option[data-en-label]').forEach(e=>e.textContent=language==='zh'?e.dataset.zhLabel:e.dataset.enLabel);
 $('language').textContent=language==='zh'?'English':'中文';$('language').setAttribute('aria-label',language==='zh'?'Switch to English':'切换到中文');
 document.dispatchEvent(new CustomEvent('languagechange'));
}
$('language').addEventListener('click',()=>{language=language==='en'?'zh':'en';try{localStorage.setItem('econo-language',language);}catch(e){}applyLanguage();});
$('menu-toggle').addEventListener('click',()=>{const open=$('menu-toggle').getAttribute('aria-expanded')!=='true';$('menu-toggle').setAttribute('aria-expanded',open);$('main-nav').classList.toggle('open',open);});
document.querySelectorAll('[data-math]').forEach(el=>{if(window.katex)katex.render(el.dataset.math,el,{displayMode:el.classList.contains('display'),throwOnError:true,strict:'warn'});else el.textContent=el.dataset.math;});
function svgStart(w,h,title){return `<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="${esc(title)}"><title>${esc(title)}</title>`;}
function line(x1,y1,x2,y2,color,width=1,extra=''){return `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${color}" stroke-width="${width}" ${extra}/>`;}
function text(x,y,value,cls='',anchor='middle'){return `<text x="${x}" y="${y}" text-anchor="${anchor}" class="${cls}">${esc(value)}</text>`;}
function hero(){
 if(!$('hero-network'))return;const coordinated=state.grouping==='coordinated';let out=svgStart(580,290,t('Model grouping of 100 traders','100名交易者的模型分组'));
 for(let g=0;g<(coordinated?10:1);g++){
  const points=[];
  for(let k=0;k<(coordinated?10:100);k++){
   const x=coordinated?58+(g%5)*116+27*Math.cos(k*2*Math.PI/10):97+(k%10)*43;
   const y=coordinated?75+Math.floor(g/5)*140+27*Math.sin(k*2*Math.PI/10):17+Math.floor(k/10)*28;
   points.push([x,y]);
  }
  if(coordinated)for(let i=1;i<points.length;i++)out+=line(...points[i-1],...points[i],colors.gray,1.2);
  for(const [x,y] of points)out+=`<circle cx="${x}" cy="${y}" r="${coordinated?4.2:3.8}" fill="${coordinated?colors.teal:colors.navy}"/>`;
 }
 $('hero-network').innerHTML=out+'</svg>';
 const r=M.moments(coordinated?Array(10).fill(10):Array(100).fill(1),.2);
 $('hero-mean').textContent=fmt(r.meanV,0);$('hero-variance').textContent=fmt(r.varV,0);$('hero-s2').textContent=fmt(r.s2,0);
 $('hero-caption').textContent=t(coordinated?'Model calculation: ten groups of ten, the same mean volume, tenfold volume variance.':'Model calculation: 100 independent traders. Compare with ten coordinated groups.',coordinated?'模型计算：十个十人群体，平均成交量相同，成交量方差为十倍。':'模型计算：100名独立交易者。可与十个协调群体比较。');
 document.querySelectorAll('[data-grouping]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.grouping===state.grouping)));
}
document.querySelectorAll('[data-grouping]').forEach(b=>b.addEventListener('click',()=>{state.grouping=b.dataset.grouping;hero();}));
function packedNetwork(g,container,selected,actions){
 const width=680,height=390,placed=[],positions={},golden=Math.PI*(3-Math.sqrt(5));
 g.groups.forEach((group,k)=>{
  const radius=group.length===1?6:6*Math.sqrt(group.length)+5;let cx=0,cy=0;
  for(let attempt=0;attempt<16000;attempt++){const rr=2.5*Math.sqrt(attempt),aa=attempt*golden;cx=rr*Math.cos(aa);cy=rr*Math.sin(aa);if(placed.every(p=>Math.hypot(cx-p.x,cy-p.y)>radius+p.r+3))break;}
  placed.push({x:cx,y:cy,r:radius});group.forEach((node,j)=>{const rr=group.length===1?0:radius*.78*Math.sqrt((j+.5)/group.length),a=j*golden;positions[node]=[cx+rr*Math.cos(a),cy+rr*Math.sin(a)];});
 });
 const xmin=Math.min(...placed.map(p=>p.x-p.r)),xmax=Math.max(...placed.map(p=>p.x+p.r)),ymin=Math.min(...placed.map(p=>p.y-p.r)),ymax=Math.max(...placed.map(p=>p.y+p.r));
 const scale=Math.min((width-35)/(xmax-xmin),(height-35)/(ymax-ymin)),p=v=>[(v[0]-(xmin+xmax)/2)*scale+width/2,(v[1]-(ymin+ymax)/2)*scale+height/2];
 let out=svgStart(width,height,t('Simulated trader coordination network; groups share one action','模拟交易者协调网络；同群体共享动作'));
 for(const [a,b]of g.edges){const pa=p(positions[a]),pb=p(positions[b]);out+=line(...pa,...pb,colors.gray,.8);}
 g.groups.forEach((group,k)=>{const col=actions?(actions[k]===1?colors.teal:actions[k]===-1?colors.red:colors.gray):(k===selected?colors.navy:colors.gray);out+=`<g data-group="${k}" role="button" tabindex="${k===selected?0:-1}" aria-label="${esc(t('Group','群体'))} ${k+1}: ${group.length}; S2 ${group.length**2}">`;
  for(const node of group){const [x,y]=p(positions[node]);out+=`<circle cx="${x}" cy="${y}" r="9" fill="transparent"/><circle cx="${x}" cy="${y}" r="${k===selected?4:3.3}" fill="${col}"/>`;}
  out+='</g>';
 });container.innerHTML=out+'</svg>';
 container.querySelectorAll('[data-group]').forEach(el=>{const select=()=>{state.selectedGroup=+el.dataset.group;renderPhysics();};el.addEventListener('click',select);el.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();select();}else if(e.key==='ArrowRight'||e.key==='ArrowLeft'){e.preventDefault();state.selectedGroup=(+el.dataset.group+(e.key==='ArrowRight'?1:-1)+g.groups.length)%g.groups.length;renderPhysics();container.querySelector('[data-group=\"'+state.selectedGroup+'\"]').focus();}});});
}
function renderPhysics(){
 if(!$('physics-network'))return;const c=+$('physics-c').value,q=+$('physics-q').value,g=M.graph(128,c,state.seed);state.graph=g;
 if(state.selectedGroup>=g.groups.length)state.selectedGroup=0;
 $('physics-c-value').value=fmt(c);$('physics-q-value').value=fmt(q);
 const v=q*(.02/128)**2*g.s2;
 $('physics-stats').innerHTML=stat(t('Largest group','最大群体'),g.largest+' / 128')+stat(t('Squared-size sum S₂','规模平方和 S₂'),fmt(g.s2,0))+stat(t('Conditional return SD','条件收益标准差'),fmt(100*Math.sqrt(v),3)+'%');
 packedNetwork(g,$('physics-network'),state.selectedGroup,state.actions);
 $('physics-group').innerHTML=g.groups.map((a,i)=>`<option value="${i}" ${i===state.selectedGroup?'selected':''}>${t('Group','群体')} ${i+1}: ${a.length} ${t(a.length===1?'trader':'traders','名交易者')}</option>`).join('');
 const size=g.groups[state.selectedGroup].length;
 $('group-contribution').textContent=t(`Selected group: ${size} ${size===1?'trader contributes':'traders contribute'} ${size}² = ${size*size} to S₂ (${fmt(100*size*size/g.s2,1)}%).`,`所选群体：${size}名交易者，对S₂贡献${size}²=${size*size}，占${fmt(100*size*size/g.s2,1)}%。`);
 state.physicsResult={c,q,n:128,seed:state.seed,s2:g.s2,largest:g.largest,conditionalReturnVariance:v,meanVolume:q*128,lambda:.02,u:1,selectedGroup:{index:state.selectedGroup,size,squaredSize:size*size,share:size*size/g.s2},period:state.actions?{return:.02/128*state.actions.reduce((s,a,i)=>s+a*g.groups[i].length,0),volume:state.actions.reduce((s,a,i)=>s+Math.abs(a)*g.groups[i].length,0),groupActions:state.actions}:null};
}
function renderIdentity(){
 if(!$('identity-network'))return;const points=[[55,115],[145,40],[235,115],[325,190]],edges=state.topology==='chain'?[[0,1],[1,2],[2,3]]:[[0,1],[0,2],[0,3]];
 let out=svgStart(380,230,t('A connected four-trader '+state.topology,'四名交易者的连通'+(state.topology==='chain'?'链':'星')));
 for(const [a,b]of edges)out+=line(...points[a],...points[b],colors.teal,2);
 points.forEach(([x,y],i)=>{out+=`<circle cx="${x}" cy="${y}" r="12" fill="${colors.navy}"/><text x="${x}" y="${y+5}" fill="white" text-anchor="middle" font-size="14">${i+1}</text>`;});
 $('identity-network').innerHTML=out+'</svg>';
 $('identity-law').innerHTML='<div class="law-row header"><span>'+t('Return r','收益 r')+'</span><span>'+t('Volume V','成交量 V')+'</span><span>'+t('Probability','概率')+'</span></div>'+M.chainLaw(.2).map(a=>`<div class="law-row"><span>${fmt(a.r)}</span><span>${a.v}</span><span class="probability">${fmt(a.p,1)}</span></div>`).join('');
 document.querySelectorAll('[data-topology]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.topology===state.topology)));
}
function chartAxes(w,h,xlabel,ylabel,xTicks,yTicks,sx,sy){
 const L=65,R=w-20,T=30,B=h-48;let out='';
 for(const y of yTicks){out+=line(L,sy(y),R,sy(y),colors.line,.7);out+=text(L-10,sy(y)+4,fmt(y,Number.isInteger(y)?0:1),'','end');}
 out+=line(L,B,R,B,colors.gray);for(const[x,label]of xTicks){out+=line(sx(x),B,sx(x),B+5,colors.gray);out+=text(sx(x),B+22,label);}
 out+=text((L+R)/2,h-5,xlabel,'axis-title');out+=text(L,T-12,ylabel,'axis-title','start');return out;
}
function renderInference(){
 if(!$('inference-curve'))return;const c=+$('infer-c').value,q=+$('infer-q').value,mode=$('infer-mode').value;
 $('infer-c-value').value=fmt(c);$('infer-q-value').value=fmt(q);
 const s2=M.interp(D.curve,c);let moments;
 if(mode==='population')moments={meanV:q*128,varV:q*(1-q)*s2,varR:q*(.02/128)**2*s2};else moments=M.sample(128,c,q,.02,1,+mode,state.inferSeed);
 const result=M.infer(moments.meanV,moments.varV,moments.varR,D.curve);if(result.flag==='degenerate'){state.inferenceResult=null;$('inference-stats').textContent=t('The sample activity is degenerate; draw another window.','样本活动退化，请重采窗口。');$('inference-curve').innerHTML='';$('inference-detail').textContent='';return;}state.inferenceResult={truth:{c,q,lambda:.02},mode,seed:state.inferSeed,observed:{meanV:moments.meanV,varV:moments.varV,varR:moments.varR},estimate:result};
 $('inference-stats').innerHTML=stat(t('Estimated c','估计 c'),fmt(result.c,3))+stat(t('Estimated q','估计 q'),fmt(result.q,3))+stat(t('Estimated λ','估计 λ'),fmt(result.lambda,4));
 const e=$('inference-curve'),w=Math.max(300,e.clientWidth),h=310,xmax=Math.max(2.5,Math.ceil(result.c*2)/2),rows=D.curve.filter(r=>r.rho<=xmax),ymax=Math.max(...rows.map(r=>r.s2),result.s2)*1.08;
 const sx=x=>65+(w-85)*x/xmax,sy=y=>h-48-(h-78)*y/ymax;
 let out=svgStart(w,h,t('Finite ER expected squared-size sum and inferred moment','有限ER期望规模平方和与反演矩'));
 const nTicks=w<500?3:5,xTicks=Array.from({length:nTicks},(_,i)=>[i*xmax/(nTicks-1),fmt(i*xmax/(nTicks-1),1)]),yTicks=Array.from({length:4},(_,i)=>Math.round(i*ymax/3/100)*100);
 out+=chartAxes(w,h,t('Connectivity c','连接程度 c'),'E[S₂]',xTicks,yTicks,sx,sy);
 out+=`<path d="${rows.map((r,i)=>(i?'L':'M')+sx(r.rho)+','+sy(r.s2)).join(' ')}" fill="none" stroke="${colors.navy}" stroke-width="2"/>`;
 out+=line(sx(result.c),sy(0),sx(result.c),sy(result.s2),colors.teal,1,'stroke-dasharray="4 4"');out+=`<circle cx="${sx(result.c)}" cy="${sy(result.s2)}" r="5" fill="${colors.teal}"/>`;
 e.innerHTML=out+'</svg>';
 $('inference-detail').textContent=result.flag!=='interior'?t('The sample moment is outside the physical curve domain; the displayed estimate is at its boundary.','样本矩超出物理曲线范围；显示的是边界估计。'):mode==='population'?t('Population moments recover the selected parameters through the frozen interpolation curve.','总体矩通过既有插值曲线恢复所选参数。'):t(`A ${mode}-period model window gives connectivity error ${fmt(Math.abs(result.c-c),3)}. Draw another window to inspect sampling variation.`,`${mode}期模型窗口的连接参数误差为${fmt(Math.abs(result.c-c),3)}；可重采窗口观察抽样变化。`);
}
function initRisk(){
 if(!$('risk-date'))return;
 $('risk-date').innerHTML=D.risk.map(x=>`<option value="${x.date}" ${x.date==='2020-03-31'?'selected':''}>${x.date}</option>`).join('');
 const names=['Materials','Energy','Financials','Industrials','Technology','Consumer staples','Utilities','Health care','Consumer discretionary'];
 $('risk-weights').innerHTML=D.assets.map((a,i)=>`<div class="asset-control"><label for="weight-${i}"><strong>${a}</strong><span class="sector-name" data-index="${i}">${esc(names[i])}</span></label><input id="weight-${i}" data-weight="${i}" type="number" min="0" max="100" step="1" value="10" aria-label="${a} relative weight"></div>`).join('');
 $('risk-weights').addEventListener('input',renderRisk);['risk-date','risk-lookback','risk-eta'].forEach(id=>$(id).addEventListener('input',renderRisk));
 $('risk-equal').addEventListener('click',()=>{D.assets.forEach((_,i)=>$('weight-'+i).value=10);renderRisk();});
 state.sectorNames=names;
}
function renderRisk(){
 if(!$('risk-chart'))return;
 document.querySelectorAll('.sector-name').forEach(e=>e.textContent=language==='zh'?D.asset_labels[+e.dataset.index]:state.sectorNames[+e.dataset.index]);
 const date=$('risk-date').value,lookback=$('risk-lookback').value,eta=+$('risk-eta').value,weights=D.assets.map((_,i)=>+$('weight-'+i).value);
 $('risk-eta-value').value=fmt(100*eta,0)+'%';let result;
 try{result=M.risk(D.risk.find(x=>x.date===date).cov[lookback],weights,eta);}catch(e){$('risk-stats').textContent=t('Use non-negative weights, with at least one positive value.','权重应为非负数，并至少保留一个正值。');$('risk-chart').innerHTML='';$('risk-detail').textContent='';state.riskResult=null;return;}
 state.riskResult={date,lookback:+lookback,eta,weights,...result};
 $('risk-stats').innerHTML=stat(t('Full covariance','完整协方差'),fmt(result.fullVol)+'%')+stat(t('Diagonal only','仅个体方差'),fmt(result.diagonalVol)+'%')+stat(t('Retained co-movement','保留联动'),fmt(result.counterVol)+'%');
 const e=$('risk-chart'),w=Math.max(300,e.clientWidth),h=300,ymax=Math.ceil(Math.max(result.fullVol,result.diagonalVol,result.counterVol)*1.12/5)*5||5,sy=y=>h-48-(h-78)*y/ymax;
 const data=[[t('Full','完整'),result.fullVol,colors.navy],[t('Retained','保留'),result.counterVol,colors.teal],[t('Diagonal','对角'),result.diagonalVol,colors.gray]],sx=i=>65+(w-85)*(i+.5)/3;
 let out=svgStart(w,h,t('Annualized portfolio volatility estimates in percent','组合年化波动估计，百分比'));
 out+=chartAxes(w,h,t('Covariance treatment','协方差处理'),t('Annual vol. (%)','年化波动 (%)'),data.map((d,i)=>[i,d[0]]),[0,ymax/3,2*ymax/3,ymax],sx,sy);
 const bw=Math.min(75,(w-95)/5);
 data.forEach((d,i)=>{out+=`<rect x="${sx(i)-bw/2}" y="${sy(d[1])}" width="${bw}" height="${sy(0)-sy(d[1])}" fill="${d[2]}"/>`+text(sx(i),sy(d[1])-10,fmt(d[1],2),'data-label');});
 e.innerHTML=out+'</svg>';
 $('risk-detail').textContent=t(`Co-movement contributes ${fmt(result.collectiveShare*100,1)}% of the retained covariance variance estimate.`, `当前保留联动的估计中，联动项占组合方差的${fmt(result.collectiveShare*100,1)}%。`);
}
function showLab(name){
 if(!['mechanism','inference','risk'].includes(name))name='mechanism';state.lab=name;
 document.querySelectorAll('[data-lab]').forEach(b=>{const selected=b.dataset.lab===name;b.setAttribute('aria-selected',selected);b.tabIndex=selected?0:-1;});
 ['mechanism','inference','risk'].forEach(k=>$(k).hidden=k!==name);
 if(name==='mechanism')renderPhysics();if(name==='inference'){renderInference();renderIdentity();}if(name==='risk')renderRisk();
}
if($('physics-network')){
 $('physics-group').addEventListener('change',()=>{state.selectedGroup=+$('physics-group').value;renderPhysics();});
 ['physics-c','physics-q'].forEach(id=>$(id).addEventListener('input',()=>{state.actions=null;$('one-action-result').textContent='';renderPhysics();}));
 $('new-graph').addEventListener('click',()=>{state.seed+=1;state.actions=null;state.selectedGroup=0;$('one-action-result').textContent='';renderPhysics();});
 $('one-action').addEventListener('click',()=>{const q=+$('physics-q').value,r=M.rng(++state.actionSeed);let signed=0,volume=0;state.actions=state.graph.groups.map(g=>{const z=r(),a=z<q/2?-1:z<q?1:0;signed+=a*g.length;volume+=Math.abs(a)*g.length;return a;});renderPhysics();$('one-action-result').textContent=t('This period: ','本期：')+'r = '+fmt(.02/128*signed,5)+', V = '+volume+'. '+t('Teal: buy. Red: sell. Gray: inactive.','青色：买；红色：卖；灰色：不交易。');});
 ['infer-c','infer-q','infer-mode'].forEach(id=>$(id).addEventListener('input',renderInference));
 $('infer-resample').addEventListener('click',()=>{if($('infer-mode').value==='population')$('infer-mode').value='256';state.inferSeed++;renderInference();});
 document.querySelectorAll('[data-topology]').forEach(b=>b.addEventListener('click',()=>{state.topology=b.dataset.topology;renderIdentity();}));
 document.querySelectorAll('[data-lab]').forEach((b,i)=>{b.addEventListener('click',()=>{location.hash=b.dataset.lab;showLab(b.dataset.lab);});b.addEventListener('keydown',e=>{if(e.key==='ArrowRight'||e.key==='ArrowLeft'){e.preventDefault();const all=[...document.querySelectorAll('[data-lab]')],j=(i+(e.key==='ArrowRight'?1:-1)+all.length)%all.length;all[j].click();all[j].focus();}});});
 window.addEventListener('hashchange',()=>showLab(location.hash.slice(1)));initRisk();showLab(location.hash.slice(1)||'mechanism');
 $('export-experiment').addEventListener('click',()=>{const result=state.lab==='mechanism'?state.physicsResult:state.lab==='inference'?{...state.inferenceResult,identityExample:{topology:state.topology,q:.2,n:4,lambda:.02,u:1,law:M.chainLaw(.2)}}:state.riskResult;
  const body=JSON.stringify({experiment:state.lab,recordedAt:new Date().toISOString(),result,sources:state.lab==='inference'?D.sources.curve:state.lab==='risk'?D.sources.risk:'src/econophysics/model.py',scope:state.lab==='risk'?'Historical covariance estimate':'Model calculation or educational simulation'},null,2),url=URL.createObjectURL(new Blob([body],{type:'application/json'})),a=document.createElement('a');a.href=url;a.download='econophysics-'+state.lab+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),2000);
 });
}
function forecastSelection(){
 if(!$('forecast-chart'))return;const d=D.forecast,i=state.forecastIndex,e=$('forecast-chart'),svg=e.querySelector('svg');
 $('forecast-date').value=i;$('forecast-date-value').value=d.dates[i];
 $('forecast-detail').textContent=d.dates[i]+' · '+t('Observed','实际')+' '+fmt(d.actual[i])+'%'+[...state.visible].map(k=>' · '+k+' '+fmt(d.models[k][i])+'%').join('');
 if(!svg)return;const w=+svg.dataset.width,h=+svg.dataset.height,ymax=+svg.dataset.ymax,sx=j=>65+(w-85)*j/(d.dates.length-1),sy=y=>h-48-(h-78)*y/ymax;
 const guide=svg.querySelector('.forecast-guide');guide.setAttribute('x1',sx(i));guide.setAttribute('x2',sx(i));
 svg.querySelectorAll('[data-marker]').forEach(m=>{const key=m.dataset.marker,y=key==='actual'?d.actual[i]:d.models[key][i];m.setAttribute('cx',sx(i));m.setAttribute('cy',sy(y));});
}
function renderForecast(){
 if(!$('forecast-chart'))return;const d=D.forecast,e=$('forecast-chart'),w=Math.max(300,e.clientWidth),h=w<500?300:370,series=[['actual',d.actual,colors.ink],...['HAR','HAR+All','Persistence'].filter(k=>state.visible.has(k)).map(k=>[k,d.models[k],k==='HAR'? '#8196a3':k==='HAR+All'?colors.blue:colors.gold])],ymax=Math.ceil(Math.max(...series.flatMap(s=>s[1]))*1.1),sx=i=>65+(w-85)*i/(d.dates.length-1),sy=y=>h-48-(h-78)*y/ymax;
 const xt=(w<500?[0,61,122,182]:[0,30,61,91,122,153,182]).map(i=>[i,language==='zh'?d.dates[i].slice(5).replace('-','/'):new Date(d.dates[i]+'T00:00:00Z').toLocaleDateString('en-US',{month:'short',day:'numeric',timeZone:'UTC'})]);
 let out=svgStart(w,h,t('Observed and forecast daily realized volatility across 183 held-out dates','183个留出日期的实际与预测日实现波动')).replace('<svg ','<svg data-width="'+w+'" data-height="'+h+'" data-ymax="'+ymax+'" ');
 out+=chartAxes(w,h,t('Target day (UTC)','目标日期 (UTC)'),t('Daily volatility (%)','日波动 (%)'),xt,[0,ymax/3,2*ymax/3,ymax],sx,sy);
 for(const [key,values,col]of series){out+=`<path d="${values.map((y,i)=>(i?'L':'M')+sx(i)+','+sy(y)).join(' ')}" stroke="${col}" fill="none" stroke-width="${key==='HAR+All'?2:1.5}" ${key==='Persistence'?'stroke-dasharray="4 3"':''}/>`;}
 out+=line(sx(state.forecastIndex),30,sx(state.forecastIndex),h-48,colors.gray,1,'class="forecast-guide" stroke-dasharray="3 3"');
 for(const[key,values,col]of series)out+=`<circle data-marker="${key}" cx="${sx(state.forecastIndex)}" cy="${sy(values[state.forecastIndex])}" r="3.5" fill="${col}"/>`;
 out+='<rect class="forecast-hit" x="65" y="30" width="'+(w-85)+'" height="'+(h-78)+'" fill="transparent"/></svg>';e.innerHTML=out;
 const hit=e.querySelector('.forecast-hit');const onPoint=event=>{const rect=e.querySelector('svg').getBoundingClientRect(),x=(event.clientX-rect.left)*w/rect.width;state.forecastIndex=Math.max(0,Math.min(182,Math.round((x-65)/(w-85)*182)));forecastSelection();};hit.addEventListener('pointermove',onPoint);hit.addEventListener('pointerdown',onPoint);
 forecastSelection();
}
document.querySelectorAll('[data-series]').forEach(b=>b.addEventListener('click',()=>{const key=b.dataset.series;if(state.visible.has(key))state.visible.delete(key);else state.visible.add(key);b.setAttribute('aria-pressed',String(state.visible.has(key)));renderForecast();}));
if($('forecast-date'))$('forecast-date').addEventListener('input',()=>{state.forecastIndex=+$('forecast-date').value;forecastSelection();});
const redraw=()=>{hero();if($('physics-network'))showLab(state.lab);renderForecast();};
document.addEventListener('languagechange',redraw);applyLanguage();
if(window.ResizeObserver){let width=0;new ResizeObserver(entries=>{const now=entries[0].contentRect.width;if(Math.abs(now-width)>2){width=now;redraw();}}).observe(document.body);}
window.EconoApp={state,redraw,getLanguage:()=>language};
})();
