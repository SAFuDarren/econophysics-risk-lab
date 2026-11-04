#!/usr/bin/env python3
"""Small exact-theory checks and independent numerical/data aggregation checks."""
from pathlib import Path
from fractions import Fraction as F
import argparse,csv,json,sys,tempfile,zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import numpy as np
from scipy import integrate,stats
from econophysics.market_data import read_archive
from econophysics.real_market_statistics import (daily_moments,moments_to_statistics,circular_day_weights,weighted_spearman_bootstrap,tail_logpdf,tail_cdf,fixed_tail_calibration)
from check_theory_foundations import graph_profiles,law,expectation


def main():
    p=argparse.ArgumentParser();p.add_argument('--run-id',default='real_market_v1');args=p.parse_args();checks=[]
    def check(name,valid):
        checks.append({'check':name,'passed':bool(valid)})
        if not valid:raise AssertionError(name)
    for n in (2,3,4):
        for edge in (F(0),F(1,4),F(3,4),F(1)):
            profiles=graph_profiles(n,edge);s2=sum(w*sum(s*s for s in sizes) for sizes,w in profiles.items());s3=sum(w*sum(s**3 for s in sizes) for sizes,w in profiles.items())
            for q in (F(1,5),F(1,2),F(4,5)):
                pmf={}
                for profile,w in profiles.items():
                    for state,prob in law(profile,q).items():pmf[state]=pmf.get(state,F(0))+w*prob
                ex=lambda fn:expectation(pmf,fn);mean=q*n;varq=ex(lambda x,m:x*x);varm=ex(lambda x,m:(m-mean)**2);third=ex(lambda x,m:(m-mean)**3);cross=ex(lambda x,m:x*x*(m-mean))
                b=cross/varq/mean;a=third/varm/mean;delta=b-a
                check(f'network-free Delta exact N={n},p={edge},q={q}',delta==s3/(n*s2))
                check(f'unknown-unit activity inversion N={n},p={edge},q={q}',delta/(b+delta)==q)
                check(f'Delta bounds N={n},p={edge},q={q}',F(1,n)<=delta<=1)
    rng=np.random.default_rng(2026102704)
    for L in (1,7,28):
        weights=circular_day_weights(28,L,30,rng);check(f'day weights preserve count L={L}',np.all(weights.sum(1)==28))
        if L==28:check('full-cycle block exactly preserves all dates',np.all(weights==1))
    x=np.array([1,1,2,5,3,0,0,2]);y=np.array([2,1,4,1,3,3,0,5]);weights=np.array([[2,0,1,1],[0,1,3,0],[1,1,1,1]])
    observed=weighted_spearman_bootstrap(x,y,weights,2)
    for i,w in enumerate(weights):
        ww=np.repeat(w,2);reference=stats.spearmanr(np.repeat(x,ww),np.repeat(y,ww)).statistic
        check(f'weighted tied ranks equal explicit resampling {i}',abs(observed[i]-reference)<1e-14)
    r=np.array([-.2,.3,-.1,.4,.05,-.5,.25,.1]);v=np.array([1,4,2,7,2,8,3,2.]);m=moments_to_statistics(daily_moments(r,v,2).sum(0));rc=r-r.mean();vc=v-v.mean()
    expected=(np.mean(rc*rc*vc)/np.var(r)-np.mean(vc**3)/np.var(v))/v.mean()
    check('sufficient moment Delta equals direct centered formula',abs(float(m['delta'])-expected)<1e-13)
    for a,b in [(.1,3),(5,.01),(1,1)]:
        z=moments_to_statistics(daily_moments(a*r,b*v,2).sum(0))
        check(f'Delta invariant to return/volume units {a},{b}',abs(float(z['delta'])-expected)<1e-12)
    parameters={'Pareto':{'alpha':3.4},'Exponential':{'rate':.5},'Lognormal':{'mu':0.,'sigma':1.}}
    for method,pars in parameters.items():
        integral=integrate.quad(lambda z:float(np.exp(tail_logpdf(np.array([z]),3.,method,pars)[0])),3.,np.inf)[0]
        check(f'conditional tail normalization {method}',abs(integral-1)<1e-8)
        values=np.array([3.,4.,10.]);check(f'tail CDF valid {method}',np.all(np.diff(tail_cdf(values,3.,method,pars))>=0) and tail_cdf(values,3.,method,pars)[0]==0)
    sample=3+rng.exponential(2,120);w=circular_day_weights(12,1,50,rng);gof=fixed_tail_calibration(sample,3.,'Exponential',{'rate':.5},w,10);reference=stats.kstest(sample,lambda z:tail_cdf(z,3.,'Exponential',{'rate':.5})).statistic
    check('tail KS distance matches independent SciPy implementation',abs(gof['ks']-reference)<1e-14)
    with tempfile.TemporaryDirectory() as td:
        for year,unit,multiplier,start in [(2024,'milliseconds',1000,1735603200000),(2025,'microseconds',1,1735689600000000)]:
            row=[start,100.,102.,99.,101.,2.,start+(300000000-multiplier)//multiplier,201.,12,1.,101.,0]
            archive=Path(td)/f'{year}.zip'
            with zipfile.ZipFile(archive,'w') as z:z.writestr('sample.csv',','.join(map(str,row))+'\n')
            parsed=list(read_archive(archive,unit))[0]
            check(f'explicit {unit} timestamp parsing',parsed['open_time_us']==start*multiplier and parsed['close']==101.)
    rows=list(csv.DictReader((ROOT/'data/processed/binance_btcusdt_2025_5m_v1/bars.csv').open()));r=np.array([float(x['return_log']) for x in rows]);c=np.array([float(x['close']) for x in rows]);reference_close=json.loads((ROOT/'data/manifests/binance_btcusdt_2025_5m_v1/quality_report.json').read_text())['reference_close'];previous=np.r_[reference_close,c[:-1]]
    for k in (1,3,12,48,288):
        summed=r.reshape(-1,k).sum(1);endpoint=np.log(c[k-1::k]/previous[::k]);check(f'all non-overlapping return sums equal endpoint returns k={k}',np.max(np.abs(summed-endpoint))<2e-14)
    report={'status':'pass','count':len(checks),'checks':checks,'evidence_types':['MODEL_CHECK','REAL_DATA aggregation audit'],'member_review':'not_run'}
    out=ROOT/'results/checks'/args.run_id/'method_checks.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2)+'\n');print(f'{len(checks)} real-market method checks passed')


if __name__=='__main__':main()
