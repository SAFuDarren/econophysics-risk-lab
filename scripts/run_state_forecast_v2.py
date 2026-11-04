#!/usr/bin/env python3
"""Frozen state-aware forecast comparison with separate new-asset/new-time tests."""
from pathlib import Path
import argparse,csv,hashlib,itertools,json,os,sys,time
os.environ.setdefault('OPENBLAS_NUM_THREADS','1');os.environ.setdefault('OMP_NUM_THREADS','1')
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import numpy as np
from econophysics.state_forecasting import state_daily,state_samples,walk_forward
from econophysics.forecasting import daily_losses
from econophysics.real_market_statistics import circular_day_weights
from econophysics.study_statistics import holm_adjust
from econophysics.model import derived_seed


def read(p):return list(csv.DictReader(p.open()))
def write(p,rows):
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def interval(v):return [float(x) for x in np.quantile(v,[.025,.975])]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run-id',default='state_forecast_v2');args=parser.parse_args()
    if not args.run_id.replace('_','').replace('-','').isalnum():parser.error('invalid id')
    tables=ROOT/'results/tables'/args.run_id;checks=ROOT/'results/checks'/args.run_id
    if tables.exists():parser.error('run exists; preserve it')
    tables.mkdir(parents=True);checks.mkdir(parents=True,exist_ok=True);cfgpath=ROOT/'configs/state_forecast_v2.json';cfg=json.loads(cfgpath.read_text());started=time.perf_counter()
    freeze=json.loads((ROOT/'data/manifests/state_forecast_v2_pre_download.json').read_text());assert freeze['config_sha256']==hashlib.sha256(cfgpath.read_bytes()).hexdigest();assert freeze['contract_sha256']==hashlib.sha256((ROOT/'docs/AB/state_forecast_v2_contract.md').read_bytes()).hexdigest()
    files=[cfgpath,Path(__file__).resolve(),ROOT/'src/econophysics/state_forecasting.py',ROOT/'docs/AB/state_forecast_v2_feature_spec.md']+[ROOT/'data/processed'/cfg[k]/'bars.csv' for k in ['source_btc_2025','source_btc_2026','source_btc_new','source_eth_new']]
    record={'status':'running','command':f'python scripts/run_state_forecast_v2.py --run-id {args.run_id}','source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},'member_review':'not_run'};(checks/'run_record.json').write_text(json.dumps(record,indent=2)+'\n');(checks/'locked_config.json').write_bytes(cfgpath.read_bytes())
    assets={};daily_rows=[];sample_rows=[]
    for asset,keys in [('BTCUSDT',['source_btc_2025','source_btc_2026','source_btc_new']),('ETHUSDT',['source_eth_new'])]:
        bars=list(itertools.chain.from_iterable(read(ROOT/'data/processed'/cfg[k]/'bars.csv') for k in keys));days=state_daily(bars);samples=state_samples(days);assert len(days)==663 and len(bars)==190944;assets[asset]=samples;daily_rows.extend({'asset':asset,**r} for r in days);sample_rows.extend({'asset':asset,**r} for r in samples);print('Features prepared:',asset,len(days),'complete days',flush=True)
    write(tables/'daily_features.csv',daily_rows);write(tables/'forecast_samples.csv',sample_rows)
    R=cfg['return_features'];V=cfg['state_volume_features'];legacy=cfg['legacy_volume_features'];definitions={
        'LegacyHAR-Static':('log',False,['log_rv_1','log_rv_7','log_rv_28'],'off'),
        'ReturnLog-Adaptive':('log',True,R,'off'),
        'ReturnGamma-Static':('gamma',False,R,'off'),
        'ReturnGamma-Adaptive':('gamma',True,R,'off'),
        'LegacyVolumeGamma-Adaptive':('gamma',True,R+legacy,'select'),
        'StateVolumeGamma-Adaptive':('gamma',True,R+V,'select'),
        'StateVolumeGamma-Static':('gamma',False,R+V,'select')}
    selection=[];selected={};validation=[]
    def forecast(samples,definition,alpha,beta,start,end):
        kind,adaptive,names,_=definition
        return walk_forward(samples,names,kind,alpha,beta,start,end,adaptive,cfg['refit']['training_target_window_days'],cfg['refit']['min_training_targets'])
    for asset,samples in assets.items():
        selected[asset]={}
        for name in cfg['models']:
            definition=definitions[name];kind,adaptive,names,channel=definition
            if channel=='off':candidates=[(a,'off') for a in cfg['return_penalty_grid']]
            else:
                base='ReturnGamma-Adaptive' if adaptive else 'ReturnGamma-Static';alpha=selected[asset][base]['return_penalty'];candidates=[(alpha,b) for b in cfg['volume_penalty_grid']]
            trials=[]
            for alpha,beta in candidates:
                indices,pred,refits=forecast(samples,definition,alpha,beta,cfg['validation']['start'],cfg['validation']['end_exclusive']);actual=np.array([samples[i]['target_rv'] for i in indices]);metric='log_mse' if kind=='log' else 'qlike';score=float(daily_losses(actual,pred)[metric].mean());selection.append({'asset':asset,'model':name,'return_penalty':alpha,'volume_penalty':beta,'validation_metric':metric,'validation_loss':score,'validation_days':len(indices)});trials.append((score,alpha,beta,indices,pred))
            score,alpha,beta,indices,pred=min(trials,key=lambda x:(x[0],0 if x[2]=='off' else 1));selected[asset][name]={'kind':kind,'adaptive':adaptive,'features':names,'return_penalty':alpha,'volume_penalty':beta,'validation_metric':metric,'validation_loss':score}
            validation.extend({'asset':asset,'model':name,'target_date':samples[i]['target_date'],'actual_rv':samples[i]['target_rv'],'log_forecast':float(p)} for i,p in zip(indices,pred));print('Selected',asset,name,'alpha',alpha,'volume',beta,flush=True)
    (checks/'selected_models.json').write_text(json.dumps({'status':'selected_before_evaluation_metrics','assets':selected,'scope':'Q1 data only; primary channels may select off'},indent=2)+'\n');write(tables/'validation_grid.csv',selection);write(tables/'validation_predictions.csv',validation)
    evaluations=cfg['evaluations']+[{'asset':'BTCUSDT','name':'development_old_time','start':cfg['development_only']['start'],'end_exclusive':cfg['development_only']['end_exclusive'],'expected_days':183,'status':'Previously examined BTC dates; diagnostic only, not fresh'}]
    all_predictions=[];refit_records=[];metrics=[];contrasts=[];primary=[];monthly=[];risk=[]
    for evaluation in evaluations:
        asset=evaluation['asset'];tag=evaluation['name'];samples=assets[asset];model_loss={};actual=None
        for name in cfg['models']:
            spec=selected[asset][name];indices,pred,refits=forecast(samples,definitions[name],spec['return_penalty'],spec['volume_penalty'],evaluation['start'],evaluation['end_exclusive']);assert len(indices)==evaluation['expected_days'];actual=np.array([samples[i]['target_rv'] for i in indices]);loss=daily_losses(actual,pred);ratio=np.exp(np.log(actual)-pred);loss.update(budget_overrun=np.maximum(ratio-1,0),double_budget=(ratio>2).astype(float));model_loss[name]=loss
            refit_records.extend({'asset':asset,'evaluation':tag,'model':name,**r} for r in refits)
            all_predictions.extend({'asset':asset,'evaluation':tag,'model':name,'origin_date':samples[i]['origin_date'],'target_date':samples[i]['target_date'],'actual_rv':samples[i]['target_rv'],'log_forecast':float(p),'forecast_rv':float(np.exp(p)),'actual_volatility_pct':float(100*np.sqrt(samples[i]['target_rv'])),'forecast_volatility_pct':float(100*np.exp(p/2)),**{k:float(v[j]) for k,v in loss.items()}} for j,(i,p) in enumerate(zip(indices,pred)))
            risk.append({'asset':asset,'evaluation':tag,'model':name,'days':len(indices),'mean_realised_to_forecast_variance':float(ratio.mean()),'mean_excess_above_budget':float(np.maximum(ratio-1,0).mean()),'fraction_above_twice_budget':float(np.mean(ratio>2)),'interpretation':'Theoretical uncapped target-volatility diagnostic, not implemented portfolio utility'})
        D=len(actual);dates=np.array([samples[i]['target_date'] for i in indices]);baseline=cfg['primary_comparison']['baseline'];main=cfg['primary_comparison']['model']
        for m in model_loss:
            for month in sorted(set(d[:7] for d in dates)):
                ix=np.array([d.startswith(month) for d in dates]);monthly.append({'asset':asset,'evaluation':tag,'model':m,'month':month,'days':int(ix.sum()),'qlike':float(model_loss[m]['qlike'][ix].mean()),'improvement_vs_return_gamma_pct':float(100*(1-model_loss[m]['qlike'][ix].mean()/model_loss[baseline]['qlike'][ix].mean()))})
        for L in cfg['bootstrap']['day_block_lengths']:
            w=circular_day_weights(D,L,cfg['bootstrap']['replicates'],np.random.default_rng(derived_seed(cfg['seed'],f'{asset}:{tag}:{L}')))
            for m,ls in model_loss.items():
                for metric,values in ls.items():
                    lo,hi=interval(w@values/D);metrics.append({'asset':asset,'evaluation':tag,'model':m,'metric':metric,'estimate':float(values.mean()),'ci_low':lo,'ci_high':hi,'days':D,'day_block_length':L})
            pairs=[(m,baseline) for m in cfg['models'] if m!=baseline]+[(main,'LegacyVolumeGamma-Adaptive'),(main,'StateVolumeGamma-Static')]
            for metric in ['qlike','log_mse','volatility_mae']:
                family=[]
                for m,b in pairs:
                    a=model_loss[m][metric];bb=model_loss[b][metric];delta=a-bb;point=float(delta.mean());boot=w@delta/D;dlo,dhi=interval(boot);slo,shi=interval(100*(1-(w@a)/(w@bb)));p=float((1+np.sum(np.abs(boot-point)>=abs(point)))/(len(boot)+1));row={'asset':asset,'evaluation':tag,'model':m,'baseline':b,'metric':metric,'improvement_pct':float(100*(1-a.mean()/bb.mean())),'ci_low':slo,'ci_high':shi,'loss_difference':point,'difference_ci_low':dlo,'difference_ci_high':dhi,'p_approx':p,'days':D,'day_block_length':L,'scope':'Primary pair if named, otherwise exploratory model-control family'};family.append(row)
                    if m==main and b==baseline and tag!='development_old_time':primary.append(dict(row))
                for row,adjusted in zip(family,holm_adjust([r['p_approx'] for r in family])):row['p_holm_exploratory_family']=adjusted
                contrasts.extend(family)
        print('Evaluated',asset,tag,D,'days',flush=True)
    for L in cfg['bootstrap']['day_block_lengths']:
        for metric in ['qlike','log_mse','volatility_mae']:
            family=[r for r in primary if r['day_block_length']==L and r['metric']==metric];assert len(family)==3
            for row,adjusted in zip(family,holm_adjust([r['p_approx'] for r in family])):row['p_holm_primary_three']=adjusted
    write(tables/'predictions.csv',all_predictions);write(tables/'refit_records.csv',refit_records);write(tables/'metrics.csv',metrics);write(tables/'contrasts.csv',contrasts);write(tables/'primary_contrasts.csv',primary);write(tables/'monthly_metrics.csv',monthly);write(tables/'risk_budget_diagnostic.csv',risk)
    mainrows=[r for r in primary if r['metric']=='qlike' and r['day_block_length']==7];summary={'status':'pass','member_review':'not_run','new_real_bars':198144,'new_archive_count':72,'asset_days_each':663,'fresh_external_days':183,'fresh_time_distinct_dates':25,'primary_qlike':mainrows,'selected_volume_penalties':{a:{m:s['volume_penalty'] for m,s in ss.items() if 'Volume' in m} for a,ss in selected.items()},'practical_gate':'Not evaluated as a deployment guarantee; see explicit report gate and short-time limits','seconds':time.perf_counter()-started}
    (checks/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');record.update(status='pass',seconds=summary['seconds'],outputs_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in tables.glob('*.csv')});(checks/'run_record.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
