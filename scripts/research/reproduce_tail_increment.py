#!/usr/bin/env python3
"""Independently reconstruct all numeric evidence using the frozen price snapshot."""

from pathlib import Path as _ProjectPath
import sys as _project_sys
_project_sys.path.insert(0, str(_ProjectPath(__file__).resolve().parents[1]))
from _bootstrap import ROOT as PROJECT_ROOT, script_path, resolve_recorded_path
from pathlib import Path
import hashlib,json,shutil,subprocess,sys,tempfile,time
ROOT=PROJECT_ROOT

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    import numpy as np
    start=time.perf_counter();check=ROOT/'results/checks/tail_increment_v1';source=ROOT/'results/tables/tail_increment_v1';commands=[];log=[]
    files=['configs/tail_increment_v1.json','configs/us_equity_v1.json','docs/AB/tail_increment_v1_contract.md','docs/decisions/2026-10-27-tail-increment.md','data/manifests/tail_increment_v1/method_before_external_download.json','src/econophysics/model.py','src/econophysics/us_equity.py','src/econophysics/tail_increment.py','data/processed/us_equity_v1/historical.csv','data/processed/us_equity_v1/confirmation.csv']
    scripts=['run_tail_increment.py','run_tail_synthetic.py','analyze_tail_increment.py','run_tail_mc_full.py','audit_tail_analytic.py','supplement_tail_scores.py']
    missing = [name for name in files if not (ROOT / name).is_file()]
    for name in scripts:
        try:
            script_path(name)
        except FileNotFoundError:
            missing.append(name)
    if missing:
        raise SystemExit('The complete frozen tail-study bundle is required for this historical full rerun. Missing: ' + ', '.join(missing))
    with tempfile.TemporaryDirectory(prefix='erl-tail-reproduce-') as folder:
        fresh=Path(folder).resolve()
        for name in files:
            target=fresh/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
        shutil.copytree(ROOT / 'src', fresh / 'src', dirs_exist_ok=True, ignore=shutil.ignore_patterns('__pycache__'))
        shutil.copytree(ROOT / 'scripts', fresh / 'scripts', dirs_exist_ok=True, ignore=shutil.ignore_patterns('__pycache__'))
        def run(script,*arguments):
            command=[sys.executable,str(script_path(script, root=fresh)),*arguments];commands.append(command);result=subprocess.run(command,cwd=fresh,capture_output=True,text=True);log.append(result.stdout+'\n'+result.stderr);
            if result.returncode:raise RuntimeError(result.stderr)
            print(json.dumps({'completed':script,'arguments':arguments}),flush=True)
        run('run_tail_increment.py','--stage','select')
        original_selection=json.loads((check/'selection_freeze.json').read_text())['selection'];new_selection=json.loads((fresh/'results/checks/tail_increment_v1/selection_freeze.json').read_text())['selection'];assert original_selection==new_selection
        target=fresh/'data/processed/tail_increment_v1/external.csv';target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/'data/processed/tail_increment_v1/external.csv',target)
        run('run_tail_increment.py','--stage','sector');run('run_tail_increment.py','--stage','external');run('run_tail_increment.py','--stage','mc');run('run_tail_synthetic.py');run('analyze_tail_increment.py');run('run_tail_mc_full.py');run('audit_tail_analytic.py');run('supplement_tail_scores.py')
        table_checks=[];array_checks={}
        for p in sorted(source.glob('*.csv')):
            rebuilt=fresh/p.relative_to(ROOT);table_checks.append({'table':p.name,'identical_bytes':rebuilt.exists() and sha(p)==sha(rebuilt),'sha256':sha(p)})
        for p in sorted(source.glob('*.npz')):
            a=np.load(p);b=np.load(fresh/p.relative_to(ROOT));array_checks[p.name]={key:bool(np.array_equal(a[key],b[key],equal_nan=True) if a[key].dtype.kind in 'fc' else np.array_equal(a[key],b[key])) for key in a.files}
        good=all(x['identical_bytes'] for x in table_checks) and all(all(v.values()) for v in array_checks.values())
        report={'status':'pass' if good else 'fail','scope':'Isolated-directory full numeric rerun from same frozen provider snapshots; no new download or new holdout','csv_tables':table_checks,'causal_arrays':array_checks,'validation_selection_identical':True,'commands':commands,'seconds':time.perf_counter()-start,'member_scientific_review':'not_run'}
    (check/'portable_reproduction.json').write_text(json.dumps(report,indent=2)+'\n');(check/'portable_reproduction.log').write_text('\n'.join(log));print(json.dumps({k:v for k,v in report.items() if k not in ['commands','causal_arrays','csv_tables']},indent=2))
    if not good:raise SystemExit(1)

if __name__=='__main__':main()
