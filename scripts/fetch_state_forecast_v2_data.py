#!/usr/bin/env python3
"""Acquire only the frozen new-asset/new-time archives; verify every byte/grid."""
from pathlib import Path
from publication_integrity import matches_recorded_digest
from concurrent.futures import ThreadPoolExecutor
import calendar,csv,datetime,hashlib,io,json,math,shutil,sys,zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from fetch_market_data import get
from econophysics.market_data import read_archive,iso_from_us


def main():
    cfgpath=ROOT/'configs/state_forecast_v2.json';cfg=json.loads(cfgpath.read_text());contract=ROOT/'docs/AB/state_forecast_v2_contract.md';freeze=ROOT/'data/manifests/state_forecast_v2_pre_download.json'
    datasets={'BTCUSDT':cfg['source_btc_new'],'ETHUSDT':cfg['source_eth_new']};initial={s:len(list((ROOT/'data/raw'/d).glob('*.zip'))) for s,d in datasets.items()}
    j={'config_sha256':hashlib.sha256(cfgpath.read_bytes()).hexdigest(),'contract_sha256':hashlib.sha256(contract.read_bytes()).hexdigest(),'initial_archive_counts':initial,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    if freeze.exists():assert matches_recorded_digest(cfgpath,json.loads(freeze.read_text())['config_sha256'],ROOT)
    else:
        assert not any(initial.values());freeze.write_text(json.dumps(j,indent=2)+'\n')
    requests=[]
    for symbol,dataset in datasets.items():
        raw=ROOT/'data/raw'/dataset;manifest=ROOT/'data/manifests'/dataset;raw.mkdir(parents=True,exist_ok=True);manifest.mkdir(parents=True,exist_ok=True)
        if symbol=='ETHUSDT':
            requests.append((symbol,dataset,'daily','2024-12-31','milliseconds','reference'))
            for year,end in [(2025,12),(2026,9)]:
                for month in range(1,end+1):requests.append((symbol,dataset,'monthly',f'{year}-{month:02}','microseconds','analysis'))
        for day in range(1,26):requests.append((symbol,dataset,'daily',f'2026-10-{day:02}','microseconds','analysis'))
    def fetch(request):
        symbol,dataset,freq,period,unit,role=request;raw=ROOT/'data/raw'/dataset;name=f'{symbol}-5m-{period}.zip';url=f'https://data.binance.vision/data/spot/{freq}/klines/{symbol}/5m/{name}';path=raw/name;checksum=raw/(name+'.CHECKSUM')
        if not checksum.exists():checksum.write_bytes(get(url+'.CHECKSUM')[0])
        if not path.exists():path.write_bytes(get(url)[0])
        expected=checksum.read_text().split()[0].lower();actual=hashlib.sha256(path.read_bytes()).hexdigest();assert actual==expected
        with zipfile.ZipFile(path) as z:assert z.testzip() is None
        print(f'Verified {symbol} {period}',flush=True)
        return {'symbol':symbol,'period':period,'frequency':freq,'role':role,'timestamp_unit':unit,'raw_path':str(path.relative_to(ROOT)),'checksum_path':str(checksum.relative_to(ROOT)),'url':url,'checksum_url':url+'.CHECKSUM','sha256':actual,'bytes':path.stat().st_size}
    with ThreadPoolExecutor(max_workers=4) as pool:records=list(pool.map(fetch,requests))
    reports=[]
    for symbol,dataset in datasets.items():
        manifest=ROOT/'data/manifests'/dataset;files=[r for r in records if r['symbol']==symbol];allrows=[];previous=None
        if symbol=='BTCUSDT':
            with (ROOT/'data/processed'/cfg['source_btc_2026']/'bars.csv').open() as f:old=list(csv.DictReader(f))
            assert old[-1]['date_utc']=='2026-09-30';previous=float(old[-1]['close'])
        for item in files:
            part=list(read_archive(ROOT/item['raw_path'],item['timestamp_unit']));date=item['period']+'-01' if item['frequency']=='monthly' else item['period'];dt=datetime.datetime.fromisoformat(date).replace(tzinfo=datetime.timezone.utc);expected=calendar.monthrange(dt.year,dt.month)[1]*288 if item['frequency']=='monthly' else 288;start=int(dt.timestamp()*1e6)
            assert [r['open_time_us'] for r in part]==list(range(start,start+expected*300_000_000,300_000_000));item['rows']=len(part)
            if item['role']=='reference':previous=part[-1]['close']
            else:allrows.extend(part)
        assert previous is not None;processed=[]
        for row in allrows:
            timestamp=iso_from_us(row['open_time_us']);dt=datetime.datetime.fromtimestamp(row['open_time_us']/1e6,datetime.timezone.utc);ret=math.log(row['close']/previous);previous=row['close']
            processed.append({'timestamp_utc':timestamp,**row,'return_log':ret,'signed_taker_volume':2*row['taker_buy_volume']-row['volume'],'range_log':math.log(row['high']/row['low']),'date_utc':timestamp[:10],'month_utc':timestamp[:7],'slot_utc':dt.hour*12+dt.minute//5,'split':'v2_new_data'})
        count=7200 if symbol=='BTCUSDT' else 190944;assert len(processed)==count;times=[r['open_time_us'] for r in processed];assert times==list(range(times[0],times[0]+count*300_000_000,300_000_000))
        output=ROOT/'data/processed'/dataset;output.mkdir(parents=True,exist_ok=True);target=output/'bars.csv';s=io.StringIO(newline='');w=csv.DictWriter(s,fieldnames=list(processed[0]));w.writeheader();w.writerows(processed);content=s.getvalue().encode()
        if target.exists():assert target.read_bytes()==content
        else:target.write_bytes(content)
        documents=[]
        for name in ['README.md','TERMS_AND_CONDITIONS.md']:
            source=ROOT/'data/manifests'/cfg['source_btc_2026']/name;dest=manifest/name
            if not dest.exists():shutil.copyfile(source,dest)
            documents.append({'path':str(dest.relative_to(ROOT)),'url':'https://raw.githubusercontent.com/binance/binance-public-data/master/'+name,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'origin':'Byte-identical same-session terms snapshot retained from existing BTC acquisition'})
        record={'symbol':symbol,'dataset':dataset,'source':'Binance Vision spot','frequency':'5m','timezone':'UTC','documents':documents,'files':files,'license':'Observed CC BY-NC-SA 4.0; Binance Vision attribution','retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};p=manifest/'download_manifest.json'
        if p.exists():assert [r['sha256'] for r in json.loads(p.read_text())['files']]==[r['sha256'] for r in files]
        else:p.write_text(json.dumps(record,indent=2)+'\n')
        report={'status':'pass','symbol':symbol,'rows':count,'days':count//288,'first_utc':processed[0]['timestamp_utc'],'last_utc':processed[-1]['timestamp_utc'],'missing':0,'duplicates':0,'rows_dropped':0,'gaps_filled':0,'processed_sha256':hashlib.sha256(content).hexdigest(),'member_review':'not_run'};(manifest/'quality_report.json').write_text(json.dumps(report,indent=2)+'\n');reports.append(report)
    print(json.dumps({'status':'pass','archives':len(records),'datasets':reports},indent=2))


if __name__=='__main__':main()
