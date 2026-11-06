'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const H=require('../web/assets/trading-history.js'),A=require('../web/assets/trading-account.js');const data=JSON.parse(fs.readFileSync(path.join(__dirname,'../web/assets/data/historical-replays-v1.json')));let checks=0;function check(x,m){checks++;assert.ok(x,m);}
check(H.validate(data),'Library validates');
for(const c of data.cases){const e=H.create(data,{caseId:c.id});let s=e.snapshot();check(s.tick===0&&s.price===c.initialPrice,'Initial price is playable close');check(s.bars.every(b=>b.tick<=0)&&s.bars.length===41,'Only already known warm-up bars');check(!s.historicalReview,'No future outcome initially');const saved=JSON.stringify(s);
 for(let t=1;t<=c.steps;t++){s=e.step();check(s.tick===t&&s.bars.at(-1).tick===t,'One completed candle per step');check(s.bars.every(b=>b.tick<=t)&&s.events.every(a=>a.tick<=t),'Causal snapshot prefix');check(JSON.stringify(s.bars.at(-1))===JSON.stringify(c.bars.find(b=>b.tick===t)),'Original OHLC and flow are unchanged');check(!!s.historicalReview===(t===c.steps),'Outcome revealed only at the end');}
 check(s.done&&JSON.stringify(e.step())===JSON.stringify(s),'Completed replay is stable');check(JSON.stringify(e.reset())===saved,'Retry reproduces the same excerpt');
 const primary=c.alerts.find(a=>a.tick===20);check(primary&&primary.direction===c.review.direction,'Primary observed alert is in the actual event stream');check(c.review.favorableMove>=.02&&c.review.minutesToPeak>=5&&c.review.minutesToPeak<=90,'Signal precedes selected substantial move');
 const p0=c.initialPrice,a=A.create();a.mark(p0,0);a.mark(c.bars.find(b=>b.tick===10).close,10);const r=a.review({bars:c.bars.filter(b=>b.tick<=10),initialPrice:p0});const expected=100*(a.snapshot().lastPrice/(p0*(1.0002)*(1.0005))-1);check(Math.abs(r.benchmark.passiveReturnPct-expected)<1e-9,'Passive baseline excludes warm-up and uses identical entry time');
}
const e=H.create(data,{caseId:data.cases[0].id}),a=e.snapshot();a.bars[0].close=1;check(e.snapshot().bars[0].close!==1,'Snapshots cannot mutate the replay');check(data.cases.length===9,'Nine real excerpts');
console.log(JSON.stringify({status:'pass',checks,cases:data.cases.length,scope:'Original OHLC preservation, causal prefixes, hidden future outcomes, deterministic replay, account benchmark timing'},null,2));
