"""Covariance-matched innovation laws and past-only tail forecasts.

The herding factor loading is a declared observation extension, not causal
identification of a financial-market network.
"""
from dataclasses import dataclass
import hashlib, json, math, random
import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.special import gammaln
from scipy.stats import norm
from sklearn.covariance import LedoitWolf
from .model import er_edges, components


def seed_for(seed, label):
    return int.from_bytes(hashlib.sha256(f'{seed}:{label}'.encode()).digest()[:8],'big')


def matrix_root(cov, inverse=False):
    eig, vec = np.linalg.eigh(cov)
    if eig.min() <= 0: raise ValueError('Positive definite covariance required')
    return (vec*(eig**(-.5 if inverse else .5)))@vec.T


def whiten(x):
    x=np.asarray(x,float);x=x-x.mean(0)
    return x@matrix_root(x.T@x/len(x),inverse=True)


def standardize(h):
    h=np.asarray(h,float);h=h-h.mean()
    return h/np.sqrt(np.mean(h*h))


def orthogonal_gaussian(h, seed, dim=9):
    rng=np.random.default_rng(seed);z=rng.normal(size=(len(h),dim))
    z-=z.mean(0);z-=np.outer(h,h@z/len(h))
    return whiten(z)


def cluster_pool(cfg,rho,q,seed):
    n=cfg['herding']['n'];graphs=cfg['herding']['graphs_per_rho'];actions=cfg['herding']['actions_per_graph']
    graph_rng=random.Random(seed_for(seed,f'graphs/{rho}'))
    act_rng=np.random.default_rng(seed_for(seed,f'actions/{rho}/{q}'))
    draws=[];moments=[]
    for _ in range(graphs):
        sizes=np.array([len(c) for c in components(n,er_edges(n,rho/(n-1),graph_rng))])
        uniforms=act_rng.random((actions,len(sizes)))
        signs=(uniforms<q/2).astype(np.int8)-(uniforms>=1-q/2).astype(np.int8)
        draws.append(signs@sizes);moments.append([sum(sizes*sizes),sum(sizes**4),max(sizes)])
    raw=np.concatenate(draws).astype(float)
    h=standardize(np.r_[raw,-raw])
    return h,{'rho':rho,'q':q,'graphs':graphs,'actions_per_graph':actions,'mean_s2':float(np.mean(np.array(moments)[:,0])),'mean_s4':float(np.mean(np.array(moments)[:,1])),'mean_largest':float(np.mean(np.array(moments)[:,2])),'raw_variance':float(np.var(raw)),'q_mean_s2':q*float(np.mean(np.array(moments)[:,0])),'zero_frequency':float(np.mean(raw==0))}


@dataclass
class Law:
    name: str
    family: str
    params: dict
    h: np.ndarray|None
    z: np.ndarray
    log_density: np.ndarray


def density_grid(pool,kappa,grid):
    step=grid[1]-grid[0]
    edges=np.r_[grid-step/2,grid[-1]+step/2]
    counts=np.histogram(np.sqrt(kappa)*pool,bins=edges)[0].astype(float)
    density=gaussian_filter1d(counts/len(pool)/step,np.sqrt(1-kappa)/step,mode='constant',truncate=10)
    density/=density.sum()*step
    return np.log(np.maximum(density,1e-300))


