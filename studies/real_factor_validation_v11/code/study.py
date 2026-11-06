"""Frozen monthly factor-risk validation; official observations vs computed portfolios."""
from pathlib import Path
import argparse,calendar,csv,datetime,hashlib,io,json,sys,urllib.request,zipfile
import numpy as np
import pandas as pd
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[1]

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x):Path(p).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def cfg():return json.loads((R/'PROTOCOL.json').read_text())
def freeze():
    paths=[R/'PROTOCOL.json',Path(__file__)]
    dump(R/'checks/pre_download_freeze.json',{'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'before_download':True,'files':{str(p.relative_to(R)):sha(p) for p in paths}})
def guard():
    f=json.loads((R/'checks/pre_download_freeze.json').read_text())
    for p,h in f['files'].items():assert sha(R/p)==h,p
    return f

def download():
    guard();records=[]
    for url in cfg()['official_sources']:
        request=urllib.request.Request(url,headers={'User-Agent':'Econophysics academic research contact via source project'})
        with urllib.request.urlopen(request,timeout=60) as f:body=f.read();headers=dict(f.headers);status=f.status
        p=R/'inputs'/url.rsplit('/',1)[1];p.write_bytes(body)
        with zipfile.ZipFile(p) as z:
            assert z.testzip() is None
            names=z.namelist()
            for name in names:
                text=z.read(name).decode('utf-8-sig',errors='strict');(R/'inputs'/Path(name).name).write_text(text)
        records.append(dict(url=url,status=status,bytes=len(body),sha256=sha(p),retrieved_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),headers=headers,archive_members=names))
    dump(R/'checks/download_manifest.json',{'source':'Kenneth R. French Data Library, Dartmouth Tuck','records':records,'terms':'Original files retain author copyright; no new license over source data is granted. Research attribution and source URL retained.'})

def parse_file(p,names):
    lines=p.read_text().splitlines();out=[]
    for line in lines:
        parts=[x.strip() for x in line.split(',')]
        if len(parts)>=len(names)+1 and len(parts[0])==8 and parts[0].isdigit():
            vals=[float(x) for x in parts[1:len(names)+1]]
            if any(x in [-99.99,-999] for x in vals):raise ValueError('Missing source factor observation')
            out.append([pd.to_datetime(parts[0],format='%Y%m%d'),*[x/100 for x in vals]])
    d=pd.DataFrame(out,columns=['date']+names).set_index('date')
    assert not d.empty and d.index.is_unique and d.index.is_monotonic_increasing
    return d

def panel():
    five_path=next(p for p in (R/'inputs').iterdir() if p.name.lower()=='f-f_research_data_5_factors_2x3_daily.csv')
    momentum_path=next(p for p in (R/'inputs').iterdir() if p.name.lower()=='f-f_momentum_factor_daily.csv')
    five=parse_file(five_path,['MktRF','SMB','HML','RMW','CMA','RF'])
    mom=parse_file(momentum_path,['Mom'])
    d=five.join(mom,how='inner')[cfg()['factor_order']]
    d=d[(d.index>=cfg()['start'])&(d.index<=cfg()['end_cap'])]
    assert not d.isna().any().any() and np.isfinite(d.to_numpy()).all()
    last=d.index.max();year,month=last.year,last.month;end=pd.Timestamp(year,month,calendar.monthrange(year,month)[1])
    while end.weekday()>=5:end-=pd.Timedelta(days=1)
    if last<end:d=d[d.index.to_period('M')<last.to_period('M')]
    assert not d.empty
    return d

def gamma_fit(x,y,penalty):
    mean=x.mean(0);sd=x.std(0);sd[sd<1e-14]=1.;D=np.c_[np.ones(len(x)),(x-mean)/sd];scale=float(y.mean());ly=np.log(y/scale);pen=np.r_[0.,np.full(x.shape[1],penalty)];b=np.zeros(D.shape[1])
    def objective(p):
        with np.errstate(over='ignore'):e=ly-D@p;return float(np.sum(np.expm1(e)-e)+.5*np.dot(pen*p,p))
    old=objective(b)
    for it in range(150):
        rat=np.exp(ly-D@b);g=D.T@(1-rat)+pen*b;H=D.T@(rat[:,None]*D)+np.diag(pen);step=np.linalg.solve(H,g);dec=float(g@step)
        if dec<1e-10 or np.max(abs(g))/len(y)<1e-9:break
        rate=1.
        while rate>2**-35:
            new=b-rate*step;value=objective(new)
            if np.isfinite(value) and value<=old-1e-4*rate*dec:break
            rate*=.5
        if rate<=2**-35:
            if dec<1e-7:break
            raise ArithmeticError('Gamma line search')
        b=new;old=value
    grad=float(np.max(abs(D.T@(1-np.exp(ly-D@b))+pen*b))/len(y))
    if grad>1e-5:raise ArithmeticError('Gamma convergence '+str(grad))
    return dict(mean=mean.tolist(),sd=sd.tolist(),b=b.tolist(),scale=scale,penalty=penalty,gradient=grad,iterations=it+1)
def predict(f,x):return f['scale']*np.exp(f['b'][0]+((x-np.array(f['mean']))/np.array(f['sd']))@np.array(f['b'][1:]))
def qlike(y,p):
    z=np.log(y/p);return np.expm1(z)-z

def allocate(p,score):
    log=np.log(p)+.1*np.clip(score,-2,2);q=np.exp(log-log.max());q/=q.sum();return .98*q+.02/6
def features(past,w):
    port=past@w;har=np.log([np.mean(port[-k:]**2) for k in [22,66,252]])
    second=np.log(np.array([np.mean(past[-k:]**2,0) for k in [22,66,252]]).ravel())
    corr=np.corrcoef(past[-63:].T);return har,np.r_[har,second,past[-63:].mean(0),corr[np.triu_indices(6,1)]]

def build_predictions():
    guard();d=panel();d.to_csv(R/'tables/observed_factor_returns.csv',index_label='date')
    a=d.to_numpy();months=d.index.to_period('M');unique=months.unique();budget={n:np.full(6,1/6) for n in ['Fixed','Performance','Permuted']};oldweights={n:None for n in budget}
    rows=[];x0=[];xall=[];truth_dev=[];weights={n:[] for n in budget};exposure_rows=[];lastperiod=[]
    for period in unique[:-1]:
        ii=np.flatnonzero(months==period);t=ii[-1]
        if t<251:continue
        past=a[t-251:t+1];sd=past.std(0,ddof=1)
        assert np.all(sd>0)
        score=a[ii].sum(0)/(sd*np.sqrt(len(ii)))
        budget['Performance']=allocate(budget['Performance'],score)
        h=int(hashlib.sha256(str(period).encode()).hexdigest()[:16],16)
        perm=np.random.default_rng(h).permutation(6);budget['Permuted']=allocate(budget['Permuted'],score[perm])
        for mode in budget:
            w=budget[mode]/sd;w/=w.sum();weights[mode].append(w.copy())
            turnover=0. if oldweights[mode] is None else .5*abs(w-oldweights[mode]).sum()
            exposure_rows.append(dict(origin=str(d.index[t].date()),future_month=str(period+1),mode=mode,HHI=float(w@w),risk_budget_HHI=float(budget[mode]@budget[mode]),turnover=float(turnover),assumed_1bp_turnover_charge=float(.0001*turnover),**{n:float(v) for n,v in zip(cfg()['factor_order'],w)},**{'budget_'+n:float(v) for n,v in zip(cfg()['factor_order'],budget[mode])}))
            oldweights[mode]=w.copy()
        w=weights['Fixed'][-1];p=past[-63:];mu=p.mean(0);cov=np.cov(p,rowvar=False,ddof=0);drift=float((w@mu)**2);full=float(drift+w@cov@w);diag=float(drift+np.sum(w*w*np.diag(cov)))
        corr=np.corrcoef(p.T);eigen=np.linalg.eigvalsh(corr);neff=float(eigen.sum()**2/np.dot(eigen,eigen));h0,h1=features(past,w)
        future=np.flatnonzero(months==period+1)
        target_month=(period+1).year
        role='fit' if target_month<=2009 else 'development' if target_month<=2019 else 'evaluation'
        # Only fit/development targets are supplied to fitting. Evaluation truth joins below after freeze.
        if role!='evaluation':
            fy=a[future]@w;truth_dev.append(float(np.mean(fy*fy)))
        else:truth_dev.append(np.nan)
        rows.append(dict(origin=str(d.index[t].date()),future_month=str(period+1),role=role,FullCov=full,Diagonal=diag,cross_term=full-diag,full_over_diagonal=full/diag,effective_corr_modes=neff,future_days=len(future)))
        x0.append(h0);xall.append(h1);lastperiod.append(period)
    frame=pd.DataFrame(rows);X={'HAR-Portfolio':np.array(x0),'HAR-All':np.array(xall)};y=np.array(truth_dev);fit=(frame.role=='fit').to_numpy();dev=(frame.role=='development').to_numpy()
    assert fit.sum()>100 and dev.sum()>=60
    models={};grid=[]
    for name,x in X.items():
        choices=[]
        for penalty in [.1,10.,1000.]:
            model=gamma_fit(x[fit],y[fit],penalty);pr=predict(model,x);loss=float(qlike(y[dev],pr[dev]).mean());grid.append(dict(model=name,penalty=penalty,development_QLIKE=loss));choices.append((loss,penalty,model,pr))
        loss,pen,model,pr=min(choices,key=lambda z:(z[0],z[1]));models[name]=dict(parameters=model,development_QLIKE=loss);frame[name]=pr
    assert np.isfinite(frame[['FullCov','Diagonal','HAR-Portfolio','HAR-All']]).all().all()
    frame.to_csv(R/'tables/predictions_before_truth.csv',index=False);pd.DataFrame(exposure_rows).to_csv(R/'tables/computed_allocations.csv',index=False);pd.DataFrame(grid).to_csv(R/'tables/development_grid.csv',index=False)
    dump(R/'checks/fitted_models.json',models)
    np.savez_compressed(R/'tables/past_features.npz',HAR_Portfolio=X['HAR-Portfolio'],HAR_All=X['HAR-All'],**{'weights_'+n:np.array(v) for n,v in weights.items()})
    dump(R/'checks/prediction_freeze.json',dict(evaluation_truth_joined=False,files={n:sha(R/n) for n in ['tables/predictions_before_truth.csv','tables/computed_allocations.csv','tables/past_features.npz','checks/fitted_models.json']},data_sha256=sha(R/'tables/observed_factor_returns.csv'),sample=dict(first=str(d.index.min().date()),last=str(d.index.max().date()),daily_rows=len(d),months=len(frame),fit=int(fit.sum()),development=int(dev.sum()),evaluation=int((frame.role=='evaluation').sum()))))
    print(json.dumps({'predictions_frozen':True,'sample':json.loads((R/'checks/prediction_freeze.json').read_text())['sample']}))

def boot(n,block):
    rg=np.random.default_rng(11062026);starts=rg.integers(n,size=(4999,(n+block-1)//block));return ((starts[:,:,None]+np.arange(block))%n).reshape(4999,-1)[:,:n]
def contrast(d,refmean,ii,**meta):
    mu=float(d.mean());b=d[ii].mean(1);null=(d-mu)[ii].mean(1);sd=float(d.std(ddof=1))
    return dict(**meta,n=len(d),mean_difference=mu,paired_SD=sd,CI_low=float(2*mu-np.quantile(b,.975)),CI_high=float(2*mu-np.quantile(b,.025)),relative_difference=mu/refmean,paired_dz=mu/sd if sd else 0.,p_raw=float((1+np.sum(abs(null)>=abs(mu)))/5000))
def holm(a):
    last=0.
    for j,i in enumerate(np.argsort([x['p_raw'] for x in a])):last=max(last,min(1.,(len(a)-j)*a[i]['p_raw']));a[i]['p_holm']=last
    return a

def score():
    guard();fr=json.loads((R/'checks/prediction_freeze.json').read_text())
    for p,h in fr['files'].items():assert sha(R/p)==h,p
    d=panel();a=d.to_numpy();months=d.index.to_period('M');frame=pd.read_csv(R/'tables/predictions_before_truth.csv');w=np.load(R/'tables/past_features.npz');truth={n:[] for n in ['Fixed','Performance','Permuted']}
    for i,row in frame.iterrows():
        future=a[months==pd.Period(row.future_month)]
        for mode in truth:truth[mode].append(float(np.mean((future@w['weights_'+mode][i])**2)))
    for mode,y in truth.items():frame['realized_'+mode]=y
    frame.to_csv(R/'tables/predictions_scored.csv',index=False);ev=(frame.role=='evaluation').to_numpy();evalframe=frame[ev];n=ev.sum();summ=[]
    for name in ['FullCov','Diagonal','HAR-Portfolio','HAR-All']:
        losses=qlike(frame.realized_Fixed.to_numpy()[ev],frame[name].to_numpy()[ev]);summ.append(dict(model=name,n=int(n),QLIKE=float(losses.mean()),QLIKE_SD=float(losses.std(ddof=1))))
    pd.DataFrame(summ).to_csv(R/'tables/forecast_scores.csv',index=False)
    allocation=pd.read_csv(R/'tables/computed_allocations.csv');hhi={mode:allocation[allocation['mode']==mode].HHI.to_numpy()[ev] for mode in ['Fixed','Performance','Permuted']};results=[]
    for block in [3,6]:
        ii=boot(n,block);family=[]
        for model,reference in [('FullCov','Diagonal'),('FullCov','HAR-All')]:
            m=qlike(evalframe.realized_Fixed.to_numpy(),evalframe[model].to_numpy());ref=qlike(evalframe.realized_Fixed.to_numpy(),evalframe[reference].to_numpy());family.append(contrast(m-ref,float(ref.mean()),ii,model=model,reference=reference,metric='QLIKE',block_months=block))
        for ref in ['Fixed','Permuted']:
            m=evalframe.realized_Performance.to_numpy();b=evalframe['realized_'+ref].to_numpy();family.append(contrast(m-b,float(b.mean()),ii,model='Performance',reference=ref,metric='realized_risk',block_months=block))
            family.append(contrast(hhi['Performance']-hhi[ref],float(hhi[ref].mean()),ii,model='Performance',reference=ref,metric='held_HHI',block_months=block))
        results+=holm(family)
    pd.DataFrame(results).to_csv(R/'tables/primary_contrasts.csv',index=False)
    descript=dict(evaluation_months=int(n),first_month=str(evalframe.future_month.iloc[0]),last_month=str(evalframe.future_month.iloc[-1]),negative_cross_term_months=int((evalframe.cross_term<0).sum()),positive_cross_term_months=int((evalframe.cross_term>0).sum()),median_full_over_diagonal=float(evalframe.full_over_diagonal.median()),min_full_over_diagonal=float(evalframe.full_over_diagonal.min()),max_full_over_diagonal=float(evalframe.full_over_diagonal.max()),median_effective_corr_modes=float(evalframe.effective_corr_modes.median()),min_effective_corr_modes=float(evalframe.effective_corr_modes.min()),max_effective_corr_modes=float(evalframe.effective_corr_modes.max()),HHI_means={k:float(v.mean()) for k,v in hhi.items()},RV_means={k:float(np.array(truth[k])[ev].mean()) for k in truth})
    summary=dict(status='completed',data_scope='observed research-factor portfolio returns; allocations and risks computed, no actual institutional flows or market-impact identification',sample=fr['sample'],descriptive=descript,forecast_scores=summ,primary=[x for x in results if x['block_months']==3],sensitivity=[x for x in results if x['block_months']==6],no_prospective_claim=True,no_actual_quant_attribution=True)
    dump(R/'results_summary.json',summary);print(json.dumps(summary,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['freeze','download','predict','score']);args=p.parse_args();{'freeze':freeze,'download':download,'predict':build_predictions,'score':score}[args.command]()
