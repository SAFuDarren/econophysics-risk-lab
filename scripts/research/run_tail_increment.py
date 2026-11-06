#!/usr/bin/env python3
"""Run frozen, covariance-matched forecast comparisons with stage boundaries."""

from pathlib import Path as _ProjectPath
import sys as _project_sys
_project_sys.path.insert(0, str(_ProjectPath(__file__).resolve().parents[1]))
from _bootstrap import ROOT as PROJECT_ROOT, script_path, resolve_recorded_path
from publication_integrity import matches_recorded_digest
from pathlib import Path
import argparse,csv,datetime as dt,hashlib,json,sys,time
ROOT=PROJECT_ROOT;sys.path.insert(0,str(ROOT/'src'))
import numpy as np
from econophysics.us_equity import load_panel,write_csv
from econophysics.tail_increment import build_laws,evaluate_panel

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def load_external(cfg):
    rows=list(csv.DictReader((ROOT/'data/processed/tail_increment_v1/external.csv').open()));names=cfg['external_panel'];dates=sorted(set(r['date'] for r in rows));lookup={(r['date'],r['symbol']):float(r['adjusted_close']) for r in rows};p=np.array([[lookup[d,s] for s in names] for d in dates]);return np.array(dates[1:]),p[1:]/p[:-1]-1

def main():
    p=argparse.ArgumentParser();p.add_argument('--stage',choices=['select','sector','external','mc'],required=True);a=p.parse_args();cfg=json.loads((ROOT/'configs/tail_increment_v1.json').read_text());out=ROOT/'results/tables/tail_increment_v1';check=ROOT/'results/checks/tail_increment_v1';out.mkdir(parents=True,exist_ok=True);check.mkdir(parents=True,exist_ok=True);start=time.perf_counter()
    frozen=json.loads((ROOT/'data/manifests/tail_increment_v1/method_before_external_download.json').read_text())
    for path,h in frozen['sha256'].items():assert matches_recorded_digest(ROOT/path,h,ROOT),('Frozen method changed',path)
    if a.stage=='select':assert not (ROOT/'data/raw/tail_increment_v1').exists(),'Selection must precede external download'
    draws=cfg['mc_sensitivity_draws'] if a.stage=='mc' else cfg['forecast_draws'];laws,grid,diagnostics,_=build_laws(cfg,draws=draws)
    if a.stage=='select':
        write_csv(out/'law_bank_diagnostics.csv',diagnostics);(check/'law_inventory.json').write_text(json.dumps([{'index':j,'name':l.name,'family':l.family,**l.params} for j,l in enumerate(laws)],indent=2)+'\n')
    if a.stage in ['select','sector']:
        uscfg=json.loads((ROOT/'configs/us_equity_v1.json').read_text());dates,r,_,_=load_panel(ROOT,uscfg);r=r[:,:9]
    else:
        if not (check/'selection_freeze.json').exists():raise SystemExit('Missing selection freeze')
        dates,r=load_external(cfg)
    allrows=[];allchoices=[]
    for covariance in cfg['covariances'] if a.stage!='mc' else [cfg['primary_covariance']]:
        periods={'validation':cfg['splits']['validation']} if a.stage=='select' else {k:v for k,v in cfg['splits'].items() if k!='validation'}
        rows,choices,arrays=evaluate_panel(dates,r,covariance,cfg,laws,grid,periods,sensitivity=a.stage=='mc');allrows+=rows;allchoices+=choices
        if a.stage!='select':np.savez_compressed(out/f'{a.stage}_{covariance}_causal_arrays.npz',dates=dates,returns=r,**arrays)
        print(json.dumps({'stage':a.stage,'covariance':covariance,'forecast_rows':len(rows),'elapsed_seconds':round(time.perf_counter()-start,2)}),flush=True)
    write_csv(out/f'{a.stage}_daily.csv',allrows);write_csv(out/f'{a.stage}_law_choices.csv',allchoices)
    if a.stage=='select':
        selected={}
        for covariance in cfg['covariances']:
            selected[covariance]={}
            for metric in ['pinball05','brier']:
                means={name:float(np.mean([row[metric] for row in allrows if row['covariance']==covariance and row['method']==name])) for name in cfg['baselines']}
                selected[covariance][metric]={'baseline':min(means,key=lambda name:(means[name],name)),'validation_scores':means}
        record={'recorded_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'status':'frozen_before_external_download','selection':selected,'external_raw_count':0,'method_sha256':frozen['sha256'],'source_sha256':{str(path.relative_to(ROOT)):sha(path) for path in [Path(__file__),ROOT/'src/econophysics/tail_increment.py',out/'select_daily.csv']}}
        path=check/'selection_freeze.json';assert not path.exists(),'Keep original selection freeze';path.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(selected,indent=2))
    record={'stage':a.stage,'status':'pass','seconds':time.perf_counter()-start,'draws':draws,'source_sha256':{str(path.relative_to(ROOT)):sha(path) for path in [Path(__file__),ROOT/'src/econophysics/tail_increment.py',ROOT/'configs/tail_increment_v1.json']},'output_sha256':sha(out/f'{a.stage}_daily.csv'),'forecast_rows':len(allrows),'member_scientific_review':'not_run'};(check/f'{a.stage}_run.json').write_text(json.dumps(record,indent=2)+'\n')

if __name__=='__main__':main()
