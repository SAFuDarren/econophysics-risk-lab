from pathlib import Path
import json,csv
import numpy as np
import pandas as pd
from scipy.stats import skew,kurtosis
from model import R,BUDGETS,load,summaries,window,forecast,pressure_fit,losses

def write(path,rows):
    with Path(path).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def draws(n,block,rng,B=19999):
    starts=rng.integers(0,n,(B,int(np.ceil(n/block))))
    return ((starts[:,:,None]+np.arange(block))%n).reshape(B,-1)[:,:n]

def holm(p):
    p=np.asarray(p);order=np.argsort(p);out=np.empty(len(p));val=0.
    for j,i in enumerate(order):val=max(val,min(1.,(len(p)-j)*p[i]));out[i]=val
    return out

def contrast(model,ref,period,B,metric,block,family,frame,rng,reference_budget=None):
    sub=frame[frame.period==period];x=sub[(sub.budget_days==B)&(sub.model==model)].sort_values('target_date');y=sub[(sub.budget_days==(B if reference_budget is None else reference_budget))&(sub.model==ref)].sort_values('target_date');assert list(x.target_date)==list(y.target_date)
    xx=x[metric].to_numpy();yy=y[metric].to_numpy();delta=yy-xx;ii=draws(len(delta),block,rng);boot=delta[ii].mean(1);base=yy[ii].mean(1);null=(delta-delta.mean())[ii].mean(1)
    basic_low=float(2*delta.mean()-np.quantile(boot,.975));basic_high=float(2*delta.mean()-np.quantile(boot,.025))
    return dict(model=model,reference=ref,budget_days=B,reference_budget=B if reference_budget is None else reference_budget,period=period,metric=metric,block_days=block,family=family,days=len(delta),model_loss_mean=float(xx.mean()),reference_loss_mean=float(yy.mean()),improvement=float(delta.mean()),improvement_pct=float(100*delta.mean()/yy.mean()),ci_low=float(np.quantile(boot,.025)),ci_high=float(np.quantile(boot,.975)),pct_ci_low=float(np.quantile(100*boot/base,.025)),pct_ci_high=float(np.quantile(100*boot/base,.975)),basic_ci_low=basic_low,basic_ci_high=basic_high,basic_pct_ci_low=float(100*basic_low/yy.mean()),basic_pct_ci_high=float(100*basic_high/yy.mean()),paired_sd=float(delta.std(ddof=1)),paired_standardized_effect=float(delta.mean()/delta.std(ddof=1)) if delta.std()>0 else 0.,paired_skew=float(skew(delta,bias=False)),paired_excess_kurtosis=float(kurtosis(delta,bias=False)),days_improved=int(np.sum(delta>0)),p_bootstrap=float((1+np.sum(null>=delta.mean()))/20000))

