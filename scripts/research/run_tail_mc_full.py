#!/usr/bin/env python3
"""Numerical-resolution audit, no parameter/grid/reference changes."""

from pathlib import Path as _ProjectPath
import sys as _project_sys
_project_sys.path.insert(0, str(_ProjectPath(__file__).resolve().parents[1]))
from _bootstrap import ROOT as PROJECT_ROOT, script_path, resolve_recorded_path
from pathlib import Path
import csv,json,sys,time
ROOT=PROJECT_ROOT;sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'scripts'))
import numpy as np
from econophysics.tail_increment import build_laws,evaluate_panel
from econophysics.us_equity import write_csv,block_weights
from run_tail_increment import load_external

def main():
    cfg=json.loads((ROOT/'configs/tail_increment_v1.json').read_text());table=ROOT/'results/tables/tail_increment_v1';check=ROOT/'results/checks/tail_increment_v1';start=time.perf_counter();laws,grid,_,_=build_laws(cfg,draws=cfg['mc_sensitivity_draws']);dates,r=load_external(cfg);periods={k:v for k,v in cfg['splits'].items() if k!='validation'};rows,choices,_=evaluate_panel(dates,r,cfg['primary_covariance'],cfg,laws,grid,periods);write_csv(table/'mc_full_daily.csv',rows)
    selection=json.loads((check/'selection_freeze.json').read_text())['selection'][cfg['primary_covariance']];primary=list(csv.DictReader((table/'external_daily.csv').open()));lookup={(r['date'],r['method']):r for r in primary if r['covariance']==cfg['primary_covariance']};disagreements=sum(row['law']!=lookup[row['date'],row['method']]['law'] for row in rows);rng=np.random.default_rng(cfg['seed']+930);summary=[]
    for period in periods:
        grouped={m:[row for row in rows if row['period']==period and row['method']==m] for m in cfg['methods']};n=len(grouped['Herding']);w=block_weights(n,20,cfg['bootstrap']['replicates'],rng)
        for metric in ['pinball05','brier']:
            baseline=selection[metric]['baseline'];a=np.array([x[metric] for x in grouped['Herding']]);b=np.array([x[metric] for x in grouped[baseline]]);gain=100*(1-(w@a)/(w@b));summary.append({'period':period,'metric':metric,'baseline':baseline,'improvement_pct':100*(1-a.mean()/b.mean()),'ci_low':float(np.quantile(gain,.025)),'ci_high':float(np.quantile(gain,.975)),'scope':'16384-draw numerical sensitivity, not replacement primary result'})
    write_csv(table/'mc_full_contrasts.csv',summary);report={'status':'pass' if disagreements==0 else 'fail','scope':'Numerical resolution audit, same market observations and same fitted shapes','forecast_rows':len(rows),'shape_choice_disagreements':disagreements,'summary':summary,'seconds':time.perf_counter()-start};(check/'mc_full_run.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
