"""Transparent diagnostic calculations for the offline risk/factor laboratory."""
import numpy as np


def portfolio_risk(cov,weights,eta=1.):
    cov=np.asarray(cov,dtype=float);w=np.asarray(weights,dtype=float)
    if w.sum()<=0 or np.any(w<0) or not 0<=eta<=1:raise ValueError('Nonnegative weights with positive total and eta in [0,1] required')
    w=w/w.sum();own=float(np.dot(w*w,np.diag(cov)));observed=float(w@cov@w);v=own+eta*(observed-own)
    return {'normalized_weights':w.tolist(),'variance_self':own,'variance_full_observed':observed,'variance_counterfactual':v,'annual_vol_diagonal_pct':100*np.sqrt(252*own),'annual_vol_observed_pct':100*np.sqrt(252*observed),'annual_vol_counterfactual_pct':100*np.sqrt(252*v),'volatility_ratio':np.sqrt(v/own),'collective_share':(v-own)/v}


def screen_candidates(corr,turnover,names,threshold=.8):
    order=sorted(range(len(names)),key=lambda j:(turnover[j],names[j]));retained=[];decisions=[]
    for j in order:
        representative=max(retained,key=lambda i:corr[i,j]) if retained else None
        redundant=representative is not None and corr[representative,j]>=threshold
        decisions.append({'strategy':names[j],'index':j,'retained':not redundant,'representative':names[representative] if redundant else '', 'training_correlation':float(corr[representative,j]) if representative is not None else None,'training_turnover':float(turnover[j])})
        if not redundant:retained.append(j)
    return sum(1<<i for i in retained),decisions


def subset_pnl(units,price_index,mask,active,cost_bps,borrow_bps_annual=100):
    selected=[i for i in range(units.shape[1]) if mask&(1<<i)]
    if not selected:raise ValueError('At least one strategy')
    q=units[:,selected].mean(axis=1)*np.asarray(active)[:,None];prev=np.vstack([np.zeros(q.shape[1]),q[:-1]]);delta=np.vstack([np.zeros(price_index.shape[1]),np.diff(price_index,axis=0)]);gross=np.sum(prev*delta,axis=1);turnover=np.sum(abs(q-prev)*price_index,axis=1);short=np.zeros(len(q));short[1:]=np.maximum(-prev[1:]*price_index[:-1],0).sum(1);net=gross-cost_bps/1e4*turnover-borrow_bps_annual/1e4/252*short
    return {'net':net,'gross':gross,'turnover':turnover,'gross_exposure':np.sum(abs(q*price_index),axis=1),'short_exposure':short}


def reconstruction(train,observed,retained,excluded):
    x=np.c_[np.ones(len(train)),train[:,retained]];coef=np.linalg.lstsq(x,train[:,excluded],rcond=None)[0];prediction=np.c_[np.ones(len(observed)),observed[:,retained]]@coef;y=observed[:,excluded];residual=y-prediction;reference=y-train[:,excluded].mean();r2=1-float(np.mean(residual**2)/np.mean(reference**2))
    return {'reconstruction_r2':r2,'residual_annual_mean_pct':float(residual.mean()*252*100),'residual_annual_sigma_pct':float(residual.std(ddof=1)*np.sqrt(252)*100),'coef':coef.tolist()}
