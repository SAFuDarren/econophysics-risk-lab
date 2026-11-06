"""Run the locked simulation-only phase, discrete tail, inference and stress study."""

from pathlib import Path as _ProjectPath
import sys as _project_sys
_project_sys.path.insert(0, str(_ProjectPath(__file__).resolve().parents[1]))
from _bootstrap import ROOT as PROJECT_ROOT, script_path, resolve_recorded_path

from pathlib import Path
from collections import Counter
import argparse
import csv
from dataclasses import asdict
import hashlib
import json
import platform
import random
import sys
import time

ROOT = PROJECT_ROOT
sys.path.insert(0,str(ROOT/'src'))
import numpy as np
import scipy
import sklearn
from econophysics.model import Parameters,components,derived_seed,er_edges,simulate_aggregates,simulate_window
from econophysics.features import PRICE_FEATURES,VOLUME_FEATURES,window_features
from econophysics.inference import select_regressor
from econophysics.study_statistics import interval,stratified_bootstrap_mean,holm_adjust,tail_diagnostic


def write_json(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def write_csv(path,rows):
    with path.open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',default='configs/simulation_study_v1.json')
    parser.add_argument('--run-id',default='simulation_study_v1')
    args=parser.parse_args()
    if not args.run_id.replace('_','').replace('-','').isalnum(): parser.error('invalid run ID')
    config_path=ROOT/args.config
    cfg=json.loads(config_path.read_text())
    tables,checks,predictions=[ROOT/p/args.run_id for p in ['results/tables','results/checks','results/predictions']]
    if any(p.exists() for p in [tables,checks,predictions]): parser.error('run ID exists; use a new ID')
    for p in [tables,checks,predictions]:p.mkdir(parents=True)
    write_json(checks/'locked_config.json',cfg)
    started=time.perf_counter()
    source_paths=sorted((ROOT/'src/econophysics').glob('*.py'))+[Path(__file__).resolve(),config_path]
    record={'run_id':args.run_id,'protocol_id':cfg['protocol_id'],'status':'running',
            'command':f'python3 scripts/research/run_simulation_study.py --config {args.config} --run-id {args.run_id}',
            'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths},
            'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,'sklearn':sklearn.__version__,
            'member_review':'not_run','scope':'simulation only; one training split; fixed finite parameter grid'}
    write_json(checks/'run_record.json',record)
    def rng(label):return np.random.default_rng(derived_seed(cfg['seed'],label))
    validation=[]
    def check(name,condition,**details):
        validation.append({'check':name,'status':'pass' if condition else 'fail',**details})
        if not condition: raise AssertionError(name)
    try:
        params=Parameters(n=16,rho=.9)
        full=simulate_window(params,32,cfg['seed'])[0]
        fast=simulate_aggregates(params,32,cfg['seed'])
        check('aggregate-only sampler is exactly the executed r,V marginal',all(a['r']==b['r'] and a['V']==b['V'] for a,b in zip(full,fast)))
        phase_rows,cluster_rows,phase_summary=[] ,[],[]
        for n in cfg['phase']['n']:
            for rho in cfg['phase']['rho']:
                cell=[]
                for rep in range(cfg['phase']['graphs_per_cell']):
                    seed=derived_seed(cfg['seed'],f'phase:{n}:{rho}:{rep}')
                    groups=components(n,er_edges(n,rho/(n-1),random.Random(seed)))
                    sizes=sorted([len(g) for g in groups],reverse=True)
                    rest=sizes[1:]
                    row={'n':n,'rho':rho,'graph_id':rep,'seed':seed,'largest_fraction':sizes[0]/n,
                         'm2_per_node':sum(s*s for s in sizes)/n,'finite_chi':sum(s*s for s in rest)/sum(rest) if rest else None}
                    phase_rows.append(row);cell.append(row)
                    cluster_rows.extend({'n':n,'rho':rho,'graph_id':rep,'cluster_id':i,'size':size,'excluded_largest':int(i==0)} for i,size in enumerate(sizes))
                summary={'n':n,'rho':rho,'graphs':len(cell)}
                for key in ['largest_fraction','m2_per_node','finite_chi']:
                    values=np.array([r[key] for r in cell if r[key] is not None])
                    boot=stratified_bootstrap_mean(values,np.zeros(len(values)),rng(f'phase_ci:{n}:{rho}:{key}'),cfg['statistics']['phase_bootstrap_replicates'])
                    lo,hi=interval(boot)
                    summary.update({key+'_mean':float(values.mean()),key+'_sd':float(values.std(ddof=1)),key+'_ci_low':lo,key+'_ci_high':hi,key+'_valid_graphs':len(values)})
                phase_summary.append(summary)
            print(f'Phase scan complete: N={n}',flush=True)
        write_csv(tables/'phase_graphs.csv',phase_rows);write_csv(tables/'phase_summary.csv',phase_summary);write_csv(tables/'cluster_sizes.csv',cluster_rows)
        series_rows,series_lookup=[],{}
        requested={(cfg['series']['n'],rho) for rho in cfg['series']['rho']} | {(n,1.0) for n in cfg['series']['scaling_n']}
        for n,rho in sorted(requested):
            seed=derived_seed(cfg['seed'],f'series:{n}:{rho}')
            observations=simulate_aggregates(Parameters(n=n,rho=rho,a=cfg['series']['a'],lambda_impact=cfg['series']['lambda_impact']),cfg['series']['length'],seed)
            series_lookup[(n,rho)]=observations
            series_rows.extend({'n':n,'rho':rho,'t':i,**row} for i,row in enumerate(observations))
            print(f'Series complete: N={n}, rho={rho}',flush=True)
        write_csv(tables/'return_volume_series.csv',series_rows)
        tails,pmf_rows=[],[]
        for rho in cfg['series']['rho']:
            ret=np.array([r['r'] for r in series_lookup[(128,rho)]])
            scaled=np.abs(ret)*128/cfg['series']['lambda_impact']
            check(f'discrete tail lattice rho={rho}',np.max(np.abs(scaled-np.rint(scaled)))<1e-9)
            tail,pmf=tail_diagnostic(np.rint(scaled).astype(int),cfg['tail']['upper_support'],cfg['tail']['xmin_order_units'],cfg['tail'],rng(f'tail:{rho}'))
            tails.append({'n':128,'rho':rho,**tail})
            pmf_rows.extend({'rho':rho,**r} for r in pmf)
        adjusted=holm_adjust([r['power_gof_p'] for r in tails])
        for row,pvalue in zip(tails,adjusted):row['power_gof_p_holm']=pvalue
        write_csv(tables/'tail_diagnostics.csv',tails);write_csv(tables/'tail_probabilities.csv',pmf_rows)
        print('Discrete tail diagnostics complete',flush=True)
        inf=cfg['inference']; windows=[]; observed_rows=[]; features=[]; labels=[]
        for ri,rho in enumerate(inf['rho']):
            for ai,a in enumerate(inf['a']):
                permutation=rng(f'split:{ri}:{ai}').permutation(inf['windows_per_cell'])
                assignment={int(i):('train' if j<inf['train_per_cell'] else 'validation' if j<inf['train_per_cell']+inf['validation_per_cell'] else 'test') for j,i in enumerate(permutation)}
                for replicate in range(inf['windows_per_cell']):
                    wid=f'r{ri}_a{ai}_w{replicate:02d}'
                    seed=derived_seed(cfg['seed'],f'learning:{wid}')
                    obs=simulate_aggregates(Parameters(n=inf['n'],rho=rho,a=a,lambda_impact=inf['lambda_impact'],unit_order=inf['unit_order']),inf['window_length'],seed)
                    feat=window_features(obs)
                    label={'window_id':wid,'rho':rho,'a':a,'seed':seed,'split':assignment[replicate],'stratum':f'{ri}_{ai}'}
                    windows.append(obs);features.append(feat);labels.append(label)
                    observed_rows.extend({'window_id':wid,'t':t,**row} for t,row in enumerate(obs))
            print(f'Learning windows complete: rho={rho}',flush=True)
        write_csv(tables/'learning_observations.csv',observed_rows)
        write_csv(tables/'learning_labels_NOT_FEATURES.csv',labels)
        write_csv(tables/'learning_features.csv',[{'window_id':lab['window_id'],**feat} for lab,feat in zip(labels,features)])
        check('unique independent mother seeds and IDs',len({r['seed'] for r in labels})==len(labels)==len({r['window_id'] for r in labels}))
        counts=Counter(r['split'] for r in labels)
        check('locked split counts',counts=={'train':252,'validation':84,'test':84},counts=dict(counts))
        x=np.array([[np.nan if row[k] is None else row[k] for k in PRICE_FEATURES+VOLUME_FEATURES] for row in features])
        y=np.array([r['rho'] for r in labels]); splits=np.array([r['split'] for r in labels]); strata=np.array([r['stratum'] for r in labels])
        check('no label metadata used as features',not(set(PRICE_FEATURES+VOLUME_FEATURES)&{'rho','a','seed','window_id','t','stratum','split'}))
        train=np.flatnonzero(splits=='train');val=np.flatnonzero(splits=='validation');test=np.flatnonzero(splits=='test')
        test_groups=strata[test];views={'Return only':list(range(len(PRICE_FEATURES))),'Return + volume':list(range(x.shape[1]))}
        candidate_rows,metric_rows,pred_rows=[],[],[]
        models={};losses={}
        for fraction in inf['training_fractions']:
            subset=np.concatenate([train[strata[train]==g][:max(1,round(inf['train_per_cell']*fraction))] for g in np.unique(strata[train])])
            for view,columns in views.items():
                for method in ['Dummy','Ridge','RBF']:
                    model,candidates,selected=select_regressor(method,x[np.ix_(subset,columns)],y[subset],x[np.ix_(val,columns)],y[val],inf)
                    predicted=model.predict(x[np.ix_(test,columns)])
                    error=np.abs(predicted-y[test])
                    boot=stratified_bootstrap_mean(error,test_groups,rng(f'mae:{fraction}:{view}:{method}'),cfg['statistics']['bootstrap_replicates'])
                    lo,hi=interval(boot)
                    metric_rows.append({'training_fraction':fraction,'training_windows':len(subset),'validation_windows':len(val),'test_windows':len(test),'training_runs':1,'view':view,'method':method,'mae':float(error.mean()),'loss_sd':float(error.std(ddof=1)),'ci_low':lo,'ci_high':hi,'selected_specification':json.dumps(model.specification,sort_keys=True),'validation_mae':candidates[selected]['validation_mae']})
                    candidate_rows.extend({'training_fraction':fraction,'view':view,'method':method,'candidate_id':i,'selected':i==selected,**c} for i,c in enumerate(candidates))
                    if fraction==1:
                        models[(view,method)]=model;losses[(view,method)]=error
                        pred_rows.extend({'window_id':labels[index]['window_id'],'rho':float(y[index]),'a':labels[index]['a'],'view':view,'method':method,'prediction':float(p),'absolute_error':float(e)} for index,p,e in zip(test,predicted,error))
        write_csv(tables/'learning_metrics.csv',metric_rows);write_csv(tables/'validation_candidates.csv',candidate_rows);write_csv(predictions/'test_predictions.csv',pred_rows)
        contrasts=[]
        for method in ['Dummy','Ridge','RBF']:
            difference=losses[('Return + volume',method)]-losses[('Return only',method)]
            boot=stratified_bootstrap_mean(difference,test_groups,rng(f'paired:{method}'),cfg['statistics']['bootstrap_replicates'])
            mean=float(difference.mean());lo,hi=interval(boot)
            pvalue=(1+int(np.sum(np.abs(boot-mean)>=abs(mean))))/(len(boot)+1) if np.any(difference) else 1.0
            contrasts.append({'method':method,'test_windows':len(test),'difference_joint_minus_return':mean,'ci_low':lo,'ci_high':hi,'paired_loss_sd':float(difference.std(ddof=1)),'paired_standardized_effect':mean/float(difference.std(ddof=1)) if np.std(difference)>0 else 0.0,'relative_mae_reduction_percent':float(-100*mean/losses[('Return only',method)].mean()),'bootstrap_p_approx':pvalue})
        for row,p in zip(contrasts,holm_adjust([r['bootstrap_p_approx'] for r in contrasts])):row['p_holm']=p
        write_csv(tables/'view_contrasts.csv',contrasts)
        stress_metrics,stress_predictions=[],[]
        for factor in cfg['stress']['lambda_multipliers']:
            stress_features=[window_features([{'r':row['r']*factor,'V':row['V']} for row in windows[index]]) for index in test]
            sx=np.array([[np.nan if row[k] is None else row[k] for k in PRICE_FEATURES+VOLUME_FEATURES] for row in stress_features])
            for view,columns in views.items():
                prediction=models[(view,'RBF')].predict(sx[:,columns]);error=np.abs(prediction-y[test])
                boot=stratified_bootstrap_mean(error,test_groups,rng(f'stress:{factor}:{view}'),cfg['statistics']['bootstrap_replicates'])
                lo,hi=interval(boot)
                stress_metrics.append({'lambda_multiplier':factor,'view':view,'method':'RBF','mae':float(error.mean()),'loss_sd':float(error.std(ddof=1)),'ci_low':lo,'ci_high':hi,'independent_base_windows':len(test),'training_runs':1})
                stress_predictions.extend({'window_id':labels[index]['window_id'],'rho':float(y[index]),'lambda_multiplier':factor,'view':view,'prediction':float(p),'absolute_error':float(e)} for index,p,e in zip(test,prediction,error))
        write_csv(tables/'stress_metrics.csv',stress_metrics);write_csv(predictions/'stress_predictions.csv',stress_predictions)
        group_rows=[]
        for rho in inf['rho']:
            for a in inf['a']:
                for view in views:
                    group=[r['absolute_error'] for r in pred_rows if r['rho']==rho and r['a']==a and r['view']==view and r['method']=='RBF']
                    group_rows.append({'rho':rho,'a':a,'view':view,'method':'RBF','test_windows':len(group),'mae':float(np.mean(group)),'loss_sd':float(np.std(group,ddof=1))})
        write_csv(tables/'rbf_group_errors.csv',group_rows)
        check('all configured windows used',len(features)==420 and len(observed_rows)==420*inf['window_length'])
        check('no nonfinite main predictions',all(np.isfinite(r['prediction']) for r in pred_rows))
        check('stress identity equals primary predictions',all(abs(r['absolute_error']-next(p['absolute_error'] for p in pred_rows if p['window_id']==r['window_id'] and p['view']==r['view'] and p['method']=='RBF'))<1e-12 for r in stress_predictions if r['lambda_multiplier']==1))
        check('train and test IDs disjoint',not(set(labels[i]['window_id'] for i in train)&set(labels[i]['window_id'] for i in test)))
        write_json(checks/'checks.json',{'status':'pass','evidence_types':['MODEL_CHECK','SIMULATION'],'checks':validation})
        record.update(status='pass',elapsed_seconds=time.perf_counter()-started,phase_graphs=len(phase_rows),series_periods=len(series_rows),learning_windows=len(labels),test_windows=len(test),outputs={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for folder in [tables,predictions] for p in sorted(folder.iterdir())})
        write_json(checks/'run_record.json',record)
        print(json.dumps({'status':'pass','run_id':args.run_id,'seconds':record['elapsed_seconds'],'phase_graphs':len(phase_rows),'learning_windows':len(labels),'primary_view_contrasts':contrasts},indent=2),flush=True)
    except Exception as exc:
        record.update(status='failed',error=repr(exc),elapsed_seconds=time.perf_counter()-started)
        write_json(checks/'run_record.json',record)
        raise


if __name__=='__main__':main()
