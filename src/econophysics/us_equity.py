"""Causal US-panel risk estimates and fixed-capital strategy P&L research controls."""
from pathlib import Path
import csv,datetime as dt
import numpy as np
from scipy.cluster.hierarchy import linkage,leaves_list
from scipy.spatial.distance import squareform
from scipy.optimize import minimize
from sklearn.covariance import LedoitWolf
import exchange_calendars as xcals


def write_csv(path,rows):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if not rows:raise ValueError('Refuse empty evidence table '+str(path))
    names=list(dict.fromkeys(k for row in rows for k in row))
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=names);w.writeheader();w.writerows(rows)


def load_panel(root,cfg):
    rows=[]
    for name in ['historical','confirmation']:
        p=Path(root)/f'data/processed/us_equity_v1/{name}.csv'
        if p.exists():rows.extend(csv.DictReader(p.open()))
    symbols=cfg['network_assets']+cfg['context_assets'];dates=sorted(set(r['date'] for r in rows));lookup={(r['date'],r['symbol']):r for r in rows}
    if len(lookup)!=len(rows):raise ValueError('Duplicated panel cells')
    price=np.array([[float(lookup[d,s]['adjusted_close']) for s in symbols] for d in dates]);r=price[1:]/price[:-1]-1
    if not np.isfinite(r).all():raise ValueError('Nonfinite returns')
    return np.array(dates[1:]),r,price[1:],symbols


def correlation(cov):
    sd=np.sqrt(np.diag(cov));out=cov/np.outer(sd,sd)
    if not np.isfinite(out).all():raise ValueError('Degenerate covariance')
    return np.clip((out+out.T)/2,-1,1)


def covariance_estimates(past,cfg,fixed):
    out={}
    for length in cfg['risk_controls']['lookbacks']:
        x=past[-length:];s=np.cov(x,rowvar=False,ddof=1);sd=np.sqrt(np.diag(s));out[f'Diagonal-{length}']=np.diag(np.diag(s));out[f'FixedCorrelation-{length}']=fixed*np.outer(sd,sd);out[f'Sample-{length}']=s;out[f'LedoitWolf-{length}']=LedoitWolf().fit(x).covariance_
        for decay in cfg['risk_controls']['ewma_decays']:
            weight=decay**np.arange(len(x)-1,-1,-1);weight/=weight.sum();out[f'EWMA-{length}-{decay}']=x.T@(weight[:,None]*x)
    return out


def daily_risk(dates,r,cfg):
    n=len(cfg['network_assets']);x=r[:,:n];w=np.ones(n)/n;basket=x@w;train=(dates>=cfg['splits']['train'][0])&(dates<cfg['splits']['train'][1]);fixed=np.corrcoef(x[train],rowvar=False);daily=[];matrices={};features={}
    # Fixed training correlation is not used for origins inside its own estimation period.
    # Train-period calibration samples only need the selected dynamic strong reference.
    for i in range(126,len(dates)):
        covs=covariance_estimates(x[:i+1],cfg,fixed);matrices[i]=covs;s=covs['Sample-63'];c=correlation(s);e=np.linalg.eigvalsh(c);neff=e.sum()**2/(e@e);q=basket[i-62:i+1]**2
        feat=np.array([np.log(np.var(basket[i-20:i+1],ddof=1)/np.var(basket[i-125:i+1],ddof=1)),float(q[basket[i-62:i+1]<0].sum()/q.sum()),float(q.max()/q.sum()),float((c.sum()-n)/(n*(n-1))),float(e[-1]/n),float(neff/n)])
        features[i]=feat
        total=float(w@s@w);own=float(np.dot(w*w,np.diag(s)));row={'date':str(dates[i]),'origin_index':i,'basket_return':float(basket[i]),'variance_self':own,'variance_collective':total-own,'variance_total':total,'collective_fraction':(total-own)/total,'volatility_ratio_full_to_diagonal':np.sqrt(total/own),'mean_correlation':feat[3],'eigenvalue_share':feat[4],'effective_dimension':neff}
        row.update({name:float(w@cov@w) for name,cov in covs.items()});daily.append(row)
    return daily,matrices,features


