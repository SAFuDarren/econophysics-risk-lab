#!/usr/bin/env python3
"""Independent raw-data, chronology, ridge-algebra and metric verification."""

from pathlib import Path as _ProjectPath
import sys as _project_sys
_project_sys.path.insert(0, str(_ProjectPath(__file__).resolve().parents[1]))
from _bootstrap import ROOT as PROJECT_ROOT, script_path, resolve_recorded_path
from pathlib import Path
import argparse,csv,hashlib,io,json,sys,zipfile
ROOT=PROJECT_ROOT;sys.path.insert(0,str(ROOT/'src'))
import numpy as np
from econophysics.forecasting import daily_features,forecast_samples,daily_losses
from econophysics.real_market_statistics import circular_day_weights


def read(p):return list(csv.DictReader(p.open()))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run-id',default='forecast_v1');args=parser.parse_args();tables=ROOT/'results/tables'/args.run_id;checks=ROOT/'results/checks'/args.run_id;cfg=json.loads((ROOT/'configs/forecast_v1.json').read_text());tests=[]
    def check(name,condition):
        tests.append({'check':name,'passed':bool(condition)})
        if not condition:raise AssertionError(name)
    manifest=json.loads((ROOT/'data/manifests'/cfg['dataset_2026']/'download_manifest.json').read_text());pieces=[]
    for item in manifest['files']:
        p=ROOT/item['raw_path'];check('Archive hash '+item['period'],hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256'])
        with zipfile.ZipFile(p) as z:a=np.loadtxt(io.BytesIO(z.read(z.namelist()[0])),delimiter=',')
        pieces.append(a)
    raw=np.concatenate(pieces);processed=read(ROOT/'data/processed'/cfg['dataset_2026']/'bars.csv');check('All new bars independently read',len(raw)==len(processed)==78624)
    for key,j in [('open',1),('high',2),('low',3),('close',4),('volume',5),('quote_volume',7),('trades',8),('taker_buy_volume',9),('taker_buy_quote_volume',10)]:check('Independent archive field '+key,np.array_equal(raw[:,j],np.array([float(r[key]) for r in processed])))
    previous=float(read(ROOT/'data/processed'/cfg['dataset_2025']/'bars.csv')[-1]['close']);returns=np.log(raw[:,4]/np.r_[previous,raw[:-1,4]]);check('All new returns independent reconstruction',np.array_equal(returns,np.array([float(r['return_log']) for r in processed])))
    daily=read(tables/'daily_features.csv');sample=read(tables/'forecast_samples.csv');sel=json.loads((checks/'selected_models.json').read_text());feature_names=list(dict.fromkeys(x for v in cfg['groups'].values() for x in v));X=np.array([[float(r[k]) for k in feature_names] for r in sample]);y=np.array([float(r['target_rv']) for r in sample]);target=np.array([r['target_date'] for r in sample]);fit=target<cfg['test_target_start'];test=~fit
    check('Positive complete daily targets',len(daily)==638 and len(sample)==610 and np.all(y>0));check('Final split counts',fit.sum()==427 and test.sum()==183)
    from datetime import date,timedelta
    check('Forecast origins exactly one day before target',all(date.fromisoformat(r['target_date'])-date.fromisoformat(r['origin_date'])==timedelta(days=1) for r in sample))
    lookup={r['date']:r for r in daily}
    for r in sample:
        check('Daily RV lag '+r['target_date'],abs(float(r['log_rv_1'])-np.log(float(lookup[r['origin_date']]['rv'])))<1e-14)
    # A future-state perturbation must not alter any earlier forecast input.
    dd=[{k:(float(v) if k!='date' else v) for k,v in r.items()} for r in daily];alter=[dict(r) for r in dd];cut=500
    for r in alter[cut:]:
        for k in r:
            if k!='date':r[k]*=7
    old=forecast_samples(dd);new=forecast_samples(alter)
    check('Future perturbation leaves earlier features unchanged',all(all(a[k]==b[k] for k in feature_names) for a,b in zip(old,new) if a['origin_date']<dd[cut]['date']))
    predictions=read(tables/'test_predictions.csv');max_ridge_error=0
    for name in ['HAR','HAR+All','HAR+Activity','HAR+Coupling','HAR+Tail']:
        spec=sel['models'][name];indices=[feature_names.index(k) for k in spec['features']];xx=X[:,indices];mean=xx[fit].mean(0);scale=xx[fit].std(0);xx=(xx-mean)/scale;zz=np.log(y[fit]);center=zz.mean();alpha=spec['parameters']['alpha'];coef=np.linalg.solve(xx[fit].T@xx[fit]+alpha*np.eye(len(indices)),xx[fit].T@(zz-center));expected=center+xx[test]@coef;actual=np.array([float(r['log_prediction']) for r in predictions if r['model']==name]);error=float(np.max(np.abs(expected-actual)));max_ridge_error=max(max_ridge_error,error);check('Independent ridge normal equations '+name,error<1e-10)
    for name in cfg['regression_models']:
        rows=[r for r in predictions if r['model']==name];actual=np.array([float(r['actual_rv']) for r in rows]);pred=np.array([float(r['prediction_rv']) for r in rows]);log=np.array([float(r['log_prediction']) for r in rows])
        check('Positive forecasts '+name,np.all(pred>0) and len(rows)==183)
        check('Log-MSE direct '+name,np.allclose((np.log(actual)-np.log(pred))**2,[float(r['log_mse']) for r in rows],atol=1e-13))
        check('QLIKE direct '+name,np.allclose(actual/pred-np.log(actual/pred)-1,[float(r['qlike']) for r in rows],atol=1e-13))
    contrast=read(tables/'regression_contrasts.csv');by={m:np.array([float(r['log_mse']) for r in predictions if r['model']==m]) for m in cfg['regression_models']}
    for r in contrast:
        if r['metric']=='log_mse':check('Relative score '+r['model']+'/'+r['baseline']+'/'+r['day_block_length'],abs(100*(1-by[r['model']].mean()/by[r['baseline']].mean())-float(r['improvement_pct']))<1e-10)
    for L in cfg['bootstrap_day_block_lengths']:
        w=circular_day_weights(183,L,40,np.random.default_rng(100+L));check('Block total count '+str(L),np.all(w.sum(1)==183))
    probability=read(tables/'probability_predictions.csv')
    check('Probability targets defined by training threshold',all(int(r['event'])==int(float(r['actual_rv'])>float(r['threshold_rv'])) for r in probability))
    check('Brier direct',all(abs((float(r['probability'])-int(r['event']))**2-float(r['brier']))<1e-14 for r in probability))
    check('Valid probabilities',all(0<=float(r['probability'])<=1 for r in probability))
    report={'status':'pass','checks':tests,'count':len(tests),'new_bars_verified':len(raw),'direct_ridge_max_log_prediction_error':max_ridge_error,'member_scientific_review':'not_run'}
    (checks/'method_audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='checks'},indent=2))


if __name__=='__main__':main()
