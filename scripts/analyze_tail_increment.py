#!/usr/bin/env python3
"""Paired day-block analysis; primary family fixed before external download."""
from pathlib import Path
import csv,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import numpy as np
from econophysics.us_equity import write_csv,block_weights

def read(path):return list(csv.DictReader(path.open()))
def mean(rows,key):return float(np.mean([float(r[key]) for r in rows]))

def main():
    cfg=json.loads((ROOT/'configs/tail_increment_v1.json').read_text());base=ROOT/'results/tables/tail_increment_v1';check=ROOT/'results/checks/tail_increment_v1';selection=json.loads((check/'selection_freeze.json').read_text())['selection'];rng=np.random.default_rng(cfg['seed']+500);summaries=[];contrasts=[];calibration=[]
    for panel in ['sector','external']:
        data=read(base/f'{panel}_daily.csv')
        for covariance in cfg['covariances']:
            for period in ['historical_test','confirmation']:
                grouped={model:sorted([r for r in data if r['covariance']==covariance and r['period']==period and r['method']==model],key=lambda r:r['date']) for model in cfg['methods']};dates=[r['date'] for r in grouped['Gaussian']];n=len(dates)
                assert n>0 and all([r['date'] for r in v]==dates for v in grouped.values())
                for model,rows in grouped.items():
                    summaries.append({'panel':panel,'covariance':covariance,'period':period,'method':model,'days':n,'co_events':sum(int(r['co3']) for r in rows),'mean_pred_co_probability':mean(rows,'p_co3'),'observed_co_frequency':mean(rows,'co3'),'var05_coverage':mean(rows,'hit05'),'var01_coverage':mean(rows,'hit01'),'mean_pinball05':mean(rows,'pinball05'),'mean_pinball01':mean(rows,'pinball01'),'mean_brier':mean(rows,'brier'),'mean_fz05':mean(rows,'fz05'),'mean_log_score':mean(rows,'log_score'),'mean_covariance_relative_error':mean(rows,'covariance_relative_error'),'gaussian_off_frequency':float(np.mean([r['law']=='Gaussian' for r in rows]))})
                    for lo,hi in zip([0,.025,.05,.1,.2],[.025,.05,.1,.2,1.00001]):
                        binrows=[r for r in rows if lo<=float(r['p_co3'])<hi]
                        if binrows:calibration.append({'panel':panel,'covariance':covariance,'period':period,'method':model,'probability_bin_lower':lo,'probability_bin_upper':min(hi,1.),'days':len(binrows),'events':sum(int(r['co3']) for r in binrows),'mean_prediction':mean(binrows,'p_co3'),'event_frequency':mean(binrows,'co3')})
                # Same resampling weights for every model and endpoint.
                for block in cfg['bootstrap']['block_sessions']:
                    weights=block_weights(n,block,cfg['bootstrap']['replicates'],rng)
                    for metric in ['pinball05','brier']:
                        baseline=selection[covariance][metric]['baseline'];b=np.array([float(r[metric]) for r in grouped[baseline]]);boot_b=weights@b/n
                        for model in cfg['methods']:
                            a=np.array([float(r[metric]) for r in grouped[model]]);difference=a-b;boot_a=weights@a/n;gain=100*(1-boot_a/boot_b);observed=float(difference.mean());boot_diff=boot_a-boot_b
                            p=float((1+np.count_nonzero(np.abs(boot_diff-observed)>=abs(observed)))/(len(boot_diff)+1))
                            contrasts.append({'panel':panel,'covariance':covariance,'period':period,'model':model,'baseline':baseline,'metric':metric,'block_sessions':block,'days':n,'co_events':sum(int(r['co3']) for r in grouped[model]),'mean_model_loss':float(a.mean()),'mean_baseline_loss':float(b.mean()),'loss_difference':observed,'improvement_pct':100*(1-float(a.mean()/b.mean())),'ci_low':float(np.quantile(gain,.025)),'ci_high':float(np.quantile(gain,.975)),'p_centered_block_approx':p,'primary_family':panel=='external' and covariance==cfg['primary_covariance'] and period=='historical_test' and model=='Herding' and block==cfg['bootstrap']['primary_block']})
    family=sorted([r for r in contrasts if r['primary_family']],key=lambda r:r['p_centered_block_approx']);last=0.
    for rank,row in enumerate(family):last=max(last,min(1.,(len(family)-rank)*row['p_centered_block_approx']));row['p_holm_primary']=last
    # Direct critical-vs-subcritical diagnostic; same six non-Gaussian candidates each.
    ablation=[]
    for panel in ['sector','external']:
        data=read(base/f'{panel}_daily.csv')
        for period in ['historical_test','confirmation']:
            a=sorted([r for r in data if r['covariance']==cfg['primary_covariance'] and r['period']==period and r['method']=='HerdingCritical'],key=lambda r:r['date']);b=sorted([r for r in data if r['covariance']==cfg['primary_covariance'] and r['period']==period and r['method']=='HerdingSubcritical'],key=lambda r:r['date']);n=len(a);w=block_weights(n,20,cfg['bootstrap']['replicates'],rng)
            for metric in ['pinball05','brier']:
                av=np.array([float(r[metric]) for r in a]);bv=np.array([float(r[metric]) for r in b]);gain=100*(1-(w@av)/(w@bv));ablation.append({'panel':panel,'period':period,'model':'HerdingCritical','baseline':'HerdingSubcritical','metric':metric,'improvement_pct':100*(1-av.mean()/bv.mean()),'ci_low':float(np.quantile(gain,.025)),'ci_high':float(np.quantile(gain,.975)),'scope':'Exploratory same-budget rho=1 vs rho=.6; not real criticality identification'})
    write_csv(base/'metrics.csv',summaries);write_csv(base/'contrasts.csv',contrasts);write_csv(base/'reliability.csv',calibration);write_csv(base/'critical_ablation.csv',ablation)
    synthetic=read(base/'synthetic_repetitions.csv');synthetic_summary=[]
    for truth in cfg['synthetic']['truths']:
        for model in cfg['methods']:
            rows=[r for r in synthetic if r['truth']==truth and r['method']==model];entry={'truth':truth,'method':model,'repetitions':len(rows)}
            for metric in ['pinball05','brier','var05_absolute_error','es05_absolute_error','tail_probability_absolute_error']:
                values=np.array([float(r[metric]) for r in rows]);bootstrap=values[rng.integers(0,len(values),(cfg['bootstrap']['replicates'],len(values)))].mean(1);entry.update({metric+'_mean':float(values.mean()),metric+'_sd':float(values.std(ddof=1)),metric+'_ci_low':float(np.quantile(bootstrap,.025)),metric+'_ci_high':float(np.quantile(bootstrap,.975))})
            synthetic_summary.append(entry)
    write_csv(base/'synthetic_metrics.csv',synthetic_summary)
    paired=[]
    for truth in cfg['synthetic']['truths']:
        source={m:sorted([r for r in synthetic if r['truth']==truth and r['method']==m],key=lambda r:int(r['repetition'])) for m in cfg['methods']}
        ix=rng.integers(0,cfg['synthetic']['train_repetitions'],(cfg['bootstrap']['replicates'],cfg['synthetic']['train_repetitions']))
        for metric in ['pinball05','brier']:
            b=np.array([float(r[metric]) for r in source['Gaussian']])
            for model in cfg['methods']:
                a=np.array([float(r[metric]) for r in source[model]]);gain=100*(1-a[ix].mean(1)/b[ix].mean(1));paired.append({'truth':truth,'model':model,'baseline':'Gaussian','metric':metric,'improvement_pct':100*(1-a.mean()/b.mean()),'ci_low':float(np.quantile(gain,.025)),'ci_high':float(np.quantile(gain,.975)),'repetitions':len(a),'scope':'Paired independent training-run bootstrap conditional on the fixed large test law; synthetic only'})
    write_csv(base/'synthetic_paired_effects.csv',paired)
    sensitivity=read(base/'mc_daily.csv');external=read(base/'external_daily.csv');lookup={(r['date'],r['covariance'],r['method']):r for r in external};mc=[]
    for model in cfg['methods']:
        pairs=[(r,lookup[r['date'],r['covariance'],r['method']]) for r in sensitivity if r['method']==model];entry={'model':model,'paired_days':len(pairs),'shape_choice_disagreements':sum(a['law']!=b['law'] for a,b in pairs)}
        for metric in ['q05','q01','p_co3']:
            diff=np.array([float(a[metric])-float(b[metric]) for a,b in pairs]);entry[metric+'_rms_change']=float(np.sqrt(np.mean(diff*diff)));entry[metric+'_max_absolute_change']=float(abs(diff).max())
        mc.append(entry)
    write_csv(base/'mc_sensitivity.csv',mc)
    primary=[r for r in contrasts if r['primary_family']];conf=[r for r in contrasts if r['panel']=='external' and r['covariance']==cfg['primary_covariance'] and r['period']=='confirmation' and r['model']=='Herding' and r['block_sessions']==20]
    gates={}
    for r in primary:
        confirmation=next(c for c in conf if c['metric']==r['metric']);gates[r['metric']]=r['improvement_pct']>=5 and r['ci_low']>0 and r.get('p_holm_primary',1)<.05 and confirmation['improvement_pct']>=0
    result={'status':'pass','primary':primary,'confirmation':conf,'task_specific_research_gate_met':gates,'stable_live_economic_value_established':False,'causal_herding_or_criticality_identified':False,'external_data_scope':'Pre-frozen external assets; known historical dates, not new future-time validation','max_covariance_relative_error':max(float(r['covariance_relative_error']) for r in external),'member_scientific_review':'not_run'}
    analysis=ROOT/'results/analysis/tail_increment_v1';analysis.mkdir(parents=True,exist_ok=True);(analysis/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
