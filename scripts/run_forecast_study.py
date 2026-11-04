#!/usr/bin/env python3
"""Execute the frozen 2025/2026 chronological forecast experiment once."""
from pathlib import Path
import argparse,csv,hashlib,itertools,json,os,sys,time
os.environ.setdefault('OPENBLAS_NUM_THREADS','1');os.environ.setdefault('OMP_NUM_THREADS','1')
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import numpy as np
from econophysics.forecasting import daily_features,forecast_samples,feature_names,LogRegressor,fit_logit,daily_losses,ewma_at_origin
from econophysics.model import derived_seed
from econophysics.real_market_statistics import circular_day_weights
from econophysics.study_statistics import holm_adjust


def read(p):return list(csv.DictReader(p.open()))
def write(p,rows):
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def ci(x):return [float(v) for v in np.quantile(x,[.025,.975])]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run-id',default='forecast_v1');args=parser.parse_args()
    if not args.run_id.replace('_','').replace('-','').isalnum():parser.error('invalid id')
    tables=ROOT/'results/tables'/args.run_id;checks=ROOT/'results/checks'/args.run_id
    if tables.exists():parser.error('run exists; preserve evidence')
    tables.mkdir(parents=True);checks.mkdir(parents=True,exist_ok=True);cfgpath=ROOT/'configs/forecast_v1.json';cfg=json.loads(cfgpath.read_text());start=time.perf_counter()
    sources=[cfgpath,Path(__file__).resolve(),ROOT/'src/econophysics/forecasting.py',ROOT/'docs/AB/forecast_contract.md']+[ROOT/'data/processed'/cfg[k]/'bars.csv' for k in ['dataset_2025','dataset_2026']]
    record={'status':'running','member_review':'not_run','command':f'python scripts/run_forecast_study.py --run-id {args.run_id}','source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}}
    (checks/'run_record.json').write_text(json.dumps(record,indent=2)+'\n');(checks/'locked_config.json').write_bytes(cfgpath.read_bytes())
    bars=list(itertools.chain.from_iterable(read(ROOT/'data/processed'/cfg[k]/'bars.csv') for k in ['dataset_2025','dataset_2026']));days=daily_features(bars);samples=forecast_samples(days);write(tables/'daily_features.csv',days);write(tables/'forecast_samples.csv',samples)
    dates=np.array([s['target_date'] for s in samples]);train=dates<cfg['validation_target_start'];valid=(dates>=cfg['validation_target_start'])&(dates<cfg['test_target_start']);test=dates>=cfg['test_target_start'];refit=train|valid
    y=np.array([s['target_rv'] for s in samples]);z=np.log(y);threshold=float(np.quantile([d['rv'] for d in days if d['date']<'2026-01-01'],.9));event=(y>threshold).astype(int)
    assert (train.sum(),valid.sum(),test.sum())==(337,90,183)
    def X(names):
        values=np.array([[s[k] for k in names] for s in samples]);assert np.all(np.isfinite(values));return values
    predictions={};validation_predictions={};selection=[];chosen={};frozen=[]
    for name in cfg['regression_models']:
        if name=='Persistence':
            prediction=X(['log_rv_1']).ravel();chosen[name]={'kind':'persistence'}
        elif name=='EWMA':
            candidates=[]
            for alpha in cfg['ewma_alpha']:
                lookup=ewma_at_origin(days,alpha);pred=np.array([np.log(lookup[s['origin_date']]) for s in samples]);score=float(np.mean((z[valid]-pred[valid])**2));candidates.append((score,alpha,pred));selection.append({'model':name,'parameters':json.dumps({'alpha':alpha}),'validation_log_mse':score})
            _,alpha,prediction=min(candidates,key=lambda a:a[0]);chosen[name]={'kind':'ewma','alpha':alpha}
        else:
            names=feature_names(name,cfg['groups']);xx=X(names);kind='rbf' if name.startswith('RBF') else 'ridge';specs=[{'alpha':a} for a in cfg['ridge_alpha']] if kind=='ridge' else [{'alpha':a,'gamma':g/len(names)} for a,g in itertools.product(cfg['rbf_alpha'],cfg['rbf_gamma_multipliers'])];candidates=[]
            for spec in specs:
                model=LogRegressor(kind,spec).fit(xx[train],z[train]);pred=model.predict(xx[valid]);score=float(np.mean((z[valid]-pred)**2));candidates.append((score,spec,pred));selection.append({'model':name,'parameters':json.dumps(spec,sort_keys=True),'validation_log_mse':score})
            _,spec,pred=min(candidates,key=lambda a:a[0]);validation_predictions[name]=pred;chosen[name]={'kind':kind,'features':names,'parameters':spec};model=LogRegressor(kind,spec).fit(xx[refit],z[refit]);prediction=model.predict(xx)
            if kind=='ridge':
                scaler=model.pipeline.steps[0][1];estimator=model.pipeline.steps[-1][1]
                for f,coef,mean,scale in zip(names,estimator.coef_,scaler.mean_,scaler.scale_):frozen.append({'model':name,'feature':f,'coefficient_per_training_SD':float(coef),'training_feature_mean':float(mean),'training_feature_sd':float(scale),'target_mean':model.mean,'interpretation':'Linear association conditional on included predictors, not causal contribution'})
        predictions[name]=prediction[test]
        if name not in validation_predictions:validation_predictions[name]=prediction[valid]
        print('Fitted regression:',name,flush=True)
    probability={};prob_selection=[]
    for name in cfg['probability_models']:
        if name=='Climatology':probability[name]=np.full(test.sum(),event[refit].mean());chosen[name]={'probability':float(event[refit].mean())};continue
        names=feature_names(name,cfg['groups']);xx=X(names);candidates=[]
        for C in cfg['probability_C']:
            model=fit_logit(xx[train],event[train],C);prob=model.predict_proba(xx[valid])[:,1];score=float(np.mean((prob-event[valid])**2));candidates.append((score,C));prob_selection.append({'model':name,'C':C,'validation_brier':score})
        _,C=min(candidates,key=lambda a:a[0]);model=fit_logit(xx[refit],event[refit],C);probability[name]=model.predict_proba(xx[test])[:,1];chosen[name]={'features':names,'C':C}
    # Freeze selections before calculating any final metrics.
    frozen_record={'status':'selected_before_final_metric_calculation','models':chosen,'high_volatility_RV_threshold_2025':threshold,'train_targets':int(train.sum()),'validation_targets':int(valid.sum()),'test_targets':int(test.sum()),'final_fit_last_target':'2026-03-31','test_coefficients_fixed':True}
    (checks/'selected_models.json').write_text(json.dumps(frozen_record,indent=2)+'\n');write(tables/'validation_grid.csv',selection);write(tables/'probability_validation_grid.csv',prob_selection);write(tables/'linear_coefficients.csv',frozen)
    write(tables/'validation_predictions.csv',[{'model':m,'target_date':date,'actual_rv':float(actual),'prediction_rv':float(np.exp(pred)),'log_prediction':float(pred)} for m in validation_predictions for date,actual,pred in zip(dates[valid],y[valid],validation_predictions[m])])
    yt=y[test];labels=event[test];D=len(yt);weights={L:circular_day_weights(D,L,cfg['bootstrap_replicates'],np.random.default_rng(derived_seed(cfg['seed'],f'forecast-block:{L}'))) for L in cfg['bootstrap_day_block_lengths']};loss={m:daily_losses(yt,pred) for m,pred in predictions.items()};rows=[]
    test_samples=[s for s,t in zip(samples,test) if t]
    for m,pred in predictions.items():
        for i,s in enumerate(test_samples):rows.append({'model':m,'origin_date':s['origin_date'],'target_date':s['target_date'],'actual_rv':float(yt[i]),'log_prediction':float(pred[i]),'prediction_rv':float(np.exp(pred[i])),'actual_volatility_pct':float(100*np.sqrt(yt[i])),'prediction_volatility_pct':float(100*np.exp(pred[i]/2)),'high_volatility_day':int(labels[i]),**{k:float(v[i]) for k,v in loss[m].items()}})
    write(tables/'test_predictions.csv',rows)
    metric=[];contrast=[];pairs=[(m,'HAR') for m in cfg['regression_models'] if m!='HAR']+[('RBF-All','RBF-HAR')]
    for L,w in weights.items():
        for m in loss:
            for k,v in loss[m].items():
                lo,hi=ci(w@v/D);metric.append({'model':m,'metric':k,'mean_loss':float(v.mean()),'ci_low':lo,'ci_high':hi,'day_block_length':L,'test_days':D})
        for k in ['log_mse','qlike','volatility_mae']:
            family=[]
            for m,b in pairs:
                delta=loss[m][k]-loss[b][k];point=float(delta.mean());boot=w@delta/D;lo,hi=ci(boot);skill=100*(1-float(loss[m][k].mean()/loss[b][k].mean()));skillboot=100*(1-(w@loss[m][k])/(w@loss[b][k]));slo,shi=ci(skillboot);p=(1+np.sum(np.abs(boot-point)>=abs(point)))/(len(boot)+1)
                family.append({'model':m,'baseline':b,'metric':k,'loss_difference':point,'difference_ci_low':lo,'difference_ci_high':hi,'improvement_pct':skill,'improvement_ci_low':slo,'improvement_ci_high':shi,'p_approx':float(p),'day_block_length':L,'test_days':D,'primary':m=='HAR+All' and b=='HAR' and k=='log_mse'})
            for row,adjusted in zip(family,holm_adjust([x['p_approx'] for x in family])):row['p_holm']=adjusted
            contrast.extend(family)
    write(tables/'regression_metrics.csv',metric);write(tables/'regression_contrasts.csv',contrast)
    months=np.array([s['target_date'][:7] for s in test_samples]);monthly=[]
    cuts=np.quantile([d['rv'] for d in days if d['date']<'2026-01-01'],[.25,.5,.9]);regime=np.searchsorted(cuts,yt,side='right');regime_rows=[]
    for m in loss:
        for month in sorted(set(months)):
            ix=months==month;monthly.append({'model':m,'month':month,'days':int(ix.sum()),'log_mse':float(loss[m]['log_mse'][ix].mean()),'HAR_log_mse':float(loss['HAR']['log_mse'][ix].mean()),'improvement_vs_HAR_pct':float(100*(1-loss[m]['log_mse'][ix].mean()/loss['HAR']['log_mse'][ix].mean()))})
        for j in range(4):
            ix=regime==j
            if ix.any():regime_rows.append({'model':m,'regime':j,'label':['Below train Q25','Train Q25-Q50','Train Q50-Q90','Above train Q90'][j],'days':int(ix.sum()),'log_mse':float(loss[m]['log_mse'][ix].mean()),'improvement_vs_HAR_pct':float(100*(1-loss[m]['log_mse'][ix].mean()/loss['HAR']['log_mse'][ix].mean()))})
    write(tables/'monthly_metrics.csv',monthly);write(tables/'regime_metrics.csv',regime_rows)
    probs=[];prob_metrics=[];prob_contrasts=[];calibration=[];ploss={m:(p-labels)**2 for m,p in probability.items()}
    for m,pp in probability.items():
        for i,s in enumerate(test_samples):probs.append({'model':m,'target_date':s['target_date'],'probability':float(pp[i]),'event':int(labels[i]),'brier':float(ploss[m][i]),'actual_rv':float(yt[i]),'threshold_rv':threshold})
        bins=np.searchsorted(cfg['probability_bins'][1:-1],pp,side='right')
        for j in range(len(cfg['probability_bins'])-1):
            ix=bins==j;n=int(ix.sum());calibration.append({'model':m,'bin':j,'lower':cfg['probability_bins'][j],'upper':cfg['probability_bins'][j+1],'days':n,'events':int(labels[ix].sum()),'mean_probability':float(pp[ix].mean()) if n else None,'event_frequency':float(labels[ix].mean()) if n else None,'interpretation':'Descriptive fixed bins; dependence and sparse counts preclude a precision claim'})
    for L,w in weights.items():
        for m,v in ploss.items():
            lo,hi=ci(w@v/D);prob_metrics.append({'model':m,'brier':float(v.mean()),'ci_low':lo,'ci_high':hi,'events':int(labels.sum()),'test_days':D,'day_block_length':L})
        family=[]
        for m,b in [('Logit-HAR','Climatology'),('Logit-All','Climatology'),('Logit-All','Logit-HAR')]:
            delta=ploss[m]-ploss[b];point=float(delta.mean());boot=w@delta/D;lo,hi=ci(boot);slo,shi=ci(100*(1-(w@ploss[m])/(w@ploss[b])));p=(1+np.sum(np.abs(boot-point)>=abs(point)))/(len(boot)+1);family.append({'model':m,'baseline':b,'loss_difference':point,'difference_ci_low':lo,'difference_ci_high':hi,'improvement_pct':float(100*(1-ploss[m].mean()/ploss[b].mean())),'improvement_ci_low':slo,'improvement_ci_high':shi,'p_approx':float(p),'day_block_length':L})
        for row,p in zip(family,holm_adjust([r['p_approx'] for r in family])):row['p_holm']=p
        prob_contrasts.extend(family)
    write(tables/'probability_predictions.csv',probs);write(tables/'probability_metrics.csv',prob_metrics);write(tables/'probability_contrasts.csv',prob_contrasts);write(tables/'probability_calibration.csv',calibration)
    summary={'status':'pass','member_review':'not_run','real_bars':len(bars),'daily_observations':len(days),'train_targets':int(train.sum()),'validation_targets':int(valid.sum()),'test_targets':D,'first_test':str(dates[test][0]),'last_test':str(dates[test][-1]),'test_events':int(labels.sum()),'event_threshold_rv':threshold,'event_threshold_volatility_pct':100*np.sqrt(threshold),'primary':[r for r in contrast if r['primary'] and r['day_block_length']==7][0],
             'primary_metrics':[r for r in metric if r['model'] in ['HAR','HAR+All'] and r['day_block_length']==7],'secondary_probability':[r for r in prob_contrasts if r['day_block_length']==7],'regime_thresholds_rv':cuts.tolist(),'seconds':time.perf_counter()-start}
    (checks/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');record.update(status='pass',seconds=summary['seconds'],outputs_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in tables.glob('*.csv')});(checks/'run_record.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
