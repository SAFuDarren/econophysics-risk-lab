/* Synthetic collective market: weighted interacting fast/slow decisions.
 * Deterministic random streams; no DOM, network requests, or future price tape.
 * This is a mechanism experiment, not a fitted or validated market predictor.
 */
(function (root, factory) {
  'use strict';
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.TradingEngine = api;
}(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  const VERSION = '1.0.0';
  const DEFAULTS = Object.freeze({seed: 5253, scenario: 'buy', mode: 'guided', steps: 180,
    coupling: 0.55, memory: 0.75, weighting: 'heterogeneous', externalOrders: true, nodes: 48, initialPrice: 100});
  const TEXT = {
    buy: {title: {en: 'A large buyer arrives', zh: '大额买入出现'},
      description: {en: 'A revealed buying plan meets a market that can follow, absorb or resist it.', zh: '买入计划出现，观察跟随、承接与价格响应。'}},
    sell: {title: {en: 'A large seller arrives', zh: '大额卖出出现'},
      description: {en: 'A revealed selling plan tests market support and your position timing.', zh: '卖出计划出现，观察承接变化与仓位时机。'}},
    split: {title: {en: 'Small orders, one persistent plan', zh: '小单背后的持续计划'},
      description: {en: 'A parent order is executed in small pieces while directional pressure accumulates.', zh: '母单分批执行，观察同向力量如何跨时间积累。'}},
    turn: {title: {en: 'From alignment to a contest', zh: '从一致到分歧'},
      description: {en: 'An initially aligned market later faces a newly revealed opposing program.', zh: '最初的同向力量，随后面对新出现的反向交易计划。'}}
  };
  const SCENARIOS = Object.freeze(Object.keys(TEXT).map(id => Object.freeze({id,
    title: Object.freeze(TEXT[id].title), description: Object.freeze(TEXT[id].description)})));
  const PLANS = {
    buy: [{id:'buyer', announce:18, start:24, duration:36, sign:1, child:650}],
    sell: [{id:'seller', announce:18, start:24, duration:36, sign:-1, child:650}],
    split: [{id:'split-buyer', announce:18, start:24, duration:84, sign:1, child:225}],
    turn: [{id:'first-buyer', announce:18, start:24, duration:36, sign:1, child:600},
      {id:'new-seller', announce:75, start:82, duration:38, sign:-1, child:750}]
  };
  const PARAMETERS = Object.freeze({fastInteraction:0.72, slowInteraction:0.65,
    fastInertia:0.24, slowInertia:0.32, slowUpdateProbability:0.14,
    adaptationRate:0.055, fastAdaptation:0.95, slowAdaptation:0.35,
    inverseTemperature:1.5, activeProbability:0.58, backgroundScale:1200,
    residualSigma:0.00115, impactBound:0.009, impactScale:0.34,
    liquidityRecovery:0.075, liquidityFloor:0.35, liquidityCeiling:1.8,
    maximumAbsLogReturn:0.018, minimumPrice:0.01});
  const copy = obj => JSON.parse(JSON.stringify(obj));
  const clamp = (x,lo,hi) => Math.max(lo,Math.min(hi,x));
  function hashSeed(value) {
    const s=String(value); let h=2166136261;
    for(let i=0;i<s.length;i++){h^=s.charCodeAt(i);h=Math.imul(h,16777619);}
    return h>>>0;
  }
  function random(seed) {
    let state=seed>>>0;
    return function () {state=(state+0x6D2B79F5)>>>0; let t=state;
      t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);
      return ((t^(t>>>14))>>>0)/4294967296;};
  }
  function normal(rng) {const u=Math.max(rng(),1e-15);return Math.sqrt(-2*Math.log(u))*Math.cos(2*Math.PI*rng());}
  function validated(options) {
    if(options==null) options={};
    if(typeof options!=='object'||Array.isArray(options))throw new TypeError('Configuration must be an object');
    const c=Object.assign({},DEFAULTS,options);
    if(!Object.prototype.hasOwnProperty.call(PLANS,c.scenario))throw new RangeError('Unknown scenario');
    if(!['guided','experiment'].includes(c.mode))throw new RangeError('Unknown mode');
    if(!['equal','heterogeneous'].includes(c.weighting))throw new RangeError('Unknown weighting');
    if(typeof c.externalOrders!=='boolean')throw new TypeError('externalOrders must be boolean');
    if(!Number.isInteger(c.steps)||c.steps<1||c.steps>5000)throw new RangeError('steps must be an integer in [1,5000]');
    for(const key of ['coupling','memory'])if(!Number.isFinite(c[key])||c[key]<0||c[key]>2)throw new RangeError(key+' must be in [0,2]');
    // A fixed population and starting price keep all scenarios/grades comparable.
    c.nodes=DEFAULTS.nodes;c.initialPrice=DEFAULTS.initialPrice;
    if(!['string','number'].includes(typeof c.seed)||(typeof c.seed==='number'&&!Number.isFinite(c.seed)))throw new TypeError('seed must be a finite number or string');
    return Object.freeze(c);
  }
  function topology(n,rng,layer) {
    const edges=[]; const seen=new Set(); const neighbors=Array.from({length:n},()=>[]);
    function add(a,b){if(a===b)return;const low=Math.min(a,b),high=Math.max(a,b),key=low+':'+high;
      if(seen.has(key))return;seen.add(key);neighbors[a].push(b);neighbors[b].push(a);
      edges.push({source:low,target:high,layer,weight:1});}
    for(let i=0;i<n;i++){add(i,(i+1)%n);add(i,(i+2)%n);add(i,Math.floor(rng()*n));}
    return {edges,neighbors};
  }
  function create(options) {
    const config=validated(options);
    let tick,price,bars,events,nodes,fastGraph,slowGraph,liquidity,previousAlignment,metrics;
    let graphRng,stateRng,noiseRng,orderRng,wicksRng,plans;
    function emit(id,type,title,body){events.push({id,tick,type,title,body});}
    function reset() {
      const base=hashSeed(config.seed);
      graphRng=random(base^0x641A4B9D);stateRng=random(base^0x87B913D7);
      noiseRng=random(base^0x31B582D1);orderRng=random(base^0x428DDC71);wicksRng=random(base^0x144C901B);
      tick=0;price=100;bars=[];events=[];liquidity=1;previousAlignment=0;
      const weights=Array.from({length:config.nodes},()=>{const g=normal(graphRng);return config.weighting==='equal'?1:Math.exp(.65*g);});
      const total=weights.reduce((a,b)=>a+b,0);
      nodes=weights.map((w,i)=>({id:i,x:.5+.42*Math.cos(2*Math.PI*i/config.nodes),
        y:.5+.42*Math.sin(2*Math.PI*i/config.nodes),weight:w/total,
        fast:stateRng()<.5?-1:1,slow:stateRng()<.5?-1:1,active:false,trace:0}));
      fastGraph=topology(config.nodes,graphRng,'fast');slowGraph=topology(config.nodes,graphRng,'slow');
      plans=(config.externalOrders?PLANS[config.scenario]:[]).map(p=>Object.assign({},p,{executed:0,announced:false,started:false,completed:false}));
      const initial=nodes.reduce((sum,n)=>sum+n.weight*n.fast,0);previousAlignment=Math.abs(initial);
      metrics={pressure:0,coherence:Math.abs(initial),liquidity:1,phase:'mixed',fastAlignment:initial,
        slowAlignment:nodes.reduce((sum,n)=>sum+n.weight*n.slow,0)};
      emit('session', 'session', {en:config.mode==='guided'?'Guided model market':'Model market experiment',zh:config.mode==='guided'?'引导式虚拟市场':'自主市场实验'},
        {en:config.mode==='guided'?'Teaching conditions are set. Large-order messages reveal intent, not a guaranteed price or profit.':
          'Only current messages are revealed. Market response and order execution remain uncertain.',
        zh:config.mode==='guided'?'本局采用教学条件。大单消息表示交易意向，未来价格与盈利不作保证。':'只显示当前可知的消息，市场响应和订单执行仍有不确定性。'});
      return snapshot();
    }
    function neighborMean(graph,i,states) {
      let numerator=0,denominator=0;
      for(const j of graph.neighbors[i]){numerator+=nodes[j].weight*states[j];denominator+=nodes[j].weight;}
      return denominator?numerator/denominator:0;
    }
    function orderStep() {
      let quantity=0,signed=0,publicIntent=0;
      for(const p of plans) {
        if(tick===p.announce) {
          p.announced=true;
          const buy=p.sign>0;
          emit(p.id+'-intent','intent', {en:buy?'Large buying plan announced':'Large selling plan announced',zh:buy?'大额买入计划出现':'大额卖出计划出现'},
            {en:p.duration>60?'A participant reports a plan to execute many small same-direction orders. Execution has not started.':'A participant reports a sizeable directional program. Execution has not started.',
            zh:p.duration>60?'有参与者计划分批执行多笔同方向小单，目前尚未开始。':'有参与者计划执行较大规模的同方向交易，目前尚未开始。'});
        }
        // Draw one random execution amount for each plan on every tick, including inactive ticks.
        const u=orderRng(),v=orderRng();
        if(p.announced&&!p.completed&&tick>=p.announce)publicIntent+=p.sign*.1;
        if(tick>=p.start&&tick<p.start+p.duration) {
          if(!p.started){p.started=true;emit(p.id+'-start','execution',
            {en:p.sign>0?'Buy program is executing':'Sell program is executing',zh:p.sign>0?'买入计划开始执行':'卖出计划开始执行'},
            {en:'Orders are now entering the market. Watch price response as well as direction.',zh:'订单已进入市场，同时观察交易方向和价格响应。'});}
          const fill=config.mode==='guided'?p.child*(.85+.3*u):(v<.22?0:p.child*(.3+1.1*u));
          quantity+=fill;signed+=p.sign*fill;p.executed+=fill;
        }
        if(tick===p.start+p.duration&&!p.completed) {
          p.completed=true;
          emit(p.id+'-complete','completion',{en:'Announced program has ended',zh:'已公布的交易计划结束'},
            {en:'That program is no longer supplying child orders. Other market participants can continue trading.',zh:'该计划不再继续产生子单，其他参与者仍可继续交易。'});
        }
      }
      return {quantity,signed,publicIntent:clamp(publicIntent,-.2,.2)};
    }
    function step() {
      if(tick>=config.steps)return snapshot();
      tick++;
      const order=orderStep();
      const oldFast=nodes.map(n=>n.fast),oldSlow=nodes.map(n=>n.slow);
      // Revealed intent/current program fills precede the background decisions within this tick.
      const executionField=.85*order.signed/(order.quantity+PARAMETERS.backgroundScale);
      const intentField=config.mode==='guided'?order.publicIntent:order.publicIntent*.3;
      const nextFast=[],nextSlow=[],active=[];
      for(let i=0;i<nodes.length;i++) {
        const n=nodes[i],fastU=stateRng(),slowUpdateU=stateRng(),slowSignU=stateRng(),activeU=stateRng();
        const localFast=neighborMean(fastGraph,i,oldFast),localSlow=neighborMean(slowGraph,i,oldSlow);
        const fatigue=PARAMETERS.fastAdaptation*config.memory*n.trace;
        const fastField=PARAMETERS.fastInteraction*localFast+config.coupling*oldSlow[i]+
          PARAMETERS.fastInertia*config.memory*oldFast[i]-fatigue+executionField+intentField;
        const fastProbability=.5*(1+Math.tanh(PARAMETERS.inverseTemperature*fastField));
        nextFast[i]=fastU<fastProbability?1:-1;
        const slowField=PARAMETERS.slowInteraction*localSlow+.55*config.coupling*oldFast[i]+
          PARAMETERS.slowInertia*config.memory*oldSlow[i]-PARAMETERS.slowAdaptation*config.memory*n.trace+.25*executionField;
        const slowProbability=.5*(1+Math.tanh(PARAMETERS.inverseTemperature*slowField));
        nextSlow[i]=slowUpdateU<PARAMETERS.slowUpdateProbability?(slowSignU<slowProbability?1:-1):oldSlow[i];
        active[i]=activeU<PARAMETERS.activeProbability;
      }
      let volume=order.quantity,flow=order.signed,fastMean=0,slowMean=0,flippedWeight=0;
      for(let i=0;i<nodes.length;i++) {
        const n=nodes[i]; if(nextFast[i]!==n.fast)flippedWeight+=n.weight;
        n.fast=nextFast[i];n.slow=nextSlow[i];n.active=active[i];
        n.trace=(1-PARAMETERS.adaptationRate)*n.trace+PARAMETERS.adaptationRate*n.fast;
        fastMean+=n.weight*n.fast;slowMean+=n.weight*n.slow;
        if(n.active){const q=PARAMETERS.backgroundScale*n.weight;volume+=q;flow+=q*n.fast;}
      }
      const pressure=volume>0?clamp(flow/volume,-1,1):0;
      const alignment=Math.abs(fastMean),change=alignment-previousAlignment;
      let phase='mixed';
      if(alignment>=.22&&change>.025)phase='forming';
      else if(previousAlignment>=.22&&change<-.025)phase='fragmenting';
      else if(alignment>=.42)phase='holding';
      // Accommodation adapts; this is a positive synthetic state, not measured book depth.
      const targetLiquidity=config.mode==='guided'?1.1:1.3;
      liquidity=clamp(liquidity+PARAMETERS.liquidityRecovery*(targetLiquidity-liquidity)-.065*Math.abs(pressure)+.04*normal(noiseRng),
        PARAMETERS.liquidityFloor,PARAMETERS.liquidityCeiling);
      const residual=PARAMETERS.residualSigma*normal(noiseRng);
      const impact=PARAMETERS.impactBound*Math.tanh(PARAMETERS.impactScale*(flow/PARAMETERS.backgroundScale)/liquidity);
      const logReturn=clamp(impact+residual,-PARAMETERS.maximumAbsLogReturn,PARAMETERS.maximumAbsLogReturn);
      const open=price;price=Math.max(PARAMETERS.minimumPrice,open*Math.exp(logReturn));
      const upper=.00025+.0007*wicksRng(),lower=.00025+.0007*wicksRng();
      const high=Math.max(open,price)*Math.exp(upper),low=Math.min(open,price)*Math.exp(-lower);
      bars.push({tick,open,high,low,close:price,volume,flow,pressure,phase});
      metrics={pressure,coherence:clamp(alignment,0,1),liquidity,phase,fastAlignment:clamp(fastMean,-1,1),slowAlignment:clamp(slowMean,-1,1),
        switching:clamp(flippedWeight,0,1),alignmentChange:change};
      if(phase==='fragmenting'&&metrics.coherence<.55&&previousAlignment>=.55&&
        !events.some(e=>e.id==='alignment-break'))emit('alignment-break','state',
          {en:'Directional agreement is weakening',zh:'同向一致正在减弱'},
          {en:'The fast decision layer is losing alignment. This is a current model-state observation, not a price forecast.',zh:'快速决策层的方向一致性正在下降。这是当前模型状态，并非价格预测。'});
      previousAlignment=alignment;
      return snapshot();
    }
    function snapshot() {
      const crossEdges=config.coupling===0?[]:nodes.flatMap(n=>[
        {source:n.id,target:n.id,sourceLayer:'slow',targetLayer:'fast',layer:'cross',weight:config.coupling},
        {source:n.id,target:n.id,sourceLayer:'fast',targetLayer:'slow',layer:'cross',weight:.55*config.coupling}]);
      const edges=fastGraph.edges.concat(slowGraph.edges,crossEdges);
      return copy({tick,totalSteps:config.steps,done:tick>=config.steps,price,bars,events,metrics,
        network:{nodes:nodes.map(({trace,...n})=>n),edges}});
    }
    reset();
    return {step,snapshot,reset,config};
  }
  function simulate(options) {const engine=create(options);let s=engine.snapshot();while(!s.done)s=engine.step();return s;}
  function covarianceVariance(covariance,weights) {
    if(!Array.isArray(weights)||!Array.isArray(covariance)||covariance.length!==weights.length)throw new TypeError('Invalid covariance dimensions');
    let total=0;
    for(let i=0;i<weights.length;i++){
      if(!Number.isFinite(weights[i])||!Array.isArray(covariance[i])||covariance[i].length!==weights.length)throw new TypeError('Invalid covariance input');
      for(let j=0;j<weights.length;j++){
        if(!Number.isFinite(covariance[i][j]))throw new TypeError('Covariance must be finite');
        total+=weights[i]*weights[j]*covariance[i][j];
      }
    }
    return total;
  }
  return Object.freeze({version:VERSION,scenarios:SCENARIOS,create,simulate,
    defaults:DEFAULTS,parameters:PARAMETERS,
    math:Object.freeze({covarianceVariance}),
    configuration:()=>copy({version:VERSION,defaults:DEFAULTS,parameters:PARAMETERS,plans:PLANS,
      evidence:'Synthetic educational mechanism, not fitted market parameters',
      pricing:'Bounded signed-flow response plus independent residual; player is a price taker'})});
}));