def build_laws(cfg,draws=None,seed_offset=0):
    seed=cfg['seed']+seed_offset;m=draws or cfg['forecast_draws'];grid=np.arange(-45,45.0001,.025)
    g=whiten(np.random.default_rng(seed_for(seed,'baseGaussian')).normal(size=(m,9)))
    laws=[Law('Gaussian','Gaussian',{'kappa':0.},None,g,norm.logpdf(grid))];diagnostics=[]
    pools={}
    def add(family,name,params,pool,logd=None):
        k=params['kappa'];rng=np.random.default_rng(seed_for(seed,'draw/'+name))
        h=standardize(pool[rng.integers(0,len(pool),m)])
        z=orthogonal_gaussian(h,seed_for(seed,'residual/'+name))
        laws.append(Law(name,family,params,h,z,density_grid(pool,k,grid) if logd is None else logd))
    for rho in cfg['herding']['rho']:
        for q in cfg['herding']['activity_q']:
            pool,diag=cluster_pool(cfg,rho,q,seed);pools[rho,q]=pool;diagnostics.append(diag)
            for k in cfg['herding']['factor_variance_fraction']:
                add('Herding',f'H-r{rho}-q{q}-k{k}',{'rho':rho,'q':q,'kappa':k},pool)
    for nu in cfg['factor_student_df']:
        pool=standardize(np.random.default_rng(seed_for(seed,f'tPool/{nu}')).standard_t(nu,262144))
        for k in cfg['herding']['factor_variance_fraction']:
            add('FactorT',f'FT-nu{nu}-k{k}',{'nu':nu,'kappa':k},pool)
    for p in cfg['mixture_p']:
        for ratio in cfg['mixture_sd_ratio']:
            rng=np.random.default_rng(seed_for(seed,f'mixPool/{p}/{ratio}'))
            sd=np.where(rng.random(262144)<p,ratio,1.)/np.sqrt((1-p)+p*ratio**2)
            pool=standardize(rng.normal(size=len(sd))*sd)
            for k in cfg['herding']['factor_variance_fraction']:
                scale=np.sqrt((1-p)+p*ratio**2)
                low=np.sqrt(1-k+k/scale**2);high=np.sqrt(1-k+k*ratio**2/scale**2)
                logd=np.log(np.maximum((1-p)*norm.pdf(grid,scale=low)+p*norm.pdf(grid,scale=high),1e-300))
                add('FactorMixture',f'FM-p{p}-r{ratio}-k{k}',{'p':p,'ratio':ratio,'kappa':k},pool,logd)
    for nu in cfg['student_df']:
        rng=np.random.default_rng(seed_for(seed,f'elliptic/{nu}'))
        z=whiten(rng.normal(size=(m,9))*np.sqrt((nu-2)/rng.chisquare(nu,size=m))[:,None])
        laws.append(Law(f'T-nu{nu}','StudentT',{'nu':nu,'kappa':0.},None,z,np.zeros(len(grid))))
    return laws,grid,diagnostics,pools


def law_choices(laws,grid,past_z,past_h):
    scores=[]
    for law in laws:
        if law.family=='StudentT':
            nu=law.params['nu'];n=past_z.shape[1];radius=np.sum(past_z*past_z,1)
            logd=gammaln((nu+n)/2)-gammaln(nu/2)-n/2*np.log((nu-2)*np.pi)-(nu+n)/2*np.log1p(radius/(nu-2))
        else:logd=np.interp(past_h,grid,law.log_density,left=law.log_density[0],right=law.log_density[-1])
        scores.append(-float(np.mean(logd)))
    result={}
    for family in ['Gaussian','StudentT','FactorT','FactorMixture','Herding','HerdingSubcritical','HerdingCritical']:
        allowed=[j for j,law in enumerate(laws) if law.family==family or law.family=='Gaussian']
        if family in ['HerdingSubcritical','HerdingCritical']:
            target=.6 if family=='HerdingSubcritical' else 1.
            allowed=[j for j,law in enumerate(laws) if law.family=='Gaussian' or (law.family=='Herding' and law.params['rho']==target)]
        # StudentT full-vector scores and Gaussian full-vector score need the same
        # orthogonal Gaussian terms; scalar candidates omit only that common term.
        if family=='StudentT':
            gaussian_nll=float(np.mean(.5*np.sum(past_z*past_z,1)+4.5*np.log(2*np.pi)))
            result[family]=min(allowed,key=lambda j:(gaussian_nll if laws[j].family=='Gaussian' else scores[j],laws[j].name))
        else:result[family]=min(allowed,key=lambda j:(scores[j],laws[j].name))
    return result,scores


def factor_scenarios(cov,law):
    root=matrix_root(cov);x=law.z@root
    if law.h is not None:
        eig,vec=np.linalg.eigh(cov);u=vec[:,-1];u=u*(1 if u.sum()>=0 else -1)
        k=law.params['kappa'];g=law.z@u
        x+=np.outer(np.sqrt(k)*law.h-(1-np.sqrt(1-k))*g,np.sqrt(eig[-1])*u)
    return x


def empirical_scenarios(cov,past_z,past_h,mode,seed):
    if mode=='FHS':return whiten(past_z)@matrix_root(cov)
    h=standardize(past_h);z=orthogonal_gaussian(h,seed)
    return factor_scenarios(cov,Law('emp','emp',{'kappa':1.},h,z,np.array([])))


