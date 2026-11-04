#!/usr/bin/env python3
"""Download and independently calendar-check the frozen US ETF panel."""
from pathlib import Path
import argparse,csv,datetime as dt,hashlib,json,sys,time,urllib.request
from concurrent.futures import ThreadPoolExecutor
from zoneinfo import ZoneInfo
import exchange_calendars as xcals

ROOT=Path(__file__).resolve().parents[1]

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--stage',choices=['historical','confirmation'],default='historical');args=p.parse_args()
    config=ROOT/'configs/us_equity_v1.json';cfg=json.loads(config.read_text());raw=ROOT/'data/raw/us_equity_v1'/args.stage;man=ROOT/'data/manifests/us_equity_v1';processed=ROOT/'data/processed/us_equity_v1';man.mkdir(parents=True,exist_ok=True);processed.mkdir(parents=True,exist_ok=True)
    output=processed/f'{args.stage}.csv'
    if output.exists():raise SystemExit('Preserve processed evidence; use an isolated reproduction root.')
    interval=cfg[args.stage+'_download'];start,end=interval['start'],interval['end_exclusive'];freeze=man/f'{args.stage}_before_download.json'
    sources=[config,ROOT/'docs/AB/us_equity_v1_contract.md',Path(__file__)]
    if args.stage=='confirmation':
        selected=ROOT/'results/checks/us_equity_v1/selection_freeze.json'
        if not selected.exists():raise SystemExit('Freeze validation selections before confirmation download.')
        sources.append(selected)
    if not freeze.exists():
        assert not raw.exists(),'Unrecorded existing raw batch'
        freeze.write_text(json.dumps({'recorded_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'stage':args.stage,'range':interval,'sha256':{str(s.relative_to(ROOT)):sha(s) for s in sources},'raw_count_before_download':0},indent=2)+'\n')
    else:
        prior=json.loads(freeze.read_text())
        for name,h in prior['sha256'].items():assert sha(ROOT/name)==h,(name,'freeze drift')
    raw.mkdir(parents=True,exist_ok=True)
    def epoch(date):return int(dt.datetime.fromisoformat(date).replace(tzinfo=dt.timezone.utc).timestamp())
    symbols=cfg['network_assets']+cfg['context_assets']
    def get(symbol):
        url=f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?period1={epoch(start)}&period2={epoch(end)}&interval=1d&events=div%2Csplits';path=raw/f'{symbol}.json'
        if not path.exists():
            for attempt in range(3):
                try:
                    req=urllib.request.Request(url,headers={'User-Agent':'PC5253-academic-research/1.0'})
                    with urllib.request.urlopen(req,timeout=30) as r:data=r.read()
                    json.loads(data);path.write_bytes(data);break
                except Exception:
                    if attempt==2:raise
                    time.sleep(attempt+1)
        result=json.loads(path.read_text())['chart']['result'][0];meta=result['meta'];assert meta['currency']=='USD' and meta['exchangeTimezoneName']=='America/New_York'
        timestamps=result['timestamp'];quote=result['indicators']['quote'][0];adjusted=result['indicators']['adjclose'][0]['adjclose'];assert len(set(timestamps))==len(timestamps)
        dividends={dt.datetime.fromtimestamp(v['date'],ZoneInfo('America/New_York')).date().isoformat():v['amount'] for v in result.get('events',{}).get('dividends',{}).values()}
        splits={dt.datetime.fromtimestamp(v['date'],ZoneInfo('America/New_York')).date().isoformat():v['numerator']/v['denominator'] for v in result.get('events',{}).get('splits',{}).values()}
        rows=[]
        for i,t in enumerate(timestamps):
            date=dt.datetime.fromtimestamp(t,ZoneInfo('America/New_York')).date().isoformat();assert start<=date<end
            row={'date':date,'symbol':symbol,**{k:quote[k][i] for k in ['open','high','low','close','volume']},'adjusted_close':adjusted[i],'dividend':dividends.get(date,0.),'split_ratio':splits.get(date,1.)}
            assert all(row[k] is not None and row[k]>0 for k in ['open','high','low','close','adjusted_close']) and row['volume'] is not None and row['volume']>=0,row
            assert row['high']+1e-6>=max(row['open'],row['close'],row['low']) and row['low']-1e-6<=min(row['open'],row['close']),row
            rows.append(row)
        return rows,{'symbol':symbol,'url':url,'path':str(path.relative_to(ROOT)),'bytes':path.stat().st_size,'sha256':sha(path),'rows':len(rows),'dividend_records':len(dividends),'split_records':len(splits),'volume_scope':'Provider-reported, consolidated-tape scope not independently verified'}
    with ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(get,symbols))
    calendar=xcals.get_calendar('XNYS',start=start,end=end);expected=[x.date().isoformat() for x in calendar.sessions if start<=x.date().isoformat()<end]
    allrows=[];records=[]
    for rows,record in results:
        dates=[r['date'] for r in rows];assert dates==expected,{'symbol':record['symbol'],'missing':sorted(set(expected)-set(dates)),'extra':sorted(set(dates)-set(expected))};allrows.extend(rows);records.append(record)
    allrows.sort(key=lambda r:(r['date'],r['symbol']))
    with output.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(allrows[0]));writer.writeheader();writer.writerows(allrows)
    report={'status':'pass','stage':args.stage,'symbols':symbols,'sessions':len(expected),'rows':len(allrows),'first':expected[0],'last':expected[-1],'missing':0,'duplicates':0,'filled_or_deleted':0,'calendar':'exchange_calendars XNYS 4.13.2, community calendar rather than official exchange certification','processed_path':str(output.relative_to(ROOT)),'processed_sha256':sha(output),'records':records,'member_review':'not_run'}
    (man/f'{args.stage}_manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['status','stage','sessions','rows','first','last']},indent=2))

if __name__=='__main__':main()
