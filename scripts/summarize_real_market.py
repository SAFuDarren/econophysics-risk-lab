#!/usr/bin/env python3
"""Evidence index, H1 calibration uncertainty and deterministic support audit."""
from pathlib import Path
import argparse,csv,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import numpy as np
from econophysics.model import derived_seed
from econophysics.real_market_statistics import daily_moments,moments_to_statistics,circular_day_weights,percentile_interval


def read(path):return list(csv.DictReader(path.open()))
def write(path,rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run-id',default='real_market_v1');args=parser.parse_args()
    if not args.run_id.replace('_','').replace('-','').isalnum():parser.error('invalid run-id')
    tables=ROOT/'results/tables'/args.run_id;out=ROOT/'results/analysis'/args.run_id;out.mkdir(parents=True,exist_ok=True)
    cfg=json.loads((ROOT/'configs/real_market_v1.json').read_text());data=read(ROOT/'data/processed'/cfg['dataset']/'bars.csv');train=[r for r in data if r['split']=='calibration'];test=[r for r in data if r['split']=='holdout'];rt=np.array([float(r['return_log']) for r in train]);vt=np.array([float(r['volume']) for r in train]);rtest=np.array([float(r['return_log']) for r in test]);parameters=read(tables/'calibration_parameters.csv');moments=daily_moments(rt,vt);uncertainty=[]
    for L in cfg['bootstrap_day_block_lengths']:
        w=circular_day_weights(len(train)//288,L,cfg['bootstrap_replicates'],np.random.default_rng(derived_seed(cfg['seed'],f'calibration-weights:{L}')));m=moments_to_statistics(w@moments)
        for row in parameters:
            n=float(row['n']);A=float(row['theory_s2']);q=A/(A+n*n*m['volume_cv']**2);u=m['mean_volume']/(q*n);lam=n*m['return_std']/np.sqrt(q*A)
            for name,values in [('q',q),('unit_order',u),('lambda_impact',lam)]:
                lo,hi=percentile_interval(values);uncertainty.append({'rho':float(row['rho']),'parameter':name,'estimate':float(row[name]),'ci_low':lo,'ci_high':hi,'day_block_length':L,'scope':'H1 date-block sensitivity; trajectory bands remain conditional on point calibration'})
    write(tables/'calibration_parameter_intervals.csv',uncertainty)
    support=[]
    for row in parameters:
        lam=float(row['lambda_impact']);support.append({'rho':float(row['rho']),'fixed_model_return_bound':lam,'holdout_max_abs_return':float(np.abs(rtest).max()),'holdout_events_outside_model_support':int(np.sum(np.abs(rtest)>lam+1e-14)),
                                                       'holdout_bars':len(rtest),'interpretation':'Post-analysis deterministic support check at fixed H1 calibration, not a new fitted rho or a global exclusion of all calibrations'})
    write(tables/'model_support_audit.csv',support)
    metric=read(tables/'market_metrics.csv');acf=read(tables/'market_acf.csv');scaling=read(tables/'market_scaling.csv')
    def pick(rows,**conditions):return next(r for r in rows if all(str(r[k])==str(v) for k,v in conditions.items()))
    summary={'status':'pass','kind':['REAL_DATA','SIMULATION'],'dataset_quality':json.loads((ROOT/'data/manifests'/cfg['dataset']/'quality_report.json').read_text()),
             'primary_market_metrics':[pick(metric,metric=k,day_block_length=7) for k in ['spearman_abs_return_volume','spearman_season_adjusted_abs_volume','delta','excess_kurtosis']],
             'lag1_acf':[pick(acf,series=k,lag=1,day_block_length=7) for k in ['signed_return','absolute_return','season_adjusted_absolute_return']],
             'daily_variance_ratio':pick(scaling,metric='variance_ratio',aggregation_bars=288,day_block_length=7),'tail_exponents_primary':[r for r in read(tables/'tail_exponents.csv') if r['threshold_H1_sd']=='3.0' and r['day_block_length']=='7'],
             'tail_calibration_primary':[r for r in read(tables/'tail_fixed_calibration.csv') if r['day_block_length']=='7'],'impact':pick(read(tables/'impact_association.csv'),day_block_length=7),
             'support_audit':support,'monthly_delta_all_negative':all(float(r['delta'])<0 for r in read(tables/'joint_constraint_sensitivity.csv') if r['case']=='calendar_month'),'leave_extreme_day_delta_all_negative':all(float(r['delta'])<0 for r in read(tables/'joint_constraint_sensitivity.csv') if r['case'].startswith('leave_')),
             'member_review':'not_run','source_attribution':'Binance Vision, BTCUSDT spot; market-derived outputs CC BY-NC-SA 4.0; terms snapshot retained.'}
    (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':'pass','support_audit':support,'month_negative':summary['monthly_delta_all_negative'],'extreme_day_negative':summary['leave_extreme_day_delta_all_negative']},indent=2))
    (ROOT/'results/checks'/args.run_id/'summary_provenance.json').write_text(json.dumps({'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'source_tables_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in tables.glob('*.csv')}},indent=2)+'\n')


if __name__=='__main__':main()
