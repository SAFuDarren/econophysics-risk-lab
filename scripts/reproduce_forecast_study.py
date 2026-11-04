#!/usr/bin/env python3
"""Reconstruct raw data and all forecast tables in a fresh directory."""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--destination',type=Path,required=True);parser.add_argument('--use-local-data',action='store_true');args=parser.parse_args();dest=args.destination.resolve()
    if dest.exists():parser.error('destination must not exist')
    dest.mkdir(parents=True);start=time.perf_counter();cfg=json.loads((ROOT/'configs/forecast_v1.json').read_text());shutil.copytree(ROOT/'src',dest/'src',ignore=shutil.ignore_patterns('__pycache__'));(dest/'scripts').mkdir();(dest/'configs').mkdir();(dest/'docs/AB').mkdir(parents=True)
    for name in ['fetch_market_data.py','prepare_market_data.py','fetch_forecast_data.py','run_forecast_study.py','summarize_forecast_study.py','check_forecast_study.py']:shutil.copyfile(ROOT/'scripts'/name,dest/'scripts'/name)
    shutil.copyfile(ROOT/'configs/forecast_v1.json',dest/'configs/forecast_v1.json');shutil.copyfile(ROOT/'docs/AB/forecast_contract.md',dest/'docs/AB/forecast_contract.md')
    for key in ['dataset_2025','dataset_2026']:shutil.copytree(ROOT/'data/manifests'/cfg[key],dest/'data/manifests'/cfg[key])
    commands=[]
    def call(name):
        command=[sys.executable,str(dest/'scripts'/name)];commands.append(command);subprocess.run(command,cwd=dest,check=True)
    if args.use_local_data:
        for key in ['dataset_2025','dataset_2026']:shutil.copytree(ROOT/'data/processed'/cfg[key],dest/'data/processed'/cfg[key])
    else:
        call('fetch_market_data.py');call('prepare_market_data.py');call('fetch_forecast_data.py')
    call('run_forecast_study.py');call('summarize_forecast_study.py')
    if not args.use_local_data:call('check_forecast_study.py')
    comparisons=[]
    for expected in sorted((ROOT/'results/tables/forecast_v1').glob('*.csv')):
        actual=dest/'results/tables/forecast_v1'/expected.name;same=actual.exists() and expected.read_bytes()==actual.read_bytes();comparisons.append({'table':expected.name,'identical_bytes':same,'sha256':hashlib.sha256(expected.read_bytes()).hexdigest()})
    assert all(r['identical_bytes'] for r in comparisons),comparisons
    report={'status':'pass','fresh_download':not args.use_local_data,'tables':comparisons,'commands':commands,'seconds':time.perf_counter()-start,'member_review':'not_run'};(dest/'results/checks/forecast_v1/portable_reproduction.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':'pass','identical_csv_tables':len(comparisons),'fresh_download':not args.use_local_data,'seconds':report['seconds']},indent=2))


if __name__=='__main__':main()
