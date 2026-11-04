#!/usr/bin/env python3
"""Audit stored raw data -> all features -> validation selection -> every prediction."""
from pathlib import Path
from itertools import groupby
import argparse,csv,hashlib,json,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import numpy as np
from econophysics.features import window_features,PRICE_FEATURES,VOLUME_FEATURES
from econophysics.inference import select_regressor
from econophysics.physics_inference import scale_invariant_joint,volume_moment_estimate,finite_er_moments


def read(p):return list(csv.DictReader(p.open()))
def view_matrix(features,view):
    keys={'RBF_return':PRICE_FEATURES,'RBF_joint':PRICE_FEATURES+VOLUME_FEATURES,'RBF_volume':VOLUME_FEATURES[:3]}
    data=[scale_invariant_joint(f) for f in features] if view=='RBF_shape_joint' else [[f[k] for k in keys[view]] for f in features]
    return np.array([[np.nan if v is None else v for v in row] for row in data])


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run-id',default='depth_study_v1');args=parser.parse_args()
    if not args.run_id.replace('_','').replace('-','').isalnum():parser.error('invalid run ID')
    start=time.perf_counter();tables=ROOT/'results/tables'/args.run_id;checks=ROOT/'results/checks'/args.run_id;cfg=json.loads((ROOT/'configs/depth_study_v1.json').read_text())
    labels=read(tables/'labels_NOT_FEATURES.csv');stored={r['window_id']:r for r in read(tables/'learning_features.csv')};features={};periods=0;max_feature_error=0.
    for wid,rows in groupby(csv.DictReader((tables/'observations.csv').open()),lambda r:r['window_id']):
        data=[{'r':float(r['r']),'V':float(r['V'])} for r in rows];assert len(data)==cfg['window_length'];periods+=len(data)
        f=window_features(data);features[wid]=f
        for key,value in f.items():
            original=stored[wid][key]
            if value is None:assert original==''
            else:
                error=abs(value-float(original));max_feature_error=max(max_feature_error,error)
                assert np.isclose(value,float(original),rtol=1e-13,atol=1e-15)
    assert len(features)==len(labels)==4920 and len({r['seed'] for r in labels})==len(labels)
    old=set()
    for path in [ROOT/'results/tables/simulation_study_v1/learning_labels_NOT_FEATURES.csv',ROOT/'results/tables/simulation_followup_v1/unseen_rho_labels_NOT_FEATURES.csv']:
        if path.exists():old.update(r['seed'] for r in read(path))
    assert not old & {r['seed'] for r in labels}
    predictions=read(ROOT/'results/predictions'/args.run_id/'test_predictions.csv');lookup={(r['window_id'],r['method'],float(r['lambda_multiplier'])):float(r['prediction']) for r in predictions};assert len(lookup)==len(predictions)
    curve=[{k:float(v) for k,v in r.items()} for r in read(tables/'finite_er_curve.csv')]
    curve_errors=[abs(r['s2']-finite_er_moments(cfg['n'],r['rho'])['s2']) for r in curve];assert max(curve_errors)<1e-10
    max_prediction_error=0.;matched=0
    for rep in range(cfg['replications']):
        ll=[r for r in labels if int(r['replication'])==rep];ff=[features[r['window_id']] for r in ll];y=np.array([float(r['rho']) for r in ll]);tr=[i for i,r in enumerate(ll) if r['split']=='train'];va=[i for i,r in enumerate(ll) if r['split']=='validation'];te=[i for i,r in enumerate(ll) if r['split'] in ['test','unseen']]
        models={}
        for method in ['RBF_return','RBF_joint','RBF_volume','RBF_shape_joint']:
            x=view_matrix(ff,method);model,_,_=select_regressor('RBF',x[tr],y[tr],x[va],y[va],cfg);models[method]=model
        for factor in cfg['lambda_multipliers']:
            test=[]
            for i in te:
                f=dict(ff[i])
                for key in PRICE_FEATURES[:4]:f[key]*=factor
                test.append(f)
            results={method:model.predict(view_matrix(test,method)) for method,model in models.items()}
            results['Moment_volume']=[volume_moment_estimate(f,curve,cfg['n'],cfg['unit_order'])['rho'] for f in test]
            for method,predicted in results.items():
                for i,prediction in zip(te,predicted):
                    error=abs(prediction-lookup[ll[i]['window_id'],method,factor]);max_prediction_error=max(max_prediction_error,float(error));matched+=1
                    assert error<1e-12
    assert matched==len(predictions)
    report={'status':'pass','periods_reloaded':periods,'windows_recomputed':len(features),'training_studies_refitted':cfg['replications'],'predictions_reproduced':matched,'max_feature_error':max_feature_error,'max_prediction_error':max_prediction_error,'max_curve_error':max(curve_errors),'prior_primary_and_followup_seeds_disjoint':True,'seconds':time.perf_counter()-start,'member_review':'not_run','script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (checks/'end_to_end_reproduction.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
