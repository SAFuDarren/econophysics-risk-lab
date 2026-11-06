/* Virtual-account accounting. Pure JavaScript, shared by the page and acceptance tests. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.TradingAccount=api;})(typeof globalThis!=='undefined'?globalThis:this,function(){
 'use strict';
 const EPS=1e-9;
 const copy=x=>JSON.parse(JSON.stringify(x));
 const msg=(en,zh)=>({en,zh});
 function create(options={}){
  const initialCash=options.initialCash??100000,feeBps=options.feeBps??5,slippageBps=options.slippageBps??2,maxLeverage=options.maxLeverage??1;
  if(!Number.isFinite(initialCash)||initialCash<=0||!Number.isFinite(feeBps)||feeBps<0||feeBps>100||!Number.isFinite(slippageBps)||slippageBps<0||slippageBps>100||!Number.isFinite(maxLeverage)||maxLeverage<=0||maxLeverage>2)throw new RangeError('Invalid virtual-account configuration');
  const fee=feeBps/10000,slip=slippageBps/10000;
  let cash=initialCash,quantity=0,averageEntry=0,entryFees=0,realizedPnl=0,totalFees=0,lastPrice=100,lastTick=-1,peak=initialCash,maxDrawdownPct=0,insolvent=false,liquidated=false;
  const history=[],trades=[];
  function equity(price=lastPrice){return cash+quantity*price;}
  function valid(price,tick){return Number.isFinite(price)&&price>0&&Number.isInteger(tick)&&tick>=0&&tick>=lastTick;}
  function record(price,tick){
   lastPrice=price;lastTick=tick;const eq=equity();peak=Math.max(peak,eq);maxDrawdownPct=Math.max(maxDrawdownPct,100*(peak-eq)/peak);
   const point={tick,price,equity:eq,cash,quantity};if(history.length&&history[history.length-1].tick===tick)history[history.length-1]=point;else history.push(point);
   if(eq<=0)insolvent=true;
  }
  function snapshot(){const eq=equity(),unrealizedPnl=quantity*(lastPrice-averageEntry);return copy({initialCash,cash,quantity,averageEntry,equity:eq,unrealizedPnl,realizedPnl,totalFees,returnPct:100*(eq/initialCash-1),maxDrawdownPct,grossExposure:Math.abs(quantity*lastPrice)/Math.max(eq,EPS),history,trades,lastPrice,insolvent,liquidated,feeBps,slippageBps,maxLeverage});}
  function reject(message){return {ok:false,message,state:snapshot()};}
  function execute(side,units,price,tick,forced=false){
   const buying=side==='buy'||side==='cover',execution=price*(buying?1+slip:1-slip),cost=units*execution*fee,delta=buying?units:-units,closing=quantity!==0&&Math.sign(delta)!==Math.sign(quantity);
   let gross=0,netClosed=0;
   if(closing){
    const oldAbs=Math.abs(quantity);gross=units*(execution-averageEntry)*Math.sign(quantity);const allocated=entryFees*units/oldAbs;netClosed=gross-cost-allocated;entryFees-=allocated;realizedPnl+=gross-cost;
   }else{
    const oldAbs=Math.abs(quantity);averageEntry=(averageEntry*oldAbs+execution*units)/(oldAbs+units);entryFees+=cost;realizedPnl-=cost;
   }
   cash-=delta*execution+cost;quantity+=delta;totalFees+=cost;
   if(Math.abs(quantity)<EPS){quantity=0;averageEntry=0;entryFees=0;}
   const item={id:trades.length+1,tick,side,quantity:units,price:execution,midPrice:price,fees:cost,isClosing:closing,realizedPnl:closing?gross-cost:-cost,roundTripPnl:closing?netClosed:null,grossRealizedPnl:gross,forced};trades.push(item);record(price,tick);item.cash=cash;item.equity=equity();
   return {ok:true,message:forced?msg('Position automatically closed at the maintenance limit.','持仓触及维持保证金线，已自动平仓。'):msg('Order filled.','订单已成交。'),trade:copy(item),state:snapshot()};
  }
  function mark(price,tick){
   if(!valid(price,tick))throw new RangeError('A mark needs a positive price and chronological integer tick');
   record(price,tick);
   if(quantity!==0&&equity()<=.25*Math.abs(quantity*price)){
    liquidated=true;execute(quantity>0?'sell':'cover',Math.abs(quantity),price,tick,true);
   }
   return snapshot();
  }
  function trade(order={}){
   const {side,price,tick}=order;let fraction=order.fraction??1;
   if(!valid(price,tick))return reject(msg('Use the current valid market price.','请使用当前有效行情价格。'));
   if(!['buy','sell','short','cover','close'].includes(side)||!Number.isFinite(fraction)||fraction<=0||fraction>1)return reject(msg('Choose a valid action and size.','请选择有效的交易方向和比例。'));
   mark(price,tick);
   if(insolvent)return reject(msg('This account has no remaining equity. Start a new round.','账户净值已耗尽，请开始新一局。'));
   if(side==='close'){
    if(quantity===0)return reject(msg('There is no open position.','当前没有持仓。'));
    return execute(quantity>0?'sell':'cover',Math.abs(quantity),price,tick);
   }
   if(side==='sell'||side==='cover'){
    if((side==='sell'&&quantity<=0)||(side==='cover'&&quantity>=0))return reject(side==='sell'?msg('There is no long position to sell.','当前没有可卖出的多头持仓。'):msg('There is no short position to cover.','当前没有可平的空头持仓。'));
    return execute(side,Math.abs(quantity)*fraction,price,tick);
   }
   if((side==='buy'&&quantity<0)||(side==='short'&&quantity>0))return reject(msg('Close the opposite position before opening this side.','请先平掉反向持仓，再开新方向。'));
   const eq=equity(),capacity=maxLeverage*eq-Math.abs(quantity*price);
   if(capacity<=EPS)return reject(msg('The position has reached the exposure limit.','持仓已达到风险敞口上限。'));
   const execution=price*(side==='buy'?1+slip:1-slip),friction=Math.abs(execution-price)+fee*execution;
   let units=fraction*capacity/(price+maxLeverage*friction);
   if(side==='buy'&&maxLeverage<=1)units=Math.min(units,cash/(execution*(1+fee)));
   if(!Number.isFinite(units)||units<=EPS)return reject(msg('There is not enough available equity.','可用净值不足。'));
   return execute(side,units,price,tick);
  }
  function close(order){return trade({...order,side:'close',fraction:1});}
  function review(context={}){
   const s=snapshot(),bars=(context.bars||[]).filter(b=>Number.isFinite(b.close)&&b.close>0&&b.tick<=lastTick);const p0=Number.isFinite(context.initialPrice)&&context.initialPrice>0?context.initialPrice:bars.length?(bars[0].open||bars[0].close):100,p1=s.lastPrice;
   const passiveUnits=initialCash/(p0*(1+slip)*(1+fee)),passiveValue=passiveUnits*p1*(context.done===true?(1-slip)*(1-fee):1),passiveReturnPct=100*(passiveValue/initialCash-1);
   const score=Math.max(0,Math.min(100,Math.round(50+40*Math.tanh(s.returnPct/5)-20*Math.min(s.maxDrawdownPct/10,1))));
   const closed=trades.filter(t=>t.isClosing),winRate=closed.length?100*closed.filter(t=>t.roundTripPnl>0).length/closed.length:0;
   const notes=[];
   if(!trades.length)notes.push(msg('You stayed in cash. Compare the path and decide which information would have justified a position.','本局保持空仓。回看行情，判断哪些已知信息足以支持你开仓。'));
   else{
    notes.push(msg('The chart marks your actual entries and exits. Inspect the event information available at those times.','图上标出了实际进出场点，请对照当时已发布的事件信息复盘。'));
    if(s.returnPct>0)notes.push(msg('Your gain remains positive after fees and slippage. Use the trade markers to locate the part of the move you captured.','本局扣除手续费和滑点后仍盈利。对照交易标记，检查主要收益来自哪一段行情。'));
    if(s.maxDrawdownPct>5)notes.push(msg('The largest equity decline exceeded 5%. Compare the same decision with a smaller position.','最大净值回撤超过5%，可重试并比较较小仓位下的同一决策。'));
    if(liquidated)notes.push(msg('An adverse move triggered the maintenance rule. The close is included in your trade record and costs.','不利行情触发了维持保证金规则，强制平仓及成本已计入交易记录。'));
   }
   const events=(context.events||[]).filter(e=>e.tick<=lastTick);
   if(events.length&&trades.length){const first=trades[0].tick,known=events.filter(e=>e.tick<=first).length;notes.push(msg(`At your first trade, ${known} event message${known===1?' was':'s were'} already visible.`,`首次交易时，已有${known}条事件消息可见。`));}
   return copy({score,grade:score>=80?msg('Strong execution','交易表现稳健'):score>=65?msg('Positive execution','交易表现良好'):score>=45?msg('Mixed execution','仍有改进空间'):msg('Review risk and timing','复盘风险与时机'),metrics:{returnPct:s.returnPct,maxDrawdownPct:s.maxDrawdownPct,totalFees:s.totalFees,trades:trades.length,winRate,grossExposure:s.grossExposure,equity:s.equity,initialCash},benchmark:{cashReturnPct:0,passiveReturnPct,edgePct:s.returnPct-passiveReturnPct,settled:context.done===true},notes,rules:msg('Score = clip(50 + 40 tanh(net return % / 5) − 20 min(max drawdown % / 10, 1), 0, 100). Virtual execution: 5 bp fee and 2 bp slippage by default; opening gross exposure up to 1× equity; automatic close below 25% equity/gross exposure. Passive benchmark is marked to market during the round and closed with exit costs at the end.','得分=截断至0–100的[50+40 tanh(净收益率%/5)−20 min(最大回撤%/10,1)]。默认每笔手续费5基点、滑点2基点；开仓总敞口不超过净值1倍；净值低于总敞口25%时自动平仓。持有基准盘中按市价估值，收盘平仓时扣除退出成本。')});
  }
  return {trade,mark,snapshot,close,review};
 }
 return {version:'1.0.0',create};
});
