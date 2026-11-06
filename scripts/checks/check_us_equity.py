#!/usr/bin/env python3
"""Independent source, arithmetic, execution and holdout audits of the US study."""

from pathlib import Path as _ProjectPath
import sys as _project_sys
_project_sys.path.insert(0, str(_ProjectPath(__file__).resolve().parents[1]))
from _bootstrap import ROOT as PROJECT_ROOT, script_path, resolve_recorded_path
from publication_integrity import matches_recorded_digest
from pathlib import Path
import csv,datetime as dt,hashlib,json,sys
from zoneinfo import ZoneInfo
ROOT=PROJECT_ROOT;sys.path.insert(0,str(ROOT/'src'))
import numpy as np
from scipy.optimize import minimize
from econophysics.us_equity import load_panel,strategy_library,hrp

def main():
    checks=[]
    def ok(name,condition):
        checks.append({'check':name,'pass':bool(condition)})
        if not condition:raise AssertionError(name)
    def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
    def read(name):return list(csv.DictReader((ROOT/f'results/tables/us_equity_v1/{name}.csv').open()))
    cfg=json.loads((ROOT/'configs/us_equity_v1.json').read_text());check=ROOT/'results/checks/us_equity_v1';selection=json.loads((check/'selection_freeze.json').read_text())
    for name,h in selection['sources_sha256'].items():ok('Selection bound source '+name,matches_recorded_digest(ROOT/name,h,ROOT))
    for stage in ['historical','confirmation']:
        folder=ROOT/'data/manifests/us_equity_v1';freeze=json.loads((folder/f'{stage}_before_download.json').read_text());manifest=json.loads((folder/f'{stage}_manifest.json').read_text());ok('Zero raw archives before '+stage,freeze['raw_count_before_download']==0)
        for name,h in freeze['sha256'].items():
            actual=resolve_recorded_path(ROOT/name,ROOT)
            if stage=='historical' and name=='scripts/fetch_us_equity.py' and not matches_recorded_digest(actual,h,ROOT):actual=check/'fetch_us_equity_before_calendar_fix.py'
            ok('Pre-download frozen '+stage+' '+name,matches_recorded_digest(actual,h,ROOT))
        independent={}
        for record in manifest['records']:
            path=ROOT/record['path'];ok('Raw SHA '+stage+' '+record['symbol'],sha(path)==record['sha256']);x=json.loads(path.read_text())['chart']['result'][0];q=x['indicators']['quote'][0];adj=x['indicators']['adjclose'][0]['adjclose']
            divs={dt.datetime.fromtimestamp(v['date'],ZoneInfo('America/New_York')).date().isoformat():v['amount'] for v in x.get('events',{}).get('dividends',{}).values()};splits={dt.datetime.fromtimestamp(v['date'],ZoneInfo('America/New_York')).date().isoformat():v['numerator']/v['denominator'] for v in x.get('events',{}).get('splits',{}).values()}
            for j,t in enumerate(x['timestamp']):
                day=dt.datetime.fromtimestamp(t,ZoneInfo('America/New_York')).date().isoformat();independent[day,record['symbol']]={**{k:q[k][j] for k in ['open','high','low','close','volume']},'adjusted_close':adj[j],'dividend':divs.get(day,0.),'split_ratio':splits.get(day,1.)}
        rows=list(csv.DictReader((ROOT/manifest['processed_path']).open()));ok('Independent raw row count '+stage,len(independent)==len(rows)==manifest['rows'])
        for key in ['open','high','low','close','volume','adjusted_close','dividend','split_ratio']:ok('Independent all raw fields '+stage+' '+key,all(float(row[key])==independent[row['date'],row['symbol']][key] for row in rows))
        ok('Processed SHA '+stage,sha(ROOT/manifest['processed_path'])==manifest['processed_sha256'])
    dates,r,price,symbols=load_panel(ROOT,cfg);n=9;basket=r[:,:n].mean(1);ok('Finite complete panel',np.isfinite(r).all() and len(set(dates))==len(dates));daily=read('daily_risk');lookup={row['date']:row for row in daily};samples=read('risk_samples');pred=read('risk_forecasts');fit=json.loads((check/'fitted_calibration.json').read_text());index={str(day):i for i,day in enumerate(dates)}
    scorechecks=[];lasttargets={}
    for row in samples:
        i=index[row['origin_date']];j=index[row['target_start']];k=index[row['target_end']];scorechecks.append(j==i+1 and k-j==4 and np.isclose(float(row['target']),np.mean(basket[j:k+1]**2),rtol=1e-13));lasttargets.setdefault(row['split'],[]).extend(range(j,k+1));left,right=cfg['splits'][row['split']];ok('Target boundary '+row['split']+' '+row['target_start'],left<=row['target_start']<=row['target_end']<right)
    ok('All five-session target reconstruction',all(scorechecks))
    for split,targets in lasttargets.items():ok('Nonoverlap targets '+split,len(set(targets))==len(targets))
    rng=np.random.default_rng(cfg['seed']+400);ix=rng.choice(np.arange(126,len(dates)),size=48,replace=False)
    for i in ix:
        x=r[i-62:i+1,:n];centered=x-x.mean(0);s=centered.T@centered/62;row=lookup[str(dates[i])];selfvar=np.trace(s)/81;full=s.sum()/81
        ok('Independent risk identity '+str(dates[i]),np.allclose([float(row['variance_self']),float(row['variance_total']),float(row['variance_collective'])],[selfvar,full,full-selfvar],rtol=1e-12,atol=1e-18));c=s/np.sqrt(np.outer(np.diag(s),np.diag(s)));e=np.linalg.eigvalsh(c)
        ok('Independent spectrum '+str(dates[i]),np.allclose([float(row['mean_correlation']),float(row['eigenvalue_share']),float(row['effective_dimension'])],[(c.sum()-9)/72,e[-1]/9,81/(e@e)],rtol=1e-11))
    samplookup={(s['split'],s['target_start']):s for s in samples}
    for name,record in fit.items():
        ok('Calibration train cutoff '+name,record['training_last_target']<'2020-01-01');trainrows=[s for s in samples if s['split'] in ['train','validation']];dimension=len(record['coefficient'])-1;xx=np.array([[float(s[f'x{i}']) for i in range(dimension)] for s in trainrows]);yy=np.array([float(s['target'])/float(s[selection['risk_reference']]) for s in trainrows]);z=(xx-np.array(record['feature_center']))/np.array(record['feature_scale']);design=np.c_[np.ones(len(z)),z];penalty=np.r_[0.,np.full(3,selection['return_alpha']),np.full(max(0,dimension-3),float(selection['network_alpha']) if selection['network_alpha']!='off' else 0.)];logy=np.log(yy/record['target_scale'])
        def fun(b):a=logy-design@b;return float(np.sum(np.exp(a)-a-1)+.5*np.dot(penalty*b,b))
        def jac(b):return design.T@(1-np.exp(logy-design@b))+penalty*b
        answer=minimize(fun,np.zeros(dimension+1),jac=jac,method='L-BFGS-B',options={'ftol':1e-14,'gtol':1e-8,'maxiter':1000});ok('Independent SciPy Gamma optimum '+name,np.max(abs(design@answer.x-design@np.array(record['coefficient'])))<1e-5)
    for name in ['ReturnGamma','NetworkGamma']:
        rec=fit[name];d=len(rec['coefficient'])-1;rows=[p for p in pred if p['model']==name];actual=[];expected=[]
        for p in rows:
            s=samplookup[p['split'],p['target_start']];x=np.array([float(s[f'x{i}']) for i in range(d)]);z=(x-np.array(rec['feature_center']))/np.array(rec['feature_scale']);v=float(s[selection['risk_reference']])*rec['target_scale']*np.exp(rec['coefficient'][0]+z@np.array(rec['coefficient'][1:]));actual.append(float(p['forecast']));expected.append(v)
        ok('Independent all calibration predictions '+name,np.allclose(actual,expected,rtol=1e-12))
    ok('All stored QLIKE losses',all(np.isclose(float(p['qlike']),float(p['actual'])/float(p['forecast'])-np.log(float(p['actual'])/float(p['forecast']))-1,rtol=1e-11,atol=1e-15) for p in pred))
    position=np.load(ROOT/'results/tables/us_equity_v1/positions.npz');q=position['strategy_units'];p=price[:,:n]/price[0,:n];gross=np.zeros(q.shape[:2]);gross[1:]=np.einsum('tki,ti->tk',q[:-1],np.diff(p,axis=0));turn=np.sum(abs(q-np.concatenate([np.zeros_like(q[:1]),q[:-1]]))*p[:,None,:],axis=2);short=np.zeros(q.shape[:2]);short[1:]=np.maximum(-q[:-1]*p[:-1,None,:],0).sum(2)
    ok('All strategy gross PnL independent',np.allclose(gross,position['strategy_gross'],rtol=1e-12,atol=1e-17));ok('All strategy turnover independent',np.allclose(turn,position['strategy_turnover'],atol=1e-15));ok('All strategy borrow notional',np.allclose(short,position['strategy_shorts'],atol=1e-15))
    sr=read('strategy_daily');names=position['strategy_names'].tolist();borrow=cfg['strategy_library']['borrow_bps_annual']/1e4/252
    for cost in cfg['strategy_library']['cost_bps']:ok('All strategy net costs '+str(cost),all(np.isclose(float(row[f'net_{cost}bp']),gross[index[row['date']],names.index(row['strategy'])]-cost/1e4*turn[index[row['date']],names.index(row['strategy'])]-borrow*short[index[row['date']],names.index(row['strategy'])],rtol=1e-12,atol=1e-17) for row in sr))
    ok('All strategy signals lag execution',all(not row['signal_date'] or row['signal_date']<row['date'] for row in sr));ar=read('allocation_daily');ok('All allocation signals lag execution',all(not row['signal_date'] or row['signal_date']<row['date'] for row in ar))
    for method in cfg['allocation']['methods']:
        a=position[f'weights_{method}'];aggregate=position[f'units_{method}'];ok('Underlying sleeve netting '+method,np.allclose(np.einsum('tk,tki->ti',a,q),aggregate,rtol=1e-12,atol=1e-15));sums=a.sum(1);active=sums>0;ok('Long-only unit capital '+method,a.min()>-1e-9 and np.allclose(sums[active],1.,atol=1e-8))
        if method=='LW-MinVariance':ok('Min variance allocation cap',a.max()<=cfg['allocation']['minvar_cap']+1e-8)
        gain=np.zeros(len(dates));gain[1:]=np.einsum('ti,ti->t',aggregate[:-1],np.diff(p,axis=0));turnover=np.sum(abs(aggregate-np.vstack([np.zeros(n),aggregate[:-1]]))*p,axis=1);negative=np.zeros(len(dates));negative[1:]=np.maximum(-aggregate[:-1]*p[:-1],0).sum(1)
        for cost in cfg['strategy_library']['cost_bps']:ok('All aggregate execution costs '+method+' '+str(cost),all(np.isclose(float(row[f'net_{cost}bp']),gain[index[row['date']]]-cost/1e4*turnover[index[row['date']]]-borrow*negative[index[row['date']]],rtol=1e-12,atol=1e-17) for row in ar if row['method']==method))
    cut=index['2021-01-15']+1;truncated=strategy_library(dates[:cut],r[:cut],price[:cut],cfg);ok('Strategy causality prefix and week boundaries',np.array_equal(truncated['units'],q[:cut]) and np.allclose(truncated['gross'],gross[:cut],atol=1e-17))
    ok('HRP known diagonal solution',np.allclose(hrp(np.diag([1.,4.,9.,16.])),np.array([1.,1/4,1/9,1/16])/sum([1.,1/4,1/9,1/16])))
    exposed=read('exposure_decomposition');ok('Every W Sigma W decomposition',all(np.isclose(float(row['shared_exposure_covariance'])+float(row['cross_asset_covariance']),float(row['conditional_implied_covariance']),rtol=1e-12,atol=1e-16) for row in exposed))
    report={'status':'pass','checks':checks,'count':len(checks),'source_rows_checked':44286+2244,'source_and_method_scope':'Independent raw-field reconstruction, model arithmetic/offset solver, past-target/lag, portfolio netting and cost checks. Same runtime/source for deterministic reproduction, not independent market replication.','scientific_member_review':'not_run'};(check/'method_audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':'pass','checks':len(checks),'raw_rows_checked':report['source_rows_checked']},indent=2))

if __name__=='__main__':main()
