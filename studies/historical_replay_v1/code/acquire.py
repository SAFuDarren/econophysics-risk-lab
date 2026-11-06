from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import urllib.request,zipfile,hashlib,json,time
import numpy as np,pandas as pd
import argparse
parser=argparse.ArgumentParser();parser.add_argument('--cache',type=Path,required=True);parser.add_argument('--reuse-cache',type=Path,action='append',default=[]);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
O=args.output;O.mkdir(parents=True,exist_ok=True);args.cache.mkdir(parents=True,exist_ok=True)
manifest=json.loads((Path(__file__).resolve().parents[1]/'inputs/source-manifest.json').read_text())
def ensure(source):
 name=source['url'].rsplit('/',1)[-1];p=next((d/name for d in args.reuse_cache if (d/name).exists()),args.cache/name)
 if not p.exists():p.write_bytes(urllib.request.urlopen(source['url'],timeout=180).read())
 assert hashlib.sha256(p.read_bytes()).hexdigest()==source['sha256'],name
 return (source['date'],source['kind']),p
with ThreadPoolExecutor(max_workers=6) as pool:paths=dict(pool.map(ensure,manifest['sources']))
sources={x['date']:x for x in manifest['sources'] if x['kind']=='aggTrades'}
klines={x['date']:x for x in manifest['sources'] if x['kind']=='klines_1m'}
frames=[];provenance=[]
for date in sorted(sources):
 ap=paths[(date,'aggTrades')]
 assert hashlib.sha256(ap.read_bytes()).hexdigest()==sources[date]['sha256']
 with zipfile.ZipFile(paths[(date,'klines_1m')]) as z:k=pd.read_csv(z.open(z.namelist()[0]),header=None)
 assert len(k)==1440
 start=int(k.iloc[0,0]);unit=60000000 if start>1e14 else 60000
 minute=((k[0].to_numpy(np.int64)-start)//unit).astype(int);assert np.array_equal(minute,np.arange(1440))
 buy=np.zeros(1440);sell=np.zeros(1440);lbuy=np.zeros(1440);lsell=np.zeros(1440);bmax=np.zeros(1440);smax=np.zeros(1440);flowbase=np.zeros(1440);size2=np.zeros(1440);count=np.zeros(1440,np.int64);rawcount=np.zeros(1440,np.int64)
 with zipfile.ZipFile(ap) as z:
  for x in pd.read_csv(z.open(z.namelist()[0]),header=None,usecols=[1,2,3,4,5,6],chunksize=500000):
   ind=((x[5].to_numpy(np.int64)-start)//unit).astype(int);assert ind.min()>=0 and ind.max()<1440
   sizes=x[2].to_numpy(float);q=x[1].to_numpy(float)*sizes;maker=x[6].astype(str).str.lower().eq('true').to_numpy();large=q>=100000
   flowbase+=np.bincount(ind,weights=np.where(maker,-sizes,sizes),minlength=1440);size2+=np.bincount(ind,weights=sizes*sizes,minlength=1440)
   buy+=np.bincount(ind,weights=np.where(~maker,q,0),minlength=1440);sell+=np.bincount(ind,weights=np.where(maker,q,0),minlength=1440)
   lbuy+=np.bincount(ind,weights=np.where(~maker&large,q,0),minlength=1440);lsell+=np.bincount(ind,weights=np.where(maker&large,q,0),minlength=1440)
   np.maximum.at(bmax,ind,np.where(~maker,q,0));np.maximum.at(smax,ind,np.where(maker,q,0))
   count+=np.bincount(ind,minlength=1440);rawcount+=np.bincount(ind,weights=x[4].to_numpy(np.int64)-x[3].to_numpy(np.int64)+1,minlength=1440).astype(np.int64)
 assert np.allclose(buy,k[10].to_numpy(float),rtol=2e-8,atol=.05),date+' taker buy'
 assert np.allclose(buy+sell,k[7].to_numpy(float),rtol=2e-8,atol=.05),date+' total'
 assert np.array_equal(rawcount,k[8].to_numpy(np.int64)),date+' raw count'
 assert np.allclose(flowbase,2*k[9].to_numpy(float)-k[5].to_numpy(float),rtol=2e-8,atol=1e-7),date+' signed base flow'
 assert np.all(size2>=0) and np.all(size2<=k[5].to_numpy(float)**2+1e-7)
 frame=pd.DataFrame(dict(date=date,minute=np.arange(1440),timestamp=(k[0].to_numpy(np.int64)//1000 if unit==60000000 else k[0].to_numpy(np.int64)),open=k[1],high=k[2],low=k[3],close=k[4],volume=k[5],quoteVolume=k[7],buyQuote=buy,sellQuote=sell,largeBuyQuote=lbuy,largeSellQuote=lsell,maxBuyQuote=bmax,maxSellQuote=smax,aggregateCount=count,tradeCount=rawcount,flowBase=flowbase,squaredSizeBase=size2))
 frames.append(frame);provenance.extend([sources[date],klines[date]])
 print(date,'aggregates',count.sum(),'range',round(100*(k[2].max()/k[3].min()-1),2),flush=True)
pd.concat(frames).to_csv(O/'minute-observables.csv.gz',index=False,compression={'method':'gzip','mtime':0},float_format='%.10g')
(O/'source-manifest.json').write_text(json.dumps({'status':'pass','sources':provenance,'checks':'All 26 dates have 1440 contiguous one-minute candles. Independent aggregate-trade quote volume, taker-buy quote volume and raw fill counts reconcile to official candle records. Large aggregate trade threshold: 100000 USDT.'},indent=2))
print('COMPLETE',len(frames),flush=True)
