/* End-to-end acceptance against an already served web/ directory.
 * TRADING_BASE_URL=http://127.0.0.1:8765/
 * PLAYWRIGHT_MODULE_PATH=playwright (or an installed module's absolute path)
 * PLAYWRIGHT_CHROMIUM_EXECUTABLE=/optional/path/to/chromium
 * TRADING_QA_OUTPUT=/optional/output/directory (or first CLI argument)
 */
'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE_PATH||'playwright');
const base=process.env.TRADING_BASE_URL||'http://127.0.0.1:8765/';
const url=new URL('trading.html',base.endsWith('/')?base:base+'/').href;
const out=path.resolve(process.env.TRADING_QA_OUTPUT||process.argv[2]||path.join(__dirname,'../.runs/trading-browser'));
fs.mkdirSync(out,{recursive:true});
let checks=0;
function check(condition,message){checks++;assert.ok(condition,message);}
async function snapshot(page){return page.evaluate(()=>TradingLab.snapshot());}
async function advance(page,n){await page.evaluate(n=>TradingLab.advance(n),n);}
async function modalBounds(page){return page.evaluate(()=>{const d=document.getElementById('trade-review-dialog'),r=d.getBoundingClientRect(),c=document.getElementById('trade-review-close').getBoundingClientRect();return {top:r.top,bottom:r.bottom,left:r.left,right:r.right,width:innerWidth,height:innerHeight,closeTop:c.top,closeBottom:c.bottom,scrollHeight:d.scrollHeight,clientHeight:d.clientHeight};});}