def main():
    frame=pd.read_csv(R/'tables/predictions.csv');fit=pd.read_csv(R/'tables/fit_diagnostics.csv');sel=json.loads((R/'fits/selection.json').read_text())['budgets'];scores=[]
    rng=np.random.default_rng(52530707)
    for (model,budget,period),g in frame.groupby(['model','budget_days','period']):
        for metric in ['qlike','mse','log_mse']:
            x=g[metric].to_numpy();ii=draws(len(x),7,rng);means=x[ii].mean(1);scores.append(dict(model=model,budget_days=int(budget),period=period,metric=metric,days=len(x),mean=float(x.mean()),sd=float(x.std(ddof=1)),ci_low=float(np.quantile(means,.025)),ci_high=float(np.quantile(means,.975)),forecast_actual_total_ratio=float(g.forecast_rv.sum()/g.actual_rv.sum())))
    write(R/'tables/scores.csv',scores)
    contrasts=[]
    for period in ['primary','october']:
        for metric in ['qlike','mse']:
            for block in [1,7,14]:
                family=[]
                for B in BUDGETS:
                    for ref in ['MacroStat','PressureAR','DirectFlow']:family.append(contrast('MechanismSelected',ref,period,B,metric,block,'primary_12',frame,rng))
                for item,p in zip(family,holm([r['p_bootstrap'] for r in family])):item['p_holm']=float(p)
                contrasts.extend(family)
                family=[contrast('MechanismSelected','ReturnHAR',period,B,metric,block,'history_field_tradeoff_4',frame,rng,reference_budget=240) for B in BUDGETS]
                for item,p in zip(family,holm([r['p_bootstrap'] for r in family])):item['p_holm']=float(p)
                contrasts.extend(family)
    write(R/'tables/contrasts.csv',contrasts)
    diagnostics=[]
    for (model,B),g in fit.groupby(['model','budget_days']):
        p=sel[str(int(B))][model]['penalty'];g=g[g.penalty==p];diagnostics.append(dict(model=model,budget_days=int(B),selected_penalty=p,fits=len(g),condition_median=float(g.pressure_condition.median()),condition_max=float(g.pressure_condition.max()),fits_at_upper_bound=int(np.sum(g.at_upper_bound>0)),fits_at_zero=int(np.sum(g.at_zero>0)),transition_mse_mean=float(g.transition_mse.mean()),risk_scale_min=float(g.risk_scale.min()),risk_scale_max=float(g.risk_scale.max()),flow_scale_min=float(g.flow_scale.min()),flow_scale_max=float(g.flow_scale.max()),gradient_max=float(g.gradient.max())))
    write(R/'tables/selected_diagnostics.csv',diagnostics)
    data=load();a=summaries(data);checks={}
    checks['predictions_positive_finite']=bool(np.all(np.isfinite(frame.forecast_rv)) and np.all(frame.forecast_rv>0));checks['target_after_all_inputs']=bool(np.all(frame.input_last_date<frame.target_date));checks['budget_counts_correct']=bool(np.all(frame.training_pairs==frame.budget_days-1) and np.all(frame.input_days==frame.budget_days))
    ff=fit[fit.model.str.startswith('MeanField')];checks['meanfield_max_normalized_projected_gradient']=float(np.max(ff.gradient/(ff.budget_days-1)))
    checks['date_budget_exact']=bool(all(int((np.datetime64(t)-np.datetime64(first))/np.timedelta64(1,'D'))==B for t,first,B in zip(frame.target_date,frame.input_first_date,frame.budget_days)))
    err=[];pressure_errors=[];prefix=[]
    for B in [30,240]:
        for target_date in ['2026-01-01','2026-05-10']:
            target=int(np.flatnonzero(data['dates']==target_date)[0]);w=window(a,target-B,target);model=sel[str(B)]['MechanismSelected']['variant'];p=sel[str(B)]['MechanismSelected']['penalty'];base,_=forecast(w,model,p)
            changed={k:v.copy() for k,v in data.items()};changed['returns'][target:]*=9;altered=summaries(changed);other,_=forecast(window(altered,target-B,target),model,p);err.append(abs(base-other))
            clipped={k:v[:target].copy() for k,v in data.items()};aa=summaries(clipped);pred,_=forecast(window(aa,target-B,target),model,p);prefix.append(abs(base-pred))
            changed['returns']*=2;altered=summaries(changed);pp,_=pressure_fit(w,model,p);qq,_=pressure_fit(window(altered,target-B,target),model,p);pressure_errors.append(float(np.max(abs(pp-qq))))
    checks['future_return_forecast_max_difference']=max(err);checks['prefix_forecast_max_difference']=max(prefix);checks['all_return_pressure_max_difference']=max(pressure_errors)
    ls=losses(frame.actual_rv.to_numpy(),frame.forecast_rv.to_numpy());checks['loss_recalculation_max_difference']=max(float(np.max(abs(ls[k]-frame[k].to_numpy()))) for k in ls)
    # Distinguish the two risk targets on the actual panel; equality is not assumed.
    rv=np.sum(data['returns']**2,axis=1);sq=np.sum(data['returns'],axis=1)**2;cross=2*np.array([np.sum(np.outer(x,x)[np.triu_indices(len(x),1)]) for x in data['returns']])
    checks['cumulative_square_identity_max_difference']=float(np.max(abs(sq-rv-cross)));checks['rv_equals_squared_daily_return']=bool(np.allclose(rv,sq));checks['microscopic_calibration_labels']=0;checks['warmup_days_outside_budget']=0
    assert all(checks[k] for k in ['predictions_positive_finite','target_after_all_inputs','budget_counts_correct','date_budget_exact'])
    assert checks['future_return_forecast_max_difference']==0 and checks['prefix_forecast_max_difference']==0 and checks['all_return_pressure_max_difference']==0 and checks['loss_recalculation_max_difference']<1e-10 and checks['cumulative_square_identity_max_difference']<1e-12 and not checks['rv_equals_squared_daily_return'] and checks['meanfield_max_normalized_projected_gradient']<1e-5
    (R/'checks/causal_audit.json').write_text(json.dumps(checks,indent=2))
    print('Audits',checks,flush=True)
    primary=[r for r in scores if r['period']=='primary' and r['metric']=='qlike'];print(pd.DataFrame(primary).pivot(index='budget_days',columns='model',values='mean').to_string(),flush=True)

if __name__=='__main__':main()
