#!/usr/bin/env python3
"""Marginal-preserving surrogate and joint-moment diagnostics on frozen iid simulations."""
from pathlib import Path
import argparse,csv,hashlib,json,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import numpy as np
from econophysics.model import derived_seed
from econophysics.mechanism_statistics import joint_diagnostics
from econophysics.study_statistics import holm_adjust


def write_csv(path,rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-id',default='depth_study_v1');args=p.parse_args()
    cfgpath=ROOT/'configs/depth_study_v1.json';cfg=json.loads(cfgpath.read_text());c=cfg['mechanism_test']
    tables=ROOT/'results/tables'/args.run_id;checks=ROOT/'results/checks'/args.run_id
    if (tables/'mechanism_diagnostics.csv').exists():p.error('mechanism output already exists')
    source=ROOT/'results/tables'/c['source_run']/'return_volume_series.csv'
    data=list(csv.DictReader(source.open()));rows=[];nullrows=[];bootrows=[];source_rows=[];begin=time.perf_counter()
    for rho in c['rho']:
        selected=[r for r in data if int(r['n'])==c['n'] and float(r['rho'])==rho]
        r=np.array([float(x['r']) for x in selected]);v=np.array([float(x['V']) for x in selected]);n=len(r)
        assert n==8192
        rng=np.random.default_rng(derived_seed(cfg['seed'],f'mechanism:{rho}'))
        obs=joint_diagnostics(r,v,c['n']);surrogate=v[rng.permutation(n)];sur=joint_diagnostics(r,surrogate,c['n'])
        assert np.array_equal(np.sort(v),np.sort(surrogate))
        source_rows.extend({'rho':rho,'t':i,'r':float(rr),'V_original':float(vv),'V_surrogate':float(ss)} for i,(rr,vv,ss) in enumerate(zip(r,v,surrogate)))
        null=[];r2=r*r;center_r2=r2-r2.mean();den=r2.mean()*c['n'];vc=v-v.mean()
        for j in range(c['permutations']):
            stat=float(np.mean(center_r2*vc[rng.permutation(n)])/den);null.append(stat);nullrows.append({'rho':rho,'permutation':j,'normalized_coupling':stat})
        pvalue=(1+sum(s>=obs['normalized_coupling'] for s in null))/(1+len(null))
        boot_original=[];boot_surrogate=[]
        for j in range(c['bootstrap_replicates']):
            idx=rng.integers(0,n,n);a=joint_diagnostics(r[idx],v[idx],c['n']);b=joint_diagnostics(r[idx],surrogate[idx],c['n'])
            boot_original.append(a);boot_surrogate.append(b)
            bootrows.append({'rho':rho,'bootstrap':j,'coupling_original':a['normalized_coupling'],'constraint_original':a['constraint_residual'],'constraint_surrogate':b['constraint_residual']})
        def interval(records,key):return np.quantile([x[key] for x in records],[.025,.975]).tolist()
        clo,chi=interval(boot_original,'normalized_coupling');zlo,zhi=interval(boot_original,'constraint_residual');slo,shi=interval(boot_surrogate,'constraint_residual')
        rows.append({'rho':rho,'periods':n,'q_estimate':obs['q'],'coupling_original':obs['normalized_coupling'],'coupling_ci_low':clo,'coupling_ci_high':chi,'coupling_surrogate':sur['normalized_coupling'],
                     'permutation_p_one_sided':pvalue,'constraint_original':obs['constraint_residual'],'constraint_ci_low':zlo,'constraint_ci_high':zhi,'constraint_surrogate':sur['constraint_residual'],'surrogate_constraint_ci_low':slo,'surrogate_constraint_ci_high':shi,
                     'identical_empirical_return_marginal':True,'identical_empirical_volume_marginal':True,'permutations':c['permutations'],'bootstrap_replicates':c['bootstrap_replicates']})
        print(f'Mechanism test complete: rho={rho}',flush=True)
    for row,pvalue in zip(rows,holm_adjust([r['permutation_p_one_sided'] for r in rows])):row['permutation_p_holm']=pvalue
    write_csv(tables/'mechanism_diagnostics.csv',rows);write_csv(tables/'mechanism_null_distribution.csv',nullrows);write_csv(tables/'mechanism_bootstrap.csv',bootrows);write_csv(tables/'mechanism_observations.csv',source_rows)
    paths=[Path(__file__).resolve(),ROOT/'src/econophysics/mechanism_statistics.py',cfgpath,source]
    report={'status':'pass','scope':'post-primary joint diagnostics; existing iid series; no new independent market evidence','elapsed_seconds':time.perf_counter()-begin,'command':f'python3 scripts/run_mechanism_checks.py --run-id {args.run_id}',
            'source_sha256':{str(x.relative_to(ROOT)):hashlib.sha256(x.read_bytes()).hexdigest() for x in paths},'member_review':'not_run','limits':['Permutation null is independence of contemporaneous squared returns and volume, not all alternative market mechanisms.','Bootstrap residual intervals are descriptive finite-sample model checks, not proof that the model is true.','q is re-estimated from volume inside every bootstrap.','This invariant is shared by arbitrary graph families under the action interface; it cannot identify ER topology or criticality.']}
    (checks/'mechanism_record.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(rows,indent=2),flush=True)


if __name__=='__main__':main()
