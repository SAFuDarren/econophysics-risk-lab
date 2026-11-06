#!/usr/bin/env python3
"""Controlled persistence interventions; shuffled pairs preserve joint data exactly."""

from pathlib import Path as _ProjectPath
import sys as _project_sys
_project_sys.path.insert(0, str(_ProjectPath(__file__).resolve().parents[1]))
from _bootstrap import ROOT as PROJECT_ROOT, script_path, resolve_recorded_path
from pathlib import Path
import argparse,csv,gzip,hashlib,json,math,random,sys,time
ROOT=PROJECT_ROOT;sys.path.insert(0,str(ROOT/'src'))
import numpy as np
from econophysics.model import er_edges,components,derived_seed
from econophysics.physics_inference import finite_er_moments
from econophysics.real_market_statistics import daily_moments,moments_to_statistics


def write(p,rows):
    with p.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run-id',default='state_mechanism_v2');args=parser.parse_args();folder=ROOT/'results/tables'/args.run_id;checks=ROOT/'results/checks'/args.run_id
    if folder.exists():parser.error('run exists')
    folder.mkdir(parents=True);checks.mkdir(parents=True);cfgpath=ROOT/'configs/state_forecast_v2.json';cfg=json.loads(cfgpath.read_text());c=cfg['mechanism'];qbar=(1-c['high_state_probability'])*c['q_low']+c['high_state_probability']*c['q_high'];metrics=[];acfs=[];starts=time.perf_counter();seeds=[];checks_rows=[]
    with gzip.open(folder/'series.csv.gz','wt',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['replication','arm','t','r','V']);writer.writeheader()
        for rep in range(c['paths']):
            seed=derived_seed(cfg['seed'],f'mechanism-v2:{rep}');graphs=random.Random(derived_seed(seed,'graphs'));actions=random.Random(derived_seed(seed,'actions'));rng=np.random.default_rng(derived_seed(seed,'state'));T=c['length'];state=int(rng.random()<c['high_state_probability']);s=float(rng.normal(0,c['log_impact_stationary_sd']));series={k:[] for k in ['Constant','PersistentActivity','PersistentImpact']}
            for t in range(T):
                if rng.random()>c['state_persistence']:state=int(rng.random()<c['high_state_probability'])
                s=c['state_persistence']*s+c['log_impact_stationary_sd']*np.sqrt(1-c['state_persistence']**2)*rng.normal();q=c['q_high'] if state else c['q_low'];lam=c['lambda0']*np.exp(s-c['log_impact_stationary_sd']**2)
                sizes=[len(g) for g in components(c['n'],er_edges(c['n'],c['rho']/(c['n']-1),graphs))];u=[actions.random() for _ in sizes]
                def aggregate(prob,impact):
                    xi=[-1 if z<prob/2 else (1 if z>=1-prob/2 else 0) for z in u];return (impact/c['n']*sum(ss*x for ss,x in zip(sizes,xi)),c['unit_order']*sum(ss*abs(x) for ss,x in zip(sizes,xi)))
                series['Constant'].append(aggregate(qbar,c['lambda0']));series['PersistentActivity'].append(aggregate(q,c['lambda0']));series['PersistentImpact'].append(aggregate(qbar,float(lam)))
            arrays={k:np.asarray(v) for k,v in series.items()};arrays['ShuffledActivity']=arrays['PersistentActivity'][rng.permutation(T)]
            for arm in c['arms']:
                a=arrays[arm];r=a[:,0];v=a[:,1];m=moments_to_statistics(daily_moments(r,v,T).sum(0));metrics.append({'replication':rep,'arm':arm,'mean_volume':float(v.mean()),'return_variance':float(r.var()),'delta':float(m['delta']),'magnitude_acf1':float(np.corrcoef(np.abs(r[1:]),np.abs(r[:-1]))[0,1]),'volume_acf1':float(np.corrcoef(v[1:],v[:-1])[0,1])});writer.writerows({'replication':rep,'arm':arm,'t':t,'r':float(a[t,0]),'V':float(a[t,1])} for t in range(T))
                for lag in [1,4,16,64,256]:
                    for kind,x in [('magnitude',np.abs(r)),('volume',v)]:acfs.append({'replication':rep,'arm':arm,'series':kind,'lag':lag,'correlation':float(np.corrcoef(x[lag:],x[:-lag])[0,1])})
            original=arrays['PersistentActivity'];shuffled=arrays['ShuffledActivity'];equal=np.array_equal(original[np.lexsort((original[:,1],original[:,0]))],shuffled[np.lexsort((shuffled[:,1],shuffled[:,0]))]);checks_rows.append({'replication':rep,'joint_empirical_pairs_preserved':equal,'volume_identical_constant_impact':bool(np.array_equal(arrays['Constant'][:,1],arrays['PersistentImpact'][:,1]))});assert all(checks_rows[-1][k] for k in ['joint_empirical_pairs_preserved','volume_identical_constant_impact']);seeds.append({'replication':rep,'seed':seed});print('Mechanism replication',rep+1,'complete',flush=True)
    A=finite_er_moments(c['n'],c['rho']);n=c['n'];u=c['unit_order'];lam=c['lambda0'];m1=qbar;m2=(1-c['high_state_probability'])*c['q_low']**2+c['high_state_probability']*c['q_high']**2;m3=(1-c['high_state_probability'])*c['q_low']**3+c['high_state_probability']*c['q_high']**3;mean=u*n*m1;varv=u*u*((m1-m2)*A['s2']+n*n*(m2-m1*m1));varr=(lam/n)**2*m1*A['s2'];cross=(lam/n)**2*u*((m1-m2)*A['s3']+n*A['s2']*(m2-m1*m1));third=u**3*((m1-3*m2+2*m3)*A['s3']+3*n*A['s2']*((m2-m3)-m1*(m1-m2))+n**3*(m3-3*m1*m2+2*m1**3));theory_delta=(cross/varr-third/varv)/mean
    theory={'qbar':qbar,'mean_volume_all_arms_stationary':mean,'return_variance_all_arms_stationary':varr,'fixed_activity_delta':A['s3']/(n*A['s2']),'mixed_activity_delta':theory_delta,'mixed_activity_volume_variance':varv,'scope':'Activity mixing changes marginal moments; temporal shuffling preserves the exact observed joint law. Persistent impact independent of activity keeps fixed Delta in population. No parameters fit to market.'}
    write(folder/'path_metrics.csv',metrics);write(folder/'path_acf.csv',acfs);write(folder/'seeds.csv',seeds);summary=[];rng=np.random.default_rng(derived_seed(cfg['seed'],'mechanism-summary'));ix=rng.integers(0,c['paths'],size=(4999,c['paths']))
    for arm in c['arms']:
        rr=[r for r in metrics if r['arm']==arm]
        for key in ['mean_volume','return_variance','delta','magnitude_acf1','volume_acf1']:
            v=np.array([r[key] for r in rr]);lo,hi=np.quantile(v[ix].mean(1),[.025,.975]);summary.append({'arm':arm,'metric':key,'estimate':float(v.mean()),'ci_low':float(lo),'ci_high':float(hi),'independent_paths':c['paths']})
    write(folder/'summary.csv',summary);(checks/'checks.json').write_text(json.dumps({'status':'pass','joint_pair_checks':checks_rows,'theory':theory,'periods':c['paths']*c['length']*4,'seconds':time.perf_counter()-starts,'member_review':'not_run','source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [cfgpath,Path(__file__).resolve(),ROOT/'src/econophysics/model.py']}},indent=2)+'\n');print(json.dumps({'status':'pass','theory':theory,'seconds':time.perf_counter()-starts},indent=2))


if __name__=='__main__':main()
