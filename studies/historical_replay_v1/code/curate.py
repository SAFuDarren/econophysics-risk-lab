#!/usr/bin/env python3
"""Select labelled historical teaching excerpts; no population prediction inference."""
from pathlib import Path
import argparse,json,hashlib
import numpy as np,pandas as pd
RULES=dict(large_trade_quote=100000,flow_window_minutes=3,minimum_side_quote=1000000,minimum_side_share=.70,lagged_quantile=.90,lagged_window_minutes=120,alert_cooldown_minutes=12,context_bars=40,primary_alert_tick=20,play_steps=120,outcome_horizon_minutes=90,minimum_favorable_close_move=.02,minimum_peak_lead_minutes=5,max_cases=12)

def run(input_path,output_dir):
 O=Path(output_dir);O.mkdir(parents=True,exist_ok=True);df=pd.read_csv(input_path);pool=[];days={};all_alerts=[]
 for date,g in df.groupby('date',sort=True):
  g=g.reset_index(drop=True);assert len(g)==1440;days[date]=g
  B=g.largeBuyQuote.rolling(3,min_periods=3).sum();S=g.largeSellQuote.rolling(3,min_periods=3).sum();c=g.close.to_numpy();last=-100
  thresholds={d:arr.shift(1).rolling(120,min_periods=120).quantile(.9) for d,arr in [(1,B),(-1,S)]}
  for i in range(122,1440):
   d=1 if B.iloc[i]>=S.iloc[i] else -1;side=B.iloc[i] if d==1 else S.iloc[i];other=S.iloc[i] if d==1 else B.iloc[i];thr=max(1000000,float(thresholds[d].iloc[i]))
   if not(side>=thr and side/max(side+other,1)>=.70 and i-last>=12):continue
   last=i
   a=dict(date=date,minute=i,direction=d,sideQuote=float(side),opposingQuote=float(other),share=float(side/max(side+other,1)),pastThreshold=float(thr),maxAggregateQuote=float(g.iloc[i-2:i+1][('maxBuyQuote' if d==1 else 'maxSellQuote')].max()))
   all_alerts.append(a)
   if i<60 or i+100>=1440:continue
   future=d*(c[i+1:i+91]/c[i]-1);j=int(np.argmax(future))+1;peak=float(future[j-1]);before=future[:j];adverse=float(max(0,-before.min()));end=float(d*(c[i+100]/c[i]-1))
   a={**a,'favorableMove':peak,'minutesToPeak':j,'adverseBeforePeak':adverse,'endDirectionalReturn':end}
   if peak>=.02 and j>=5:pool.append(a)
 pd.DataFrame(all_alerts).to_csv(O/'all-alerts.csv',index=False,float_format='%.10g');pd.DataFrame(pool).to_csv(O/'eligible-candidates.csv',index=False,float_format='%.10g')
 # Alternate buy/sell, prioritise actual pullbacks; avoid overlapping excerpts.
 selected=[]
 for slot in range(12):
  d=1 if slot%2==0 else -1;candidates=[x for x in pool if x['direction']==d and all(x['date']!=y['date'] or abs(x['minute']-y['minute'])>=180 for y in selected)]
  if not candidates:continue
  date_counts={date:sum(y['date']==date for y in selected) for date in days}
  candidates.sort(key=lambda x:(date_counts[x['date']],-min(x['adverseBeforePeak'],.015),-x['favorableMove'],x['date'],x['minute']))
  selected.append(candidates[0])
 cases=[];catalog=[]
 for j,a in enumerate(selected):
  case_id=f'history-{j+1:02}';g=days[a['date']];start=a['minute']-20;first=start-40;end=start+120
  bars=[]
  for i in range(first,end+1):
   r=g.iloc[i];bars.append(dict(tick=int(i-start),time=int(r.timestamp),open=float(r.open),high=float(r.high),low=float(r.low),close=float(r.close),volume=float(r.volume),quoteVolume=float(r.quoteVolume),buyQuote=float(r.buyQuote),sellQuote=float(r.sellQuote),largeBuyQuote=float(r.largeBuyQuote),largeSellQuote=float(r.largeSellQuote),maxBuyQuote=float(r.maxBuyQuote),maxSellQuote=float(r.maxSellQuote),flowBase=float(r.flowBase),squaredSizeBase=float(r.squaredSizeBase)))
  alerts=[{**x,'tick':x['minute']-start,'time':int(g.iloc[x['minute']].timestamp)+60000} for x in all_alerts if x['date']==a['date'] and start<x['minute']<=end]
  proof={**a,'primaryAlertTick':20,'signalCloseTime':int(g.iloc[a['minute']].timestamp)+60000,'peakCloseTime':int(g.iloc[a['minute']+a['minutesToPeak']].timestamp)+60000}
  cases.append(dict(id=case_id,label=f'Excerpt {chr(65+j)}',symbol='BTCUSDT',interval='1m',initialPrice=float(g.iloc[start].close),steps=120,startTime=int(g.iloc[start].timestamp)+60000,bars=bars,alerts=alerts,review=proof))
  catalog.append(dict(id=case_id,**proof,startMinute=start,endMinute=end,alertCount=len(alerts)))
 assert len(cases)>=8 and sum(x['review']['direction']==1 for x in cases)>=4 and sum(x['review']['direction']==-1 for x in cases)>=4,(len(cases),len(pool))
 payload=dict(version='1.0.0',source='Binance public BTCUSDT spot klines and aggregate trades',source_docs='https://github.com/binance/binance-public-data',selection='Retrospectively curated teaching excerpts; not an unbiased strategy backtest. Every primary alert precedes a >=2% same-direction close-price excursion within90minutes; secondary alerts are not selected by outcome.',rules=RULES,input_sha256=hashlib.sha256(Path(input_path).read_bytes()).hexdigest(),cases=cases)
 (O/'historical-replays-v1.json').write_text(json.dumps(payload,separators=(',',':'),ensure_ascii=False)+'\n');pd.DataFrame(catalog).to_csv(O/'selected-cases.csv',index=False,float_format='%.10g')
 print(json.dumps({'dates':len(days),'alerts':len(all_alerts),'eligible':len(pool),'selected':len(cases),'buy':sum(x['review']['direction']==1 for x in cases),'sell':sum(x['review']['direction']==-1 for x in cases),'adverse_before_peak_min':min(x['review']['adverseBeforePeak'] for x in cases),'adverse_before_peak_max':max(x['review']['adverseBeforePeak'] for x in cases)},indent=2))
 return payload
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.input,a.output)
