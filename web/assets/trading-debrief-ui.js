(function(){
 'use strict';const $=id=>document.getElementById(id),stage=$('trade-theory-review');if(!stage)return;
 let current=null,key='',selected=20,lang='en';const t=(en,zh)=>lang==='zh'?zh:en,esc=x=>String(x).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])),fmt=(x,n=2)=>Number.isFinite(x)?x.toLocaleString(lang==='zh'?'zh-CN':'en-US',{minimumFractionDigits:n,maximumFractionDigits:n}):'—',time=x=>new Date(x).toISOString().slice(11,16);
 const sources={
  observed:['Market data','真实行情'],
  virtual:['Your virtual trades','你的虚拟成交'],
  calculated:['Computed from trades','由成交计算'],
  estimated:['Model estimate','模型估计'],
  mixed:['Market data + model','真实行情与模型'],
 };
 const badge=(type,text=t(...sources[type]))=>`<span class="debrief-source ${type}">${esc(text)}</span>`;
 function shell(){
 stage.innerHTML=`<div class="debrief-heading">
   <h3>${t('From this market to our model','从这段行情理解我们的模型')}</h3>
   <div class="debrief-guide">
    <p><strong>${t('1. Start with the trades.','1. 先看成交。')}</strong> ${t('Two buys of one BTC add to +2 BTC of net buying. A buy and a sell of one BTC cancel to zero. In both cases two BTC changed hands.','两笔各 1 BTC 的主动买入，净买入就是 2 BTC。一买一卖各 1 BTC，净买入就是零。两种情况下成交量都是 2 BTC。')}</p>
    <p><strong>${t('2. Connect to the homepage.','2. 接回首页的分组。')}</strong> ${t('When orders move together, their effects can add. G compares how widely net buying swung over the past 15 minutes with a reference based on trade sizes. A value above 1 means wider swings than that reference. The size reference adds squared trade sizes. One trade of 4 BTC contributes 16 BTC². Two trades of 2 BTC contribute 8 BTC² together.','订单同向时，作用会叠加。G 把过去 15 分钟净买入的起伏，与按成交大小算出的独立参照比较。G 大于 1，说明起伏大于参照。大小基线把每笔成交量平方后相加。一笔 4 BTC 的成交贡献 16 BTC²，两笔各 2 BTC 的成交合计贡献 8 BTC²。')}</p>
    <p><strong>${t('3. Compare risk at the same moment.','3. 在同一时点比较风险。')}</strong> ${t('The model uses recent trades and the price response fitted before play. Its dashed reference keeps those inputs and sets G to 1. The gap shows how much directional amplification changes the model estimate. A thin order book can make pressure move prices more. This replay keeps the fitted response fixed.','模型用近期成交和开局前拟合的价格响应估计风险。虚线保留这些输入，只把 G 设为 1。两条线的差值就是方向放大对模型读数的影响。盘口薄时，同样的交易压力可能推动更大的价格变动。本回放固定拟合出的价格响应。')}</p>
    <p>${t('RMS expresses the typical size of a price move in percent. Square the returns, average them, then take the square root. For +1% and −1%, RMS is 1%. The chart shows past observed RMS and a model estimate of next-minute RMS.','RMS（均方根）用百分比表示价格通常变动多大。把收益率平方、求平均、再开平方。比如 +1% 和 −1% 的 RMS 是 1%。图中分别画过去实测的 RMS 和模型估计的下一分钟 RMS。')}</p>
   </div>
  </div><div class="debrief-checkpoints" id="debrief-checkpoints"></div><label class="debrief-slider"><span>${t('Inspect a moment','选择复盘时点')}</span><input id="debrief-tick" type="range" min="0" max="${current.market.tick}" value="${selected}" step="1"><output id="debrief-time"></output></label><div id="debrief-timeline" class="debrief-timeline"></div><div id="debrief-reading" class="debrief-reading"></div>   <details class="debrief-check"><summary>${t('Check yourself: can estimated risk rise while price falls?','想一想：估计风险升高时，价格还能下跌吗？')}</summary>
    <p>${t('Yes. Risk measures how large a move could be in either direction. A large buy is a record of a completed trade. The next move also depends on new buying, selling and available liquidity.','可以。风险衡量价格向任一方向变动的幅度。大额买入是已完成的成交记录，之后的价格还取决于新出现的买卖和当时的流动性。')}</p></details><p class="debrief-information">${t('This post-round view uses aggregate executions to measure the size baseline B. That is richer information than macro-only inversion. It does not change the information recorded as visible during your trades.','本复盘使用聚合成交测量大小基线B，信息比仅用宏观量价反演更充分；不会更改你交易时实际可见的信息记录。')}</p><details class="debrief-math"><summary>${t('How these quantities follow the theory','这些量怎样对应理论')}</summary><div class="debrief-equations"><div><span class="debrief-equation" data-tex="B_t=\\sum_i v_{it}^{2},\\quad F_t=\\sum_i\\epsilon_{it}v_{it}"></span><p>${t('F adds signed BTC. B adds the squared sizes, in BTC². With the same total volume, larger executions raise B. Related trade directions can add to swings in F.','F 把带方向的成交量相加，单位为 BTC。B 把各笔成交量平方后相加，单位为 BTC²。同样的总成交量越集中成大单，B 越大。成交方向有关联时，F 的起伏还会随之改变。')}</p></div><div><span class="debrief-equation" data-tex="\\widehat G_t=\\frac{\\widehat{\\operatorname{Var}}_{15}(F)}{\\overline B_{15}},\\qquad\\overline B_{15}\\widehat G_t=\\widehat{\\operatorname{Var}}_{15}(F)"></span><p>${t('G is execution-direction amplification relative to that baseline. Splitting and size–direction dependence can also affect it; it does not identify people or a real network. The same-window product is exactly direct flow variance.','G是相对该基线的执行方向放大指标。拆单、大小与方向的依赖也会影响它，不能据此识别人群或真实网络。同窗口相乘严格还原成交流方差。')}</p></div><div><span class="debrief-equation" data-tex="\\widehat h_{t+1|t}=(\\alpha+\\beta\\overline F_{15})^2+\\beta^2\\overline B_3\\widehat G_t+\\sigma_\\eta^2"></span><p>${t('The risk mapping transfers recent activity and slower directional dispersion through a fixed price response. Setting G=1 is a model reference, not a causal measurement of what would happen if traders stopped coordinating.','风险映射用固定价格响应连接近期活动和较慢的方向离散程度。设G=1是模型参照，不是移除真实协同交易后的因果测量。')}</p></div></div><p id="debrief-fit"></p><p>${t('Response coefficients use only the 30 completed minutes before play and remain fixed. Three-/15-minute windows are a local teaching version of the fast-activity/slow-amplification hypothesis. Residual orthogonality, response stability and persistence are assumptions.','价格响应仅用开局前30个已完成分钟校准，局中固定。3/15分钟窗口是活动快、放大慢这一假设的局部教学版本；残差正交、响应稳定和状态延续均为模型假设。')}</p><p>${t('The observed curve is trailing 15-minute realized RMS. The model curve is an estimate of next-minute RMS made at each displayed origin; they are not the same target. RMS includes the mean-return term and is not the centred standard deviation. Curated episodes do not establish predictive skill.','实测曲线是截至该时点的15分钟已实现RMS；模型曲线是该时点对下一分钟RMS的估计，二者目标不同；RMS包含均值项，不等于去均值后的标准差。精选片段不能证明预测能力。')}</p><a href="methods.html#execution-risk-bridge">${t('Read the full mathematical bridge','查看完整数学衔接')}</a></details><div class="debrief-next"><a href="trading.html?source=model">${t('Change coordination and memory in the model','在模型中改变协同与记忆')}</a><a href="findings.html#information-efficiency">${t('See the matched-information risk test','查看同信息预算的风险检验')}</a></div>`;
 stage.querySelectorAll('[data-tex]').forEach(e=>{if(window.katex)window.katex.render(e.dataset.tex,e,{throwOnError:true,displayMode:true});else e.textContent=e.dataset.tex;});
 const last=current.market.tick,primary=current.market.historicalReview.primaryAlertTick,first=current.account.trades[0]?.tick;
 const moments=[{tick:Math.max(0,primary-15),label:t('15 min before signal','信号前15分钟')},{tick:primary,label:t('Primary large flow','主要大额成交')},{tick:Math.min(last,primary+15),label:t('15 min later','15分钟后')}];if(first!==undefined)moments.push({tick:first,label:t('My first trade','我的首次交易')});const peak=current.analysis.points.reduce((a,b)=>a.observedTrailingRmsPct>b.observedTrailingRmsPct?a:b);moments.push({tick:peak.tick,label:t('Observed RMS peak (post hoc)','观测RMS峰值（事后）')});
 $('debrief-checkpoints').innerHTML=moments.map(m=>`<button type="button" data-debrief-tick="${m.tick}">${esc(m.label)}</button>`).join('');
 const c=current.analysis.calibration;$('debrief-fit').textContent=t(`Fixed pre-play response: α=${c.alpha.toExponential(2)}, β=${c.beta.toExponential(2)} per BTC; residual RMS=${fmt(100*Math.sqrt(c.residualSecondMoment),3)}% per minute.`,`开局前固定校准：α=${c.alpha.toExponential(2)}，β=${c.beta.toExponential(2)} /BTC；残差每分钟RMS=${fmt(100*Math.sqrt(c.residualSecondMoment),3)}%。`);
 }
 function plot(kind,title,type,legend){
  const pts=current.analysis.points,W=Math.max(180,Math.round(stage.clientWidth||760)),H=126,L=58,R=15,T=12,B=24,maxTick=current.market.tick,xx=v=>L+(W-L-R)*v/Math.max(1,maxTick),x=xx(selected);let lines=[],range;
  if(kind==='price'){lines=[{values:pts.map(p=>current.market.bars.find(b=>b.tick===p.tick).close),color:'#173e60'}];range=[Math.min(...lines[0].values),Math.max(...lines[0].values)];}
  if(kind==='flow'){range=[-Math.max(...pts.map(p=>Math.max(p.largeBuyQuote,p.largeSellQuote)))/1e6,Math.max(...pts.map(p=>Math.max(p.largeBuyQuote,p.largeSellQuote)))/1e6];}
  if(kind==='g'){lines=[{values:pts.map(p=>Math.log10(Math.max(.01,p.g))),color:'#8b632a'}];range=[Math.floor(Math.min(0,...lines[0].values)),Math.ceil(Math.max(1,...lines[0].values))];}
  if(kind==='risk'){lines=[{values:pts.map(p=>p.modelRmsPct),color:'#8b632a'},{values:pts.map(p=>p.independentRmsPct),color:'#8b98a2',dash:'3 3'},{values:pts.map(p=>p.observedTrailingRmsPct),color:'#197b70'}];range=[0,Math.max(...lines.flatMap(a=>a.values))];}
  let [lo,hi]=range;const pad=(hi-lo||1)*.07;lo-=['price','flow'].includes(kind)?pad:0;if(kind!=='g')hi+=pad;const yy=v=>T+(hi-v)/(hi-lo||1)*(H-T-B);let svg=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(title)}"><title>${esc(title)}</title>`;
  for(let j=0;j<3;j++){const v=lo+(hi-lo)*j/2,y=yy(v),label=kind==='g'?fmt(10**v,v<0?2:1):fmt(v,kind==='price'?0:2);svg+=`<line x1="${L}" x2="${W-R}" y1="${y}" y2="${y}" stroke="#dce5eb" stroke-width=".7"/><text x="${L-7}" y="${y+3}" text-anchor="end">${label}</text>`;}
  if(kind==='flow'){const zero=yy(0);svg+=`<line x1="${L}" x2="${W-R}" y1="${zero}" y2="${zero}" stroke="#8fa4b2" stroke-width=".8"/>`;for(const p of pts){const z=xx(p.tick),a=yy(p.largeBuyQuote/1e6),b=yy(-p.largeSellQuote/1e6);svg+=`<line x1="${z}" x2="${z}" y1="${zero}" y2="${a}" stroke="#197b70" stroke-width="2"/><line x1="${z}" x2="${z}" y1="${zero}" y2="${b}" stroke="#b34e43" stroke-width="2"/>`;}}
  for(const line of lines){const path=line.values.map((v,i)=>(i?'L':'M')+xx(pts[i].tick).toFixed(2)+','+yy(v).toFixed(2)).join(' ');svg+=`<path d="${path}" fill="none" stroke="${line.color}" stroke-width="1.8" ${line.dash?`stroke-dasharray="${line.dash}"`:''}/>`;}
  if(kind==='g'){svg+=`<line x1="${L}" x2="${W-R}" y1="${yy(0)}" y2="${yy(0)}" stroke="#8b98a2" stroke-dasharray="3 3"/>`;}
  for(const ev of current.market.events.filter(e=>e.type==='large-flow'))svg+=`<line x1="${xx(ev.tick)}" x2="${xx(ev.tick)}" y1="${T}" y2="${H-B}" stroke="${ev.direction>0?'#197b70':'#b34e43'}" opacity=".16"/>`;
  for(const tr of current.account.trades){const y=kind==='price'?yy(tr.price):H-B+1,buy=tr.side==='buy'||tr.side==='cover';svg+=`<path d="M${xx(tr.tick)},${y} l-3,${buy?6:-6} h6 z" fill="#173e60" stroke="white" stroke-width=".5"><title>${esc(t('Your execution','你的成交'))} ${fmt(tr.price)}</title></path>`;}
  svg+=`<line data-cursor="${selected}" x1="${x}" x2="${x}" y1="${T}" y2="${H-B}" stroke="#173e60" stroke-width="1.2"/>`;
  for(const tick of [0,Math.floor(maxTick/2),maxTick])svg+=`<text x="${xx(tick)}" y="${H-5}" text-anchor="middle">${time(pts[tick].time)}</text>`;
  return `<div class="debrief-plot"><div>${badge(type)}<strong>${esc(title)}</strong></div>${svg}</svg><p>${legend}</p></div>`;
 }
 function paint(){
  if(!current?.market.done)return;const points=current.analysis.points,p=points[selected],before=points[Math.max(0,selected-15)],price=current.market.bars.find(b=>b.tick===selected).close;$('debrief-tick').value=selected;$('debrief-time').textContent=`${time(p.time)} UTC · ${fmt(price)} USDT`;
  stage.querySelectorAll('[data-debrief-tick]').forEach(button=>{
   button.setAttribute('aria-pressed',String(Number(button.dataset.debriefTick)===selected));
  });
  $('debrief-timeline').innerHTML=
   plot('price',t('Price and your trades','价格与你的交易'),'observed',
    t('The line is the real close price, in USDT. Faint vertical lines mark observed large flow.','线条是以 USDT 计的真实收盘价。浅色竖线标记真实大额成交。')+
    '<br>'+badge('virtual')+t('Triangles are your simulated fills.','三角标记你的模拟成交。'))+
   plot('flow',t('Large aggressive flow over 3 minutes','近 3 分钟大额主动买卖'),'observed',
    t('Sum of large executed buys and sells, in million USDT. Buying above zero and selling below zero.','统计已完成的大额买卖，单位为百万 USDT。零线上方为主动买入，下方为主动卖出。'))+
   plot('g',t('Execution-direction amplification G','执行方向放大指标 G'),'calculated',
    t('The dashed line is the independent reference G=1. Equal vertical distances represent equal ratios. Trade splitting or one trader acting repeatedly can also affect G.','虚线是独立参照 G=1。纵轴等距离代表相同的倍数变化。拆单或同一交易者重复下单也会影响 G。'))+
   plot('risk',t('Risk estimate and past fluctuation','风险估计与过去的实际波动'),'mixed',
    badge('estimated')+`<span class="risk-model">${t('Brown: next-minute RMS','棕线为下一分钟模型 RMS')}</span> · <span class="risk-g1">${t('Dashed: same model with G=1','虚线为同一模型取 G=1')}</span><br>`+
    badge('observed')+`<span class="risk-observed">${t('Green: past 15-minute RMS','绿线为过去 15 分钟实测 RMS')}</span>`);
  const pct=x=>fmt(x,3)+'%';
  const referenceComparison=pct(p.modelRmsPct)===pct(p.independentRmsPct)
   ?t('Both model values are equal at the displayed precision.','按显示精度，两种模型读数相同。')
   :p.modelRmsPct>p.independentRmsPct
    ?t('The measured G raises the model estimate above its G=1 reference.','代入算出的 G 后，模型估计高于 G=1 的参照。')
    :t('The measured G lowers the model estimate below its G=1 reference.','代入算出的 G 后，模型估计低于 G=1 的参照。');
  const minutes=selected-before.tick;
  const delta=minutes===0?'':t(
   `Compared with ${minutes} min earlier, G moved from ${fmt(before.g)} to ${fmt(p.g)}. Estimated risk moved from ${pct(before.modelRmsPct)} to ${pct(p.modelRmsPct)}. Past observed RMS moved from ${pct(before.observedTrailingRmsPct)} to ${pct(p.observedTrailingRmsPct)}.`,
   `与 ${minutes} 分钟前相比，G 从 ${fmt(before.g)} 变为 ${fmt(p.g)}，模型风险估计从 ${pct(before.modelRmsPct)} 变为 ${pct(p.modelRmsPct)}，过去实测 RMS 从 ${pct(before.observedTrailingRmsPct)} 变为 ${pct(p.observedTrailingRmsPct)}。`);
  $('debrief-reading').innerHTML=`<dl class="debrief-chain">
   <div><dt>${badge('observed')}${t('Trade sizes and directions','成交大小与方向')}</dt>
    <dd>${t('Large buys / sells in the past 3 minutes','过去 3 分钟大额主动买入／卖出')}
    <strong>${fmt(p.largeBuyQuote/1e6)} / ${fmt(p.largeSellQuote/1e6)} ${t('M USDT','百万 USDT')}</strong>
    <span>${t('Net aggressive buying as a share of total volume','净主动买入占总成交量')} ${fmt(100*p.pressure,1)}%</span>
    <span>${t('Size baseline','大小基线')} B₃=${fmt(p.bFast,3)} BTC²</span></dd></div>
   <div><dt>${badge('calculated')}${t('How much net buying swings','净买入的起伏有多大')}</dt>
    <dd><strong id="debrief-g-value">G=${fmt(p.g)}</strong><span>${t('The same G can arise with different traders. Persistent one-sided flow can shift the mean while leaving its swings small.','不同的参与者结构可以算出相同的 G。持续单向成交可能抬高平均净买入，但起伏仍然小。')}</span></dd></div>
   <div><dt>${badge('estimated')}${t('Next-minute risk scale','下一分钟风险尺度')}</dt>
    <dd><strong id="debrief-risk-value">${pct(p.modelRmsPct)}</strong><span>${t('G=1 reference','G=1 参照')} ${pct(p.independentRmsPct)}</span>
    <span class="debrief-next-return">${badge('observed')} ${t('Actual size of the next minute’s move','下一分钟实际变动幅度')} ${p.nextAbsReturnPct===null?t('outside excerpt','在片段之外'):pct(p.nextAbsReturnPct)}</span></dd></div>
   </dl><p class="debrief-interpretation">${esc(referenceComparison)}</p>
   ${delta?`<p>${esc(delta)}</p>`:''}
`;

 }
 stage.addEventListener('input',e=>{if(e.target.id==='debrief-tick'){selected=Number(e.target.value);paint();}});stage.addEventListener('click',e=>{const b=e.target.closest('[data-debrief-tick]');if(b){selected=Number(b.dataset.debriefTick);paint();}});
 function render(view){lang=view.language;stage.hidden=view.market.source!=='history';if(stage.hidden)return;if(!view.market.done){key='';current=null;stage.innerHTML=`<h3>${t('Mechanism debrief after the round','本轮结束后解读机理')}</h3><p>${t('Complete the round to compare the full observed flow, conditional amplification and risk path. The trading information record is preserved.','完成本轮后，对照完整成交、模型条件下的放大指标与风险路径；交易时的信息记录保持不变。')}</p>`;return;}
  const nextKey=view.market.caseId+lang;if(nextKey!==key){const same=current?.market.caseId===view.market.caseId;current={...view,analysis:window.TradingDebrief.analyze(view.market)};if(!same)selected=view.market.historicalReview.primaryAlertTick;key=nextKey;shell();}else current={...current,...view};paint();
 }
 window.TradingDebriefView={render,reset:()=>{key='';current=null;stage.innerHTML='';stage.hidden=true;},snapshot:()=>current?{selectedTick:selected,analysis:current.analysis}:null};
}());
