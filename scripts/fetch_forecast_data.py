#!/usr/bin/env python3
"""Fetch the predeclared 2026 extension, preserving the existing 2025 snapshot."""
from pathlib import Path
from publication_integrity import matches_recorded_digest
import calendar,csv,datetime,hashlib,json,sys,zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from fetch_market_data import get
from econophysics.market_data import read_archive,iso_from_us


def main():
    cfgpath=ROOT/'configs/forecast_v1.json';cfg=json.loads(cfgpath.read_text());dataset=cfg['dataset_2026'];manifest=ROOT/'data/manifests'/dataset;raw=ROOT/'data/raw'/dataset
    manifest.mkdir(parents=True,exist_ok=True);raw.mkdir(parents=True,exist_ok=True);lock=manifest/'pre_download_freeze.json'
    frozen={'config_sha256':hashlib.sha256(cfgpath.read_bytes()).hexdigest(),'contract_sha256':hashlib.sha256((ROOT/'docs/AB/forecast_contract.md').read_bytes()).hexdigest(),'recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'2026_local_archive_count_before_first_download':len(list(raw.glob('*.zip')))}
    if lock.exists():assert matches_recorded_digest(cfgpath,json.loads(lock.read_text())['config_sha256'],ROOT)
    else:
        assert frozen['2026_local_archive_count_before_first_download']==0
        lock.write_text(json.dumps(frozen,indent=2)+'\n')
    docs=[]
    for name in ['README.md','TERMS_AND_CONDITIONS.md']:
        path=manifest/name;url='https://raw.githubusercontent.com/binance/binance-public-data/master/'+name
        if not path.exists():path.write_bytes(get(url)[0])
        docs.append({'path':str(path.relative_to(ROOT)),'url':url,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    files=[];rows=[]
    for month in range(1,10):
        period=f'2026-{month:02}';name=f'BTCUSDT-5m-{period}.zip';url=f'https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/5m/{name}';path=raw/name;checksum=raw/(name+'.CHECKSUM')
        if not checksum.exists():checksum.write_bytes(get(url+'.CHECKSUM')[0])
        expected=checksum.read_text().split()[0].lower()
        if not path.exists():path.write_bytes(get(url)[0])
        actual=hashlib.sha256(path.read_bytes()).hexdigest();assert actual==expected
        with zipfile.ZipFile(path) as z:assert z.testzip() is None
        part=list(read_archive(path,'microseconds'));first=int(datetime.datetime(2026,month,1,tzinfo=datetime.timezone.utc).timestamp()*1_000_000);n=calendar.monthrange(2026,month)[1]*288
        assert [r['open_time_us'] for r in part]==list(range(first,first+n*300_000_000,300_000_000))
        rows.extend(part);files.append({'period':period,'raw_path':str(path.relative_to(ROOT)),'checksum_path':str(checksum.relative_to(ROOT)),'url':url,'checksum_url':url+'.CHECKSUM','timestamp_unit':'microseconds','sha256':actual,'rows':n,'bytes':path.stat().st_size})
        print(f'Verified {period}: {n} bars',flush=True)
    oldpath=ROOT/'data/processed'/cfg['dataset_2025']/'bars.csv';old=list(csv.DictReader(oldpath.open()));previous=float(old[-1]['close']);assert old[-1]['timestamp_utc']=='2025-12-31T23:55:00Z'
    output=ROOT/'data/processed'/dataset;output.mkdir(parents=True,exist_ok=True);target=output/'bars.csv';processed=[]
    import math
    for row in rows:
        timestamp=iso_from_us(row['open_time_us']);dt=datetime.datetime.fromtimestamp(row['open_time_us']/1e6,datetime.timezone.utc);ret=math.log(row['close']/previous);previous=row['close']
        processed.append({'timestamp_utc':timestamp,**row,'return_log':ret,'signed_taker_volume':2*row['taker_buy_volume']-row['volume'],'range_log':math.log(row['high']/row['low']),'date_utc':timestamp[:10],'month_utc':timestamp[:7],'slot_utc':dt.hour*12+dt.minute//5,'split':'validation' if timestamp[:10]<cfg['test_target_start'] else 'holdout'})
    import io
    stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fieldnames=list(processed[0]));writer.writeheader();writer.writerows(processed);content=stream.getvalue().encode()
    if target.exists():assert target.read_bytes()==content
    else:target.write_bytes(content)
    quality={'status':'pass','rows':len(processed),'days':len(processed)//288,'expected_rows':78624,'validation_days':90,'test_days':183,'missing':0,'duplicates':0,'rows_dropped':0,'gaps_filled':0,'zero_volume_bars':sum(r['volume']==0 for r in processed),'first_utc':processed[0]['timestamp_utc'],'last_utc':processed[-1]['timestamp_utc'],'processed_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'previous_close_from_2025':float(old[-1]['close']),'member_review':'not_run'}
    assert len(processed)==78624
    (manifest/'quality_report.json').write_text(json.dumps(quality,indent=2)+'\n')
    record={'dataset':dataset,'source':'Binance Vision','venue':'Binance spot','symbol':'BTCUSDT','frequency':'5m','timezone':'UTC','retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'documents':docs,'files':files,'existing_2025_processed_sha256':hashlib.sha256(oldpath.read_bytes()).hexdigest(),'market_derived_license':'Observed Binance Vision terms; CC BY-NC-SA 4.0; attribution retained'}
    p=manifest/'download_manifest.json'
    if p.exists():assert [(r['url'],r['sha256']) for r in json.loads(p.read_text())['files']]==[(r['url'],r['sha256']) for r in files]
    else:p.write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(quality,indent=2))


if __name__=='__main__':main()
