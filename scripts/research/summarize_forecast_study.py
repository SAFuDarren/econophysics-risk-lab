#!/usr/bin/env python3
"""Explicit post-analysis nested-input and naive-baseline descriptive contrasts."""

from pathlib import Path as _ProjectPath
import sys as _project_sys
_project_sys.path.insert(0, str(_ProjectPath(__file__).resolve().parents[1]))
from _bootstrap import ROOT as PROJECT_ROOT, script_path, resolve_recorded_path
from pathlib import Path
import argparse,csv,hashlib,json,sys
ROOT=PROJECT_ROOT;sys.path.insert(0,str(ROOT/'src'))
import numpy as np
from econophysics.real_market_statistics import circular_day_weights
from econophysics.model import derived_seed


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run-id',default='forecast_v1');args=parser.parse_args();tables=ROOT/'results/tables'/args.run_id;cfg=json.loads((ROOT/'configs/forecast_v1.json').read_text());rows=list(csv.DictReader((tables/'test_predictions.csv').open()));by={m:np.array([float(r['log_mse']) for r in rows if r['model']==m]) for m in ['Persistence','HAR','HAR+Tail','HAR+All']};n=len(by['HAR']);out=[]
    for L in cfg['bootstrap_day_block_lengths']:
        w=circular_day_weights(n,L,cfg['bootstrap_replicates'],np.random.default_rng(derived_seed(cfg['seed'],f'forecast-block:{L}')))
        for m,b in [('HAR+All','HAR+Tail'),('HAR+All','Persistence'),('HAR','Persistence')]:
            values=100*(1-(w@by[m])/(w@by[b]));lo,hi=np.quantile(values,[.025,.975]);out.append({'model':m,'baseline':b,'metric':'log_mse','improvement_pct':float(100*(1-by[m].mean()/by[b].mean())),'ci_low':float(lo),'ci_high':float(hi),'day_block_length':L,'status':'Post-analysis descriptive; not part of the frozen confirmatory comparison family','reason':'All adds both volume-related features and return-only tail features. Nested Tail baseline clarifies attribution; Persistence reference separates total from incremental gains.'})
    with (tables/'post_analysis_contrasts.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(out[0]));writer.writeheader();writer.writerows(out)
    (ROOT/'results/checks'/args.run_id/'post_analysis_record.json').write_text(json.dumps({'status':'pass','scope':'Explicit post-analysis descriptive contrasts; original confirmatory family unchanged','script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'input_predictions_sha256':hashlib.sha256((tables/'test_predictions.csv').read_bytes()).hexdigest(),'output_sha256':hashlib.sha256((tables/'post_analysis_contrasts.csv').read_bytes()).hexdigest()},indent=2)+'\n')
    print(json.dumps([r for r in out if r['day_block_length']==7],indent=2))


if __name__=='__main__':main()
