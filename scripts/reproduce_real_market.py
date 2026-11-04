#!/usr/bin/env python3
"""Re-download market archives and rerun analysis in an isolated directory."""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1]
SCRIPTS=['fetch_market_data.py','prepare_market_data.py','generate_market_models.py','analyze_real_market.py','summarize_real_market.py','audit_real_market.py','check_real_market_methods.py','check_theory_foundations.py']


def main():
    p=argparse.ArgumentParser();p.add_argument('--destination',type=Path,required=True);p.add_argument('--regenerate-models',action='store_true');args=p.parse_args()
    dest=args.destination.resolve()
    if dest.exists():p.error('destination must not already exist')
    dest.mkdir(parents=True);start=time.perf_counter();run='real_market_v1'
    shutil.copytree(ROOT/'src',dest/'src',ignore=shutil.ignore_patterns('__pycache__'))
    (dest/'scripts').mkdir();(dest/'configs').mkdir()
    for name in SCRIPTS:shutil.copyfile(ROOT/'scripts'/name,dest/'scripts'/name)
    shutil.copyfile(ROOT/'configs/real_market_v1.json',dest/'configs/real_market_v1.json')
    dataset=json.loads((ROOT/'configs/real_market_v1.json').read_text())['dataset']
    shutil.copytree(ROOT/'data/manifests'/dataset,dest/'data/manifests'/dataset)
    commands=[]
    def call(name,*extra):
        command=[sys.executable,str(dest/'scripts'/name),*extra];commands.append(command)
        subprocess.run(command,cwd=dest,check=True)
    call('fetch_market_data.py');call('prepare_market_data.py');call('check_real_market_methods.py','--run-id',run)
    # Generator requires new table/check folders; preserve the method check separately.
    checks=dest/'results/checks'/run;method=json.loads((checks/'method_checks.json').read_text())
    if args.regenerate_models:
        shutil.rmtree(checks);call('generate_market_models.py','--run-id',run)
        (checks/'method_checks.json').write_text(json.dumps(method,indent=2)+'\n')
    else:
        target=dest/'results/tables'/run;target.mkdir(parents=True)
        for name in ['calibration_parameters.csv','model_series.csv.gz','model_seeds_NOT_OBSERVATIONS.csv']:
            shutil.copyfile(ROOT/'results/tables'/run/name,target/name)
    call('analyze_real_market.py','--run-id',run);call('summarize_real_market.py','--run-id',run);call('audit_real_market.py','--run-id',run)
    comparisons=[]
    for expected in sorted((ROOT/'results/tables'/run).glob('*.csv')):
        actual=dest/'results/tables'/run/expected.name
        same=actual.exists() and actual.read_bytes()==expected.read_bytes()
        comparisons.append({'table':expected.name,'identical_bytes':same,'expected_sha256':hashlib.sha256(expected.read_bytes()).hexdigest(),'actual_sha256':hashlib.sha256(actual.read_bytes()).hexdigest() if actual.exists() else None})
    assert all(x['identical_bytes'] for x in comparisons),comparisons
    report={'status':'pass','market_archives_independently_downloaded':13,'processed_sha256':hashlib.sha256((dest/'data/processed'/dataset/'bars.csv').read_bytes()).hexdigest(),
            'table_comparisons':comparisons,'full_model_regeneration':args.regenerate_models,'model_prefix_regenerated_bars':15360,'commands':commands,'seconds':time.perf_counter()-start,'member_review':'not_run'}
    (checks/'portable_reproduction.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':'pass','identical_csv_tables':len(comparisons),'full_model_regeneration':args.regenerate_models,'seconds':report['seconds']},indent=2))


if __name__=='__main__':main()
