#!/usr/bin/env python3
from pathlib import Path
import argparse,json,hashlib,zipfile
import numpy as np,pandas as pd
R=Path(__file__).resolve().parent;p=argparse.ArgumentParser();p.add_argument('--raw-kline-cache',type=Path);p.add_argument('--output',type=Path);args=p.parse_args()
df=pd.read_csv(R/'inputs/minute-observables.csv.gz');data=json.loads((R.parent.parent/'web/assets/data/historical-replays-v1.json').read_text());sources=json.loads((R/'inputs/source-manifest.json').read_text());assert len(df)==26*1440 and len(sources['sources'])==52
checks=[]
for c in data['cases']:
 g=df[df.date==c['review']['date']].reset_index(drop=True);start=c['review']['minute']-20;minute=c['review']['minute'];direction=c['review']['direction'];price=g.close.to_numpy()
 for b in c['bars']:
  r=g.iloc[start+b['tick']]
  for name in ['open','high','low','close','volume','quoteVolume','buyQuote','sellQuote','largeBuyQuote','largeSellQuote','maxBuyQuote','maxSellQuote']:assert b[name]==float(r[name]),(c['id'],name)
 for a in c['alerts']:
  i=start+a['tick'];B=g.largeBuyQuote.to_numpy();S=g.largeSellQuote.to_numpy();arr=B if a['direction']==1 else S;other=S if a['direction']==1 else B;side=arr[i-2:i+1].sum();opposite=other[i-2:i+1].sum();past=np.convolve(arr[:i],np.ones(3),'valid')[-120:];threshold=max(1000000,float(np.quantile(past,.9)))
  assert np.isclose(side,a['sideQuote'],rtol=1e-10,atol=1e-5) and np.isclose(threshold,a['pastThreshold'],rtol=1e-10,atol=1e-5)
  assert side>=threshold-1e-5 and side/(side+opposite)>=.7 and a['time']==int(g.iloc[i].timestamp)+60000
 future=direction*(price[minute+1:minute+91]/price[minute]-1);peak=int(np.argmax(future))+1;assert float(future.max())==c['review']['favorableMove'] and peak==c['review']['minutesToPeak'] and c['review']['signalCloseTime']<c['review']['peakCloseTime']
 assert future.max()>=.02 and peak>=5
 if args.raw_kline_cache:
  ap=args.raw_kline_cache/f'BTCUSDT-1m-{c["review"]["date"]}.zip'
  with zipfile.ZipFile(ap) as z:raw=pd.read_csv(z.open(z.namelist()[0]),header=None)
  for b in c['bars']:
   row=raw.iloc[start+b['tick']]
   for name,col in [('open',1),('high',2),('low',3),('close',4)]:assert b[name]==float(row[col]),(c['id'],name)
 checks.append({'id':c['id'],'bars':len(c['bars']),'alerts':len(c['alerts']),'signal_precedes_peak':True,'future_close_move_pct':100*float(future.max()),'maximum_adverse_before_peak_pct':100*c['review']['adverseBeforePeak'],'exact_original_raw_ohlc':bool(args.raw_kline_cache)})
report={'status':'pass','dates':26,'one_minute_bars':len(df),'official_source_archives':len(sources['sources']),'recorded_official_checksums':all(x['official_checksum_match'] for x in sources['sources']),'input_sha256':hashlib.sha256((R/'inputs/minute-observables.csv.gz').read_bytes()).hexdigest(),'checks':checks,'scope':'Every selected candle and alert checked against full minute pool; thresholds independently computed from past-only data. Optional raw Kline check compares every OHLC value exactly. Retrospective curation is not predictive validation.'}
if args.output:args.output.write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
