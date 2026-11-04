#!/usr/bin/env python3
"""Locked literature-informed replication, physical inference and scale robustness study."""
from pathlib import Path
import argparse,csv,hashlib,json,os,platform,sys,time
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
os.environ.setdefault('OMP_NUM_THREADS','1')
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import numpy as np
import scipy
import sklearn
from scipy.stats import binomtest
from econophysics.model import Parameters,derived_seed,simulate_aggregates
from econophysics.features import PRICE_FEATURES,VOLUME_FEATURES,window_features
from econophysics.inference import select_regressor
from econophysics.physics_inference import finite_er_moments,scale_invariant_joint,volume_moment_estimate
from econophysics.study_statistics import holm_adjust


def save_json(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def save_csv(path,rows):
    with path.open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)


def matrix(features,view):
    if view=='RBF_shape_joint':values=[scale_invariant_joint(f) for f in features]
    else:
        keys={'RBF_return':PRICE_FEATURES,'RBF_joint':PRICE_FEATURES+VOLUME_FEATURES,'RBF_volume':VOLUME_FEATURES[:3]}[view]
        values=[[f[k] for k in keys] for f in features]
    return np.array([[np.nan if x is None else x for x in row] for row in values])


def bootstrap(values,rng,b):
    values=np.asarray(values)
    means=values[rng.integers(0,len(values),(b,len(values)))].mean(axis=1)
    lo,hi=np.quantile(means,[.025,.975]);return float(lo),float(hi)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run-id',default='depth_study_v1');parser.add_argument('--config',default='configs/depth_study_v1.json');args=parser.parse_args()
    if not args.run_id.replace('_','').replace('-','').isalnum():parser.error('invalid run ID')
    config_path=ROOT/args.config;cfg=json.loads(config_path.read_text())
    tables,checks,predictions=[ROOT/p/args.run_id for p in ['results/tables','results/checks','results/predictions']]
    if any(p.exists() for p in (tables,checks,predictions)):parser.error('run ID exists')
    for p in (tables,checks,predictions):p.mkdir(parents=True)
    save_json(checks/'locked_config.json',cfg);start=time.perf_counter()
    source_paths=sorted((ROOT/'src/econophysics').glob('*.py'))+[Path(__file__).resolve(),config_path]
    record={'status':'running','scope':cfg['scope'],'command':f'python3 scripts/run_depth_study.py --config {args.config} --run-id {args.run_id}',
            'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,'sklearn':sklearn.__version__,
            'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths},'member_review':'not_run'}
    save_json(checks/'run_record.json',record);validations=[]
    def check(name,condition,**details):
        validations.append({'check':name,'status':'pass' if condition else 'fail',**details})
        if not condition:raise AssertionError(name)
    try:
        rhos=[i*cfg['curve_dense_step'] for i in range(round(cfg['curve_dense_max']/cfg['curve_dense_step'])+1)]+cfg['curve_coarse_tail']
        curve=[{'n':cfg['n'],'rho':rho,**finite_er_moments(cfg['n'],rho,cfg['decimal_precision'])} for rho in rhos]
        check('finite-N calibration strictly monotone',all(b['s2']>a['s2'] for a,b in zip(curve,curve[1:])))
        check('finite-N endpoints',curve[0]['s2']==cfg['n'] and curve[-1]['s2']==cfg['n']**2)
        precision=[]
        for rho in [.025,.4,1.,1.6,2.5]:
            a=finite_er_moments(cfg['n'],rho,cfg['decimal_precision']);b=finite_er_moments(cfg['n'],rho,cfg['precision_crosscheck'])
            difference=abs(a['s2']-b['s2']);precision.append({'rho':rho,'difference':difference});check(f'precision stability rho={rho}',difference<1e-10)
        interpolation=[]
        for rho in [.4125,.7875,1.0125,1.4875,1.6125]:
            a=finite_er_moments(cfg['n'],rho)['s2'];estimate=float(np.interp(a,[r['s2'] for r in curve],[r['rho'] for r in curve]))
            interpolation.append({'rho':rho,'interpolated_rho':estimate,'absolute_error':abs(estimate-rho)})
        save_csv(tables/'finite_er_curve.csv',curve);save_csv(tables/'curve_interpolation_checks.csv',interpolation)
        save_json(checks/'precision_crosscheck.json',precision)
        print('Finite-N ER reference curve complete',flush=True)
        seen=set();old_labels=ROOT/'results/tables/simulation_study_v1/learning_labels_NOT_FEATURES.csv'
        old_seeds={int(r['seed']) for r in csv.DictReader(old_labels.open())} if old_labels.exists() else set()
        metrics=[];predrows=[];feature_rows=[];labels=[];candidate_rows=[];physical_rows=[];all_training_counts=[]
        with (tables/'observations.csv').open('w',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=['window_id','t','r','V']);writer.writeheader()
            for repetition in range(cfg['replications']):
                feats=[];labs=[]
                for ri,rho in enumerate(cfg['rho']):
                    for ai,a in enumerate(cfg['a']):
                        total=cfg['train_per_cell']+cfg['validation_per_cell']+cfg['test_per_cell']
                        permutation=np.random.default_rng(derived_seed(cfg['seed'],f'split:{repetition}:{ri}:{ai}')).permutation(total)
                        assignments={int(k):('train' if j<cfg['train_per_cell'] else 'validation' if j<cfg['train_per_cell']+cfg['validation_per_cell'] else 'test') for j,k in enumerate(permutation)}
                        for j in range(total):
                            wid=f'rep{repetition:02}_r{ri}_a{ai}_w{j:02}';seed=derived_seed(cfg['seed'],wid)
                            if seed in seen or seed in old_seeds:raise AssertionError('seed reuse')
                            seen.add(seed)
                            obs=simulate_aggregates(Parameters(n=cfg['n'],rho=rho,a=a,lambda_impact=cfg['lambda_impact'],unit_order=cfg['unit_order']),cfg['window_length'],seed)
                            f=window_features(obs);lab={'window_id':wid,'replication':repetition,'rho':rho,'a':a,'seed':seed,'split':assignments[j]}
                            feats.append(f);labs.append(lab);writer.writerows({'window_id':wid,'t':t,**o} for t,o in enumerate(obs))
                for ri,rho in enumerate(cfg['unseen_rho']):
                    for ai,a in enumerate(cfg['a']):
                        for j in range(cfg['unseen_per_cell']):
                            wid=f'rep{repetition:02}_new{ri}_a{ai}_w{j:02}';seed=derived_seed(cfg['seed'],wid)
                            if seed in seen or seed in old_seeds:raise AssertionError('seed reuse')
                            seen.add(seed)
                            obs=simulate_aggregates(Parameters(n=cfg['n'],rho=rho,a=a,lambda_impact=cfg['lambda_impact'],unit_order=cfg['unit_order']),cfg['window_length'],seed)
                            f=window_features(obs);lab={'window_id':wid,'replication':repetition,'rho':rho,'a':a,'seed':seed,'split':'unseen'}
                            feats.append(f);labs.append(lab);writer.writerows({'window_id':wid,'t':t,**o} for t,o in enumerate(obs))
                labels.extend(labs);feature_rows.extend({'window_id':lab['window_id'],**f} for lab,f in zip(labs,feats))
                y=np.array([r['rho'] for r in labs]);split=np.array([r['split'] for r in labs]);train=np.flatnonzero(split=='train');val=np.flatnonzero(split=='validation')
                check(f'locked sample counts rep={repetition}',len(train)==252 and len(val)==84 and np.sum(split=='test')==84 and np.sum(split=='unseen')==72)
                all_training_counts.append(len(train));models={}
                for view in ['RBF_return','RBF_joint','RBF_volume','RBF_shape_joint']:
                    x=matrix(feats,view);model,candidates,index=select_regressor('RBF',x[train],y[train],x[val],y[val],cfg);models[view]=model
                    candidate_rows.extend({'replication':repetition,'method':view,'candidate':i,'selected':i==index,'alpha':r['specification']['alpha'],'gamma':r['specification']['gamma'],'validation_mae':r['validation_mae']} for i,r in enumerate(candidates))
                base_predictions={}
                for test_split in ['test','unseen']:
                    indices=np.flatnonzero(split==test_split);target=y[indices]
                    for factor in cfg['lambda_multipliers']:
                        sf=[]
                        for i in indices:
                            f=dict(feats[i])
                            for key in PRICE_FEATURES[:4]:f[key]*=factor
                            sf.append(f)
                        predictions_by_method={view:model.predict(matrix(sf,view)) for view,model in models.items()}
                        estimates=[volume_moment_estimate(f,curve,cfg['n'],cfg['unit_order']) for f in sf]
                        check(f'physical estimator defined rep={repetition},{test_split},{factor}',all(e['rho'] is not None for e in estimates))
                        predictions_by_method['Moment_volume']=np.array([e['rho'] for e in estimates])
                        for method,predicted in predictions_by_method.items():
                            loss=np.abs(predicted-target);check(f'finite prediction {repetition},{test_split},{factor},{method}',np.isfinite(predicted).all())
                            metrics.append({'replication':repetition,'test_split':test_split,'lambda_multiplier':factor,'method':method,'mae':float(loss.mean()),'window_loss_sd':float(loss.std(ddof=1)),'test_windows':len(indices)})
                            predrows.extend({'window_id':labs[i]['window_id'],'replication':repetition,'test_split':test_split,'rho':float(target[j]),'a':labs[i]['a'],'lambda_multiplier':factor,'method':method,'prediction':float(predicted[j]),'absolute_error':float(loss[j])} for j,i in enumerate(indices))
                            key=(test_split,method)
                            if factor==cfg['lambda_multipliers'][0]:base_predictions[key]=predicted.copy()
                            if method in ['RBF_shape_joint','RBF_volume','Moment_volume']:
                                check(f'scale invariance {repetition},{test_split},{factor},{method}',float(np.max(np.abs(predicted-base_predictions[key])))<1e-10)
                        if factor==1:
                            for i,f,e in zip(indices,sf,estimates):
                                lam=cfg['n']*cfg['unit_order']*np.sqrt((1-e['q'])*f['return_std']**2/f['volume_std']**2)
                                physical_rows.append({'window_id':labs[i]['window_id'],'replication':repetition,'test_split':test_split,'rho_true':labs[i]['rho'],'rho_estimate':e['rho'],'q_true':2*labs[i]['a'],'q_estimate':e['q'],'lambda_true':cfg['lambda_impact'],'lambda_estimate':float(lam),'s2_estimate':e['s2'],'flag':e['flag']})
                save_csv(tables/'run_metrics.csv',metrics);save_csv(tables/'learning_features.csv',feature_rows);save_csv(tables/'labels_NOT_FEATURES.csv',labels)
                save_csv(predictions/'test_predictions.csv',predrows);save_csv(tables/'physical_estimates.csv',physical_rows);save_csv(tables/'validation_candidates.csv',candidate_rows)
                record.update(completed_replications=repetition+1,elapsed_seconds=time.perf_counter()-start);save_json(checks/'run_record.json',record)
                print(f'Replication {repetition+1}/{cfg["replications"]} complete; fresh windows={len(labels)}; seconds={time.perf_counter()-start:.1f}',flush=True)
        summaries=[];rng=np.random.default_rng(derived_seed(cfg['seed'],'run-statistics'))
        for test_split in ['test','unseen']:
            for factor in cfg['lambda_multipliers']:
                for method in ['RBF_return','RBF_joint','RBF_volume','RBF_shape_joint','Moment_volume']:
                    vals=np.array([r['mae'] for r in metrics if r['test_split']==test_split and r['lambda_multiplier']==factor and r['method']==method]);lo,hi=bootstrap(vals,rng,cfg['bootstrap_replicates'])
                    summaries.append({'test_split':test_split,'lambda_multiplier':factor,'method':method,'replications':len(vals),'mean_mae':float(vals.mean()),'run_sd':float(vals.std(ddof=1)),'ci_low':lo,'ci_high':hi,'min_mae':float(vals.min()),'max_mae':float(vals.max())})
        contrasts=[]
        for name,left,right,factor in [('joint minus return','RBF_joint','RBF_return',1.),('joint minus volume','RBF_joint','RBF_volume',1.),('shape-joint minus joint','RBF_shape_joint','RBF_joint',2.)]:
            lv=np.array([r['mae'] for r in metrics if r['test_split']=='test' and r['lambda_multiplier']==factor and r['method']==left]);rv=np.array([r['mae'] for r in metrics if r['test_split']=='test' and r['lambda_multiplier']==factor and r['method']==right]);delta=lv-rv
            lo,hi=bootstrap(delta,rng,cfg['bootstrap_replicates']);wins=int(np.sum(delta<0));nonzero=int(np.sum(delta!=0))
            contrasts.append({'contrast':name,'lambda_multiplier':factor,'replications':len(delta),'mean_difference':float(delta.mean()),'difference_sd':float(delta.std(ddof=1)),'paired_standardized_effect':float(delta.mean()/delta.std(ddof=1)) if delta.std(ddof=1) else 0.,'ci_low':lo,'ci_high':hi,'left_wins':wins,'non_tied_runs':nonzero,'sign_p_two_sided':float(binomtest(wins,nonzero,.5).pvalue) if nonzero else 1.,'relative_mean_mae_reduction_percent':float(100*(1-lv.mean()/rv.mean()))})
        for row,p in zip(contrasts,holm_adjust([r['sign_p_two_sided'] for r in contrasts])):row['sign_p_holm']=p
        save_csv(tables/'summary_metrics.csv',summaries);save_csv(tables/'run_contrasts.csv',contrasts)
        check('all windows independently generated',len(seen)==cfg['replications']*492 and len(labels)==len(seen))
        check('all observed features exclude metadata',not(set(PRICE_FEATURES+VOLUME_FEATURES)&{'rho','a','seed','window_id','split','replication'}))
        save_json(checks/'checks.json',{'status':'pass','kind':['SIMULATION','MODEL_CHECK'],'checks':validations})
        record.update(status='pass',completed_replications=cfg['replications'],fresh_windows=len(labels),periods=len(labels)*cfg['window_length'],elapsed_seconds=time.perf_counter()-start,
                      outputs={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for d in [tables,predictions] for p in sorted(d.iterdir())})
        save_json(checks/'run_record.json',record)
        print(json.dumps({'status':'pass','seconds':record['elapsed_seconds'],'contrasts':contrasts},indent=2),flush=True)
    except Exception as exc:
        record.update(status='failed',error=repr(exc),elapsed_seconds=time.perf_counter()-start);save_json(checks/'run_record.json',record);raise


if __name__=='__main__':main()
