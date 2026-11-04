"""Official archive parsing with explicit per-file time units and no gap filling."""
import calendar,csv,datetime,hashlib,io,json,math,zipfile
from pathlib import Path

UTC=datetime.timezone.utc


def iso_from_us(value):
    return datetime.datetime.fromtimestamp(value/1_000_000,UTC).isoformat().replace('+00:00','Z')


def read_archive(path,timestamp_unit):
    multiplier={'milliseconds':1000,'microseconds':1}[timestamp_unit]
    with zipfile.ZipFile(path) as archive:
        files=[x for x in archive.namelist() if x.endswith('.csv')]
        if len(files)!=1:raise ValueError('unexpected archive members')
        stream=io.TextIOWrapper(archive.open(files[0]),encoding='utf-8-sig',newline='')
        for fields in csv.reader(stream):
            if fields and fields[0].lower() in ['open_time','open time']:continue
            if len(fields)!=12:raise ValueError('expected 12 kline columns')
            op,cl=int(fields[0])*multiplier,int(fields[6])*multiplier
            o,h,l,c,v,d=[float(fields[i]) for i in [1,2,3,4,5,7]]
            count=int(fields[8]);vb=float(fields[9]);db=float(fields[10])
            if not all(math.isfinite(x) for x in [o,h,l,c,v,d,vb,db]):raise ValueError('nonfinite field')
            if min(o,h,l,c)<=0 or min(v,d,vb,db,count)<0:raise ValueError('invalid price/activity')
            tolerance=1e-8
            if h+1e-7<max(o,c,l) or l-1e-7>min(o,c,h):raise ValueError('OHLC inconsistent')
            if vb>v+tolerance or db>d+1e-5:raise ValueError('taker buy exceeds total')
            if op%300_000_000:raise ValueError('open not on 5-minute UTC grid')
            expected=300_000_000-multiplier
            if cl-op!=expected:raise ValueError('unexpected close timestamp convention')
            if v and not l-1e-5<=d/v<=h+1e-5:raise ValueError('VWAP outside OHLC range')
            yield {'open_time_us':op,'close_time_us':cl,'open':o,'high':h,'low':l,'close':c,
                   'volume':v,'quote_volume':d,'trades':count,'taker_buy_volume':vb,'taker_buy_quote_volume':db}


def prepare_dataset(root,dataset):
    root=Path(root);manifest_dir=root/'data/manifests'/dataset
    manifest=json.loads((manifest_dir/'download_manifest.json').read_text())
    months=[];reference=None;all_rows=[]
    for item in manifest['files']:
        path=root/item['raw_path']
        if hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('source hash changed')
        rows=list(read_archive(path,item['timestamp_unit']))
        if item['role']=='reference_close_only':
            if len(rows)!=288:raise ValueError('reference day incomplete')
            reference=rows[-1]
            continue
        year,month=map(int,item['period'].split('-'));expected=calendar.monthrange(year,month)[1]*288
        first=int(datetime.datetime(year,month,1,tzinfo=UTC).timestamp()*1_000_000)
        times=[r['open_time_us'] for r in rows]
        correct=times==list(range(first,first+expected*300_000_000,300_000_000))
        months.append({'period':item['period'],'rows':len(rows),'expected_rows':expected,'missing_or_duplicate_or_out_of_order':not correct,'first_utc':iso_from_us(times[0]),'last_utc':iso_from_us(times[-1]),'source_sha256':item['sha256']})
        if not correct:raise ValueError('month grid incomplete or inconsistent; no filling performed')
        all_rows.extend(rows)
    times=[r['open_time_us'] for r in all_rows]
    expected_start=int(datetime.datetime(2025,1,1,tzinfo=UTC).timestamp()*1_000_000)
    assert reference and reference['open_time_us']==expected_start-300_000_000
    if len(all_rows)!=105120 or times!=list(range(expected_start,expected_start+105120*300_000_000,300_000_000)):raise ValueError('full year incomplete')
    output=root/'data/processed'/dataset;output.mkdir(parents=True,exist_ok=True)
    processed=[];previous=reference['close'];split_time=int(datetime.datetime(2025,7,1,tzinfo=UTC).timestamp()*1_000_000)
    for row in all_rows:
        timestamp=iso_from_us(row['open_time_us']);dt=datetime.datetime.fromtimestamp(row['open_time_us']/1_000_000,UTC)
        r=math.log(row['close']/previous);previous=row['close']
        processed.append({'timestamp_utc':timestamp,**row,'return_log':r,'signed_taker_volume':2*row['taker_buy_volume']-row['volume'],'range_log':math.log(row['high']/row['low']),
                          'date_utc':timestamp[:10],'month_utc':timestamp[:7],'slot_utc':dt.hour*12+dt.minute//5,'split':'calibration' if row['open_time_us']<split_time else 'holdout'})
    target=output/'bars.csv'
    if target.exists():raise FileExistsError('processed snapshot exists; do not overwrite')
    with target.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(processed[0]));w.writeheader();w.writerows(processed)
    report={'status':'pass','kind':'REAL_DATA','dataset':dataset,'rows':len(processed),'expected_rows':105120,'calibration_rows':sum(r['split']=='calibration' for r in processed),'holdout_rows':sum(r['split']=='holdout' for r in processed),
            'first_open_utc':processed[0]['timestamp_utc'],'last_open_utc':processed[-1]['timestamp_utc'],'reference_close':reference['close'],'reference_open_utc':iso_from_us(reference['open_time_us']),
            'missing':0,'duplicates':0,'out_of_order':0,'nonfinite':0,'invalid_OHLC':0,'invalid_volume_or_taker':0,'rows_dropped':0,'gaps_filled':0,'zero_volume_bars':sum(r['volume']==0 for r in processed),'zero_return_bars':sum(r['return_log']==0 for r in processed),
            'timestamp_rule':'2024 ms and 2025 us per official archive README; canonical open_time_us/close_time_us','source_files':months,'processed_path':str(target.relative_to(root)),'processed_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
            'license':'CC BY-NC-SA 4.0; Binance Vision attribution; terms snapshot in manifest folder','member_review':'not_run'}
    (manifest_dir/'quality_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return report