def samples(dates,r,cfg,daily,features):
    lookup={row['origin_index']:row for row in daily};basket=r[:,:len(cfg['network_assets'])].mean(1);out=[]
    for split,(start,end) in cfg['splits'].items():
        indices=np.flatnonzero((dates>=start)&(dates<end))
        for offset in range(0,len(indices),5):
            target=indices[offset:offset+5]
            if len(target)<5 or target[0]-1 not in lookup:continue
            origin=int(target[0]-1);row={'split':split,'origin_date':str(dates[origin]),'target_start':str(dates[target[0]]),'target_end':str(dates[target[-1]]),'origin_index':origin,'target':float(np.mean(basket[target]**2))}
            row.update({f'x{k}':float(v) for k,v in enumerate(features[origin])});row.update({k:v for k,v in lookup[origin].items() if k.startswith(('Diagonal-','FixedCorrelation-','Sample-','LedoitWolf-','EWMA-'))});out.append(row)
    return out


def qlike(y,v):
    y=np.asarray(y);v=np.asarray(v)
    if not np.all(y>0) or not np.all(v>0):raise ValueError('Positive second-moment scores required')
    ratio=y/v;return ratio-np.log(ratio)-1


def hrp(cov):
    c=correlation(cov);d=np.sqrt(np.maximum(0.,(1-c)/2));np.fill_diagonal(d,0);order=leaves_list(linkage(squareform(d,checks=False),method='single'));weights=np.ones(len(cov));clusters=[order.tolist()]
    def cluster_variance(indices):
        sub=cov[np.ix_(indices,indices)];iv=1/np.diag(sub);iv/=iv.sum();return float(iv@sub@iv)
    while clusters:
        next_clusters=[]
        for cluster in clusters:
            if len(cluster)<2:continue
            left,right=cluster[:len(cluster)//2],cluster[len(cluster)//2:];vleft,vright=cluster_variance(left),cluster_variance(right);alpha=vright/(vleft+vright);weights[left]*=alpha;weights[right]*=1-alpha;next_clusters.extend([left,right])
        clusters=next_clusters
    assert np.all(weights>0) and abs(weights.sum()-1)<1e-12
    return weights


def allocation_weights(pnl,method,cap):
    covariance=LedoitWolf().fit(pnl).covariance_ if method=='LW-MinVariance' else np.cov(pnl,rowvar=False,ddof=1)
    if method=='Equal':return np.ones(pnl.shape[1])/pnl.shape[1]
    if method=='InverseVol':v=1/np.sqrt(np.diag(covariance));return v/v.sum()
    if method=='HRP':return hrp(covariance)
    scale=float(np.trace(covariance)/len(covariance));s=covariance/scale;n=len(s);result=minimize(lambda w:float(w@s@w),np.ones(n)/n,jac=lambda w:2*s@w,bounds=[(0,cap)]*n,constraints={'type':'eq','fun':lambda w:w.sum()-1,'jac':lambda w:np.ones(n)},method='SLSQP',options={'ftol':1e-11,'maxiter':200})
    if not result.success:raise RuntimeError('Min variance failed '+result.message)
    assert abs(result.x.sum()-1)<1e-8 and result.x.min()>-1e-9 and result.x.max()<=cap+1e-8
    return result.x


def weekly_rebalance_dates(dates):
    end=(dt.date.fromisoformat(str(dates[-1]))+dt.timedelta(days=10)).isoformat();cal=xcals.get_calendar('XNYS',start=str(dates[0]),end=end);sessions=[x.date().isoformat() for x in cal.sessions];out=set()
    for a,b in zip(sessions[:-1],sessions[1:]):
        if dt.date.fromisoformat(a).isocalendar()[:2]!=dt.date.fromisoformat(b).isocalendar()[:2]:out.add(a)
    return out


def strategy_library(dates,r,price,cfg):
    n=len(cfg['network_assets']);p=price[:,:n]/price[0,:n];x=r[:,:n];recipes=[(family,length) for family,lengths in cfg['strategy_library']['families'].items() for length in lengths];names=[f'{f}-{l}' for f,l in recipes];t=len(dates);k=len(names);units=np.zeros((t,k,n));gross=np.zeros((t,k));turnover=np.zeros((t,k));shorts=np.zeros((t,k));rebalance=weekly_rebalance_dates(dates);signal_indices=np.full(t,-1)
    for i in range(1,t):
        q=units[i-1];gross[i]=q@(p[i]-p[i-1]);shorts[i]=np.maximum(-q*p[i-1],0).sum(1);units[i]=q
        if str(dates[i]) not in rebalance or i<128:continue
        origin=i-1;signal_indices[i]=origin
        for s,(family,length) in enumerate(recipes):
            if family=='Momentum':score=p[origin-cfg['strategy_library']['momentum_skip']]/p[origin-length]-1
            elif family=='Reversal':score=-(p[origin]/p[origin-length]-1)
            else:score=-np.std(x[origin-length+1:origin+1],axis=0,ddof=1)
            order=np.argsort(score,kind='stable');weight=np.zeros(n);weight[order[:3]]=-1/6;weight[order[-3:]]=1/6;new=weight/p[i];turnover[i,s]=np.dot(abs(new-q[s]),p[i]);units[i,s]=new
    costs=cfg['strategy_library']['cost_bps'];borrow=cfg['strategy_library']['borrow_bps_annual']/1e4/252;net={cost:gross-cost/1e4*turnover-borrow*shorts for cost in costs}
    return {'names':names,'price_index':p,'units':units,'gross':gross,'turnover':turnover,'shorts':shorts,'net':net,'signal_indices':signal_indices,'rebalance':rebalance}


def strategy_allocations(dates,lib,cfg):
    t,k,n=lib['units'].shape;window=cfg['allocation']['lookback'];source=lib['net'][cfg['strategy_library']['primary_cost_bps']];output={};borrow=cfg['strategy_library']['borrow_bps_annual']/1e4/252;p=lib['price_index']
    for method in cfg['allocation']['methods']:
        units=np.zeros((t,n));weights=np.zeros((t,k));gross=np.zeros(t);turnover=np.zeros(t);shorts=np.zeros(t);signal_indices=np.full(t,-1)
        for i in range(1,t):
            q=units[i-1];gross[i]=float(q@(p[i]-p[i-1]));shorts[i]=np.maximum(-q*p[i-1],0).sum();units[i]=q;weights[i]=weights[i-1]
            if str(dates[i]) not in lib['rebalance'] or i<128+window+1:continue
            past=source[i-window:i] # Last outcome is i-1; execution is close i.
            a=allocation_weights(past,method,cfg['allocation']['minvar_cap']);new=a@lib['units'][i];turnover[i]=np.dot(abs(new-q),p[i]);units[i]=new;weights[i]=a;signal_indices[i]=i-1
        net={cost:gross-cost/1e4*turnover-borrow*shorts for cost in cfg['strategy_library']['cost_bps']};output[method]={'units':units,'weights':weights,'gross':gross,'turnover':turnover,'shorts':shorts,'net':net,'signal_indices':signal_indices,'gross_exposure':np.sum(abs(units*p),axis=1)}
    return output


def pnl_metrics(pnl):
    pnl=np.asarray(pnl);mean=float(pnl.mean());sd=float(pnl.std(ddof=1));curve=np.r_[0,np.cumsum(pnl)];drawdown=float(np.max(np.maximum.accumulate(curve)-curve))
    return {'days':len(pnl),'cumulative_pnl_pct':100*float(pnl.sum()),'annual_mean_pnl_pct':100*mean*252,'annual_sigma_pnl_pct':100*sd*np.sqrt(252),'sharpe_zero_cash_proxy':mean/sd*np.sqrt(252),'max_additive_drawdown_pct':100*drawdown}


def block_weights(n,length,replicates,rng):
    starts=rng.integers(0,n,(replicates,int(np.ceil(n/length))));indices=((starts[:,:,None]+np.arange(length))%n).reshape(replicates,-1)[:,:n];out=np.zeros((replicates,n),dtype=np.int32);np.add.at(out,(np.repeat(np.arange(replicates),n),indices.ravel()),1);return out


def loss_contrast(a,b,weights):
    a=np.asarray(a);b=np.asarray(b);ba=weights@a/len(a);bb=weights@b/len(b);gain=100*(1-ba/bb);difference=ba-bb;p=min(1.,2*min(float(np.mean(difference>=0)),float(np.mean(difference<=0))))
    return {'improvement_pct':100*(1-float(a.mean()/b.mean())),'ci_low':float(np.quantile(gain,.025)),'ci_high':float(np.quantile(gain,.975)),'p_bootstrap_approx':p,'loss_difference':float((a-b).mean()),'n':len(a)}


def holm(rows,pkey='p_bootstrap_approx'):
    order=sorted(range(len(rows)),key=lambda j:rows[j][pkey]);previous=0
    for rank,j in enumerate(order):previous=max(previous,min(1.,(len(rows)-rank)*rows[j][pkey]));rows[j]['p_holm']=previous
    return rows
