#!/usr/bin/env python3
"""Download the external asset holdout only after method and reference freeze."""
from pathlib import Path
import csv,datetime as dt,hashlib,json,time,urllib.request
from concurrent.futures import ThreadPoolExecutor
from zoneinfo import ZoneInfo
import exchange_calendars as xcals
ROOT=Path(__file__).resolve().parents[1]

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    cfg=json.loads((ROOT/'configs/tail_increment_v1.json').read_text());man=ROOT/'data/manifests/tail_increment_v1';selection=ROOT/'results/checks/tail_increment_v1/selection_freeze.json'
    if not selection.exists():raise SystemExit('Complete sector-validation reference selection before external download')
    record=json.loads(selection.read_text())
    for path,digest in {**record['method_sha256'],**record['source_sha256']}.items():assert sha(ROOT/path)==digest,('Pre-download version drift',path)
    raw=ROOT/'data/raw/tail_increment_v1';processed=ROOT/'data/processed/tail_increment_v1';processed.mkdir(parents=True,exist_ok=True);output=processed/'external.csv'
    if output.exists():raise SystemExit('Preserve external data snapshot; use an isolated root to reproduce')
    before=man/'external_before_download.json'
    if not before.exists():
        assert not raw.exists();before.write_text(json.dumps({'recorded_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'raw_count_before_download':0,'selection_sha256':sha(selection),'method_freeze_sha256':sha(man/'method_before_external_download.json'),'fetch_source_sha256':sha(Path(__file__)),'scope':'External assets; same known historical market dates, not new future time'},indent=2)+'\n')
    raw.mkdir(parents=True,exist_ok=True)
    start,end=cfg['download']['start'],cfg['download']['end_exclusive']
    def epoch(d):return int(dt.datetime.fromisoformat(d).replace(tzinfo=dt.timezone.utc).timestamp())
    def fetch(symbol):
        url=f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?period1={epoch(start)}&period2={epoch(end)}&interval=1d&events=div%2Csplits';path=raw/f'{symbol}.json'
        if not path.exists():
            for attempt in range(3):
                try:
                    request=urllib.request.Request(url,headers={'User-Agent':'PC5253-academic-research/1.0'})
                    with urllib.request.urlopen(request,timeout=30) as response:payload=response.read()
                    json.loads(payload);path.write_bytes(payload);break
                except Exception:
                    if attempt==2:raise
                    time.sleep(attempt+1)
        result=json.loads(path.read_text())['chart']['result'][0];assert result['meta']['currency']=='USD'
        quote=result['indicators']['quote'][0];adj=result['indicators']['adjclose'][0]['adjclose'];rows=[]
        for i,timestamp in enumerate(result['timestamp']):
            day=dt.datetime.fromtimestamp(timestamp,ZoneInfo('America/New_York')).date().isoformat();row={'date':day,'symbol':symbol,**{k:quote[k][i] for k in ['open','high','low','close','volume']},'adjusted_close':adj[i]}
            assert start<=day<end and all(row[k] is not None and row[k]>0 for k in ['open','high','low','close','adjusted_close']) and row['volume'] is not None and row['volume']>=0
            assert row['high']+1e-6>=max(row['open'],row['close'],row['low']) and row['low']-1e-6<=min(row['open'],row['close'])
            rows.append(row)
        return rows,{'symbol':symbol,'url':url,'path':str(path.relative_to(ROOT)),'bytes':path.stat().st_size,'sha256':sha(path),'rows':len(rows),'source':'Provider adjusted-close current total-return proxy, not point-in-time vintage; full raw events preserved in JSON'}
    with ThreadPoolExecutor(max_workers=3) as pool:outputs=list(pool.map(fetch,cfg['external_panel']))
    expected=[x.date().isoformat() for x in xcals.get_calendar('XNYS',start=start,end=end).sessions if start<=x.date().isoformat()<end]
    rows=[]
    for asset_rows,record in outputs:
        actual=[r['date'] for r in asset_rows]
        assert actual==expected,{'symbol':record['symbol'],'missing':sorted(set(expected)-set(actual)),'extra':sorted(set(actual)-set(expected))}
        rows+=asset_rows
    rows.sort(key=lambda r:(r['date'],r['symbol']))
    with output.open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    report={'status':'pass','recorded_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'sessions':len(expected),'rows':len(rows),'first':expected[0],'last':expected[-1],'calendar':'XNYS community exchange_calendars, no fill/drop','missing':0,'duplicates':0,'records':[r for _,r in outputs],'processed_sha256':sha(output),'source_freeze_sha256':sha(before),'scientific_member_review':'not_run'};(man/'external_manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['status','sessions','rows','first','last']},indent=2))

if __name__=='__main__':main()
