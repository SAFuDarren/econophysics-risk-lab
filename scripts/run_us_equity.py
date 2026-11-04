#!/usr/bin/env python3
"""Frozen US sector risk, increment-P&L and strong allocation comparisons."""
from pathlib import Path
import argparse,datetime as dt,hashlib,json,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import numpy as np
from econophysics.us_equity import load_panel,daily_risk,samples,qlike,write_csv,strategy_library,strategy_allocations,pnl_metrics,block_weights,loss_contrast,holm,correlation
from econophysics.state_forecasting import ChannelRegressor

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def mean_score(rows,name):return float(qlike([r['target'] for r in rows],[r[name] for r in rows]).mean())

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--select-only',action='store_true');args=parser.parse_args();start=time.perf_counter();cfg=json.loads((ROOT/'configs/us_equity_v1.json').read_text());out=ROOT/'results/tables/us_equity_v1';check=ROOT/'results/checks/us_equity_v1';out.mkdir(parents=True,exist_ok=True);check.mkdir(parents=True,exist_ok=True)
    if (out/'risk_forecasts.csv').exists():raise SystemExit('Existing complete evidence preserved; reproduce in a new root.')
    dates,r,price,symbols=load_panel(ROOT,cfg);daily,covs,features=daily_risk(dates,r,cfg);sample=samples(dates,r,cfg,daily,features);train=[s for s in sample if s['split']=='train'];val=[s for s in sample if s['split']=='validation'];controls=[k for k in train[0] if k.startswith(('Diagonal-','FixedCorrelation-','Sample-','LedoitWolf-','EWMA-'))];strong=min([n for n in controls if n.startswith(('Sample-','LedoitWolf-','EWMA-'))],key=lambda n:(mean_score(val,n),n));grid=[{'kind':'Risk control','name':n,'validation_qlike':mean_score(val,n)} for n in controls]
    print('Daily panel and covariance controls ready; choosing on validation only.',flush=True)
    def matrix(rows):return np.array([[s[f'x{i}'] for i in range(6)] for s in rows])
    def target(rows):return np.array([s['target']/s[strong] for s in rows])
    xtrain,xval=matrix(train),matrix(val);ytrain,yval=target(train),target(val)
    best_return=None;best_value=np.inf
    for alpha in cfg['state_calibration']['return_alpha']:
        model=ChannelRegressor('gamma',alpha,'off',3).fit(xtrain,ytrain);score=float(qlike(yval,np.exp(model.predict_log(xval))).mean());grid.append({'kind':'Return Gamma','name':str(alpha),'validation_qlike':score})
        if score<best_value:best_return=alpha;best_value=score
    best_network=None;best_value=np.inf
    for beta in cfg['state_calibration']['network_alpha']:
        model=ChannelRegressor('gamma',best_return,beta,3).fit(xtrain,ytrain);score=float(qlike(yval,np.exp(model.predict_log(xval))).mean());grid.append({'kind':'Network Gamma','name':str(beta),'return_alpha':best_return,'validation_qlike':score})
        if score<best_value:best_network=beta;best_value=score
    lib=strategy_library(dates,r,price,cfg);alloc=strategy_allocations(dates,lib,cfg);vmask=(dates>=cfg['splits']['validation'][0])&(dates<cfg['splits']['validation'][1]);cost=cfg['strategy_library']['primary_cost_bps'];allocation_reference=min(['Equal','InverseVol','LW-MinVariance'],key=lambda n:(np.std(alloc[n]['net'][cost][vmask],ddof=1),n))
    sources=[ROOT/'configs/us_equity_v1.json',ROOT/'docs/AB/us_equity_v1_contract.md',ROOT/'src/econophysics/us_equity.py',ROOT/'src/econophysics/state_forecasting.py',Path(__file__),ROOT/'data/processed/us_equity_v1/historical.csv']
    selected={'status':'frozen_before_confirmation_download','risk_reference':strong,'return_alpha':best_return,'network_alpha':best_network,'allocation_reference':allocation_reference,'train_targets':len(train),'validation_targets':len(val),'sources_sha256':{str(p.relative_to(ROOT)):sha(p) for p in sources},'selection_information':'2018-2019 only; all recipes fixed before full data download'}
    freeze=check/'selection_freeze.json'
    if freeze.exists():assert json.loads(freeze.read_text())==selected,'Selection drift'
    else:freeze.write_text(json.dumps(selected,indent=2)+'\n')
    write_csv(out/'validation_grid.csv',grid)
    if args.select_only:print(json.dumps(selected,indent=2));return
    if not (ROOT/'data/processed/us_equity_v1/confirmation.csv').exists():raise SystemExit('Fetch confirmation only after selection freeze.')
    print('Selections verified; running historical and confirmation evaluation.',flush=True)
    fitrows=train+val;xx=matrix(fitrows);yy=target(fitrows);models={name:ChannelRegressor('gamma',best_return,beta,3).fit(xx,yy) for name,beta in [('ReturnGamma','off'),('NetworkGamma',best_network)]};fitrec={name:{'coefficient':m.coef.tolist(),'target_scale':m.target_scale,'feature_center':m.scaler.mean_.tolist(),'feature_scale':m.scaler.scale_.tolist(),'gradient_per_sample':m.gradient_per_sample,'training_last_target':fitrows[-1]['target_end']} for name,m in models.items()};(check/'fitted_calibration.json').write_text(json.dumps(fitrec,indent=2)+'\n')
    forecasts=[];metrics=[];yearly=[];contrast=[];primary=[];rng=np.random.default_rng(cfg['seed']);allnames=controls+list(models)
    for split in ['historical_test','confirmation']:
        rows=[s for s in sample if s['split']==split];actual=np.array([s['target'] for s in rows]);pred={name:np.array([s[name] for s in rows]) for name in controls}
        for name,model in models.items():pred[name]=np.array([s[strong] for s in rows])*np.exp(model.predict_log(matrix(rows)))
        losses={name:qlike(actual,v) for name,v in pred.items()};logloss={name:(np.log(actual)-np.log(v))**2 for name,v in pred.items()}
        for name,v in pred.items():
            metrics.append({'split':split,'model':name,'targets':len(rows),'qlike':float(losses[name].mean()),'log_mse':float(logloss[name].mean()),'mean_actual_forecast_ratio':float(np.mean(actual/v))})
            for s,value,loss in zip(rows,v,losses[name]):forecasts.append({'split':split,'model':name,'origin_date':s['origin_date'],'target_start':s['target_start'],'target_end':s['target_end'],'actual':s['target'],'forecast':float(value),'qlike':float(loss)})
            for year in sorted(set(s['target_start'][:4] for s in rows)):
                mask=np.array([s['target_start'].startswith(year) for s in rows]);yearly.append({'split':split,'year':year,'model':name,'targets':int(mask.sum()),'qlike':float(losses[name][mask].mean()),'log_mse':float(logloss[name][mask].mean())})
        for length in cfg['bootstrap']['forecast_block_lengths']:
            weights=block_weights(len(rows),length,cfg['bootstrap']['replicates'],rng)
            pairs=[('NetworkGamma','ReturnGamma')]+[(name,strong) for name in allnames if name!=strong]
            for model,baseline in pairs:
                for metric,source in [('QLIKE',losses),('LogMSE',logloss)]:
                    rec={'split':split,'model':model,'baseline':baseline,'metric':metric,'block_length':length,**loss_contrast(source[model],source[baseline],weights),'family':'primary two periods' if model=='NetworkGamma' and baseline=='ReturnGamma' and metric=='QLIKE' else 'exploratory; complete controls'};contrast.append(rec)
                    if model=='NetworkGamma' and baseline=='ReturnGamma' and metric=='QLIKE' and length==cfg['bootstrap']['primary_forecast_block_length']:primary.append(rec)
    holm(primary)
    write_csv(out/'risk_forecasts.csv',forecasts);write_csv(out/'risk_metrics.csv',metrics);write_csv(out/'risk_yearly.csv',yearly);write_csv(out/'risk_contrasts.csv',contrast);write_csv(out/'risk_primary.csv',primary);write_csv(out/'daily_risk.csv',daily);write_csv(out/'risk_samples.csv',sample)
    snapshots=[]
    for wanted in cfg['snapshots']:
        index=int(np.flatnonzero(dates<=wanted)[-1]);c=correlation(covs[index]['Sample-63'])
        for a in range(9):
            for b in range(9):snapshots.append({'requested_date':wanted,'actual_date':str(dates[index]),'row':symbols[a],'column':symbols[b],'correlation':float(c[a,b])})
    write_csv(out/'snapshot_correlations.csv',snapshots)
    # Cross-sector alignment ablation: descriptive surrogate envelope, no invalid randomization p-value.
    standardized=np.full((len(dates),9),np.nan)
    for i in range(126,len(dates)):standardized[i]=r[i,:9]/np.std(r[i-63:i,:9],axis=0,ddof=1)
    tr=(dates>=cfg['splits']['train'][0])&(dates<cfg['splits']['train'][1])&np.isfinite(standardized).all(1);threshold=-2*np.std(standardized[tr],axis=0,ddof=1);surrogate=[];surrogate_summary=[];srng=np.random.default_rng(cfg['seed']+cfg['surrogate']['seed_offset'])
    def surrogate_stats(z):return {'basket_variance':float(np.var(z.mean(1),ddof=1)),'mean_correlation':float((np.corrcoef(z,rowvar=False).sum()-9)/72),'joint_down_frequency':float(np.mean(np.sum(z<threshold,axis=1)>=3))}
    for year in sorted(set(str(d)[:4] for d in dates if str(d)>='2020-01-01')):
        mask=np.array([str(d).startswith(year) for d in dates]);z=standardized[mask];observed=surrogate_stats(z);null={k:[] for k in observed}
        for rep in range(cfg['surrogate']['replicates']):
            offsets=srng.integers(20,len(z)-19,size=9);shifted=np.column_stack([np.roll(z[:,j],offsets[j]) for j in range(9)]);values=surrogate_stats(shifted)
            for key,value in values.items():null[key].append(value)
            surrogate.append({'year':year,'replicate':rep,**values})
        for key,value in observed.items():surrogate_summary.append({'year':year,'sessions':len(z),'metric':key,'observed':value,'surrogate_mean':float(np.mean(null[key])),'surrogate_low':float(np.quantile(null[key],.025)),'surrogate_high':float(np.quantile(null[key],.975)),'interpretation':'Conditional shift distribution, not sampling CI or a causal test'})
    write_csv(out/'surrogate_draws.csv',surrogate);write_csv(out/'surrogate_summary.csv',surrogate_summary)
    strategy_rows=[];allocation_rows=[];strategy_summary=[];allocation_summary=[];allocation_comparisons=[];pair_rows=[];exposure_rows=[]
    for i,date in enumerate(dates):
        if str(date)<'2010-01-01':continue
        for s,name in enumerate(lib['names']):strategy_rows.append({'date':str(date),'strategy':name,'gross_pnl':float(lib['gross'][i,s]),'turnover':float(lib['turnover'][i,s]),'short_notional':float(lib['shorts'][i,s]),**{f'net_{c}bp':float(lib['net'][c][i,s]) for c in cfg['strategy_library']['cost_bps']},'signal_date':str(dates[lib['signal_indices'][i]]) if lib['signal_indices'][i]>=0 else ''})
        for name,a in alloc.items():allocation_rows.append({'date':str(date),'method':name,'gross_pnl':float(a['gross'][i]),'turnover':float(a['turnover'][i]),'gross_exposure':float(a['gross_exposure'][i]),'short_notional':float(a['shorts'][i]),**{f'net_{c}bp':float(a['net'][c][i]) for c in cfg['strategy_library']['cost_bps']},'signal_date':str(dates[a['signal_indices'][i]]) if a['signal_indices'][i]>=0 else ''})
    # Train thresholds are fixed, so all evaluation extremes are measured against a past reference.
    trainmask=(dates>=cfg['splits']['train'][0])&(dates<cfg['splits']['train'][1])&(np.arange(len(dates))>=128);pnlthreshold=np.quantile(lib['net'][cost][trainmask],.05,axis=0)
    for split,(left,right) in cfg['splits'].items():
        if split=='train':continue
        mask=(dates>=left)&(dates<right);ix=np.flatnonzero(mask)
        if not len(ix):continue
        for c in cfg['strategy_library']['cost_bps']:
            for s,name in enumerate(lib['names']):strategy_summary.append({'split':split,'strategy':name,'cost_bps':c,**pnl_metrics(lib['net'][c][mask,s]),'mean_daily_turnover':float(lib['turnover'][mask,s].mean())})
            for name,a in alloc.items():allocation_summary.append({'split':split,'method':name,'cost_bps':c,**pnl_metrics(a['net'][c][mask]),'mean_daily_turnover':float(a['turnover'][mask].mean()),'mean_underlying_gross_exposure':float(a['gross_exposure'][mask].mean())})
        if split=='validation':continue
        for length in [5,20,63]:
            bw=block_weights(len(ix),length,cfg['bootstrap']['replicates'],rng);a=alloc['HRP']['net'][cost][mask];b=alloc[allocation_reference]['net'][cost][mask];ma=bw@a/len(a);mb=bw@b/len(b);va=bw@(a*a)/len(a)-ma*ma;vb=bw@(b*b)/len(b)-mb*mb;gain=100*(1-np.sqrt(va/vb));diff=(ma-mb)*252*100
            allocation_comparisons.append({'split':split,'model':'HRP','baseline':allocation_reference,'block_sessions':length,'days':len(ix),'sigma_reduction_pct':100*(1-a.std(ddof=1)/b.std(ddof=1)),'sigma_ci_low':float(np.quantile(gain,.025)),'sigma_ci_high':float(np.quantile(gain,.975)),'annual_mean_pnl_difference_pp':float((a.mean()-b.mean())*252*100),'mean_difference_ci_low':float(np.quantile(diff,.025)),'mean_difference_ci_high':float(np.quantile(diff,.975)),'scope':'Exploratory allocation comparison; exposure and mean must accompany risk'})
        pnl=lib['net'][cost][mask];gross=lib['gross'][mask];corr=np.corrcoef(pnl,rowvar=False);cumcorr=np.corrcoef(np.cumsum(pnl,axis=0),rowvar=False);gcorr=np.corrcoef(gross,rowvar=False);overlap=np.zeros((6,6));co_movement=np.zeros((6,6));implied=np.zeros((6,6))
        for i in ix:
            w=lib['units'][i-1]*lib['price_index'][i-1];s=covs[i-1]['Sample-63'];d=np.diag(np.diag(s));overlap+=w@d@w.T;co_movement+=w@(s-d)@w.T;implied+=w@s@w.T
        overlap/=len(ix);co_movement/=len(ix);implied/=len(ix);assert np.allclose(overlap+co_movement,implied,atol=1e-16)
        for a in range(6):
            for b in range(a,6):exposure_rows.append({'split':split,'strategy_a':lib['names'][a],'strategy_b':lib['names'][b],'shared_exposure_covariance':float(overlap[a,b]),'cross_asset_covariance':float(co_movement[a,b]),'conditional_implied_covariance':float(implied[a,b]),'scope':'Average W_t Sigma_t W_t^T; not exact observed PnL covariance or causal partition'})
            for b in range(a+1,6):pair_rows.append({'split':split,'strategy_a':lib['names'][a],'strategy_b':lib['names'][b],'daily_net_correlation':float(corr[a,b]),'daily_gross_correlation':float(gcorr[a,b]),'cumulative_pnl_correlation_warning_only':float(cumcorr[a,b]),'joint_train_5pct_loss_frequency':float(np.mean((pnl[:,a]<pnlthreshold[a])&(pnl[:,b]<pnlthreshold[b]))),'days':len(ix),'shared_exposure_covariance':float(overlap[a,b]),'cross_asset_covariance':float(co_movement[a,b])})
    write_csv(out/'strategy_daily.csv',strategy_rows);write_csv(out/'allocation_daily.csv',allocation_rows);write_csv(out/'strategy_metrics.csv',strategy_summary);write_csv(out/'allocation_metrics.csv',allocation_summary);write_csv(out/'allocation_contrasts.csv',allocation_comparisons);write_csv(out/'strategy_pairs.csv',pair_rows);write_csv(out/'exposure_decomposition.csv',exposure_rows)
    np.savez_compressed(out/'positions.npz',dates=dates,symbols=np.array(symbols[:9]),strategy_names=np.array(lib['names']),strategy_units=lib['units'],strategy_gross=lib['gross'],strategy_turnover=lib['turnover'],strategy_shorts=lib['shorts'],**{f'weights_{name}':a['weights'] for name,a in alloc.items()},**{f'units_{name}':a['units'] for name,a in alloc.items()})
    summary={'status':'pass','selection':selected,'dates':len(dates),'panel_cells':len(dates)*len(symbols),'evaluation_targets':{split:sum(s['split']==split for s in sample) for split in cfg['splits']},'primary':primary,'pnl_strategies':6,'allocation_methods':4,'market_volume_features_used':False,'member_review':'not_run','seconds':time.perf_counter()-start,'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in sources}}
    (check/'run_record.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({'status':'pass','selected_strong':strong,'selected_network_penalty':best_network,'allocation_reference':allocation_reference,'targets':summary['evaluation_targets'],'primary':primary,'seconds':summary['seconds']},indent=2))

if __name__=='__main__':main()
