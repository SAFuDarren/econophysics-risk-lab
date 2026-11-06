#!/usr/bin/env python3
"""Fresh official-data and isolated complete numeric reproduction of the US study."""

from pathlib import Path as _ProjectPath
import sys as _project_sys
_project_sys.path.insert(0, str(_ProjectPath(__file__).resolve().parents[1]))
from _bootstrap import ROOT as PROJECT_ROOT, script_path, resolve_recorded_path
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,sys,time
import numpy as np
ROOT=PROJECT_ROOT

def main():
    p=argparse.ArgumentParser();p.add_argument('--destination',required=True,type=Path);p.add_argument('--use-local-data',action='store_true');args=p.parse_args();dest=args.destination.resolve()
    if dest.exists():p.error('Destination must not exist')
    dest.mkdir(parents=True);start=time.perf_counter();shutil.copytree(ROOT/'src',dest/'src',ignore=shutil.ignore_patterns('__pycache__'))
    for directory in ['configs','scripts','docs/AB','docs/theory','data/processed/us_equity_v1','data/manifests/us_equity_v1']:(dest/directory).mkdir(parents=True,exist_ok=True)
    shutil.copytree(ROOT/'scripts', dest/'scripts', dirs_exist_ok=True, ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copyfile(ROOT/'configs/us_equity_v1.json',dest/'configs/us_equity_v1.json');shutil.copyfile(ROOT/'docs/AB/us_equity_v1_contract.md',dest/'docs/AB/us_equity_v1_contract.md');shutil.copyfile(ROOT/'docs/theory/COLLECTIVE_PNL_v1.md',dest/'docs/theory/COLLECTIVE_PNL_v1.md')
    commands=[]
    def run(name,*args):
        command=[sys.executable,str(script_path(name+'.py', root=dest)),*args];commands.append(command);subprocess.run(command,cwd=dest,check=True)
    if args.use_local_data:shutil.copyfile(ROOT/'data/processed/us_equity_v1/historical.csv',dest/'data/processed/us_equity_v1/historical.csv')
    else:run('fetch_us_equity')
    run('run_us_equity','--select-only')
    if args.use_local_data:shutil.copyfile(ROOT/'data/processed/us_equity_v1/confirmation.csv',dest/'data/processed/us_equity_v1/confirmation.csv')
    else:run('fetch_us_equity','--stage','confirmation')
    run('run_us_equity');run('supplement_us_equity')
    if not args.use_local_data:run('check_us_equity')
    tables=[]
    for source in sorted((ROOT/'results/tables/us_equity_v1').glob('*.csv')):
        actual=dest/'results/tables/us_equity_v1'/source.name;same=source.read_bytes()==actual.read_bytes();tables.append({'table':source.name,'identical_bytes':same,'sha256':hashlib.sha256(source.read_bytes()).hexdigest()})
    a=np.load(ROOT/'results/tables/us_equity_v1/positions.npz');b=np.load(dest/'results/tables/us_equity_v1/positions.npz');arrays={k:np.array_equal(a[k],b[k]) for k in a.files};identical=all(t['identical_bytes'] for t in tables) and all(arrays.values())
    report={'status':'pass' if identical else 'source_or_numeric_drift','all_numeric_payloads_identical':identical,'fresh_download':not args.use_local_data,'source_files_if_fresh':22 if not args.use_local_data else 0,'tables':tables,'position_arrays':arrays,'commands':commands,'seconds':time.perf_counter()-start,'member_scientific_review':'not_run'};(dest/'results/checks/us_equity_v1/portable_reproduction.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'identical_csv_tables':sum(t['identical_bytes'] for t in tables),'total_csv_tables':len(tables),'identical_position_arrays':sum(arrays.values()),'total_position_arrays':len(arrays),'fresh_download':not args.use_local_data,'seconds':report['seconds']},indent=2))
    if not identical:raise SystemExit('Reproduction detected drift. Preserve both snapshots and inspect input revisions; do not overwrite the reference or silently relax equality. Fixed-snapshot replay requires --use-local-data.')

if __name__=='__main__':main()
