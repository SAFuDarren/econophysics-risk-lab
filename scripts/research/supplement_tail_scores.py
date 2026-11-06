#!/usr/bin/env python3
"""Secondary 1% tail and joint VaR/ES scores from already frozen forecasts."""

from pathlib import Path as _ProjectPath
import sys as _project_sys
_project_sys.path.insert(0, str(_ProjectPath(__file__).resolve().parents[1]))
from _bootstrap import ROOT as PROJECT_ROOT, script_path, resolve_recorded_path
from pathlib import Path
import csv,json,sys
ROOT=PROJECT_ROOT;sys.path.insert(0,str(ROOT/'src'))
import numpy as np
from econophysics.us_equity import write_csv,block_weights

def main():
    cfg=json.loads((ROOT/'configs/tail_increment_v1.json').read_text());table=ROOT/'results/tables/tail_increment_v1';rng=np.random.default_rng(cfg['seed']+960);metrics=[];contrasts=[]
    for panel in ['sector','external']:
        rows=list(csv.DictReader((table/f'{panel}_daily.csv').open()))
        for row in rows:
            y,q,e=map(float,[row['y'],row['q01'],row['es01']]);row['fz01']=max(q-y,0)/(-.01*e)+q/e+np.log(-e)-1
        for covariance in cfg['covariances']:
            for period in ['historical_test','confirmation']:
                grouped={model:[r for r in rows if r['covariance']==covariance and r['period']==period and r['method']==model] for model in cfg['methods']};n=len(grouped['Herding']);weights=block_weights(n,20,cfg['bootstrap']['replicates'],rng)
                for model,data in grouped.items():
                    metrics.append({'panel':panel,'covariance':covariance,'period':period,'method':model,'days':n,'hits01':sum(int(r['hit01']) for r in data),'mean_pinball01':float(np.mean([float(r['pinball01']) for r in data])),'mean_fz05':float(np.mean([float(r['fz05']) for r in data])),'mean_fz01':float(np.mean([float(r['fz01']) for r in data]))})
                for metric in ['pinball01','fz05','fz01']:
                    a=np.array([float(r[metric]) for r in grouped['Herding']]);ba=weights@a/n
                    for baseline in cfg['baselines']:
                        b=np.array([float(r[metric]) for r in grouped[baseline]]);diff=ba-weights@b/n
                        contrasts.append({'panel':panel,'covariance':covariance,'period':period,'model':'Herding','baseline':baseline,'metric':metric,'days':n,'mean_model_loss':float(a.mean()),'mean_baseline_loss':float(b.mean()),'mean_loss_difference':float((a-b).mean()),'difference_ci_low':float(np.quantile(diff,.025)),'difference_ci_high':float(np.quantile(diff,.975)),'direction':'Negative difference favors herding','scope':'Exploratory secondary endpoint/all-baseline diagnostic. No new corrected winner claim; FZ scores are differences, not percentages.'})
    write_csv(table/'secondary_metrics.csv',metrics);write_csv(table/'secondary_contrasts.csv',contrasts)
    print(json.dumps({'status':'pass','metric_rows':len(metrics),'contrast_rows':len(contrasts),'forecast_refit':False},indent=2))

if __name__=='__main__':main()
