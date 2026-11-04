#!/usr/bin/env python3
"""H1-calibrated / H2-held-out market-model comparison with date-block uncertainty."""
from pathlib import Path
from itertools import groupby
import argparse,csv,gzip,hashlib,json,os,sys,time
os.environ.setdefault('OPENBLAS_NUM_THREADS','1');os.environ.setdefault('OMP_NUM_THREADS','1')
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import numpy as np
from scipy import stats
from econophysics.model import derived_seed
from econophysics.study_statistics import holm_adjust
from econophysics.real_market_statistics import (circular_day_weights,daily_moments,moments_to_statistics,percentile_interval,
    weighted_spearman_bootstrap,pair_sums_by_day,correlation_from_pair_sums,scale_sums_by_day,scale_statistics,
    conditional_bin_sums,fit_tail,tail_logpdf,tail_cdf,ccdf_by_day,fixed_tail_calibration)


def read(path):return list(csv.DictReader(path.open()))
def write(path,rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run-id',default='real_market_v1');args=parser.parse_args()
    if not args.run_id.replace('_','').replace('-','').isalnum():parser.error('invalid run-id')
    cfgpath=ROOT/'configs/real_market_v1.json';cfg=json.loads(cfgpath.read_text());tables=ROOT/'results/tables'/args.run_id;checks=ROOT/'results/checks'/args.run_id
    if (tables/'market_metrics.csv').exists():parser.error('analysis already exists')
    source=ROOT/'data/processed'/cfg['dataset']/'bars.csv';data=read(source);train=[r for r in data if r['split']=='calibration'];test=[r for r in data if r['split']=='holdout'];bpd=cfg['bars_per_day'];D=len(test)//bpd
    r=np.array([float(x['return_log']) for x in test]);v=np.array([float(x['volume']) for x in test]);rt=np.array([float(x['return_log']) for x in train]);vt=np.array([float(x['volume']) for x in train]);sigma=rt.std();meanv=vt.mean();absolute=np.abs(r)/sigma;abs_train=np.abs(rt)/sigma
    started=time.perf_counter();record={'status':'running','command':f'python3 scripts/analyze_real_market.py --run-id {args.run_id}','scope':'REAL_DATA and SIMULATION comparison, conditional on H1 calibration','member_review':'not_run'}
    sources=[cfgpath,source,Path(__file__).resolve(),ROOT/'src/econophysics/real_market_statistics.py',tables/'calibration_parameters.csv',tables/'model_series.csv.gz']
    record['source_sha256']={str(x.relative_to(ROOT)):hashlib.sha256(x.read_bytes()).hexdigest() for x in sources};(checks/'analysis_record.json').write_text(json.dumps(record,indent=2)+'\n')
    weights={L:circular_day_weights(D,L,cfg['bootstrap_replicates'],np.random.default_rng(derived_seed(cfg['seed'],f'market-weights:{L}'))) for L in cfg['bootstrap_day_block_lengths']}
    train_weights={L:circular_day_weights(len(train)//bpd,L,cfg['bootstrap_replicates'],np.random.default_rng(derived_seed(cfg['seed'],f'calibration-weights:{L}'))) for L in cfg['bootstrap_day_block_lengths']}
    primary=cfg['primary_day_block_length'];daily=daily_moments(r,v,bpd);point=moments_to_statistics(daily.sum(0));bootstrap={L:moments_to_statistics(w@daily) for L,w in weights.items()}
    metric_rows=[]
    for key,value in point.items():
        for L in weights:
            lo,hi=percentile_interval(bootstrap[L][key]);degenerate=key.startswith('zero_') and float(value)==0
            metric_rows.append({'source':'Market H2','metric':key,'estimate':float(value),'ci_low':None if degenerate else lo,'ci_high':None if degenerate else hi,'day_block_length':L,'days':D,'interval_note':'Observed zero count; bootstrap interval suppressed' if degenerate else 'Pointwise circular date-block bootstrap'})
    profiles=[];season_r=np.array([np.median(np.abs(rt)[slot::bpd]) for slot in range(bpd)]);season_v=np.array([np.median(vt[slot::bpd]) for slot in range(bpd)])
    if np.any(season_r<=0) or np.any(season_v<=0):raise ValueError('zero seasonal median')
    for slot in range(bpd):profiles.append({'slot_utc':slot,'median_abs_return_H1':season_r[slot],'median_volume_H1':season_v[slot]})
    adjusted_abs=np.abs(r)/np.tile(season_r,D);adjusted_v=v/np.tile(season_v,D)
    for label,x,y in [('spearman_abs_return_volume',np.abs(r),v),('spearman_season_adjusted_abs_volume',adjusted_abs,adjusted_v)]:
        value=float(stats.spearmanr(x,y).statistic)
        for L,w in weights.items():
            bs=weighted_spearman_bootstrap(x,y,w,bpd);lo,hi=percentile_interval(bs)
            metric_rows.append({'source':'Market H2','metric':label,'estimate':value,'ci_low':lo,'ci_high':hi,'day_block_length':L,'days':D,'interval_note':'Ranks recomputed under integer date-block weights'})
        print(f'Market rank coupling complete: {label}',flush=True)
    write(tables/'market_metrics.csv',metric_rows);write(tables/'seasonality_profiles.csv',profiles)
    daily_rows=[]
    for date,rows in groupby(data,lambda x:x['date_utc']):
        rows=list(rows);rr=np.array([float(x['return_log']) for x in rows]);vol=np.array([float(x['volume']) for x in rows])
        assert len(rows)==bpd
        daily_rows.append({'date_utc':date,'open':float(rows[0]['open']),'high':max(float(x['high']) for x in rows),'low':min(float(x['low']) for x in rows),'close':float(rows[-1]['close']),
                           'volume':float(vol.sum()),'quote_volume':sum(float(x['quote_volume']) for x in rows),'return_log':float(rr.sum()),'realized_variance':float(np.dot(rr,rr)),'max_abs_return':float(np.max(np.abs(rr))),'split':rows[0]['split']})
    write(tables/'daily_overview.csv',daily_rows)
    acf_rows=[];scale_rows=[]
    for kind,x in [('signed_return',r),('absolute_return',np.abs(r)),('season_adjusted_absolute_return',adjusted_abs)]:
        for lag in cfg['acf_lags']:
            sums=pair_sums_by_day(x,lag,bpd);value=float(correlation_from_pair_sums(sums.sum(0)))
            for L,w in weights.items():
                lo,hi=percentile_interval(correlation_from_pair_sums(w@sums));acf_rows.append({'source':'Market H2','series':kind,'lag':lag,'minutes':lag*5,'estimate':value,'ci_low':lo,'ci_high':hi,'day_block_length':L,'replications':None})
    base_variance=float(np.var(r));base_boot={L:bootstrap[L]['return_std']**2 for L in weights}
    for k in cfg['aggregation_bars']:
        sums=scale_sums_by_day(r,k,bpd);value=scale_statistics(sums.sum(0),k,base_variance)
        for L,w in weights.items():
            bs=scale_statistics(w@sums,k,base_boot[L])
            for metric,estimate in value.items():
                lo,hi=percentile_interval(bs[metric]);scale_rows.append({'source':'Market H2','aggregation_bars':k,'minutes':5*k,'metric':metric,'estimate':float(estimate),'ci_low':lo,'ci_high':hi,'day_block_length':L,'replications':None})
    write(tables/'market_acf.csv',acf_rows);write(tables/'market_scaling.csv',scale_rows)
    # Calendar-block impact association, not a trading forecast.
    it=np.array([float(x['signed_taker_volume']) for x in train]);imbalance=np.array([float(x['signed_taker_volume']) for x in test]);kappa=float(np.dot(rt,it)/np.dot(it,it));prediction=kappa*imbalance
    residual=(r-prediction)**2;sse_day=residual.reshape(D,bpd).sum(1);r1_day=r.reshape(D,bpd).sum(1);r2_day=(r*r).reshape(D,bpd).sum(1)
    impact=[]
    for L,w in weights.items():
        den=(w@r2_day)-(w@r1_day)**2/(D*bpd);values=1-(w@sse_day)/den;lo,hi=percentile_interval(values)
        impact.append({'kappa_H1':kappa,'holdout_r_squared':float(1-residual.sum()/np.sum((r-r.mean())**2)),'r_squared_ci_low':lo,'r_squared_ci_high':hi,'day_block_length':L,'calibration_rows':len(train),'holdout_rows':len(test),'interpretation':'Same-bar relation; non-causal; no trading signal'})
    write(tables/'impact_association.csv',impact)
    bins=np.unique(np.quantile(it,np.linspace(.05,.95,19)));counts,sx,sy=conditional_bin_sums(imbalance,r,bins,bpd);impact_bins=[]
    boot_counts=weights[primary]@counts;boot_sum=weights[primary]@sy
    for j in range(counts.shape[1]):
        count=int(counts[:,j].sum());lo,hi=percentile_interval(boot_sum[:,j]/boot_counts[:,j]/sigma)
        impact_bins.append({'bin':j+1,'observations':count,'mean_signed_volume_over_H1_mean':float(sx[:,j].sum()/count/meanv),'mean_return_over_H1_sd':float(sy[:,j].sum()/count/sigma),'ci_low':lo,'ci_high':hi,'constant_impact_H1':float(kappa*sx[:,j].sum()/count/sigma)})
    write(tables/'impact_bins.csv',impact_bins)
    vcuts=np.unique(np.quantile(vt,np.arange(1,cfg['coupling_bins'])/cfg['coupling_bins']));counts,sx,sy=conditional_bin_sums(v,np.abs(r)/sigma,vcuts,bpd);coupling=[]
    cb=weights[primary]@counts;yb=weights[primary]@sy
    for j in range(counts.shape[1]):
        count=int(counts[:,j].sum());lo,hi=percentile_interval(yb[:,j]/cb[:,j]);coupling.append({'source':'Market H2','bin':j+1,'observations':count,'mean_relative_volume':float(sx[:,j].sum()/count/meanv),'mean_abs_return_H1_sd':float(sy[:,j].sum()/count),'ci_low':lo,'ci_high':hi,'replications':None})
    write(tables/'coupling_bins.csv',coupling)
    # Unknown-unit necessary constraint: retain all data in main, report predeclared sensitivities.
    sensitivity=[]
    for month,rr in groupby(data,lambda x:x['month_utc']):
        rr=list(rr);a=np.array([float(x['return_log']) for x in rr]);b=np.array([float(x['volume']) for x in rr]);m=moments_to_statistics(daily_moments(a,b,bpd).sum(0))
        sensitivity.append({'case':'calendar_month','period':month,'removed_date':None,'rows':len(rr),'delta':float(m['delta']),'q_joint_implied':float(m['q_joint_implied'])})
    hold_days=[x for x in daily_rows if x['split']=='holdout']
    for variable in ['volume','realized_variance','max_abs_return']:
        index=max(range(D),key=lambda i:hold_days[i][variable]);m=moments_to_statistics(np.delete(daily,index,axis=0).sum(0))
        sensitivity.append({'case':'leave_max_day_'+variable,'period':'H2','removed_date':hold_days[index]['date_utc'],'rows':len(test)-bpd,'delta':float(m['delta']),'q_joint_implied':float(m['q_joint_implied'])})
    write(tables/'joint_constraint_sensitivity.csv',sensitivity)
    calibration_parameters=read(tables/'calibration_parameters.csv');max_model=max(float(x['lambda_impact'])/sigma for x in calibration_parameters);upper=max(128.,absolute.max()*1.05,max_model*1.05);grid=np.geomspace(.1,upper,cfg['ccdf_grid_points']);market_ccdf=ccdf_by_day(absolute,grid,bpd);ccdf_rows=[]
    bs=weights[primary]@market_ccdf/(D*bpd)
    for j,x in enumerate(grid):
        lo,hi=percentile_interval(bs[:,j]);ccdf_rows.append({'source':'Market H2','threshold_H1_sd':float(x),'ccdf':float(market_ccdf[:,j].sum()/len(r)),'ci_low':lo,'ci_high':hi,'replications':None})
    # Real continuous tails: H1 fitting, H2 scoring; no continuous likelihood for discrete models.
    tail_rows=[];score_rows=[];gof_rows=[];fit_points=[]
    for threshold in cfg['tail_thresholds_training_sd']:
        fits=fit_tail(abs_train,threshold,cfg['tail_lognormal_bounds']);mask=absolute>=threshold;test_tail=absolute[mask];day=np.arange(len(r))//bpd;tail_day=np.bincount(day[mask],minlength=D)
        for phase,x,ww in [('H1',abs_train,train_weights),('H2',absolute,weights)]:
            ma=x>=threshold;counts_tail=ma.reshape(-1,bpd).sum(1);logs=np.where(ma,np.log(np.maximum(x,threshold)/threshold),0).reshape(-1,bpd).sum(1);estimate=1+ma.sum()/logs.sum()
            for L,w in ww.items():
                values=1+(w@counts_tail)/(w@logs);lo,hi=percentile_interval(values)
                tail_rows.append({'phase':phase,'threshold_H1_sd':threshold,'tail_count':int(ma.sum()),'total_bars':len(x),'pareto_density_alpha':float(estimate),'ccdf_exponent':float(estimate-1),'alpha_ci_low':lo,'alpha_ci_high':hi,'day_block_length':L})
        for method in cfg['tail_candidates']:
            pars=fits[method];ll=tail_logpdf(test_tail,threshold,method,pars);day_ll=np.bincount(day[mask],weights=ll,minlength=D)
            for L,w in weights.items():
                values=(w@day_ll)/(w@tail_day);lo,hi=percentile_interval(values)
                score_rows.append({'method':method,'threshold_H1_sd':threshold,'test_tail_count':len(test_tail),'mean_conditional_log_score':float(ll.mean()),'ci_low':lo,'ci_high':hi,'day_block_length':L,'fitted_parameters_H1':json.dumps(pars,sort_keys=True)})
                if threshold==cfg['primary_tail_threshold']:
                    gof=fixed_tail_calibration(absolute,threshold,method,pars,w[:cfg['tail_bootstrap_replicates']],bpd)
                    gof_rows.append({'method':method,'threshold_H1_sd':threshold,'day_block_length':L,**gof})
            if threshold==cfg['primary_tail_threshold']:
                xx=np.geomspace(threshold,upper,120);sf=1-tail_cdf(xx,threshold,method,pars)
                fit_points.extend({'method':method,'threshold_H1_sd':float(x),'conditional_ccdf':float(y)} for x,y in zip(xx,sf))
        if threshold==cfg['primary_tail_threshold']:
            base=tail_logpdf(test_tail,threshold,'Pareto',fits['Pareto']);contrasts=[]
            for method in ['Exponential','Lognormal']:
                diff=tail_logpdf(test_tail,threshold,method,fits[method])-base;dd=np.bincount(day[mask],weights=diff,minlength=D)
                for L,w in weights.items():
                    values=(w@dd)/(w@tail_day);lo,hi=percentile_interval(values);contrasts.append({'contrast':method+' minus Pareto','mean_log_score_difference':float(diff.mean()),'ci_low':lo,'ci_high':hi,'day_block_length':L,'test_tail_count':len(test_tail)})
            write(tables/'tail_score_contrasts.csv',contrasts)
        print(f'Real tail analysis complete: threshold={threshold} H1 sd',flush=True)
    for L in weights:
        selected=[r for r in gof_rows if r['day_block_length']==L]
        for row,pvalue in zip(selected,holm_adjust([x['calibration_p_approx'] for x in selected])):row['calibration_p_holm']=pvalue
    write(tables/'tail_exponents.csv',tail_rows);write(tables/'tail_log_scores.csv',score_rows);write(tables/'tail_fixed_calibration.csv',gof_rows);write(tables/'tail_fitted_curves.csv',fit_points)
    primary_threshold=cfg['primary_tail_threshold'];tailmask=absolute>=primary_threshold;tailcounts=ccdf_by_day(absolute,grid,bpd);n_tail_day=tailmask.reshape(D,bpd).sum(1);conditional_ccdf=[]
    denominator=weights[primary]@n_tail_day
    for j,x in enumerate(grid):
        if x<primary_threshold:continue
        values=(weights[primary]@tailcounts[:,j])/denominator;lo,hi=percentile_interval(values)
        conditional_ccdf.append({'threshold_H1_sd':float(x),'conditional_ccdf':float(tailcounts[:,j].sum()/tailmask.sum()),'ci_low':lo,'ci_high':hi})
    write(tables/'real_conditional_tail_ccdf.csv',conditional_ccdf)
    # Per-path simulation summaries; independence unit is the whole simulated path.
    model_metrics=[];model_acf=[];model_scales=[];model_bin_records=[];model_ccdf=[]
    with gzip.open(tables/'model_series.csv.gz','rt',newline='') as stream:
        for (rho,rep),rows in groupby(csv.DictReader(stream),lambda x:(float(x['rho']),int(x['replication']))):
            rows=list(rows);rr=np.array([float(x['r']) for x in rows]);vv=np.array([float(x['V']) for x in rows]);assert len(rr)==len(r)
            mm=moments_to_statistics(daily_moments(rr,vv,bpd).sum(0));mm['spearman_abs_return_volume']=float(stats.spearmanr(np.abs(rr),vv).statistic)
            mm['tail_exceedance_3_H1_sd']=float(np.mean(np.abs(rr)/sigma>=primary_threshold));mm['q99_abs_return_H1_sd']=float(np.quantile(np.abs(rr)/sigma,.99));mm['q999_abs_return_H1_sd']=float(np.quantile(np.abs(rr)/sigma,.999))
            model_metrics.extend({'rho':rho,'replication':rep,'metric':key,'estimate':float(value)} for key,value in mm.items())
            for kind,x in [('signed_return',rr),('absolute_return',np.abs(rr))]:
                for lag in cfg['acf_lags']:model_acf.append({'rho':rho,'replication':rep,'series':kind,'lag':lag,'estimate':float(correlation_from_pair_sums(pair_sums_by_day(x,lag,bpd).sum(0)))})
            for k in cfg['aggregation_bars']:
                value=scale_statistics(scale_sums_by_day(rr,k,bpd).sum(0),k,np.var(rr));model_scales.extend({'rho':rho,'replication':rep,'aggregation_bars':k,'metric':key,'estimate':float(z)} for key,z in value.items())
            cc=ccdf_by_day(np.abs(rr)/sigma,grid,bpd).sum(0)/len(rr);model_ccdf.extend({'rho':rho,'replication':rep,'threshold_H1_sd':float(x),'ccdf':float(y)} for x,y in zip(grid,cc))
            bc,bx,by=conditional_bin_sums(vv,np.abs(rr)/sigma,vcuts,bpd)
            for j in range(bc.shape[1]):model_bin_records.append({'rho':rho,'replication':rep,'bin':j+1,'count':int(bc[:,j].sum()),'sum_volume':float(bx[:,j].sum()),'sum_abs_return_H1_sd':float(by[:,j].sum())})
            print(f'Model statistics complete: rho={rho}, path={rep+1}',flush=True)
    write(tables/'model_path_metrics.csv',model_metrics);write(tables/'model_path_acf.csv',model_acf);write(tables/'model_path_scaling.csv',model_scales);write(tables/'model_path_ccdf.csv',model_ccdf);write(tables/'model_path_coupling_bins.csv',model_bin_records)
    rng=np.random.default_rng(derived_seed(cfg['seed'],'model-intervals'));resamples=rng.integers(0,cfg['model']['replications'],(cfg['bootstrap_replicates'],cfg['model']['replications']))
    def summarize(records,fields,value):
        groups={tuple(row[k] for k in fields) for row in records};out=[]
        for key in sorted(groups):
            rr=sorted([x for x in records if tuple(x[k] for k in fields)==key],key=lambda x:x['replication']);a=np.array([x[value] for x in rr]);lo,hi=percentile_interval(a[resamples].mean(1))
            out.append({**dict(zip(fields,key)),'estimate':float(a.mean()),'run_sd':float(a.std(ddof=1)),'ci_low':lo,'ci_high':hi,'replications':len(a)})
        return out
    write(tables/'model_metrics_summary.csv',summarize(model_metrics,['rho','metric'],'estimate'));write(tables/'model_acf_summary.csv',summarize(model_acf,['rho','series','lag'],'estimate'));write(tables/'model_scaling_summary.csv',summarize(model_scales,['rho','aggregation_bars','metric'],'estimate'))
    for row in summarize(model_ccdf,['rho','threshold_H1_sd'],'ccdf'):ccdf_rows.append({'source':f'ER rho={row["rho"]:.1f}','threshold_H1_sd':row['threshold_H1_sd'],'ccdf':row['estimate'],'ci_low':row['ci_low'],'ci_high':row['ci_high'],'replications':row['replications']})
    write(tables/'ccdf_comparison.csv',ccdf_rows)
    for rho in cfg['model']['rho']:
        for j in range(len(vcuts)+1):
            records=sorted([x for x in model_bin_records if x['rho']==rho and x['bin']==j+1],key=lambda x:x['replication']);count=np.array([x['count'] for x in records]);sx=np.array([x['sum_volume'] for x in records]);sy=np.array([x['sum_abs_return_H1_sd'] for x in records]);total=int(count.sum())
            if total==0:coupling.append({'source':f'ER rho={rho:.1f}','bin':j+1,'observations':0,'mean_relative_volume':None,'mean_abs_return_H1_sd':None,'ci_low':None,'ci_high':None,'replications':len(records)});continue
            denominator=count[resamples].sum(1)
            if np.any(denominator==0):raise ValueError('empty model conditional-bin bootstrap; preserve and revise report rather than drop')
            lo,hi=percentile_interval(sy[resamples].sum(1)/denominator);coupling.append({'source':f'ER rho={rho:.1f}','bin':j+1,'observations':total,'mean_relative_volume':float(sx.sum()/total/meanv),'mean_abs_return_H1_sd':float(sy.sum()/total),'ci_low':lo,'ci_high':hi,'replications':len(records)})
    write(tables/'coupling_bins.csv',coupling)
    summary={'status':'pass','dataset':cfg['dataset'],'calibration_bars':len(train),'holdout_bars':len(test),'holdout_days':D,'training_return_sd':float(sigma),'training_mean_volume':float(meanv),
             'market_holdout_statistics':{key:float(value) for key,value in point.items()},'model_paths':len({(r['rho'],r['replication']) for r in model_metrics}),'rows_excluded':0,'gaps_filled':0,'primary_day_block_length':primary,'member_review':'not_run'}
    (checks/'analysis_summary.json').write_text(json.dumps(summary,indent=2)+'\n');record.update(status='pass',seconds=time.perf_counter()-started,outputs_sha256={x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in tables.glob('*.csv')});(checks/'analysis_record.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(summary,indent=2),flush=True)


if __name__=='__main__':main()