(async()=>{
  const launch={headless:true};if(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE)launch.executablePath=process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE;
  const browser=await chromium.launch(launch);const errors=[],widthChecks=[],rects=[];
  try{
    const context=await browser.newContext({viewport:{width:1440,height:1040},hasTouch:true,reducedMotion:'reduce'});
    await context.addInitScript(()=>localStorage.setItem('econo-language','zh'));
    const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400)errors.push(r.status()+' '+r.url());});
    await page.goto(url);await page.waitForFunction(()=>window.TradingLab?.account);
    let s=await snapshot(page);check(s.market.tick===0&&s.account.equity===100000,'Initial engine/account values');
    check(await page.locator('#trade-chart-empty').isVisible(),'Empty chart has a start instruction');
    await page.screenshot({path:path.join(out,'desktop-ready.png'),fullPage:true});
    await page.locator('#trade-step').click();check((await snapshot(page)).market.tick===1,'DOM step control');
    await advance(page,16);const prefix=(await snapshot(page)).market.bars.slice(0,12);
    await page.locator('#trade-play').click();
    await page.waitForFunction(()=>TradingLab.snapshot().market.tick===18&&!TradingLab.snapshot().playing,null,{timeout:10000});
    check((await snapshot(page)).market.tick===18,'Guided playback pauses when intent arrives');
    check(await page.locator('#trade-current-event').isVisible(),'Intent ticker visible near chart');
    check((await page.locator('#trade-current-event-title').innerText()).includes('大额买入'),'Ticker shows actual current intent');
    for(let i=0;i<5;i++){s=await snapshot(page);check(s.market.events.every(e=>e.tick<=s.market.tick),'No future event at tick '+s.market.tick);await page.locator('#trade-step').click();}
    await page.locator('[data-order="buy"]').click();s=await snapshot(page);check(s.account.quantity>0&&s.account.totalFees>0,'DOM long entry includes costs');
    check(await page.locator('[data-order="short"]').isDisabled(),'Opposite opening direction blocked until close');
    await advance(page,27);await page.screenshot({path:path.join(out,'desktop-trading.png'),fullPage:true});
    const before=(await snapshot(page)).account.quantity;await page.locator('[data-fraction="0.25"]').click();await page.locator('[data-order="sell"]').click();s=await snapshot(page);
    check(Math.abs(s.account.quantity-before*.75)<1e-7,'DOM quarter partial exit');
    check(Math.abs(s.account.equity-(s.account.cash+s.account.quantity*s.market.price))<1e-7,'UI account equity identity');
    const tick=s.market.tick;await page.locator('#language').click();check(await page.locator('html').getAttribute('lang')==='en','English language switch');check((await snapshot(page)).market.tick===tick,'Language switching does not advance market');
    check((await page.locator('#trade-feedback').innerText()).includes('Order filled'),'Feedback retranslates');await page.locator('#language').click();
    await page.locator('#trade-review').click();check(await page.locator('#trade-review-dialog').isVisible(),'Review opens');check(!(await snapshot(page)).playing,'Review pauses playback');
    let rect=await modalBounds(page);rects.push({width:1440,...rect});check(rect.top>=0&&rect.bottom<=rect.height+1,'Desktop review fits viewport');
    await page.screenshot({path:path.join(out,'desktop-review.png')});await page.keyboard.press('Escape');check(!(await page.locator('#trade-review-dialog').isVisible()),'Escape closes review');
    await page.locator('#trade-scenario').selectOption('sell');s=await snapshot(page);check(s.market.tick===0&&s.account.trades.length===0,'Scenario resets market and account');
    await advance(page,18);await page.locator('[data-order="short"]').click();const shortBefore=(await snapshot(page)).account.quantity;check(shortBefore<0,'DOM short entry');
    await advance(page,24);await page.locator('[data-order="cover"]').click();check(Math.abs((await snapshot(page)).account.quantity)<Math.abs(shortBefore),'DOM partial short cover');
    await advance(page,200);s=await snapshot(page);check(s.market.done&&s.account.quantity===0,'Final tick settles open position');check(await page.locator('#trade-review-dialog').isVisible(),'Final review opens automatically');
    check(await page.locator('[data-order="buy"]').isDisabled(),'Trading disabled at the completed path');await page.keyboard.press('Escape');
    await page.locator('#trade-scenario').selectOption('buy');await advance(page,12);check(JSON.stringify((await snapshot(page)).market.bars)===JSON.stringify(prefix),'Seed retry recovers the same known path prefix');
    await page.locator('#trade-mode-experiment').click();check(await page.evaluate(()=>TradingLab.engine.config.mode)==='experiment','Experiment mode selected');
    await page.locator('#trade-coupling').uncheck();check(await page.evaluate(()=>TradingLab.engine.config.coupling)===0,'Coupling-off control');
    await page.locator('#trade-memory').uncheck();check(await page.evaluate(()=>TradingLab.engine.config.memory)===0,'Memory-off control');
    await page.locator('#trade-reset').click();await page.locator('[data-fraction="1"]').click();await page.locator('[data-order="short"]').click();
    // Deliberate account stress: public accounting API receives a large adverse mark.
    // It is a UI edge-case test, not a synthetic-market result or a future-price input.
    await page.evaluate(()=>TradingLab.account.mark(100000,TradingLab.snapshot().market.tick));await page.locator('#trade-step').click();s=await snapshot(page);check(s.account.insolvent&&s.account.quantity===0,'Insolvent account is liquidated');
    const flatCash=s.account.cash,oldTick=s.market.tick;check(!(await page.locator('#trade-step').isDisabled()),'Market remains observable after insolvency');await page.locator('#trade-step').click();s=await snapshot(page);check(s.market.tick===oldTick+1&&s.account.cash===flatCash,'Post-insolvency playback advances with flat account');check(await page.locator('[data-order="buy"]').isDisabled(),'Insolvency blocks new orders');
    for(const width of [320,390,768,1440]){
      await page.setViewportSize({width,height:width>=1000?1040:844});await page.locator('#trade-scenario').selectOption(width===320?'split':'turn');await page.locator('#trade-reset').click();await advance(page,80);
      const overflow=await page.evaluate(()=>({scroll:document.documentElement.scrollWidth,width:innerWidth}));widthChecks.push({width,...overflow});check(overflow.scroll<=overflow.width,'No horizontal overflow at '+width);
      if(width===390){await page.locator('[data-fraction="0.25"]').tap();await page.locator('[data-order="buy"]').tap();check((await snapshot(page)).account.quantity>0,'Mobile tap enters position');await page.locator('[data-order="close"]').tap();check((await snapshot(page)).account.quantity===0,'Mobile tap closes position');}
      await page.screenshot({path:path.join(out,'trading-'+width+'.png'),fullPage:true});await page.locator('#trade-review').click();rect=await modalBounds(page);rects.push({width,...rect});check(rect.top>=0&&rect.bottom<=rect.height+1&&rect.left>=0&&rect.right<=rect.width+1,'Review fits '+width+' viewport');check(rect.closeTop>=0&&rect.closeBottom<=rect.height,'Review close visible at '+width);
      await page.screenshot({path:path.join(out,'review-'+width+'.png')});await page.keyboard.press('Escape');
    }
    check(errors.length===0,'No browser or HTTP errors');
    const report={status:'pass',checks,url,errors,widthChecks,modalBounds:rects,screenshots:out};fs.writeFileSync(path.join(out,'browser-acceptance.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
  }catch(error){fs.writeFileSync(path.join(out,'browser-acceptance.json'),JSON.stringify({status:'fail',checks,url,errors,error:String(error)},null,2));throw error;}
  finally{await browser.close();}
})().catch(error=>{console.error(error);process.exit(1);});
