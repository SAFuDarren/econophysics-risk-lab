#!/usr/bin/env python3
"""Independent raw-to-processed, core-statistic and seeded-model-prefix reproduction."""

from pathlib import Path as _ProjectPath
import sys as _project_sys
_project_sys.path.insert(0, str(_ProjectPath(__file__).resolve().parents[1]))
from _bootstrap import ROOT as PROJECT_ROOT, script_path, resolve_recorded_path
from pathlib import Path
from itertools import groupby,islice
import argparse,csv,gzip,hashlib,io,json,sys,time,zipfile
ROOT=PROJECT_ROOT;sys.path.insert(0,str(ROOT/'src'))
import numpy as np
from scipy import stats
from econophysics.model import Parameters,simulate_aggregates


def read(p):return list(csv.DictReader(p.open()))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run-id',default='real_market_v1');args=parser.parse_args()
    if not args.run_id.replace('_','').replace('-','').isalnum():parser.error('invalid run-id')
    begin=time.perf_counter();cfg=json.loads((ROOT/'configs/real_market_v1.json').read_text());manifest=json.loads((ROOT/'data/manifests'/cfg['dataset']/'download_manifest.json').read_text());tables=ROOT/'results/tables'/args.run_id;raw=[];previous=None
    for item in manifest['files']:
        path=ROOT/item['raw_path'];assert hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256']
        with zipfile.ZipFile(path) as z:
            names=[x for x in z.namelist() if x.endswith('.csv')];a=np.loadtxt(io.BytesIO(z.read(names[0])),delimiter=',')
        if item['role']=='reference_close_only':previous=float(a[-1,4]);continue
        raw.append(a)
    raw=np.concatenate(raw);processed=read(ROOT/'data/processed'/cfg['dataset']/'bars.csv');assert len(raw)==len(processed)==105120
    open_times=np.array([int(r['open_time_us']) for r in processed]);assert np.array_equal(raw[:,0].astype(np.int64),open_times)
    comparisons={key:float(np.max(np.abs(raw[:,index]-np.array([float(r[key]) for r in processed])))) for key,index in [('open',1),('high',2),('low',3),('close',4),('volume',5),('quote_volume',7),('trades',8),('taker_buy_volume',9),('taker_buy_quote_volume',10)]}
    assert all(v==0 for v in comparisons.values());rr=np.log(raw[:,4]/np.r_[previous,raw[:-1,4]]);r_saved=np.array([float(r['return_log']) for r in processed]);return_error=float(np.max(np.abs(rr-r_saved)));assert return_error<1e-15
    hold=np.array([r['split']=='holdout' for r in processed]);r=r_saved[hold];v=raw[hold,5];rc=r-r.mean();vc=v-v.mean();delta=(np.mean(rc*rc*vc)/np.var(r)-stats.moment(v,moment=3)/np.var(v))/v.mean()
    metrics=read(tables/'market_metrics.csv');stored_delta=float(next(x['estimate'] for x in metrics if x['metric']=='delta' and x['day_block_length']=='7'));assert abs(delta-stored_delta)<1e-10
    spearman=float(stats.spearmanr(np.abs(r),v).statistic);stored=float(next(x['estimate'] for x in metrics if x['metric']=='spearman_abs_return_volume' and x['day_block_length']=='7'));assert abs(spearman-stored)<1e-14
    acf=float(np.corrcoef(np.abs(r[1:]),np.abs(r[:-1]))[0,1]);stored_acf=float(next(x['estimate'] for x in read(tables/'market_acf.csv') if x['series']=='absolute_return' and x['lag']=='1' and x['day_block_length']=='7'));assert abs(acf-stored_acf)<1e-12
    train=~hold;mu=float(raw[train,5].mean());varv=float(raw[train,5].var());varr=float(r_saved[train].var());params=read(tables/'calibration_parameters.csv')
    for x in params:
        n=float(x['n']);q=float(x['q']);u=float(x['unit_order']);lam=float(x['lambda_impact']);A=float(x['theory_s2'])
        assert np.isclose(q*u*n,mu,rtol=1e-12) and np.isclose(q*(1-q)*u*u*A,varv,rtol=1e-12) and np.isclose(q*(lam/n)**2*A,varr,rtol=1e-12)
    seeds={(float(x['rho']),int(x['replication'])):int(x['seed']) for x in read(tables/'model_seeds_NOT_OBSERVATIONS.csv')};matched=0;maxerror=0.
    with gzip.open(tables/'model_series.csv.gz','rt',newline='') as stream:
        for key,group in groupby(csv.DictReader(stream),lambda x:(float(x['rho']),int(x['replication']))):
            prefix=list(islice(group,512));parameter=next(x for x in params if float(x['rho'])==key[0]);model=Parameters(n=int(parameter['n']),rho=key[0],a=float(parameter['a']),lambda_impact=float(parameter['lambda_impact']),unit_order=float(parameter['unit_order']))
            expected=simulate_aggregates(model,len(prefix),seeds[key])
            for old,new in zip(prefix,expected):
                for field in ['r','V']:
                    error=abs(float(old[field])-new[field]);maxerror=max(maxerror,error);assert error==0
                matched+=1
    report={'status':'pass','independent_archive_reader':'NumPy loadtxt, separate from the production CSV parser','real_bars_verified':len(raw),'raw_fields_max_errors':comparisons,'max_return_reconstruction_error':return_error,'direct_joint_delta':float(delta),'direct_spearman':spearman,'direct_lag1_magnitude_correlation':acf,
            'calibration_moments_verified':True,'model_paths_checked':len(seeds),'model_prefix_periods_regenerated':matched,'max_model_prefix_error':maxerror,'seconds':time.perf_counter()-begin,'member_review':'not_run','script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (ROOT/'results/checks'/args.run_id/'end_to_end_audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
