"""Post-primary frozen-model diagnostics: volume control and unseen-rho interpolation."""

from pathlib import Path
import argparse,csv,hashlib,json,sys,time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import numpy as np
from econophysics.model import Parameters,derived_seed,simulate_aggregates
from econophysics.features import PRICE_FEATURES,VOLUME_FEATURES,window_features
from econophysics.inference import make_regressor,select_regressor
from econophysics.study_statistics import interval,stratified_bootstrap_mean


def load(path):
    with path.open() as stream:return list(csv.DictReader(stream))


def save(path,rows):
    with path.open('w',newline='') as stream:
        w=csv.DictWriter(stream,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id',default='simulation_followup_v1')
    args=parser.parse_args()
    if not args.run_id.replace('_','').replace('-','').isalnum():parser.error('invalid run ID')
    cfg_path=ROOT/'configs/simulation_followup_v1.json';cfg=json.loads(cfg_path.read_text())
    primary=json.loads((ROOT/'configs/simulation_study_v1.json').read_text())
    tables,checks,predictions=[ROOT/p/args.run_id for p in ['results/tables','results/checks','results/predictions']]
    if any(p.exists() for p in [tables,checks,predictions]):parser.error('run exists')
    for p in [tables,checks,predictions]:p.mkdir(parents=True)
    (checks/'locked_config.json').write_text(json.dumps(cfg,indent=2)+'\n')
    began=time.perf_counter();base=ROOT/'results/tables'/cfg['primary_run']
    labels=load(base/'learning_labels_NOT_FEATURES.csv');features=load(base/'learning_features.csv')
    assert [r['window_id'] for r in labels]==[r['window_id'] for r in features]
    names=PRICE_FEATURES+VOLUME_FEATURES
    x=np.array([[float(r[k]) if r[k] else np.nan for k in names] for r in features]);y=np.array([float(r['rho']) for r in labels])
    train=np.array([i for i,r in enumerate(labels) if r['split']=='train']);val=np.array([i for i,r in enumerate(labels) if r['split']=='validation']);test=np.array([i for i,r in enumerate(labels) if r['split']=='test'])
    groups=np.array([labels[i]['stratum'] for i in test]);models={};columns={}
    for view,cols in [('Return only',list(range(5))),('Return + volume',list(range(9)))]:
        row=next(r for r in load(base/'learning_metrics.csv') if float(r['training_fraction'])==1 and r['method']=='RBF' and r['view']==view)
        models[view]=make_regressor('RBF',json.loads(row['selected_specification'])).fit(x[np.ix_(train,cols)],y[train]);columns[view]=cols
    cols=[names.index(k) for k in cfg['volume_control_features']]
    control,candidates,index=select_regressor('RBF',x[np.ix_(train,cols)],y[train],x[np.ix_(val,cols)],y[val],primary['inference'])
    models['Volume-only control']=control;columns['Volume-only control']=cols
    save(tables/'control_validation.csv',[{'candidate_id':i,'selected':i==index,**r} for i,r in enumerate(candidates)])
    rng=np.random.default_rng(cfg['seed']);stress=[];stress_predictions=[]
    for factor in cfg['lambda_multipliers']:
        sx=x[test].copy();sx[:,:4]*=factor
        for view,model in models.items():
            prediction=model.predict(sx[:,columns[view]]);error=np.abs(prediction-y[test])
            boot=stratified_bootstrap_mean(error,groups,rng,cfg['bootstrap_replicates']);lo,hi=interval(boot)
            stress.append({'lambda_multiplier':factor,'view':view,'mae':float(error.mean()),'ci_low':lo,'ci_high':hi,'independent_base_windows':len(test),'training_runs':1})
            stress_predictions.extend({'window_id':labels[i]['window_id'],'rho':float(y[i]),'lambda_multiplier':factor,'view':view,'prediction':float(p),'absolute_error':float(e)} for i,p,e in zip(test,prediction,error))
    save(tables/'stress_control_metrics.csv',stress);save(predictions/'stress_control_predictions.csv',stress_predictions)
    held_rows=[];observed=[];held_features=[];primary_seeds={int(r['seed']) for r in labels}
    for ri,rho in enumerate(cfg['unseen_rho']):
        for ai,a in enumerate(cfg['a']):
            for rep in range(cfg['windows_per_cell']):
                wid=f'new_r{ri}_a{ai}_w{rep}';seed=derived_seed(cfg['seed'],wid)
                assert seed not in primary_seeds and rho not in primary['inference']['rho']
                obs=simulate_aggregates(Parameters(n=128,rho=rho,a=a,lambda_impact=cfg['lambda_impact']),cfg['window_length'],seed)
                held_rows.append({'window_id':wid,'rho':rho,'a':a,'seed':seed,'stratum':f'{ri}_{ai}'})
                held_features.append(window_features(obs));observed.extend({'window_id':wid,'t':t,**r} for t,r in enumerate(obs))
    sx=np.array([[np.nan if f[k] is None else f[k] for k in names] for f in held_features]);target=np.array([r['rho'] for r in held_rows]);sg=np.array([r['stratum'] for r in held_rows])
    metrics=[];prediction_rows=[]
    for view,model in models.items():
        prediction=model.predict(sx[:,columns[view]]);error=np.abs(prediction-target)
        boot=stratified_bootstrap_mean(error,sg,rng,cfg['bootstrap_replicates']);lo,hi=interval(boot)
        metrics.append({'view':view,'mae':float(error.mean()),'loss_sd':float(error.std(ddof=1)),'ci_low':lo,'ci_high':hi,'test_windows':len(target),'training_runs':1})
        prediction_rows.extend({'window_id':row['window_id'],'rho':row['rho'],'a':row['a'],'view':view,'prediction':float(p),'absolute_error':float(e)} for row,p,e in zip(held_rows,prediction,error))
    save(tables/'unseen_rho_labels_NOT_FEATURES.csv',held_rows);save(tables/'unseen_rho_observations.csv',observed)
    save(tables/'unseen_rho_metrics.csv',metrics);save(predictions/'unseen_rho_predictions.csv',prediction_rows)
    main_predictions=load(ROOT/'results/predictions'/cfg['primary_run']/'test_predictions.csv')
    reconstruction=max(abs(row['prediction']-float(next(p['prediction'] for p in main_predictions if p['window_id']==row['window_id'] and p['view']==row['view'] and p['method']=='RBF'))) for row in stress_predictions if row['lambda_multiplier']==1 and row['view']!='Volume-only control')
    control_values=[r['mae'] for r in stress if r['view']=='Volume-only control']
    assertions=[{'check':'frozen primary prediction reconstruction','status':'pass' if reconstruction<1e-12 else 'fail','max_difference':reconstruction},
                {'check':'volume control exactly invariant to lambda rescaling','status':'pass' if max(control_values)-min(control_values)<1e-14 else 'fail'},
                {'check':'new rho values and seeds excluded from original training','status':'pass','new_windows':len(held_rows)}]
    assert all(r['status']=='pass' for r in assertions)
    (checks/'checks.json').write_text(json.dumps({'status':'pass','checks':assertions},indent=2)+'\n')
    sources=list((ROOT/'src/econophysics').glob('*.py'))+[Path(__file__).resolve(),cfg_path]
    record={'status':'pass','scope':'post-primary supplementary diagnostics; original primary comparison unchanged','primary_run':cfg['primary_run'],'command':f'python3 scripts/run_simulation_followup.py --run-id {args.run_id}',
            'elapsed_seconds':time.perf_counter()-began,'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},'member_review':'not_run',
            'outputs':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for d in [tables,predictions] for p in sorted(d.iterdir())}}
    (checks/'run_record.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({'status':'pass','interpolation':metrics,'volume_control_mae':control_values[0]},indent=2))


if __name__=='__main__':main()
