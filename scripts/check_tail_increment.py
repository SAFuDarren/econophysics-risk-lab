#!/usr/bin/env python3
"""Mathematical, causal, scoring and version-boundary checks for the tail study."""
from pathlib import Path
from publication_integrity import matches_recorded_digest
import csv,datetime as dt,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import numpy as np
from econophysics.tail_increment import build_laws,whiten,matrix_root,law_choices,covariance_series,factor_scenarios,empirical_scenarios,forecast_statistics,seed_for

def main():
    cfg=json.loads((ROOT/'configs/tail_increment_v1.json').read_text());checkdir=ROOT/'results/checks/tail_increment_v1';table=ROOT/'results/tables/tail_increment_v1';checks=[]
    def test(name,passed,**details):checks.append({'name':name,'pass':bool(passed),**details})
    def read(path):return list(csv.DictReader(path.open()))
    def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
    freeze=json.loads((ROOT/'data/manifests/tail_increment_v1/method_before_external_download.json').read_text());selection=json.loads((checkdir/'selection_freeze.json').read_text());download=json.loads((ROOT/'data/manifests/tail_increment_v1/external_before_download.json').read_text())
    test('Method and selected-reference files match documented source/publication versions',all(matches_recorded_digest(ROOT/p,digest,ROOT) for p,digest in {**selection['method_sha256'],**selection['source_sha256']}.items()))
    test('Method then selection then external download, all with no new raw before freeze',freeze['recorded_utc']<selection['recorded_utc']<download['recorded_utc'] and selection['external_raw_count']==download['raw_count_before_download']==0)
    for folder,expected in [('us_equity_v1','9df828d60014521dd24e90f6431f943e6eb447239b58521be7e1a4cc1b0c4839'),('risk_lab_v1','fc5b299639f8954927b9fdf0bb6250ca44534986c3cf612fe1340cdeb51b364d')]:
        filename='Econophysics_US_Equity_PnL_v1.zip' if folder=='us_equity_v1' else 'Econophysics_Risk_Lab_v1.zip';test('Prior delivered '+folder+' unchanged',sha(ROOT/'handoff/AB_to_CD'/filename)==expected)
    laws,grid,diagnostics,_=build_laws(cfg);test('Equal 24 non-Gaussian candidates for herding/factor-t/mixture',all(sum(l.family==f for l in laws)==24 for f in ['Herding','FactorT','FactorMixture']))
    for law in laws:
        test('Innovation covariance identity '+law.name,np.allclose(law.z.T@law.z/len(law.z),np.eye(9),atol=1e-11))
        if law.h is not None:test('Common innovation orthogonal with unit variance '+law.name,abs(np.mean(law.h))<1e-12 and abs(np.mean(law.h**2)-1)<1e-12 and np.max(abs(law.h@law.z/len(law.h)))<1e-11)
        if law.family!='StudentT':test('Marginal fitting density integrates to one '+law.name,abs(np.exp(law.log_density).sum()*(grid[1]-grid[0])-1)<.001)
    for diag in diagnostics:test('Cluster action variance vs q ES2 '+str((diag['rho'],diag['q'])),abs(diag['raw_variance']/diag['q_mean_s2']-1)<.05)
    for panel in ['sector','external']:
        rows=read(table/f'{panel}_daily.csv')
        for covariance in cfg['covariances']:
            for period,n in [('historical_test',1508),('confirmation',204)]:
                groups={m:[r for r in rows if r['covariance']==covariance and r['period']==period and r['method']==m] for m in cfg['methods']}
                test('All methods same day set '+str((panel,covariance,period)),all(len(r)==n and [v['date'] for v in r]==[v['date'] for v in groups['Gaussian']] for r in groups.values()))
                for model,data in groups.items():
                    test('Past-only fit boundary '+str((panel,covariance,period,model)),all(r['fit_end']<r['date'] for r in data))
                    test('Matched predicted covariance '+str((panel,covariance,period,model)),max(float(r['covariance_relative_error']) for r in data)<1e-10)
                    test('Tail ordering probabilities and finite losses '+str((panel,covariance,period,model)),all(float(r['es05'])<=float(r['q05'])<0 and float(r['q01'])<=float(r['q05']) and 0<=float(r['p_co3'])<=1 and all(np.isfinite(float(r[k])) for k in ['pinball05','pinball01','fz05','brier']) for r in data))
                    # Independently re-evaluate proper scores and realized indicators.
                    okay=True
                    for row in data:
                        y,q,e,p,event=map(float,[row['y'],row['q05'],row['es05'],row['p_co3'],row['co3']])
                        independent_pinball=.05*max(y-q,0)+.95*max(q-y,0)
                        independent_fz=(max(q-y,0)/(-.05*e))+q/e+np.log(-e)-1
                        okay &= abs(independent_pinball-float(row['pinball05']))<1e-12 and abs(independent_fz-float(row['fz05']))<1e-12 and abs((p-event)**2-float(row['brier']))<1e-12
                    test('Independent score recomputation '+str((panel,covariance,period,model)),okay)
        arrays=np.load(table/f'{panel}_EWMA-126-0.94_causal_arrays.npz');r=arrays['returns'];i=next(i for i,d in enumerate(arrays['dates']) if d>='2020-03-16');past=r[i-126:i];w=.94**np.arange(125,-1,-1);w/=w.sum();manual=past.T@(past*w[:,None]);test('Independent current covariance from strictly past returns '+panel,np.allclose(manual,arrays['covariances'][i],atol=1e-16))
        # A future perturbation must not alter origin covariance or any fit inputs.
        altered=r[:i+2].copy();altered[i:]*=10;cs,zs,hs=covariance_series(altered,'EWMA-126-0.94')
        test('Future perturbation leaves current covariance and past features unchanged '+panel,np.array_equal(cs[i],arrays['covariances'][i]) and np.array_equal(zs[i-504:i],arrays['z'][i-504:i]) and np.array_equal(hs[i-504:i],arrays['h'][i-504:i]))
        choices,_=law_choices(laws,grid,arrays['z'][i-504:i],arrays['h'][i-504:i]);law=laws[choices['Herding']];samples=factor_scenarios(manual,law);a=forecast_statistics(samples,manual,r[i]);b=forecast_statistics(samples,manual,10*r[i]);test('Prediction unaffected by actual target '+panel,all(a[k]==b[k] for k in ['q05','q01','es05','p_co3','portfolio_sigma']))
        fhs=empirical_scenarios(manual,arrays['z'][i-504:i],arrays['h'][i-504:i],'FHS',seed_for(cfg['seed'],'empiricalResidual'));test('Empirical comparator exact covariance without future returns '+panel,forecast_statistics(fhs,manual)['covariance_relative_error']<1e-11)
    contrasts=read(table/'contrasts.csv');primary=[r for r in contrasts if r['primary_family']=='True'];test('Exactly two frozen primary endpoint tests',len(primary)==2 and {r['metric'] for r in primary}=={'pinball05','brier'})
    test('Holm adjusted p values not below unadjusted',all(float(r['p_holm_primary'])>=float(r['p_centered_block_approx']) for r in primary))
    test('2026 external zero co-events retained, no post-result event redefinition',all(int(r['co_events'])==0 for r in read(table/'metrics.csv') if r['panel']=='external' and r['period']=='confirmation') and cfg['targets']['co_crash'].startswith('At least3'))
    truth=read(table/'synthetic_truth.csv');test('All six synthetic truths matched in covariance',len(truth)==6 and max(float(r['covariance_relative_error']) for r in truth)<1e-11)
    test('Monte Carlo sensitivity preserves fitting choices',all(int(r['shape_choice_disagreements'])==0 for r in read(table/'mc_sensitivity.csv')))
    test('Full-resolution audit preserves all fitted shapes',json.loads((checkdir/'mc_full_run.json').read_text())['shape_choice_disagreements']==0)
    analytic=read(table/'analytic_tail_daily.csv')
    test('Integrated tails finite with correct order',all(float(r['es01'])<=float(r['q01'])<=float(r['q05'])<0 and float(r['es05'])<=float(r['q05']) and np.isfinite([float(r[k]) for k in ['q05','q01','es05','es01','pinball05','fz05']]).all() for r in analytic))
    from scipy.stats import norm
    test('Gaussian analytic 5% quantile exact',all(abs(float(r['q05'])-norm.ppf(.05))<1e-13 for r in analytic if r['method']=='Gaussian'))
    sys.path.insert(0,str(ROOT/'scripts'))
    from audit_tail_analytic import mixture_tail
    from scipy.integrate import quad
    q,e=mixture_tail(np.array([-1.,1.]),np.array([.5,.5]),.7,.05);b=np.sqrt(1-.7**2)
    independent=quad(lambda x:x*(.5*norm.pdf(x,loc=-.7,scale=b)+.5*norm.pdf(x,loc=.7,scale=b)),-np.inf,q,epsabs=1e-12)[0]/.05
    test('Independent truncated-mixture quadrature verifies analytic ES',abs(e-independent)<1e-10)
    report={'status':'pass' if all(r['pass'] for r in checks) else 'fail','checks':len(checks),'failures':[r for r in checks if not r['pass']],'details':checks,'scientific_member_review':'not_run','scope':'Implementation/statistical-boundary checks, not scientific acceptance or market causal validation'};(checkdir/'method_audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='details'},indent=2))
    if report['status']!='pass':raise SystemExit(1)

if __name__=='__main__':main()
