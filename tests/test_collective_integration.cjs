/* Optional Playwright integration QA; same environment options as test_trading_browser.cjs. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE_PATH||'playwright');
const base=process.env.TRADING_BASE_URL||'http://127.0.0.1:8765/';const out=path.resolve(process.env.TRADING_QA_OUTPUT||'.runs/collective-integration');fs.mkdirSync(out,{recursive:true});
(async()=>{
 const options={headless:true};if(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE)options.executablePath=process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE;
 const browser=await chromium.launch(options);const errors=[],pages=[];let checks=0;
 try{
  const context=await browser.newContext({viewport:{width:1440,height:1040},hasTouch:true,reducedMotion:'reduce'});const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400)errors.push(r.status()+' '+r.url());});
  for(const route of ['index.html','lab.html','methods.html#collective-dynamics','findings.html#information-efficiency','reproduce.html#collective-reproduction','advanced/index.html']){
   await page.goto(new URL(route,base).href);await page.waitForTimeout(150);await page.evaluate(()=>document.fonts.ready);
   const info=await page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth,mathErrors:document.querySelectorAll('.katex-error').length,title:document.title}));assert.ok(info.scroll<=info.width);assert.equal(info.mathErrors,0);checks+=2;pages.push({route,...info});
   if(route.startsWith('methods')){assert.ok(await page.locator('#collective-dynamics .katex').count()>=4);checks++;await page.screenshot({path:path.join(out,'methods-desktop.png'),fullPage:true});}
   if(route.startsWith('findings')){assert.ok((await page.locator('#information-efficiency .study-table').innerText()).includes('0.260805'));checks++;await page.screenshot({path:path.join(out,'findings-desktop.png'),fullPage:true});}
  }
  await page.goto(new URL('trading.html',base).href);await page.waitForFunction(()=>window.TradingLab?.account);await page.evaluate(()=>TradingLab.advance(18));await page.locator('[data-order="buy"]').click();await page.evaluate(()=>TradingLab.advance(42));await page.evaluate(()=>document.fonts.ready);await page.screenshot({path:path.join(out,'trading-preview.png'),fullPage:false});
  await page.setViewportSize({width:390,height:844});await page.goto(new URL('lab.html',base).href);await page.locator('#language').click();await page.locator('#trading-entry a').tap();await page.waitForFunction(()=>window.TradingLab?.account);assert.equal(await page.locator('html').getAttribute('lang'),'zh-CN');checks++;
  for(const route of ['methods.html#collective-dynamics','findings.html#information-efficiency','reproduce.html#collective-reproduction']){
   await page.goto(new URL(route,base).href);await page.waitForTimeout(150);const info=await page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth,mathErrors:document.querySelectorAll('.katex-error').length}));assert.ok(info.scroll<=info.width);assert.equal(info.mathErrors,0);checks+=2;pages.push({route,mobile:true,...info});await page.screenshot({path:path.join(out,route.split('.')[0]+'-mobile.png'),fullPage:true});
  }
  assert.deepEqual(errors,[]);checks++;const report={status:'pass',checks,pages,errors};fs.writeFileSync(path.join(out,'integration-acceptance.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
