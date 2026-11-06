from pathlib import Path
import csv,json,time,hashlib
import numpy as np
import pandas as pd
from model import R,BUDGETS,PENALTIES,PRESSURE_MODELS,load,summaries,window,forecast,losses

def write(p,rows):
    with Path(p).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
    start=time.perf_counter();a=summaries(load());dates=a['dates'];targets=np.flatnonzero(dates>='2026-01-01');allrows=[];diagrows=[];models=['Persistence','ReturnHAR','MacroStat','DirectFlow']+PRESSURE_MODELS
    for B in BUDGETS:
        for ti,target in enumerate(targets):
            first=target-B;w=window(a,first,target);assert len(w['rv'])==B and dates[target-1]<dates[target]
            for model in models:
                for penalty in ([0.] if model in ['Persistence','DirectFlow'] else PENALTIES):
                    prediction,meta=forecast(w,model,penalty);assert prediction>0 and np.isfinite(prediction)
                    allrows.append(dict(model=model,budget_days=B,penalty=penalty,origin_date=str(dates[target-1]),target_date=str(dates[target]),input_first_date=str(dates[first]),input_last_date=str(dates[target-1]),input_days=B,training_pairs=B-1,actual_rv=float(a['rv'][target]),forecast_rv=prediction))
                    diagrows.append(dict(model=model,budget_days=B,penalty=penalty,target_date=str(dates[target]),**{k:json.dumps(v) if isinstance(v,list) else v for k,v in meta.items()}))
            if ti%60==0:print('Budget',B,'target',str(dates[target]),'seconds',round(time.perf_counter()-start,1),flush=True)
    frame=pd.DataFrame(allrows);val=frame[(frame.target_date>='2026-01-01')&(frame.target_date<'2026-04-01')].copy();val['qlike']=losses(val.actual_rv.to_numpy(),val.forecast_rv.to_numpy())['qlike'];selected={};grid=[]
    for B in BUDGETS:
        selected[str(B)]={}
        for model in models:
            g=val[(val.budget_days==B)&(val.model==model)].groupby('penalty').qlike.mean();p=float(g.idxmin());selected[str(B)][model]=dict(penalty=p,validation_qlike=float(g.loc[p]))
            for pp,q in g.items():grid.append(dict(model=model,budget_days=B,penalty=float(pp),validation_qlike=float(q)))
        primary=min(PRESSURE_MODELS[:3],key=lambda n:selected[str(B)][n]['validation_qlike']);selected[str(B)]['MechanismSelected']={**selected[str(B)][primary],'variant':primary}
    # Selection lock precedes any new primary-period scoring.
    (R/'fits/selection.json').write_text(json.dumps(dict(status='Q1-only selection, locked before Apr-Sep score tables',budgets=selected),indent=2));write(R/'tables/validation_grid.csv',grid)
    final=[]
    for B in BUDGETS:
        for model in models+['MechanismSelected']:
            choice=selected[str(B)][model];variant=choice.get('variant',model);sub=frame[(frame.budget_days==B)&(frame.model==variant)&(frame.penalty==choice['penalty'])].copy();sub['model']=model;sub['variant']=variant
            ls=losses(sub.actual_rv.to_numpy(),sub.forecast_rv.to_numpy());sub['period']=np.where(sub.target_date<'2026-04-01','validation',np.where(sub.target_date<'2026-10-01','primary','october'))
            for metric,values in ls.items():sub[metric]=values
            final.extend(sub.to_dict('records'))
    write(R/'tables/predictions.csv',final);write(R/'tables/fit_diagnostics.csv',diagrows)
    write(R/'tables/input_budget.csv',[dict(model=m,budget_days=B,raw_days=B,bars_per_day=288,bar_observations=B*288,training_pairs=B-1,required_fields='r' if m in ['Persistence','ReturnHAR'] else ('r,V,K,F' if m=='MacroStat' else 'r,V,F'),microscopic_labels=0,extra_warmup_days=0,pretrained_parameters=0) for B in BUDGETS for m in models+['MechanismSelected']])
    (R/'checks/run.json').write_text(json.dumps(dict(status='complete',seconds=time.perf_counter()-start,targets=len(targets),candidate_predictions=len(allrows),selected_predictions=len(final),input_sha256=hashlib.sha256((R/'inputs/macro_observables.npz').read_bytes()).hexdigest()),indent=2));print('Complete',round(time.perf_counter()-start,1),'seconds',flush=True)

if __name__=='__main__':main()
