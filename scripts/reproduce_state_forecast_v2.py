#!/usr/bin/env python3
"""Rebuild new data, forecasts and mechanism interventions in an isolated root."""
from pathlib import Path
import argparse,gzip,hashlib,json,shutil,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser();p.add_argument('--destination',required=True,type=Path);p.add_argument('--use-local-data',action='store_true');args=p.parse_args();dest=args.destination.resolve()
    if dest.exists():p.error('destination must not exist')
    dest.mkdir(parents=True);start=time.perf_counter();shutil.copytree(ROOT/'src',dest/'src',ignore=shutil.ignore_patterns('__pycache__'))
    for folder in ['scripts','configs','docs/AB','data/manifests']:(dest/folder).mkdir(parents=True,exist_ok=True)
    for name in ['publication_integrity','fetch_market_data','prepare_market_data','fetch_forecast_data','fetch_state_forecast_v2_data','run_state_forecast_v2','run_state_mechanism_v2','summarize_state_forecast_v2','check_state_forecast_v2','check_theory_foundations']:shutil.copyfile(ROOT/f'scripts/{name}.py',dest/f'scripts/{name}.py')
    for name in ['forecast_v1','state_forecast_v2']:shutil.copyfile(ROOT/f'configs/{name}.json',dest/f'configs/{name}.json')
    for name in ['forecast_contract','state_forecast_v2_contract','state_forecast_v2_feature_spec']:shutil.copyfile(ROOT/f'docs/AB/{name}.md',dest/f'docs/AB/{name}.md')
    if (ROOT/'data/publication_adaptations.json').exists():shutil.copyfile(ROOT/'data/publication_adaptations.json',dest/'data/publication_adaptations.json')
    cfg=json.loads((ROOT/'configs/state_forecast_v2.json').read_text());datasets=[cfg[k] for k in ['source_btc_2025','source_btc_2026','source_btc_new','source_eth_new']]
    for dataset in datasets:shutil.copytree(ROOT/'data/manifests'/dataset,dest/'data/manifests'/dataset)
    shutil.copyfile(ROOT/'data/manifests/state_forecast_v2_pre_download.json',dest/'data/manifests/state_forecast_v2_pre_download.json');commands=[]
    def call(name):
        command=[sys.executable,str(dest/f'scripts/{name}.py')];commands.append(command);subprocess.run(command,cwd=dest,check=True)
    if args.use_local_data:
        for dataset in datasets:shutil.copytree(ROOT/'data/processed'/dataset,dest/'data/processed'/dataset)
    else:
        for name in ['publication_integrity','fetch_market_data','prepare_market_data','fetch_forecast_data','fetch_state_forecast_v2_data']:call(name)
    for name in ['run_state_forecast_v2','run_state_mechanism_v2','summarize_state_forecast_v2']:call(name)
    if not args.use_local_data:call('check_state_forecast_v2')
    comparisons=[]
    for run in ['state_forecast_v2','state_mechanism_v2']:
        for source in sorted((ROOT/'results/tables'/run).glob('*.csv')):
            actual=dest/'results/tables'/run/source.name;same=source.read_bytes()==actual.read_bytes();comparisons.append({'run':run,'table':source.name,'identical_bytes':same,'sha256':hashlib.sha256(source.read_bytes()).hexdigest()})
    raw=ROOT/'results/tables/state_mechanism_v2/series.csv.gz';new=dest/'results/tables/state_mechanism_v2/series.csv.gz';same=gzip.decompress(raw.read_bytes())==gzip.decompress(new.read_bytes());assert same and all(r['identical_bytes'] for r in comparisons)
    report={'status':'pass','fresh_download':not args.use_local_data,'source_archive_count_if_fresh':94 if not args.use_local_data else 0,'tables':comparisons,'mechanism_decompressed_series_identical':same,'commands':commands,'seconds':time.perf_counter()-start,'member_review':'not_run'};(dest/'results/checks/state_forecast_v2/portable_reproduction.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':'pass','identical_csv_tables':len(comparisons),'mechanism_series_identical':same,'fresh_download':not args.use_local_data,'seconds':report['seconds']},indent=2))


if __name__=='__main__':main()
