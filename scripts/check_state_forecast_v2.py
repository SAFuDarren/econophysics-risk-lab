#!/usr/bin/env python3
"""Independent archives, chronology, convex optimisation, units and state-law audit."""
from pathlib import Path
import argparse,csv,hashlib,io,json,sys,zipfile
from fractions import Fraction as F
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import numpy as np
from scipy import optimize
from econophysics.state_forecasting import ChannelRegressor,state_samples
from econophysics.physics_inference import finite_er_moments
from check_theory_foundations import graph_profiles,law,expectation


def read(p):return list(csv.DictReader(p.open()))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run-id',default='state_forecast_v2');args=parser.parse_args();tables=ROOT/'results/tables'/args.run_id;checks=ROOT/'results/checks'/args.run_id;cfg=json.loads((ROOT/'configs/state_forecast_v2.json').read_text());items=[]
    def check(name,value):
        items.append({'check':name,'pass':bool(value)})
        if not value:raise AssertionError(name)
    rows_verified=0
    for key in ['source_btc_new','source_eth_new']:
        dataset=cfg[key];manifest=json.loads((ROOT/'data/manifests'/dataset/'download_manifest.json').read_text());raw=[];previous=None
        if key=='source_btc_new':previous=float(read(ROOT/'data/processed'/cfg['source_btc_2026']/'bars.csv')[-1]['close'])
        for entry in manifest['files']:
            p=ROOT/entry['raw_path'];check('Archive SHA '+p.name,hashlib.sha256(p.read_bytes()).hexdigest()==entry['sha256'])
            with zipfile.ZipFile(p) as z:a=np.loadtxt(io.BytesIO(z.read(z.namelist()[0])),delimiter=',')
            if entry['role']=='reference':previous=float(a[-1,4])
            else:raw.append(a)
        raw=np.concatenate(raw);processed=read(ROOT/'data/processed'/dataset/'bars.csv');rows_verified+=len(raw);check('Independent archive count '+key,len(raw)==len(processed))
        for name,j in [('open',1),('high',2),('low',3),('close',4),('volume',5),('quote_volume',7),('trades',8),('taker_buy_volume',9)]:check('Archive field '+key+name,np.array_equal(raw[:,j],np.array([float(r[name]) for r in processed])))
        check('Return reconstruction '+key,np.array_equal(np.log(raw[:,4]/np.r_[previous,raw[:-1,4]]),np.array([float(r['return_log']) for r in processed])))
        check('5min complete grid '+key,np.array_equal(np.diff(raw[:,0]),np.full(len(raw)-1,300_000_000)))
    samples=read(tables/'forecast_samples.csv');daily=read(tables/'daily_features.csv');pred=read(tables/'predictions.csv');fits=read(tables/'refit_records.csv');selected=json.loads((checks/'selected_models.json').read_text())['assets']
    from datetime import date,timedelta
    check('All origins precede target by one UTC day',all(date.fromisoformat(r['target_date'])-date.fromisoformat(r['origin_date'])==timedelta(days=1) for r in samples))
    check('All fit outcomes completed before forecast block',all(r['training_last_target']<r['refit_target_date'] and 250<=int(r['training_targets'])<=365 for r in fits))
    for asset in ['BTCUSDT','ETHUSDT']:
        data=[r for r in samples if r['asset']==asset];dd=[{k:(v if k=='date' else float(v)) for k,v in r.items() if k!='asset'} for r in daily if r['asset']==asset];copy=[dict(r) for r in dd];cut=500
        for r in copy[cut:]:
            for k in r:
                if k!='date':r[k]*=3
        before=state_samples(dd);after=state_samples(copy);names=list(dict.fromkeys(cfg['return_features']+cfg['state_volume_features']));check('Future daily perturbation causal '+asset,all(all(a[k]==b[k] for k in names) for a,b in zip(before,after) if a['origin_date']<dd[cut]['date']))
        units=[dict(r) for r in dd]
        for r in units:r['volume']*=1e6;r['average_trade']*=1e6;r['response_slope']/=1e6
        changed=state_samples(units);check('State volume features invariant to quantity units '+asset,max(abs(a[k]-b[k]) for a,b in zip(before,changed) for k in cfg['state_volume_features'])<1e-10)
        # Solve the same convex objective using independent SciPy L-BFGS, not our Newton loop.
        spec=selected[asset]['StateVolumeGamma-Adaptive'];names=spec['features'];names=names[:8] if spec['volume_penalty']=='off' else names;cutoff='2026-10-01';lower='2025-10-01';train=[r for r in data if lower<=r['target_date']<cutoff];test=[r for r in data if cutoff<=r['target_date']<'2026-10-08'];xx=np.array([[float(r[k]) for k in names] for r in train]);xt=np.array([[float(r[k]) for k in names] for r in test]);mean=xx.mean(0);scale=xx.std(0);scale=np.where(scale>0,scale,1);z=np.c_[np.ones(len(xx)),(xx-mean)/scale];zt=np.c_[np.ones(len(xt)),(xt-mean)/scale];y=np.array([float(r['target_rv']) for r in train]);s=y.mean();logy=np.log(y/s);penalty=np.r_[0.,np.full(8,spec['return_penalty']),np.full(max(0,len(names)-8),float(spec['volume_penalty']) if spec['volume_penalty']!='off' else 1.)]
        def objective(b):
            error=logy-z@b;ratio=np.exp(error);return np.sum(ratio-error-1)+.5*np.sum(penalty*b*b),z.T@(1-ratio)+penalty*b
        result=optimize.minimize(objective,np.zeros(len(names)+1),jac=True,method='L-BFGS-B',options={'maxiter':3000,'ftol':1e-14,'gtol':1e-9});expect=np.log(s)+zt@result.x;actual=np.array([float(r['log_forecast']) for r in pred if r['asset']==asset and r['evaluation']=='new_time' and r['model']=='StateVolumeGamma-Adaptive' and r['target_date']<'2026-10-08']);check('Independent convex optimizer '+asset,np.max(np.abs(expect-actual))<2e-6)
    check('ETH off is exact return-only predictions',all(float(a['log_forecast'])==float(b['log_forecast']) for a,b in zip([r for r in pred if r['asset']=='ETHUSDT' and r['model']=='StateVolumeGamma-Adaptive'],[r for r in pred if r['asset']=='ETHUSDT' and r['model']=='ReturnGamma-Adaptive'])))
    check('All QLIKE losses independently recomputed',all(abs(float(r['actual_rv'])/float(r['forecast_rv'])-np.log(float(r['actual_rv'])/float(r['forecast_rv']))-1-float(r['qlike']))<1e-11 for r in pred))
    check('All forecasts positive',all(float(r['forecast_rv'])>0 for r in pred));check('All risk-budget indicators direct',all(int(float(r['double_budget']))==int(float(r['actual_rv'])/float(r['forecast_rv'])>2) for r in pred))
    # Known intercept-only Gamma optimum is the arithmetic mean, not geometric mean.
    y=np.array([1.,2.,3.,8.]);x=np.zeros((4,8));model=ChannelRegressor('gamma',10.,'off',8).fit(x,y);check('Gamma constant-feature arithmetic mean',np.allclose(np.exp(model.predict_log(x)),y.mean()))
    scaled=ChannelRegressor('gamma',10.,'off',8).fit(x,10000*y);check('Gamma target-unit equivariance',np.allclose(np.exp(scaled.predict_log(x)),10000*np.exp(model.predict_log(x))))
    # Post-analysis explanatory construction; no tuning or forecasts are added.
    qlo=F(3,200);qhi=F(9,20);pi=F(3,20);qbar=(1-pi)*qlo+pi*qhi
    for n in [2,3,4]:
        for p in [F(0),F(1,3),F(1)]:
            profiles=graph_profiles(n,p);S2=sum(w*sum(s*s for s in sizes) for sizes,w in profiles.items());S3=sum(w*sum(s**3 for s in sizes) for sizes,w in profiles.items());ev=F(0);ev2=F(0);ev3=F(0);er2=F(0);er2v=F(0)
            for q,weight in [(qlo,1-pi),(qhi,pi)]:
                for sizes,pgraph in profiles.items():
                    for (net,vol),prob in law(sizes,q).items():
                        w=weight*pgraph*prob;ev+=w*vol;ev2+=w*vol**2;ev3+=w*vol**3;er2+=w*(qbar/q)*net**2;er2v+=w*(qbar/q)*net**2*vol
            varv=ev2-ev*ev;third=ev3-3*ev*ev2+2*ev**3;B=(er2v-er2*ev)/er2;check(f'Compensated state exact cross moment N={n},p={p}',B==(1-qbar)*S3/S2)
    c=cfg['mechanism'];m=finite_er_moments(c['n'],c['rho']);m1=float(qbar);m2=float((1-pi)*qlo*qlo+pi*qhi*qhi);m3=float((1-pi)*qlo**3+pi*qhi**3);N=c['n'];var=(m1-m2)*m['s2']+N*N*(m2-m1*m1);third=(m1-3*m2+2*m3)*m['s3']+3*N*m['s2']*((m2-m3)-m1*(m1-m2))+N**3*(m3-3*m1*m2+2*m1**3);delta=((1-m1)*m['s3']/m['s2']-third/var)/(N*m1);check('Compensated finite-N example has negative Delta',delta<0)
    theory={'status':'verified_construction','post_analysis':True,'scope':'Explanatory exact population-moment construction, not a newly fitted market or forecast model','activity_states':[float(qlo),float(qhi)],'high_probability':float(pi),'mean_activity':float(qbar),'impact_rule':'lambda(q)^2=lambda0^2*qbar/q','same_stationary_mean_volume_and_return_variance_as_constant_model':True,'compensated_delta':delta,'fixed_delta':m['s3']/(N*m['s2']),'new_predictive_models_added':False};(checks/'compensation_theory.json').write_text(json.dumps(theory,indent=2)+'\n')
    report={'status':'pass','checks':items,'count':len(items),'new_real_bars_independently_verified':rows_verified,'member_review':'not_run'};(checks/'method_audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':'pass','checks':len(items),'new_bars':rows_verified,'compensated_theory_delta':delta},indent=2))


if __name__=='__main__':main()
