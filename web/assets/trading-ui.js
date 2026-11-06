(function () {
  'use strict';
  const $ = id => document.getElementById(id);
  if (!$('trade-chart')) return;
  const E = window.TradingEngine, A = window.TradingAccount;
  const colors = { navy:'#173e60', up:'#197b70', down:'#b34e43', ink:'#243b4d', slate:'#667785', grid:'#dce5eb' };
  let language = 'en';
  try { language = localStorage.getItem('econo-language') === 'zh' ? 'zh' : 'en'; } catch (_) {}
  const state = { playing:false, speed:1, fraction:.5, seed:20261106, scenario:'buy', mode:'guided', coupling:true, memory:true, settled:false, review:null };
  let engine = null, account = null, snap = null, accountSnap = null, timer = null, resizeFrame = null;
  const t = (en, zh) => language === 'zh' ? zh : en;
  const b = (en, zh) => ({en,zh});
  const local = value => typeof value === 'string' ? value : value && (value[language] || value.en || value.zh) || '';
  const esc = value => String(value ?? '').replace(/[&<>"']/g, x => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[x]));
  const fmt = (n, decimals=2) => Number.isFinite(Number(n)) ? Number(n).toLocaleString(language === 'zh' ? 'zh-CN' : 'en-US', {minimumFractionDigits:decimals, maximumFractionDigits:decimals}) : '—';
  const signed = (n, decimals=2) => (Number(n) > 0 ? '+' : '') + fmt(n, decimals);
  const tone = n => Number(n) > 1e-9 ? 'trade-up' : Number(n) < -1e-9 ? 'trade-down' : '';
  const actionName = side => ({ buy:t('Buy','买入'), sell:t('Sell','卖出'), short:t('Short','做空'), cover:t('Cover','买回'), close:t('Close','平仓') }[side] || side);
  const phaseName = phase => ({forming:t('Forming alignment','一致形成'),holding:t('Holding alignment','一致维持'),fragmenting:t('Losing alignment','一致瓦解'),mixed:t('Mixed directions','方向分歧')}[phase] || t('Mixed directions','方向分歧'));
  const phaseCopy = phase => ({forming:t('The fast group is moving toward a shared direction.','快速群体正趋向共同方向。'),holding:t('A common direction is persisting in the fast group.','快速群体保持较强的共同方向。'),fragmenting:t('The fast group is moving away from its recent alignment.','快速群体正在偏离近期的一致方向。'),mixed:t('The group has no strong common direction at this tick.','当前群体没有明显一致的方向。')}[phase] || '');

  function applyLanguage() {
    document.documentElement.lang = language === 'zh' ? 'zh-CN' : 'en';
    document.querySelectorAll('[data-en]').forEach(el => { el.hidden = language !== 'en'; });
    document.querySelectorAll('[data-zh]').forEach(el => { el.hidden = language !== 'zh'; });
    document.querySelectorAll('option[data-en-label]').forEach(el => { el.textContent = language === 'zh' ? el.dataset.zhLabel : el.dataset.enLabel; });
    $('language').textContent = language === 'zh' ? 'English' : '中文';
    $('language').setAttribute('aria-label', t('Switch to Chinese','切换到英文'));
    $('trade-step').setAttribute('aria-label', t('Advance one tick','向前推进一步'));
    $('trade-speed').setAttribute('aria-label', t('Playback speed','播放速度'));
    $('trade-review-close').setAttribute('aria-label', t('Close review','关闭复盘'));
    $('trade-chart').setAttribute('aria-label', t('Collective Index candle prices and trading volume','Collective Index 价格K线与成交量'));
    $('trade-review-chart').setAttribute('aria-label', t('Price path with your trade points','行情路径与本人的交易点位'));
    document.title = t('Trading lab | Econophysics Risk Lab','模拟交易 | Econophysics Risk Lab');
    if (snap) render();
    if ($('trade-review-dialog').open) renderReview();
    if(state.feedbackMessage) feedback(state.feedbackMessage,state.feedbackError);
  }

  function feedback(message, error=false) {
    state.feedbackMessage=message;state.feedbackError=error;
    $('trade-feedback').textContent = local(message);
    $('trade-feedback').classList.toggle('error', error);
  }

  function stop() {
    if (timer !== null) window.clearInterval(timer);
    timer = null; state.playing = false; renderPlayback();
  }

  function start() {
    if (!engine || !snap || snap.done) return;
    if (timer !== null) window.clearInterval(timer);
    state.playing = true;
    timer = window.setInterval(advanceOne, Math.max(50, 650 / state.speed));
    renderPlayback();
  }

  function renderPlayback() {
    $('trade-play-label').textContent = snap?.done ? t('Round complete','本轮已结束') : state.playing ? t('Pause market','暂停行情') : snap?.tick ? t('Continue','继续行情') : t('Start market','启动市场');
    $('trade-play').querySelector('path').setAttribute('d', state.playing ? 'M5 4h4v12H5zM12 4h4v12h-4z' : 'm7 4 9 6-9 6z');
    $('trade-play').setAttribute('aria-pressed', String(state.playing));
    $('trade-play').disabled = !engine || !!snap?.done;
    $('trade-step').disabled = !engine || !!snap?.done;
    $('trade-market-status').textContent = snap?.done ? t('Closed','已收盘') : state.playing ? t('Running','运行中') : snap?.tick ? t('Paused','已暂停') : t('Ready','等待启动');
    $('trade-market-status').classList.toggle('live', state.playing);
  }

  function reset(options={}) {
    stop();
    if ($('trade-review-dialog').open) $('trade-review-dialog').close();
    state.scenario = options.scenario || $('trade-scenario').value;
    state.mode = options.mode || state.mode;
    const inputSeed = Number($('trade-seed').value);
    state.seed = options.seed ?? (Number.isInteger(inputSeed) && inputSeed >= 1 && inputSeed <= 4294967295 ? inputSeed : 20261106);
    $('trade-seed').value = String(state.seed);
    state.coupling = $('trade-coupling').checked;
    state.memory = $('trade-memory').checked;
    state.settled = false; state.review = null;state.capitalDepleted=false;
    $('trade-current-event').dataset.eventKey='';
    if (!E || !A) {
      feedback(b('The market could not load. Reload this page to try again.','市场组件未能加载，请刷新页面重试。'), true);
      document.querySelectorAll('[data-order]').forEach(button => { button.disabled = true; });
      renderPlayback(); return;
    }
    const config = {seed:state.seed,scenario:state.scenario,mode:state.mode,steps:180};
    if (!state.coupling) config.coupling = 0;
    if (!state.memory) config.memory = 0;
    try {
      engine = E.create(config);
      account = A.create({initialCash:100000,feeBps:5,slippageBps:2,maxLeverage:1});
      snap = engine.snapshot(); accountSnap = account.mark(snap.price, snap.tick);
      if (!accountSnap || !Number.isFinite(accountSnap.equity)) accountSnap = account.snapshot();
      feedback(b('Your account is ready. You can trade at the current price.','账户已就绪，可以按当前价格交易。'));
      render();
    } catch (error) {
      engine = null;
      feedback(b('This market setup could not start. Retry with a valid seed.','当前设置未能启动，请检查种子后重试。'), true);
      console.error(error); renderPlayback();
    }
  }

  function advanceOne() {
    if (!engine || snap.done) { stop(); return; }
    const wasPlaying=state.playing;
    snap = engine.step();
    if(wasPlaying&&state.mode==='guided'&&snap.events.some(e=>e.type==='intent'&&e.tick===snap.tick)){stop();feedback(b('Order intent arrived. Choose a position, then continue.','大单意向已出现，可以选择仓位后继续行情。'));}
    accountSnap = account.mark(snap.price,snap.tick);
    if (!accountSnap || !Number.isFinite(accountSnap.equity)) accountSnap = account.snapshot();
    if (accountSnap.insolvent&&!state.capitalDepleted) {
      state.capitalDepleted=true;feedback(b('Your account has no trading capacity left. You can watch the market, review, or retry.','账户已无可用交易额度，可以继续观察行情、复盘或重试。'), true);
    }
    if (snap.done && !state.settled) {
      stop(); account.close({price:snap.price,tick:snap.tick}); accountSnap = account.mark(snap.price,snap.tick); state.settled = true;
      feedback(b('The round is complete. Positions have been closed with costs.','本轮已结束，所有持仓已计入成本平仓。'));
    }
    render();
    if (snap.done && !$('trade-review-dialog').open) openReview();
  }

  function placeOrder(side) {
    if (!account || !snap || snap.done) return;
    const outcome = side === 'close' ? account.close({price:snap.price,tick:snap.tick}) : account.trade({side,fraction:state.fraction,price:snap.price,tick:snap.tick});
    accountSnap = account.snapshot();
    feedback(outcome.message || (outcome.ok ? b('Order filled.','订单已成交。') : b('The order could not be filled.','订单未能成交。')), !outcome.ok);
    render();
  }

  function drawMarket(target, allBars=false) {
    const empty = allBars ? null : target.querySelector('#trade-chart-empty');
    const width = Math.max(280,Math.round(target.clientWidth || 800));
    const height = Math.round(target.clientHeight || (allBars ? 255 : 362));
    const margin = {left:12,right:58,top:15,bottom:24};
    const volumeHeight = allBars ? 35 : Math.max(35,Math.round(height*.16));
    const priceBottom = height-margin.bottom-volumeHeight-20;
    const priceTop = margin.top, chartRight = width-margin.right, chartWidth = chartRight-margin.left;
    const source = snap?.bars || [];
    const limit = allBars ? source.length : width < 520 ? 54 : 120;
    const bars = source.slice(-Math.max(1,limit));
    const firstTick = bars.length ? bars[0].tick : 0;
    const trades=(accountSnap?.trades||[]).filter(tr=>tr.tick>=(firstTick<=1?0:firstTick)&&tr.tick<=(bars.at(-1)?.tick??0));
    const values = bars.flatMap(b=>[b.high,b.low]);
    trades.forEach(tr=>values.push(tr.price));
    if (accountSnap?.quantity) values.push(accountSnap.averageEntry);
    if (!values.length) values.push(99.7,100.3);
    let lo=Math.min(...values), hi=Math.max(...values), span=hi-lo;
    span=Math.max(span,.3); lo-=span*.13;hi+=span*.13;
    const y = value => priceBottom-(value-lo)/(hi-lo)*(priceBottom-priceTop);
    const count = Math.max(bars.length,1), spacing = chartWidth/Math.max(count,12), candleWidth=Math.max(.9,Math.min(8,spacing*.64));
    const x = index => margin.left+(index+.5)*spacing;
    let svg=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" role="img" aria-label="${esc(t('Known price path and your executions','当前已知行情与交易记录'))}"><title>${esc(t('Collective Index price and volume','Collective Index 价格和成交量'))}</title>`;
    for (let j=0;j<5;j++) {
      const val=lo+(hi-lo)*j/4, yy=y(val);
      svg+=`<line x1="${margin.left}" x2="${chartRight}" y1="${yy}" y2="${yy}" stroke="${colors.grid}" stroke-width=".7"/><text x="${chartRight+8}" y="${yy+4}">${fmt(val,2)}</text>`;
    }
    const initial=100;
    if(initial>=lo && initial<=hi) svg+=`<line x1="${margin.left}" x2="${chartRight}" y1="${y(initial)}" y2="${y(initial)}" stroke="#aebec9" stroke-dasharray="3 4" stroke-width=".8"/>`;
    const maxVolume=Math.max(1,...bars.map(b=>b.volume));
    bars.forEach((bar,i)=>{
      const xx=x(i), color=bar.close>=bar.open?colors.up:colors.down;
      const bodyY=Math.min(y(bar.open),y(bar.close)), bodyH=Math.max(1,Math.abs(y(bar.open)-y(bar.close)));
      svg+=`<g><title>${esc(t('Tick','时点'))} ${bar.tick}: ${esc(t('Open','开'))} ${fmt(bar.open)}, ${esc(t('High','高'))} ${fmt(bar.high)}, ${esc(t('Low','低'))} ${fmt(bar.low)}, ${esc(t('Close','收'))} ${fmt(bar.close)}</title><line x1="${xx}" x2="${xx}" y1="${y(bar.high)}" y2="${y(bar.low)}" stroke="${color}" stroke-width="1"/><rect x="${xx-candleWidth/2}" y="${bodyY}" width="${candleWidth}" height="${bodyH}" fill="${color}" rx=".5"/><rect x="${xx-candleWidth/2}" y="${height-margin.bottom-bar.volume/maxVolume*volumeHeight}" width="${candleWidth}" height="${Math.max(.5,bar.volume/maxVolume*volumeHeight)}" fill="${color}" opacity=".30"/></g>`;
    });
    if (bars.length) {
      const last=bars[bars.length-1], yy=y(last.close), color=last.close>=last.open?colors.up:colors.down;
      svg+=`<line x1="${margin.left}" x2="${chartRight}" y1="${yy}" y2="${yy}" stroke="${color}" stroke-width=".8" stroke-dasharray="2 3" opacity=".7"/><rect x="${chartRight+3}" y="${yy-9}" width="53" height="18" rx="2" fill="${color}"/><text x="${chartRight+29}" y="${yy+3.5}" text-anchor="middle" style="fill:white;font-size:10px">${fmt(last.close,2)}</text>`;
      const ticks=[0,Math.floor((bars.length-1)/2),bars.length-1];
      [...new Set(ticks)].forEach(i=>{svg+=`<text x="${x(i)}" y="${height-7}" text-anchor="middle">${bars[i].tick}</text>`;});
    }
    if(accountSnap?.quantity){const yy=y(accountSnap.averageEntry);svg+=`<line x1="${margin.left}" x2="${chartRight}" y1="${yy}" y2="${yy}" stroke="${colors.navy}" stroke-width=".85" stroke-dasharray="6 4"/>`;}
    trades.forEach(tr=>{
      const index=bars.findIndex(b=>b.tick===tr.tick);if(index<0&&!(tr.tick===0&&firstTick<=1))return;
      const xx=index<0?margin.left+2:x(index), buy=tr.side==='buy'||tr.side==='cover', yy=y(tr.price);
      const path=buy?`M${xx},${yy} l-4,7 h8 z`:`M${xx},${yy} l-4,-7 h8 z`;
      svg+=`<path d="${path}" fill="${colors.navy}" stroke="white" stroke-width=".7"><title>${esc(actionName(tr.side))} ${fmt(tr.quantity,2)} @ ${fmt(tr.price)}</title></path>`;
    });
    svg+=`<text x="${margin.left+2}" y="${priceBottom+14}" style="font-size:10px">${esc(t('Volume','成交量'))}</text></svg>`;
    target.innerHTML=svg;
    if(!allBars){
      if(empty){empty.hidden=bars.length>0;target.appendChild(empty);}
      $('trade-chart-range').textContent=bars.length?t(`Ticks ${firstTick}–${bars.at(-1).tick}`,`时点 ${firstTick}–${bars.at(-1).tick}`):t('Starting price 100.00','初始价格 100.00');
    }
  }

  function drawNetwork() {
    const nodes=snap?.network?.nodes||[], edges=snap?.network?.edges||[], view=$('trade-network');
    const width=500,height=178, centres=[130,370],radius=72;
    let out=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" aria-label="${esc(t('Two coupled model layers','两个相互影响的模型层'))}" role="img">`;
    [0,1].forEach(layer=>{
      const project=n=>[centres[layer]+(n.x-.5)*radius*2,83+(n.y-.5)*radius*2];
      edges.filter(e=>e.layer===(layer?'slow':'fast')).forEach((edge,i)=>{
        if(i%2)return;const a=nodes.find(n=>n.id===edge.source),b=nodes.find(n=>n.id===edge.target);if(!a||!b)return;const [x1,y1]=project(a),[x2,y2]=project(b);out+=`<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="#b6c5ce" stroke-width=".65" opacity=".28"/>`;
      });
      nodes.forEach(n=>{const [x,y]=project(n),sign=layer?n.slow:n.fast,r=Math.max(2.2,Math.min(8,Math.sqrt(n.weight*nodes.length)*3.4));out+=`<circle cx="${x}" cy="${y}" r="${r}" fill="${sign>0?colors.up:colors.down}" opacity="${n.active?1:.55}" stroke="white" stroke-width=".6"><title>${esc(t('Weight','权重'))} ${fmt(n.weight*100,1)}%</title></circle>`;});
      out+=`<text x="${centres[layer]}" y="174" text-anchor="middle" fill="${colors.slate}" font-size="11" font-family="Source Sans 3,sans-serif">${esc(layer?t('Long horizon','长周期'):t('Short horizon','短周期'))}</text>`;
    });
    if(state.coupling)out+=`<path d="M222 76h56m-5-4 5 4-5 4M278 96h-56m5-4-5 4 5 4" stroke="#9aadb9" fill="none" stroke-width="1.2"/>`;
    view.innerHTML=out+'</svg>';
  }

  function render() {
    if(!snap||!accountSnap)return;
    $('trade-progress').textContent=`${snap.tick} / ${snap.totalSteps}`;
    $('trade-mode-description').textContent=state.mode==='guided'?t('Set teaching conditions. Watch the intent message before execution begins.','设定好的教学条件：先观察意向消息，再看订单开始执行。'):t('Current intent, evolving conditions. Choose a position without seeing the future path.','当前意向与演化中的市场：根据已知信息选择仓位。');
    document.querySelectorAll('[data-mode]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.mode===state.mode)));
    document.querySelectorAll('[data-fraction]').forEach(b=>b.setAttribute('aria-pressed',String(Number(b.dataset.fraction)===state.fraction)));
    $('trade-price').textContent=fmt(snap.price);const change=100*(snap.price/100-1);$('trade-price-change').textContent=signed(change)+'%';$('trade-price-change').className=tone(change);
    $('trade-equity').textContent=fmt(accountSnap.equity);$('trade-account-return').textContent=signed(accountSnap.returnPct)+'%';$('trade-account-return').className=tone(accountSnap.returnPct);
    $('trade-cash').textContent=fmt(accountSnap.cash);$('trade-unrealized').textContent=signed(accountSnap.unrealizedPnl);$('trade-unrealized').className=tone(accountSnap.unrealizedPnl);
    $('trade-drawdown').textContent=fmt(accountSnap.maxDrawdownPct)+'%';$('trade-exposure').textContent=fmt(accountSnap.grossExposure*100,1)+'%';
    const q=accountSnap.quantity,hasPosition=Math.abs(q)>1e-8;
    $('trade-position-label').textContent=hasPosition?(q>0?t('Long position','多头持仓'):t('Short position','空头持仓')):t('No position','空仓');
    $('trade-position-label').className='trade-position-label '+(hasPosition?(q>0?'trade-up':'trade-down'):'');
    $('trade-position-detail').textContent=hasPosition?t(`${fmt(Math.abs(q),2)} units · average entry ${fmt(accountSnap.averageEntry)}`,`${fmt(Math.abs(q),2)} 单位，持仓均价 ${fmt(accountSnap.averageEntry)}`):t('Initial capital 100,000 virtual units.','初始本金为 100,000 个虚拟单位。');
    document.querySelectorAll('[data-order]').forEach(b=>{const side=b.dataset.order;b.disabled=!!snap.done||!!accountSnap.insolvent||(side==='buy'&&q< -1e-8)||(side==='short'&&q>1e-8)||(side==='sell'&&q<=1e-8)||(side==='cover'&&q>=-1e-8)||(side==='close'&&!hasPosition);});
    $('trade-trade-count').textContent=String(accountSnap.trades.length);
    $('trade-history-empty').hidden=accountSnap.trades.length>0;
    $('trade-history-body').innerHTML=accountSnap.trades.slice(-30).reverse().map(tr=>`<tr><td>${tr.tick}</td><td class="${tr.side==='buy'||tr.side==='cover'?'trade-up':'trade-down'}">${esc(actionName(tr.side))}</td><td>${fmt(tr.price)}</td><td>${fmt(tr.quantity,2)}</td></tr>`).join('');
    $('trade-events').innerHTML=snap.events.slice(-5).reverse().map(event=>`<li class="${event.type==='intent'?'event-intent':''}"><span class="event-time">${event.tick}</span><div><strong>${esc(local(event.title))}</strong><p>${esc(local(event.body))}</p></div></li>`).join('');
    const current=snap.events.filter(e=>e.type==='intent'||e.type==='execution').at(-1);
    $('trade-current-event').hidden=!current;
    if(current&&$('trade-current-event').dataset.eventKey!==current.id+language){
      $('trade-current-event').dataset.eventKey=current.id+language;
      $('trade-current-event').classList.toggle('execution',current.type==='execution');
      $('trade-current-event-time').textContent=String(current.tick);
      $('trade-current-event-title').textContent=local(current.title);
      $('trade-current-event-body').textContent=local(current.body);
    }
    const phase=snap.metrics.phase;$('trade-phase').textContent=phaseName(phase);$('trade-phase-description').textContent=phaseCopy(phase);
    for(const [key,id] of [['fastAlignment','fast'],['slowAlignment','slow']]){
      const value=Math.max(-1,Math.min(1,Number(snap.metrics[key])||0));$('trade-'+id+'-value').textContent=signed(value,2);const bar=$('trade-'+id+'-bar');bar.style.left=(value<0?50+value*50:50)+'%';bar.style.width=Math.abs(value)*50+'%';bar.style.background=value>=0?colors.up:colors.down;
    }
    renderPlayback();
    drawMarket($('trade-chart'));
    drawNetwork();
    const rules=account.review({bars:snap.bars,events:snap.events,done:snap.done}).rules;$('trade-score-rules').textContent=local(rules);
  }

  function renderReview() {
    if(!account||!snap)return;
    const review=account.review({bars:snap.bars,events:snap.events,done:snap.done});state.review=review;
    $('trade-review-progress').textContent=snap.done?t(`Round complete · ${snap.totalSteps} ticks`,`本轮结束，共 ${snap.totalSteps} 个时点`):t(`Round in progress · tick ${snap.tick} of ${snap.totalSteps}`,`阶段复盘：第 ${snap.tick} / ${snap.totalSteps} 个时点`);
    $('trade-review-summary').innerHTML=`<div class="trade-review-score"><div><strong>${review.score}</strong><small> / 100</small></div><div><h3>${esc(local(review.grade))}</h3><p>${esc(t('A costed review of this virtual round.','根据本轮虚拟交易和成本计算。'))}</p></div></div><div class="trade-review-numbers"><div><span>${esc(t('Net return','净收益率'))}</span><strong class="${tone(review.metrics.returnPct)}">${signed(review.metrics.returnPct)}%</strong></div><div><span>${esc(t('Max drawdown','最大回撤'))}</span><strong>${fmt(review.metrics.maxDrawdownPct)}%</strong></div><div><span>${esc(t('Net value','账户净值'))}</span><strong>${fmt(review.metrics.equity)}</strong></div><div><span>${esc(t('Trading fees','累计手续费'))}</span><strong>${fmt(review.metrics.totalFees)}</strong></div></div>`;
    const notes=review.notes||[];
    $('trade-review-notes').innerHTML=`<div class="trade-review-benchmarks"><span>${esc(t('Cash','持有现金'))}<strong>${fmt(review.benchmark.cashReturnPct)}%</strong></span><span>${esc(t('Passive long, with costs','被动做多，含成本'))}<strong>${signed(review.benchmark.passiveReturnPct)}%</strong></span><span>${esc(t('Your return minus passive','相对被动收益'))}<strong>${signed(review.benchmark.edgePct)} ${esc(t('pp','个百分点'))}</strong></span></div><ul class="trade-review-notes">${notes.map(note=>`<li>${esc(local(note))}</li>`).join('')}</ul>`;
    drawMarket($('trade-review-chart'),true);
  }

  function openReview() {
    if(!account)return;stop();
    const dialog=$('trade-review-dialog');if(!dialog.open)dialog.showModal();renderReview();
  }

  $('language').addEventListener('click',()=>{language=language==='en'?'zh':'en';try{localStorage.setItem('econo-language',language);}catch(_){}applyLanguage();});
  $('menu-toggle').addEventListener('click',()=>{const open=$('menu-toggle').getAttribute('aria-expanded')!=='true';$('menu-toggle').setAttribute('aria-expanded',String(open));$('main-nav').classList.toggle('open',open);});
  $('trade-play').addEventListener('click',()=>state.playing?stop():start());
  $('trade-step').addEventListener('click',()=>{stop();advanceOne();});
  $('trade-reset').addEventListener('click',()=>reset());
  $('trade-review').addEventListener('click',openReview);
  $('trade-review-close').addEventListener('click',()=>$('trade-review-dialog').close());
  $('trade-review-resume').addEventListener('click',()=>$('trade-review-dialog').close());
  $('trade-review-retry').addEventListener('click',()=>reset());
  $('trade-review-dialog').addEventListener('click',event=>{if(event.target===$('trade-review-dialog')){const r=event.target.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)event.target.close();}});
  $('trade-scenario').addEventListener('change',()=>reset());
  $('trade-speed').addEventListener('change',()=>{state.speed=Number($('trade-speed').value);if(state.playing)start();});
  $('trade-coupling').addEventListener('change',()=>reset());$('trade-memory').addEventListener('change',()=>reset());$('trade-seed').addEventListener('change',()=>reset());
  $('trade-new-seed').addEventListener('click',()=>{let seed;if(window.crypto?.getRandomValues){const a=new Uint32Array(1);window.crypto.getRandomValues(a);seed=a[0]||1;}else seed=(Date.now()%4294967294)+1;reset({seed});});
  document.querySelectorAll('[data-mode]').forEach(button=>button.addEventListener('click',()=>{if(state.mode!==button.dataset.mode)reset({mode:button.dataset.mode});}));
  document.querySelectorAll('[data-fraction]').forEach(button=>button.addEventListener('click',()=>{state.fraction=Number(button.dataset.fraction);render();}));
  document.querySelectorAll('[data-order]').forEach(button=>button.addEventListener('click',()=>placeOrder(button.dataset.order)));
  window.addEventListener('resize',()=>{if(resizeFrame)window.cancelAnimationFrame(resizeFrame);resizeFrame=window.requestAnimationFrame(()=>{if(snap)render();if($('trade-review-dialog').open)renderReview();});});
  document.addEventListener('visibilitychange',()=>{if(document.hidden&&state.playing)stop();});

  window.TradingLab={state,get engine(){return engine;},get account(){return account;},snapshot:()=>({market:snap,account:accountSnap,playing:state.playing}),start,pause:stop,step:()=>{stop();advanceOne();},advance:n=>{stop();for(let i=0;i<n&&!snap?.done;i++)advanceOne();},reset,trade:placeOrder,review:openReview,render};
  applyLanguage();reset();
})();
