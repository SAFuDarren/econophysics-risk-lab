(function () {
  'use strict';
  const $ = id => document.getElementById(id);
  if (!$('trade-chart')) return;
  const E = window.TradingEngine, A = window.TradingAccount;
  const colors = { navy:'#173e60', up:'#197b70', down:'#b34e43', ink:'#243b4d', slate:'#667785', grid:'#dce5eb' };
  let language = 'en';
  try { language = localStorage.getItem('econo-language') === 'zh' ? 'zh' : 'en'; } catch (_) {}
  const state = { source:new URLSearchParams(location.search).get('source')==='model'?'model':'history',replayId:null, playing:false, speed:.5, showSignals:true, seenEvents:{}, fraction:.5, seed:20261106, scenario:'buy', mode:'guided', coupling:true, memory:true, settled:false, review:null };
  let engine = null, account = null, snap = null, accountSnap = null, timer = null, resizeFrame = null;
  let historyLibrary=null,historyLoading=null,resetSerial=0;
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

  const compactTrading = window.matchMedia('(max-width: 730px)');
  const mobileDock = $('trade-mobile-dock');
  const mobileHeader = $('trade-mobile-header');
  const mobileDialog = $('trade-mobile-dialog');
  const mobilePanels = {
    signals: {element:$('trade-mobile-signals'), label:['Large-order signals','大单提示']},
    activity: {element:$('trade-mobile-activity'), label:['Account activity','账户与成交明细']},
    settings: {element:$('trade-mobile-settings'), label:['Market settings','行情与交易设置']},
  };
  const mobileContent = [
    [mobileHeader, '#language'],
    [$('trade-mobile-progress'), '#trade-progress'],
    [mobileDock, '.trade-playback', '.trade-order-controls', '#trade-feedback'],
    [mobilePanels.signals.element, '#trade-signal-panel', '#trade-history-context'],
    [mobilePanels.activity.element, '.trade-account-metrics', '#trade-position-detail', '.trade-event-panel', '.trade-history-panel'],
    [mobilePanels.settings.element, '.trade-source-tabs', '.trade-setup', '.trade-session-note', '#trade-model-view', '.trade-quickstart', '.trade-order-help', '#trade-rules'],
  ].flatMap(([destination,...selectors])=>selectors.map(selector=>{
    const element=document.querySelector(selector);
    const originalPosition=document.createComment('Original desktop position');
    element.before(originalPosition);
    return {element,destination,originalPosition};
  }));

  function fitTradingControls() {
    const mobile=compactTrading.matches;
    if(!mobile&&mobileDialog.open)mobileDialog.close();
    for(const {element,destination,originalPosition} of mobileContent){
      if(mobile)destination.append(element);
      else originalPosition.after(element);
    }
    document.body.classList.toggle('trade-terminal',mobile);
    mobileHeader.hidden=mobileDock.hidden=!mobile;
  }

  function openMobilePanel(name) {
    const panel=mobilePanels[name];
    for(const {element} of Object.values(mobilePanels))element.hidden=element!==panel.element;
    $('trade-mobile-dialog-title').textContent=t(...panel.label);
    mobileDialog.showModal();
    mobileDialog.scrollTop=0;
    if(name==='settings'&&snap&&state.source==='model')drawNetwork();
  }

  function applyLanguage() {
    document.documentElement.lang = language === 'zh' ? 'zh-CN' : 'en';
    document.querySelectorAll('[data-en]').forEach(el => { el.hidden = language !== 'en'; });
    document.querySelectorAll('[data-zh]').forEach(el => { el.hidden = language !== 'zh'; });
    document.querySelectorAll('option[data-en-label]').forEach(el => { el.textContent = language === 'zh' ? el.dataset.zhLabel : el.dataset.enLabel; });
    $('language').textContent = language === 'zh' ? 'English' : '中文';
    $('language').setAttribute('aria-label', t('Switch to Chinese','切换到英文'));
    mobileDock.setAttribute('aria-label', t('Quick trading controls','快捷交易操作'));
    $('trade-mobile-dialog-close').setAttribute('aria-label',t('Close panel','关闭面板'));
    $('trade-step').setAttribute('aria-label', t('Advance one tick','向前推进一步'));
    $('trade-speed').setAttribute('aria-label', t('Market speed','行情速度'));
    $('trade-review-close').setAttribute('aria-label', t('Close review','关闭复盘'));
    $('trade-chart').setAttribute('aria-label', t('Collective Index candle prices and trading volume','Collective Index 价格K线与成交量'));
    $('trade-review-chart').setAttribute('aria-label', t('Price path with your trade points','行情路径与本人的交易点位'));
    document.title = t('Trading lab | Econophysics Risk Lab','模拟交易 | Econophysics Risk Lab');
    renderSource();
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
    timer = window.setInterval(advanceOne, 2000 / state.speed);
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
    $('trade-speed-note').textContent=t(`${2000/state.speed/1000} s / tick`,`每步 ${2000/state.speed/1000} 秒`);
  }

  function chooseExcerpt(exclude) {
    const choices=historyLibrary.cases.filter(c=>c.id!==exclude);const values=new Uint32Array(1);window.crypto.getRandomValues(values);return choices[values[0]%choices.length].id;
  }
  function loadHistory() {
    if(!historyLoading)historyLoading=fetch('assets/data/historical-replays-v1.json?v=20261106-bridge1').then(r=>{if(!r.ok)throw new Error('Historical data HTTP '+r.status);return r.json();}).then(data=>{window.TradingHistory.validate(data);historyLibrary=data;$('trade-replay').innerHTML=data.cases.map((c,i)=>`<option value="${esc(c.id)}" data-en-label="Excerpt ${String.fromCharCode(65+i)}" data-zh-label="片段 ${String.fromCharCode(65+i)}">${esc(t('Excerpt ','片段 ')+String.fromCharCode(65+i))}</option>`).join('');const requested=new URLSearchParams(location.search).get('case');state.replayId=data.cases.some(c=>c.id===requested)?requested:chooseExcerpt();$('trade-replay').value=state.replayId;return data;});
    return historyLoading;
  }
  function renderSource() {
    const h=state.source==='history';
    document.querySelectorAll('[data-source]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.source===state.source)));
    $('trade-model-scenario').hidden=h;$('trade-model-view').hidden=h;$('trade-history-selector').hidden=!h;$('trade-history-context').hidden=!h;
    $('trade-source-badge').textContent=h?t('Historical replay','真实历史回放'):t('Virtual market','模型虚拟市场');
    $('trade-source-description').textContent=h?t('Original BTC/USDT candles and executed large-order flow. Each step is one real minute.','原始BTC/USDT分钟K线与真实大额成交；每步推进真实1分钟。'):t('A generated market for testing weighted collective dynamics.','由加权集体动力学模型生成行情，用于比较机制。');
    $('trade-instrument-title').textContent=h?'BTC / USDT':'Collective Index';$('trade-instrument-description').textContent=h?t('1-minute historical candles','真实1分钟K线'):t('Fictional instrument','虚拟交易标的');
    $('trade-source-footer').textContent=h?t('Historical prices: Binance public data. Trades and account results are virtual.','历史价格来自Binance公开数据，账户交易与成绩为虚拟结算。'):t('A synthetic market generated by the collective-dynamics model. Outcomes describe this simulation.','本页行情由集体动力学模型生成，成绩仅描述本轮虚拟交易。');
    $('trade-source-rules').textContent=h?t('Historical excerpts are retrospectively selected for a later large move. Signals use only already completed trades. Aggressive buying/selling does not identify an account opening a long/short position. Your virtual fills do not alter the original prices; passive comparison starts at the playable round, excluding the visible warm-up.','历史片段按后续出现大幅变动筛选；提示只使用已经完成的成交。主动买卖不等于已识别某个账户开多或开空。虚拟交易不改变原始价格；被动持仓基准从可交易起点计算，不包含热身图形。'):t('Guided rounds use set conditions; experiment rounds have stochastic execution. You act as a small price taker. Review includes costs and a same-path passive benchmark.','引导体验采用设定条件，自主实验中的订单执行带有随机性。你作为小额参与者接受当前价格；复盘包含成本与同路径被动持仓比较。');
  }

  const flowLights=document.querySelectorAll('[data-flow-lights]');
  const flowStatuses=document.querySelectorAll('[data-flow-state]');

  function renderSignalLights(market) {
    let buy=false,sell=false;
    if(market&&state.showSignals){
      if(market.source==='history'){
        const alerts=market.events.filter(event=>event.type==='large-flow'&&event.tick===market.tick);
        buy=alerts.some(event=>event.direction>0);
        sell=alerts.some(event=>event.direction<0);
      }else{
        buy=market.metrics.programFlow>0;
        sell=market.metrics.programFlow<0;
      }
    }
    for(const lights of flowLights){
      lights.toggleAttribute('data-buy-active',buy);
      lights.toggleAttribute('data-sell-active',sell);
    }
    const message=!state.showSignals?t('Signals off','大单提示已关闭'):
      buy&&sell?t('Large buying and selling this step','当前一步有大额买入和卖出'):
      buy?t('Large buying this step','当前一步有大额买入'):
      sell?t('Large selling this step','当前一步有大额卖出'):
      t('No large-order signal this step','当前一步无大单信号');
    for(const status of flowStatuses)if(status.textContent!==message)status.textContent=message;
  }

  function reset(options={}) {
    stop();renderSignalLights(null);if(window.TradingDebriefView)window.TradingDebriefView.reset();const request=++resetSerial;renderSource();
    if(state.source==='history'&&!historyLibrary){engine=null;account=null;snap=null;accountSnap=null;feedback(b('Loading verified historical candles…','正在加载已核验的历史行情…'));document.querySelectorAll('[data-order]').forEach(b=>{b.disabled=true;});renderPlayback();loadHistory().then(()=>{if(state.source==='history'&&request===resetSerial)reset(options);}).catch(error=>{if(state.source==='history'&&request===resetSerial)feedback(b('Historical data could not load. Reload or choose the mechanism model.','历史数据未能加载，请刷新或选择机理模拟。'),true);console.error(error);});return;}
    if ($('trade-review-dialog').open) $('trade-review-dialog').close();
    state.scenario = options.scenario || $('trade-scenario').value;
    state.mode = options.mode || state.mode;
    const inputSeed = Number($('trade-seed').value);
    state.seed = options.seed ?? (Number.isInteger(inputSeed) && inputSeed >= 1 && inputSeed <= 4294967295 ? inputSeed : 20261106);
    $('trade-seed').value = String(state.seed);
    state.coupling = $('trade-coupling').checked;
    state.memory = $('trade-memory').checked;
    state.settled = false; state.review = null;state.capitalDepleted=false;state.seenEvents={};
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
      engine = state.source==='history'?window.TradingHistory.create(historyLibrary,{caseId:state.replayId,mode:state.mode}):E.create(config);
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
    if(wasPlaying&&state.showSignals&&state.mode==='guided'&&snap.events.some(e=>(e.type==='intent'||e.type==='large-flow')&&e.tick===snap.tick)){stop();feedback(state.source==='history'?b('Large executed flow detected. Choose a position, then continue.','已检测到大额成交，可以选择仓位后继续。'):b('Order intent arrived. Choose a position, then continue.','大单意向已出现，可以选择仓位后继续行情。'));}
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
    const historical=state.source==='history';const margin = {left:12,right:historical?76:58,top:15,bottom:24};
    const chartPrice=n=>fmt(n,historical?0:2);const clock=b=>new Date(b.time+60000).toISOString().slice(11,16);
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
    let svg=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" role="img" aria-label="${esc(t('Known price path and your executions','当前已知行情与交易记录'))}"><title>${esc(historical?t('BTC/USDT price and volume','BTC/USDT价格和成交量'):t('Collective Index price and volume','Collective Index 价格和成交量'))}</title>`;
    for (let j=0;j<5;j++) {
      const val=lo+(hi-lo)*j/4, yy=y(val);
      svg+=`<line x1="${margin.left}" x2="${chartRight}" y1="${yy}" y2="${yy}" stroke="${colors.grid}" stroke-width=".7"/><text x="${chartRight+8}" y="${yy+4}">${chartPrice(val)}</text>`;
    }
    const initial=snap.initialPrice||100;
    if(initial>=lo && initial<=hi) svg+=`<line x1="${margin.left}" x2="${chartRight}" y1="${y(initial)}" y2="${y(initial)}" stroke="#aebec9" stroke-dasharray="3 4" stroke-width=".8"/>`;
    const maxVolume=Math.max(1,...bars.map(b=>b.volume));
    bars.forEach((bar,i)=>{
      const xx=x(i), color=bar.close>=bar.open?colors.up:colors.down;
      const bodyY=Math.min(y(bar.open),y(bar.close)), bodyH=Math.max(1,Math.abs(y(bar.open)-y(bar.close)));
      svg+=`<g><title>${esc(t('Tick','时点'))} ${bar.tick}: ${esc(t('Open','开'))} ${fmt(bar.open)}, ${esc(t('High','高'))} ${fmt(bar.high)}, ${esc(t('Low','低'))} ${fmt(bar.low)}, ${esc(t('Close','收'))} ${fmt(bar.close)}</title><line x1="${xx}" x2="${xx}" y1="${y(bar.high)}" y2="${y(bar.low)}" stroke="${color}" stroke-width="1"/><rect x="${xx-candleWidth/2}" y="${bodyY}" width="${candleWidth}" height="${bodyH}" fill="${color}" rx=".5"/><rect x="${xx-candleWidth/2}" y="${height-margin.bottom-bar.volume/maxVolume*volumeHeight}" width="${candleWidth}" height="${Math.max(.5,bar.volume/maxVolume*volumeHeight)}" fill="${color}" opacity=".30"/></g>`;
    });
    if (bars.length) {
      const last=bars[bars.length-1], yy=y(last.close), color=last.close>=last.open?colors.up:colors.down;
      svg+=`<line x1="${margin.left}" x2="${chartRight}" y1="${yy}" y2="${yy}" stroke="${color}" stroke-width=".8" stroke-dasharray="2 3" opacity=".7"/><rect x="${chartRight+3}" y="${yy-9}" width="${margin.right-5}" height="18" rx="2" fill="${color}"/><text x="${chartRight+margin.right/2}" y="${yy+3.5}" text-anchor="middle" style="fill:white;font-size:10px">${chartPrice(last.close)}</text>`;
      const ticks=[0,Math.floor((bars.length-1)/2),bars.length-1];
      [...new Set(ticks)].forEach(i=>{svg+=`<text x="${x(i)}" y="${height-7}" text-anchor="middle">${historical?clock(bars[i]):bars[i].tick}</text>`;});
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
      $('trade-chart-range').textContent=bars.length?(historical?`${clock(bars[0])}–${clock(bars.at(-1))} UTC · 1m`:t(`Ticks ${firstTick}–${bars.at(-1).tick}`,`时点 ${firstTick}–${bars.at(-1).tick}`)):t('Starting price 100.00','初始价格 100.00');
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
    $('trade-mode-description').textContent=!state.showSignals?t('Signals are off. The market runs without order-message pauses.','大单提示已关闭；行情不会因大单消息自动暂停。'):state.mode==='guided'?t('Pauses when order intent arrives. Choose a position, then continue.','大单意向出现时自动暂停，选择仓位后再继续。'):t('Current intent, evolving conditions. Choose a position without seeing the future path.','当前意向与演化中的市场：根据已知信息选择仓位。');
    $('trade-signal-reading').hidden=state.source!=='history';
    if(state.source==='history')$('trade-mode-description').textContent=!state.showSignals?t('Signals off. Read the original price and volume path.','提示已关闭，可自行观察原始量价变化。'):state.mode==='guided'?t('Pauses on observed large flow. The next candles are still hidden.','检测到大额成交时暂停，后续K线仍未揭晓。'):t('Continuous historical replay with current observed flow.','连续回放真实行情，显示当前已发生的大额成交。');
    document.querySelectorAll('[data-mode]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.mode===state.mode)));
    document.querySelectorAll('[data-fraction]').forEach(b=>b.setAttribute('aria-pressed',String(Number(b.dataset.fraction)===state.fraction)));
    $('trade-price').textContent=fmt(snap.price);const change=100*(snap.price/(snap.initialPrice||100)-1);$('trade-price-change').textContent=signed(change)+'%';$('trade-price-change').className=tone(change);
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
    const visibleEvents=snap.events.filter(e=>state.showSignals||!['intent','execution','completion','large-flow'].includes(e.type));
    for(const event of visibleEvents)if(!(event.id in state.seenEvents))state.seenEvents[event.id]={tick:snap.tick,beforeFirstTrade:accountSnap.trades.length===0};
    $('trade-events').innerHTML=visibleEvents.slice(-5).reverse().map(event=>`<li class="${event.type==='intent'?'event-intent':''}"><span class="event-time">${event.tick}</span><div><strong>${esc(local(event.title))}</strong><p>${esc(local(event.body))}</p></div></li>`).join('');
    const current=state.showSignals?snap.events.filter(e=>['intent','execution','completion','large-flow'].includes(e.type)).at(-1):null;
    $('trade-signal-empty').hidden=!!current;
    $('trade-signal-empty').textContent=state.showSignals?(state.source==='history'?t('Watching completed trades for unusual large buying or selling.','正在根据已完成成交观察异常大额买卖。'):t('Waiting for an announced order. Guided playback will pause when one arrives.','等待已公布的大单意向；引导体验会在提示出现时暂停。')):t('Signals are off. You can turn them on at any time.','提示已关闭，可随时重新打开。');
    $('trade-signal-content').classList.toggle('signals-off',!state.showSignals);
    $('trade-current-event').hidden=!current;
    renderSignalLights(snap);
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
    if(state.source==='model')drawNetwork();
    else{$('trade-observed-buy').textContent=fmt(snap.metrics.buyQuote/10000,0)+t(' × 10k USDT','万USDT');$('trade-observed-sell').textContent=fmt(snap.metrics.sellQuote/10000,0)+t(' × 10k USDT','万USDT');}
    const rules=account.review({bars:snap.bars,events:seenEvents(),done:snap.done,initialPrice:snap.initialPrice||100}).rules;$('trade-score-rules').textContent=local(rules);
  }

  // Record first visibility so enabling hints later cannot change earlier trade information.
  function seenEvents() {
    return snap.events.filter(e=>state.seenEvents[e.id]?.beforeFirstTrade).map(e=>({...e,tick:state.seenEvents[e.id].tick}));
  }

  function renderReview() {
    if(!account||!snap)return;
    const review=account.review({bars:snap.bars,events:seenEvents(),done:snap.done,initialPrice:snap.initialPrice||100});state.review=review;
    $('trade-review-progress').textContent=snap.done?t(`Round complete · ${snap.totalSteps} ticks`,`本轮结束，共 ${snap.totalSteps} 个时点`):t(`Round in progress · tick ${snap.tick} of ${snap.totalSteps}`,`阶段复盘：第 ${snap.tick} / ${snap.totalSteps} 个时点`);
    $('trade-review-summary').innerHTML=`<div class="trade-review-score"><div><strong>${review.score}</strong><small> / 100</small></div><div><h3>${esc(local(review.grade))}</h3><p>${esc(t('The score describes this virtual round. Drawdown is the largest drop from a previous account high.','得分反映本轮虚拟交易。最大回撤指账户净值相对先前高点的最大跌幅。'))}</p></div></div><div class="trade-review-numbers"><div><span>${esc(t('Net return','净收益率'))}</span><strong class="${tone(review.metrics.returnPct)}">${signed(review.metrics.returnPct)}%</strong></div><div><span>${esc(t('Max drawdown','最大回撤'))}</span><strong>${fmt(review.metrics.maxDrawdownPct)}%</strong></div><div><span>${esc(t('Net value','账户净值'))}</span><strong>${fmt(review.metrics.equity)}</strong></div><div><span>${esc(t('Trading fees','累计手续费'))}</span><strong>${fmt(review.metrics.totalFees)}</strong></div></div>`;
    const notes=review.notes||[];
    $('trade-review-notes').innerHTML=`<div class="trade-review-benchmarks"><span>${esc(t('Cash','持有现金'))}<strong>${fmt(review.benchmark.cashReturnPct)}%</strong></span><span>${esc(t('Passive long, with costs','被动做多，含成本'))}<strong>${signed(review.benchmark.passiveReturnPct)}%</strong></span><span>${esc(t('Your return minus passive','相对被动收益'))}<strong>${signed(review.benchmark.edgePct)} ${esc(t('pp','个百分点'))}</strong></span></div><ul class="trade-review-notes">${notes.map(note=>`<li>${esc(local(note))}</li>`).join('')}</ul>`;
    const reveal=$('trade-history-reveal');reveal.hidden=state.source!=='history';
    if(state.source==='history'){
      const r=snap.historicalReview;
      reveal.innerHTML=r?`<h3>${esc(t('The real excerpt','真实片段揭晓'))}</h3><p>BTC / USDT · ${esc(new Date(r.startTime).toISOString().replace('T',' ').slice(0,16))}–${esc(new Date(r.endTime).toISOString().slice(11,16))} UTC</p><p>${esc(t('Primary observed-flow signal: ','主要成交信号：'))}${esc(r.direction>0?t('aggressive buying','主动买入'):t('aggressive selling','主动卖出'))} · ${esc(new Date(r.signalCloseTime).toISOString().slice(11,16))} UTC</p><p>${esc(t('Largest same-direction close-price move over the next 90 minutes: ','随后90分钟最大同向收盘价格变动：'))}${fmt(r.favorableMove*100)}%${esc(t('; adverse close-price move before that point: ','；到达该点前的反向收盘价格变动：'))}${fmt(r.adverseBeforePeak*100)}%。</p><p>${esc(t('This excerpt was selected after observing that move. Compare all earlier signals with your actual trades.','本片段按事后出现的波动筛选。请对照此前全部提示，检查自己的实际交易时机。'))}</p><a href="https://github.com/SAFuDarren/econophysics-risk-lab/tree/main/studies/historical_replay_v1">${esc(t('Original source and selection record','原始来源与筛选记录'))}</a>`:`<p>${esc(t('The original date and later move are revealed after the final candle.','原始日期和后续走势在最后一根K线结束后揭晓。'))}</p>`;
    }
    const completedReplay=state.source==='history'&&snap.done;
    $('trade-review-chart').hidden=completedReplay;
    $('trade-review-mechanism').hidden=!completedReplay;
    if(window.TradingDebriefView)window.TradingDebriefView.render({market:snap,account:accountSnap,language});
    drawMarket($('trade-review-chart'),true);
  }

  function openReview() {
    if(!account)return;stop();
    if(mobileDialog.open)mobileDialog.close();
    const dialog=$('trade-review-dialog');if(!dialog.open)dialog.showModal();renderReview();
  }

  $('language').addEventListener('click',()=>{language=language==='en'?'zh':'en';try{localStorage.setItem('econo-language',language);}catch(_){}applyLanguage();});
  $('menu-toggle').addEventListener('click',()=>{const open=$('menu-toggle').getAttribute('aria-expanded')!=='true';$('menu-toggle').setAttribute('aria-expanded',String(open));$('main-nav').classList.toggle('open',open);});
  $('trade-play').addEventListener('click',()=>state.playing?stop():start());
  $('trade-step').addEventListener('click',()=>{stop();advanceOne();});
  document.querySelectorAll('[data-trade-panel]').forEach(button=>{
    button.addEventListener('click',()=>openMobilePanel(button.dataset.tradePanel));
  });
  $('trade-mobile-dialog-close').addEventListener('click',()=>mobileDialog.close());
  $('trade-reset').addEventListener('click',()=>reset());
  $('trade-review').addEventListener('click',openReview);
  $('trade-review-mechanism').addEventListener('click',()=>{
    $('trade-theory-review').focus();
    $('trade-theory-review').scrollIntoView({block:'start'});
  });
  $('trade-review-close').addEventListener('click',()=>$('trade-review-dialog').close());
  $('trade-review-resume').addEventListener('click',()=>$('trade-review-dialog').close());
  $('trade-review-retry').addEventListener('click',()=>reset());
  $('trade-review-dialog').addEventListener('click',event=>{if(event.target===$('trade-review-dialog')){const r=event.target.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)event.target.close();}});
  document.querySelectorAll('[data-source]').forEach(b=>b.addEventListener('click',()=>{if(state.source!==b.dataset.source){state.source=b.dataset.source;reset();}}));
  $('trade-replay').addEventListener('change',()=>{state.replayId=$('trade-replay').value;reset();});
  $('trade-history-next').addEventListener('click',()=>{if(historyLibrary){state.replayId=chooseExcerpt(state.replayId);$('trade-replay').value=state.replayId;reset();}});
  $('trade-scenario').addEventListener('change',()=>reset());
  $('trade-speed').addEventListener('change',()=>{state.speed=Number($('trade-speed').value);if(state.playing)start();});
  $('trade-signals').addEventListener('change',()=>{state.showSignals=$('trade-signals').checked;feedback(state.showSignals?b('Large-order signals are on.','大单提示已开启。'):b('Large-order signals are off. Market conditions are unchanged.','大单提示已关闭，市场设置保持原样。'));render();});
  $('trade-coupling').addEventListener('change',()=>reset());$('trade-memory').addEventListener('change',()=>reset());$('trade-seed').addEventListener('change',()=>reset());
  $('trade-new-seed').addEventListener('click',()=>{let seed;if(window.crypto?.getRandomValues){const a=new Uint32Array(1);window.crypto.getRandomValues(a);seed=a[0]||1;}else seed=(Date.now()%4294967294)+1;reset({seed});});
  document.querySelectorAll('[data-mode]').forEach(button=>button.addEventListener('click',()=>{if(state.mode!==button.dataset.mode)reset({mode:button.dataset.mode});}));
  document.querySelectorAll('[data-fraction]').forEach(button=>button.addEventListener('click',()=>{state.fraction=Number(button.dataset.fraction);render();}));
  document.querySelectorAll('[data-order]').forEach(button=>button.addEventListener('click',()=>placeOrder(button.dataset.order)));
  window.addEventListener('resize',()=>{if(resizeFrame)window.cancelAnimationFrame(resizeFrame);resizeFrame=window.requestAnimationFrame(()=>{if(snap)render();if($('trade-review-dialog').open)renderReview();});});
  document.addEventListener('visibilitychange',()=>{if(document.hidden&&state.playing)stop();});

  window.TradingLab={state,get engine(){return engine;},get account(){return account;},snapshot:()=>({market:snap,account:accountSnap,playing:state.playing}),start,pause:stop,step:()=>{stop();advanceOne();},advance:n=>{stop();for(let i=0;i<n&&!snap?.done;i++)advanceOne();},reset,trade:placeOrder,review:openReview,render};
  compactTrading.addEventListener('change',fitTradingControls);
  fitTradingControls();
  applyLanguage();reset();
})();
