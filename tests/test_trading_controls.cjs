/* Browser acceptance for human-paced playback and optional order information.
 * Uses Playwright's controlled clock to verify real timer intervals exactly.
 * Environment variables are shared with test_trading_browser.cjs.
 */
'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE_PATH||'playwright');
const base=process.env.TRADING_BASE_URL||'http://127.0.0.1:8876/';
const out=path.resolve(process.env.TRADING_QA_OUTPUT||'.runs/trading-controls');
fs.mkdirSync(out,{recursive:true});
const checks=[],errors=[];
function check(value,label){assert.ok(value,label);checks.push(label);}
(async()=>{
 const options={headless:true};if(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE)options.executablePath=process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE;
 const browser=await chromium.launch(options);
 try{
  const context=await browser.newContext({viewport:{width:1440,height:1040},reducedMotion:'reduce'});
  await context.addInitScript(()=>localStorage.setItem('econo-language','zh'));
  const page=await context.newPage();await page.clock.install({time:new Date('2026-11-06T00:00:00Z')});await page.clock.pauseAt(new Date('2026-11-06T00:00:01Z'));
  page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400)errors.push(r.status()+' '+r.url());});
  await page.goto(new URL('trading.html',base).href);await page.waitForFunction(()=>window.TradingLab?.account);
  const snapshot=()=>page.evaluate(()=>TradingLab.snapshot());
  check(await page.locator('#trade-speed').inputValue()==='0.5','Default speed is 0.5×');
  check((await page.locator('#trade-speed-note').innerText()).includes('4'),'Default delay is visibly four seconds');
  check(await page.locator('#trade-signals').isChecked(),'Signals start enabled');
  await page.locator('#trade-play').click();await page.clock.runFor(3999);check((await snapshot()).market.tick===0,'Default waits four seconds per tick');
  await page.clock.runFor(1);check((await snapshot()).market.tick===1,'Default interval advances at four seconds');
  await page.locator('#trade-speed').selectOption('0.25');await page.clock.runFor(7999);check((await snapshot()).market.tick===1,'Quarter speed waits eight seconds');
  await page.clock.runFor(1);check((await snapshot()).market.tick===2,'Quarter speed advances at eight seconds');
  await page.locator('[data-order="buy"]').click();check((await snapshot()).account.quantity>0,'Orders remain usable during slow playback');
  await page.locator('#trade-speed').selectOption('4');await page.clock.runFor(500);check((await snapshot()).market.tick===3,'Changing speed while running reschedules playback');
  await page.locator('#trade-play').click();await page.clock.runFor(60000);check((await snapshot()).market.tick===3,'Pause stops clock-driven market changes');
  await page.evaluate(()=>TradingLab.advance(14));
  const before=await snapshot();await page.locator('#trade-signals').uncheck();const after=await snapshot();
  check(JSON.stringify(before.market)===JSON.stringify(after.market)&&JSON.stringify(before.account)===JSON.stringify(after.account),'Signal toggle preserves market and account');
  await page.locator('#trade-play').click();await page.clock.runFor(500);
  check((await snapshot()).market.tick===18&&(await snapshot()).playing,'Hidden intent does not trigger a revealing pause');
  check(await page.locator('#trade-current-event').isHidden(),'Hidden intent is absent from dedicated panel');
  check(!(await page.locator('#trade-events').innerText()).includes('大额买入计划'),'Hidden intent is absent from event tape');
  check(!(await page.locator('#trade-feedback').innerText()).includes('意向已出现'),'Hidden intent does not leak through order feedback');
  await page.clock.runFor(3000);check((await snapshot()).market.tick===24,'Playback continues through execution with signals off');
  check(!(await page.locator('#trade-events').innerText()).includes('买入计划开始执行'),'Execution message is hidden in event tape');
  await page.locator('#trade-play').click();
  await page.locator('#trade-signals').check();check(await page.locator('#trade-current-event').isVisible(),'Signals can be enabled within the same round');
  check((await page.locator('#trade-current-event-title').innerText()).includes('开始执行'),'Enabled panel shows latest already-published execution');
  check(await page.evaluate(()=>{const actual=TradingLab.snapshot().market,e=TradingEngine.create({seed:20261106,scenario:'buy',mode:'guided',steps:180});for(let i=0;i<actual.tick;i++)e.step();return JSON.stringify(actual.bars)===JSON.stringify(e.snapshot().bars);}), 'Speed and signal settings do not change generated price path');
  await page.locator('#trade-review').click();check((await page.locator('#trade-review-notes').innerText()).includes('首次交易时，已有1条'),'Review counts information at first visibility, without retroactive signal leakage');await page.keyboard.press('Escape');
  await page.locator('#trade-signals').uncheck();await page.locator('#trade-reset').click();check(!(await page.locator('#trade-signals').isChecked()),'Retry retains signal preference');await page.locator('#trade-signals').check();
  check(await page.locator('#trade-speed').inputValue()==='4','Retry retains selected speed');
  await page.evaluate(()=>TradingLab.advance(17));await page.locator('#trade-play').click();await page.clock.runFor(500);
  check((await snapshot()).market.tick===18&&!(await snapshot()).playing,'Enabled signals preserve guided intent pause');
  await page.locator('#language').click();check((await page.locator('#trade-signal-heading').innerText())==='Large-order signals','Signal panel translates to English');
  check((await page.locator('#trade-speed-note').innerText()).includes('s / tick'),'Speed explanation translates to English');
  for(const width of [320,390,768,1440]){
   await page.setViewportSize({width,height:width>=1000?1040:844});
   check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'No overflow with new controls at '+width);
   const positions=await page.evaluate(()=>{const p=document.querySelector('.trade-signal-panel').getBoundingClientRect(),w=document.querySelector('.trade-workspace').getBoundingClientRect();return {panelBottom:p.bottom,workspaceTop:w.top};});
   check(positions.panelBottom<=positions.workspaceTop+1,'Signal panel occupies its own area at '+width);
   await page.screenshot({path:path.join(out,'signals-on-'+width+'.png'),fullPage:true});
   await page.locator('#trade-signals').uncheck();await page.screenshot({path:path.join(out,'signals-off-'+width+'.png'),fullPage:true});
   await page.locator('#trade-signals').check();
  }
  await page.locator('#trade-signals').focus();await page.keyboard.press('Space');check(!(await page.locator('#trade-signals').isChecked()),'Signal switch supports keyboard activation');
  await page.locator('#trade-reset').click();await page.evaluate(()=>TradingLab.advance(18));await page.locator('[data-order="buy"]').click();await page.locator('#trade-signals').check();await page.locator('#trade-review').click();
  check((await page.locator('#trade-review-notes').innerText()).includes('At your first trade, 2 event messages'),'Enabling signals after a trade on the same tick cannot change the first-trade information count');
  check(errors.length===0,'No browser or HTTP errors');
  const report={status:'pass',url:page.url(),checks:checks.length,assertions:checks,errors};
  fs.writeFileSync(path.join(out,'controls-acceptance.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
 }catch(error){fs.writeFileSync(path.join(out,'controls-acceptance.json'),JSON.stringify({status:'fail',checks:checks.length,assertions:checks,errors,error:String(error)},null,2));throw error;}
 finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