def forecast_statistics(samples,cov,actual=None):
    w=np.ones(9)/9;sd=float(np.sqrt(w@cov@w));basket=samples.mean(1)/sd
    counts=np.sum(samples < -2*np.sqrt(np.diag(cov)),axis=1)
    out={'q05':float(np.quantile(basket,.05)),'q01':float(np.quantile(basket,.01)),'es05':float(np.mean(basket[basket<=np.quantile(basket,.05)])),'es01':float(np.mean(basket[basket<=np.quantile(basket,.01)])),'p_co3':float(np.mean(counts>=3)),'p_co5':float(np.mean(counts>=5)),'p_co3_smoothed':float((np.sum(counts>=3)+.5)/(len(samples)+1)),'portfolio_sigma':sd,'scenario_count':len(samples)}
    cov_mc=(samples-samples.mean(0)).T@(samples-samples.mean(0))/len(samples)
    out['covariance_relative_error']=float(np.linalg.norm(cov_mc-cov)/np.linalg.norm(cov))
    if actual is not None:
        y=float(np.mean(actual)/sd);event=int(np.sum(actual < -2*np.sqrt(np.diag(cov)))>=3)
        out.update({'y':y,'actual_basket_return':float(np.mean(actual)),'co3':event,'co_count':int(np.sum(actual < -2*np.sqrt(np.diag(cov))))})
        out['pinball05']=float((.05-(y<out['q05']))*(y-out['q05']))
        out['pinball01']=float((.01-(y<out['q01']))*(y-out['q01']))
        out['fz05']=float(-(y<=out['q05'])*(out['q05']-y)/(.05*out['es05'])+out['q05']/out['es05']+np.log(-out['es05'])-1)
        out['brier']=(out['p_co3']-event)**2
        p=out['p_co3_smoothed'];out['log_score']=-event*np.log(p)-(1-event)*np.log1p(-p)
        out['hit05']=int(y<out['q05']);out['hit01']=int(y<out['q01'])
    return out


def covariance_series(r,method):
    t,n=r.shape;covs=np.zeros((t,n,n));z=np.full((t,n),np.nan);h=np.full(t,np.nan)
    for i in range(126,t):
        past=r[i-126:i]
        if method.startswith('EWMA'):
            weights=.94**np.arange(125,-1,-1);weights/=weights.sum();cov=past.T@(past*weights[:,None])
        elif method=='LedoitWolf-126':cov=LedoitWolf().fit(past).covariance_
        else:raise ValueError(method)
        cov=(cov+cov.T)/2
        eig,vec=np.linalg.eigh(cov)
        if eig.min()<=0:raise ValueError('Nonpositive market covariance')
        u=vec[:,-1]*(1 if vec[:,-1].sum()>=0 else -1)
        covs[i]=cov;z[i]=r[i]@matrix_root(cov,inverse=True);h[i]=z[i]@u
    return covs,z,h


def evaluate_panel(dates,r,method,cfg,laws,grid,periods=None,sensitivity=False):
    covs,z,h=covariance_series(r,method);rows=[];choices_rows=[];window=cfg['shape_window'];choices=None;last_fit=-10**9
    periods=periods or cfg['splits'];start=next(i for i,d in enumerate(dates) if d>=min(v[0] for v in periods.values()))
    for i in range(max(126+window,start),len(r)):
        period=next((k for k,(lo,hi) in periods.items() if lo<=dates[i]<hi),None)
        if period is None:continue
        if choices is None or i-last_fit>=cfg['refit_sessions']:
            choices,scores=law_choices(laws,grid,z[i-window:i],h[i-window:i]);last_fit=i
            for model,j in choices.items():choices_rows.append({'date':str(dates[i]),'covariance':method,'method':model,'law':laws[j].name,'fit_end':str(dates[i-1]),'fit_start':str(dates[i-window]),'fitted_scalar_nll':scores[j],**laws[j].params})
        if sensitivity and (i-start)%cfg['refit_sessions']!=0:continue
        cache={};c=covs[i]
        for model in cfg['methods']:
            if model in ['FHS','FactorEmpirical']:
                samples=empirical_scenarios(c,z[i-window:i],h[i-window:i],model,seed_for(cfg['seed'],'empiricalResidual'))
                lawname='Past504';params={}
            else:
                j=choices[model];law=laws[j]
                if j not in cache:cache[j]=factor_scenarios(c,law)
                samples=cache[j];lawname=law.name;params=law.params
            stat=forecast_statistics(samples,c,r[i]);rows.append({'date':str(dates[i]),'period':period,'covariance':method,'method':model,'law':lawname,'fit_end':str(dates[last_fit-1]),**stat,**params})
    return rows,choices_rows,{'covariances':covs,'z':z,'h':h}
