#!/usr/bin/env python3
"""Same-covariance controls, separate truth seeds, independent training repeats."""

from pathlib import Path as _ProjectPath
import sys as _project_sys
_project_sys.path.insert(0, str(_ProjectPath(__file__).resolve().parents[1]))
from _bootstrap import ROOT as PROJECT_ROOT, script_path, resolve_recorded_path
from pathlib import Path
import json,sys,time
ROOT=PROJECT_ROOT;sys.path.insert(0,str(ROOT/'src'))
import numpy as np
from econophysics.us_equity import write_csv
from econophysics.tail_increment import (Law,build_laws,cluster_pool,standardize,whiten,seed_for,orthogonal_gaussian,matrix_root,law_choices,factor_scenarios,empirical_scenarios,forecast_statistics)

def truth_draw(cfg,name,m,seed,pools):
    rng=np.random.default_rng(seed);c=np.ones((9,9))*cfg['synthetic']['correlation']+np.eye(9)*(1-cfg['synthetic']['correlation'])
    if name=='Gaussian':return whiten(rng.normal(size=(m,9)))@matrix_root(c)
    if name=='StudentT-5':return whiten(rng.normal(size=(m,9))*np.sqrt(3/rng.chisquare(5,size=m))[:,None])@matrix_root(c)
    if name.startswith('Herding'):
        rho=float(name.split('rho')[1].split('-')[0]);key=rho
        if key not in pools:pools[key]=cluster_pool(cfg,rho,.05,cfg['seed']+900000)[0]
        pool=pools[key];h=standardize(pool[rng.integers(0,len(pool),m)])
    else:
        h=standardize(rng.normal(size=m)*np.where(rng.random(m)<.05,6.,1.))
    z=orthogonal_gaussian(h,seed_for(seed,'residual'))
    return factor_scenarios(c,Law('truth','truth',{'kappa':.75},h,z,np.array([])))

def main():
    cfg=json.loads((ROOT/'configs/tail_increment_v1.json').read_text());out=ROOT/'results/tables/tail_increment_v1';check=ROOT/'results/checks/tail_increment_v1';out.mkdir(parents=True,exist_ok=True);start=time.perf_counter();laws,grid,_,_=build_laws(cfg);c=np.ones((9,9))*.6+np.eye(9)*.4;rootinv=matrix_root(c,inverse=True);eig,vec=np.linalg.eigh(c);u=vec[:,-1]*(1 if vec[:,-1].sum()>=0 else -1);port_sd=np.sqrt(np.ones(9)@c@np.ones(9)/81);rows=[];truth_rows=[];ccdf=[];pools={}
    for truth in cfg['synthetic']['truths']:
        test=truth_draw(cfg,truth,cfg['synthetic']['test_draws'],seed_for(cfg['seed'],'truth-test/'+truth),pools);y=test.mean(1)/port_sd;actual=forecast_statistics(test,c);true_p=actual['p_co3'];truth_rows.append({'truth':truth,'test_draws':len(test),**actual})
        for threshold in np.linspace(0,8,81):ccdf.append({'truth':truth,'loss_threshold_sigma':float(threshold),'exceedance_probability':float(np.mean(-y>threshold))})
        for repetition in range(cfg['synthetic']['train_repetitions']):
            train=truth_draw(cfg,truth,cfg['synthetic']['train_draws'],seed_for(cfg['seed'],f'truth-train/{truth}/{repetition}'),pools);z=train@rootinv;h=z@u;choices,_=law_choices(laws,grid,z,h)
            for model in cfg['methods']:
                if model in ['FHS','FactorEmpirical']:samples=empirical_scenarios(c,z,h,model,seed_for(cfg['seed'],'empiricalResidual'));chosen='Past504'
                else:samples=factor_scenarios(c,laws[choices[model]]);chosen=laws[choices[model]].name
                stat=forecast_statistics(samples,c);q=stat['q05'];e=stat['es05'];pinball=float(np.mean((.05-(y<q))*(y-q)));fz=float(np.mean(-1.0*(y<=q)*(q-y)/(.05*e)+q/e+np.log(-e)-1));prob=stat['p_co3'];brier=prob**2-2*prob*true_p+true_p
                rows.append({'truth':truth,'repetition':repetition,'method':model,'chosen_law':chosen,'pinball05':pinball,'brier':brier,'fz05':fz,'true_p_co3':true_p,'tail_probability_absolute_error':abs(prob-true_p),'var05_absolute_error':abs(q-actual['q05']),'es05_absolute_error':abs(e-actual['es05']),**stat})
        print(json.dumps({'truth':truth,'p_co3':true_p,'q05':actual['q05'],'elapsed_seconds':round(time.perf_counter()-start,2)}),flush=True)
    write_csv(out/'synthetic_truth.csv',truth_rows);write_csv(out/'synthetic_ccdf.csv',ccdf);write_csv(out/'synthetic_repetitions.csv',rows)
    (check/'synthetic_run.json').write_text(json.dumps({'status':'pass','truths':len(truth_rows),'train_repetitions_per_truth':cfg['synthetic']['train_repetitions'],'rows':len(rows),'test_draws_per_truth':cfg['synthetic']['test_draws'],'max_covariance_relative_error':max(r['covariance_relative_error'] for r in rows+truth_rows),'scope':'Synthetic, known covariance, independent training repeats; shared large test law conditions results, not market evidence','seconds':time.perf_counter()-start},indent=2)+'\n')

if __name__=='__main__':main()
