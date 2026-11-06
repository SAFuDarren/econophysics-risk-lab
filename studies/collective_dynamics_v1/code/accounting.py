"""Post-primary, frozen-output diagnostic; no new fitting or model selection."""
import csv,json
import numpy as np
import pandas as pd
from model import R,load,summaries,window

def main():
    a=summaries(load());pred=pd.read_csv(R/'tables/predictions.csv');pred=pred[pred.model=='MechanismSelected'];fit=pd.read_csv(R/'tables/fit_diagnostics.csv');rows=[]
    lookup={(int(x.budget_days),x.target_date,x.model,float(x.penalty)):x for x in fit.itertuples()}
    for x in pred.itertuples():
        target=int(np.searchsorted(a['dates'],x.target_date));w=window(a,target-x.budget_days,target);d=lookup[(x.budget_days,x.target_date,x.variant,x.penalty)];theta=np.array(json.loads(d.coefficients));m=w['pressure'][-1];s=w['slow'][-1];adapt=w['adaptation'][-1]
        design=np.array([1,m] if x.variant=='MeanFieldFast' else ([1,m,-adapt] if x.variant=='MeanFieldMemory' else [1,m,s,-adapt]));mh=float(np.tanh(design@theta));meanf=w['Vforecast'][-1]*mh;secondf=max(d.flow_scale*w['V2forecast'][-1]*(mh*mh+w['dispersion7'][-1]+d.transition_mse),meanf*meanf);raw=x.forecast_rv/d.risk_scale/288
        rows.append(dict(budget_days=x.budget_days,target_date=x.target_date,period=x.period,variant=x.variant,predicted_pressure=mh,directional_mean_flow_share=float(meanf*meanf/secondf),predicted_residual_risk_share=float(w['eta7'][-1]/raw),pressure_condition=d.pressure_condition))
    with (R/'tables/frozen_risk_accounting.csv').open('w',newline='') as f:wri=csv.DictWriter(f,fieldnames=list(rows[0]));wri.writeheader();wri.writerows(rows)

if __name__=='__main__':main()
