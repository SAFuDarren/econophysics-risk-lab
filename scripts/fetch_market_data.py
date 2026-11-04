#!/usr/bin/env python3
"""Fetch immutable local copies of official BTCUSDT archives and verify SHA256."""
from pathlib import Path
import argparse,datetime,hashlib,json,time,urllib.request,zipfile
ROOT=Path(__file__).resolve().parents[1]


def get(url):
    last=None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url,timeout=45) as response:
                return response.read(),dict(response.headers)
        except Exception as exc:
            last=exc
            if attempt<2:time.sleep(.5*(attempt+1))
    raise last


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--dataset',default='binance_btcusdt_2025_5m_v1');args=parser.parse_args()
    if args.dataset!='binance_btcusdt_2025_5m_v1':parser.error('only the locked dataset is supported')
    raw=ROOT/'data/raw'/args.dataset;manifest=ROOT/'data/manifests'/args.dataset
    raw.mkdir(parents=True,exist_ok=True);manifest.mkdir(parents=True,exist_ok=True)
    docs=[]
    for name in ['README.md','TERMS_AND_CONDITIONS.md']:
        path=manifest/name;url='https://raw.githubusercontent.com/binance/binance-public-data/master/'+name
        if not path.exists():path.write_bytes(get(url)[0])
        docs.append({'path':str(path.relative_to(ROOT)),'url':url,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    requests=[('daily','2024-12-31','milliseconds','reference_close_only')]+[('monthly',f'2025-{m:02}','microseconds','analysis') for m in range(1,13)]
    records=[]
    for frequency,period,unit,role in requests:
        name=f'BTCUSDT-5m-{period}.zip';url=f'https://data.binance.vision/data/spot/{frequency}/klines/BTCUSDT/5m/{name}'
        target=raw/name;checksum=raw/(name+'.CHECKSUM')
        cached=target.exists() and checksum.exists()
        if not checksum.exists():checksum.write_bytes(get(url+'.CHECKSUM')[0])
        expected=checksum.read_text().split()[0].lower()
        headers={}
        if not target.exists():
            content,headers=get(url);actual=hashlib.sha256(content).hexdigest()
            if actual!=expected:raise ValueError('remote checksum mismatch: '+name)
            target.write_bytes(content)
        actual=hashlib.sha256(target.read_bytes()).hexdigest()
        if actual!=expected:raise ValueError('cached file mismatch; original retained: '+name)
        with zipfile.ZipFile(target) as z:
            if z.testzip() is not None:raise ValueError('zip CRC failure')
            members=[i for i in z.infolist() if not i.is_dir()]
            if len(members)!=1 or not members[0].filename.endswith('.csv'):raise ValueError('unexpected archive members')
        records.append({'period':period,'role':role,'url':url,'checksum_url':url+'.CHECKSUM','raw_path':str(target.relative_to(ROOT)),'checksum_path':str(checksum.relative_to(ROOT)),
                        'sha256':actual,'bytes':target.stat().st_size,'timestamp_unit':unit,'zip_crc':'pass','cached':cached,'http_etag':headers.get('ETag'),'http_last_modified':headers.get('Last-Modified')})
        print(f'Verified {name}: {target.stat().st_size} bytes',flush=True)
    output={'dataset':args.dataset,'source':'Binance Vision','venue':'Binance spot','symbol':'BTCUSDT','frequency':'5m','timezone':'UTC','start':'2025-01-01T00:00:00Z','end_exclusive':'2026-01-01T00:00:00Z',
            'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'documents':docs,'files':records,'license_as_observed':'CC BY-NC-SA 4.0; dataset terms v1.0 last updated 2026-08-26','analysis_scope':'non-commercial academic research',
            'distribution_plan':'Raw and complete processed archives remain local; share attributed aggregate outputs and downloader/manifests.','status':'all_archives_verified; content quality checked separately'}
    path=manifest/'download_manifest.json'
    if path.exists():
        old=json.loads(path.read_text());assert [(x['url'],x['sha256']) for x in old['files']]==[(x['url'],x['sha256']) for x in records]
        print('Existing immutable download manifest retained')
    else:path.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':main()
