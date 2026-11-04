#!/usr/bin/env python3
"""Reproducible run-level summaries and explicitly post-diagnostic fresh moment check."""
from pathlib import Path
from collections import defaultdict,Counter
import argparse,csv,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import numpy as np
from econophysics.model import derived_seed
from econophysics.mechanism_statistics import joint_diagnostics


def read(p):return list(csv.DictReader(p.open()))
def write(p,rows):
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run-id',default='depth_study_v1');args=parser.parse_args()
    if not args.run_id.replace('_','').replace('-','').isalnum():parser.error('invalid run ID')
    tables=ROOT/'results/tables'/args.run_id;out=ROOT/'results/analysis'/args.run_id;out.mkdir(parents=True,exist_ok=True)
    cfg=json.loads((ROOT/'configs/depth_study_v1.json').read_text());metrics=read(tables/'run_metrics.csv');summary=[]
    rng=np.random.default_rng(derived_seed(cfg['seed'],'consistent-run-intervals'))
    indices=rng.integers(0,cfg['replications'],(cfg['bootstrap_replicates'],cfg['replications']))
    for split in ['test','unseen']:
        for method in ['RBF_return','RBF_joint','RBF_volume','RBF_shape_joint','Moment_volume']:
            for factor in cfg['lambda_multipliers']:
                records=sorted([r for r in metrics if r['test_split']==split and r['method']==method and float(r['lambda_multiplier'])==factor],key=lambda r:int(r['replication']))
                vals=np.array([float(r['mae']) for r in records]);lo,hi=np.quantile(vals[indices].mean(1),[.025,.975])
                summary.append({'test_split':split,'method':method,'lambda_multiplier':factor,'mean_mae':float(vals.mean()),'run_sd':float(vals.std(ddof=1)),'ci_low':float(lo),'ci_high':float(hi),'replications':len(vals)})
    write(out/'summary_metrics.csv',summary)
    labels=read(tables/'labels_NOT_FEATURES.csv');selected={r['window_id']:r for r in labels if float(r['a'])==.1 and float(r['rho']) in [.6,1.,1.4]}
    groups=defaultdict(lambda:[[],[]])
    for r in csv.DictReader((tables/'observations.csv').open()):
        lab=selected.get(r['window_id'])
        if lab:
            group=groups[int(lab['replication']),float(lab['rho'])];group[0].append(float(r['r']));group[1].append(float(r['V']))
    fresh=[];fresh_summary=[]
    for (rep,rho),(r,v) in sorted(groups.items()):
        assert len(r)==5120
        fresh.append({'replication':rep,'rho':rho,'periods':len(r),**joint_diagnostics(r,v)})
    write(out/'fresh_joint_constraint_runs.csv',fresh)
    for rho in [.6,1.,1.4]:
        vals=np.array([r['constraint_residual'] for r in fresh if r['rho']==rho]);lo,hi=np.quantile(vals[indices].mean(1),[.025,.975])
        fresh_summary.append({'rho':rho,'replications':len(vals),'periods_per_replication':5120,'mean_residual':float(vals.mean()),'run_sd':float(vals.std(ddof=1)),'ci_low':float(lo),'ci_high':float(hi),'status':'post-diagnostic descriptive mean interval'})
    write(out/'fresh_joint_constraint_summary.csv',fresh_summary)
    physical=read(tables/'physical_estimates.csv');physical_summary=[]
    for split in ['test','unseen']:
        records=[r for r in physical if r['test_split']==split]
        q_runs=[];lambda_runs=[]
        for rep in range(cfg['replications']):
            rr=[r for r in records if int(r['replication'])==rep]
            q_runs.append(np.mean([abs(float(r['q_true'])-float(r['q_estimate'])) for r in rr]))
            lambda_runs.append(np.mean([abs(float(r['lambda_estimate'])/float(r['lambda_true'])-1) for r in rr]))
        for target,vals in [('q MAE',np.array(q_runs)),('lambda mean absolute relative error',np.array(lambda_runs))]:
            lo,hi=np.quantile(vals[indices].mean(1),[.025,.975]);physical_summary.append({'test_split':split,'target':target,'mean_error':float(vals.mean()),'run_sd':float(vals.std(ddof=1)),'ci_low':float(lo),'ci_high':float(hi),'replications':len(vals)})
    write(out/'physical_parameter_summary.csv',physical_summary)
    # Supplementary description only: not an unplanned fourth primary sign test.
    delta=[]
    for rep in range(cfg['replications']):
        get=lambda method:float(next(r['mae'] for r in metrics if int(r['replication'])==rep and r['test_split']=='unseen' and r['method']==method and float(r['lambda_multiplier'])==1))
        delta.append(get('Moment_volume')-get('RBF_joint'))
    delta=np.array(delta);lo,hi=np.quantile(delta[indices].mean(1),[.025,.975])
    stats={'status':'pass','replications':cfg['replications'],'fresh_windows':len(labels),'periods':len(labels)*cfg['window_length'],'split_totals':dict(Counter(r['split'] for r in labels)),
           'physical_flags':dict(Counter(r['flag'] for r in physical)),'fresh_constraint':fresh_summary,'physical_parameters':physical_summary,
           'unseen_physics_minus_joint':{'mean_difference':float(delta.mean()),'ci_low':float(lo),'ci_high':float(hi),'status':'supplementary descriptive comparison; no equivalence claim'},
           'interval_rule':'same resampled run indices across all method/scale cells; finite bootstrap jitter cannot fake changes in invariant methods',
           'member_review':'not_run'}
    (out/'summary.json').write_text(json.dumps(stats,indent=2)+'\n')
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__).resolve(),tables/'run_metrics.csv',tables/'observations.csv',tables/'labels_NOT_FEATURES.csv']}
    (ROOT/'results/checks'/args.run_id/'analysis_provenance.json').write_text(json.dumps({'source_sha256':hashes,'post_diagnostic_declared':'docs/decisions/2026-10-27-depth-study.md'},indent=2)+'\n')
    print(json.dumps(stats,indent=2))


if __name__=='__main__':main()
