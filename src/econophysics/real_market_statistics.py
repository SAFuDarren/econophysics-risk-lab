"""Dependence-aware market statistics; calendar resampling stays outside model fitting."""
import numpy as np
from scipy import optimize,special,stats


MOMENT_NAMES=('n','r','r2','r3','r4','v','v2','v3','rv','r2v','zero_v','zero_r')


def circular_day_weights(days,block_length,replicates,rng):
    starts=rng.integers(0,days,(replicates,int(np.ceil(days/block_length))))
    indices=((starts[:,:,None]+np.arange(block_length))%days).reshape(replicates,-1)[:,:days]
    weights=np.zeros((replicates,days),dtype=np.int32)
    np.add.at(weights,(np.repeat(np.arange(replicates),days),indices.ravel()),1)
    assert np.all(weights.sum(1)==days)
    return weights


def daily_moments(r,v,bars_per_day=288):
    r=np.asarray(r);v=np.asarray(v)
    if len(r)%bars_per_day or r.shape!=v.shape:raise ValueError('complete paired days required')
    columns=np.column_stack([np.ones(len(r)),r,r*r,r**3,r**4,v,v*v,v**3,r*v,r*r*v,v==0,r==0])
    return columns.reshape(-1,bars_per_day,len(MOMENT_NAMES)).sum(1)


def moments_to_statistics(sums):
    sums=np.asarray(sums);n=sums[...,0];m={key:sums[...,i]/n for i,key in enumerate(MOMENT_NAMES) if key!='n'}
    mr,mv=m['r'],m['v'];vr=m['r2']-mr*mr;vv=m['v2']-mv*mv
    c4=m['r4']-4*mr*m['r3']+6*mr*mr*m['r2']-3*mr**4
    cv3=m['v3']-3*mv*m['v2']+2*mv**3
    cross=m['r2v']-2*mr*m['rv']+(2*mr*mr-m['r2'])*mv
    cov=m['rv']-mr*mv
    b=cross/(vr*mv);a=cv3/(vv*mv);delta=b-a
    return {'mean_return':mr,'return_std':np.sqrt(vr),'mean_volume':mv,'volume_cv':np.sqrt(vv)/mv,
            'excess_kurtosis':c4/vr**2-3,'pearson_signed_return_volume':cov/np.sqrt(vr*vv),
            'normalized_squared_coupling':b,'normalized_volume_third':a,'delta':delta,
            'q_joint_implied':delta/(b+delta),'zero_volume_fraction':m['zero_v'],'zero_return_fraction':m['zero_r']}


def percentile_interval(values):
    values=np.asarray(values,dtype=float)
    if not np.isfinite(values).all():raise ValueError('nonfinite bootstrap, no silent filtering')
    return tuple(map(float,np.quantile(values,[.025,.975])))


def weighted_spearman_bootstrap(x,y,day_weights,bars_per_day=288):
    x=np.asarray(x);y=np.asarray(y)
    ux,ix=np.unique(x,return_inverse=True);uy,iy=np.unique(y,return_inverse=True)
    out=[]
    for row in day_weights:
        w=np.repeat(row,bars_per_day).astype(float);total=w.sum()
        wx=np.bincount(ix,weights=w,minlength=len(ux));wy=np.bincount(iy,weights=w,minlength=len(uy))
        rx=(np.cumsum(wx)-.5*wx)[ix]/total-.5;ry=(np.cumsum(wy)-.5*wy)[iy]/total-.5
        denominator=np.sqrt(np.dot(w,rx*rx)*np.dot(w,ry*ry))
        if denominator==0:raise ValueError('degenerate weighted ranks')
        out.append(float(np.dot(w,rx*ry)/denominator))
    return np.array(out)


def pair_sums_by_day(x,lag,bars_per_day=288):
    x=np.asarray(x);days=len(x)//bars_per_day
    if len(x)%bars_per_day or not 0<lag<len(x):raise ValueError('invalid lag or incomplete days')
    a,b=x[lag:],x[:-lag];end_day=np.arange(lag,len(x))//bars_per_day
    cols=[np.ones(len(a)),a,b,a*a,b*b,a*b]
    return np.column_stack([np.bincount(end_day,weights=v,minlength=days) for v in cols])


def correlation_from_pair_sums(s):
    s=np.asarray(s);n=s[...,0];a=s[...,1]/n;b=s[...,2]/n
    return (s[...,5]/n-a*b)/np.sqrt((s[...,3]/n-a*a)*(s[...,4]/n-b*b))


def scale_sums_by_day(r,k,bars_per_day=288):
    r=np.asarray(r)
    if len(r)%bars_per_day or bars_per_day%k:raise ValueError('UTC complete non-overlapping bins required')
    blocks=r.reshape(-1,bars_per_day//k,k).sum(2)
    return np.column_stack([np.full(len(blocks),blocks.shape[1]),*(np.sum(blocks**j,axis=1) for j in range(1,5))])


def scale_statistics(s,k,base_variance):
    n=s[...,0];mean=s[...,1]/n;var=s[...,2]/n-mean**2
    fourth=s[...,4]/n-4*mean*s[...,3]/n+6*mean**2*s[...,2]/n-3*mean**4
    return {'variance_ratio':var/(k*base_variance),'excess_kurtosis':fourth/var**2-3,'aggregate_std':np.sqrt(var)}


def conditional_bin_sums(x,y,cuts,bars_per_day=288):
    x=np.asarray(x);y=np.asarray(y);groups=np.searchsorted(cuts,x,side='right');days=len(x)//bars_per_day;bins=len(cuts)+1
    index=np.arange(len(x))//bars_per_day*bins+groups
    counts=np.bincount(index,minlength=days*bins).reshape(days,bins)
    sx=np.bincount(index,weights=x,minlength=days*bins).reshape(days,bins)
    sy=np.bincount(index,weights=y,minlength=days*bins).reshape(days,bins)
    return counts,sx,sy


def fit_tail(values,xmin,lognormal_bounds):
    x=np.asarray(values);x=x[x>=xmin]
    if len(x)<30:raise ValueError('too few tail observations')
    alpha=1+len(x)/np.log(x/xmin).sum();rate=1/(x-xmin).mean();logx=np.log(x)
    bounds=[tuple(lognormal_bounds['mu']),tuple(np.log(lognormal_bounds['sigma']))]
    def objective(theta):
        mu,logs=theta;sigma=np.exp(logs);z=(logx-mu)/sigma
        logdensity=-logx-logs-.5*np.log(2*np.pi)-.5*z*z-special.log_ndtr((mu-np.log(xmin))/sigma)
        return -float(logdensity.mean())
    fits=[optimize.minimize(objective,[mu,np.log(s)],method='L-BFGS-B',bounds=bounds) for mu,s in [(np.log(xmin),.5),(np.log(xmin),1.5),(0.,2.)]]
    fit=min(fits,key=lambda r:r.fun)
    if not fit.success:raise RuntimeError('lognormal tail optimization failed: '+fit.message)
    mu,logs=map(float,fit.x);sigma=float(np.exp(logs));boundary=any(abs(v-lo)<1e-4 or abs(v-hi)<1e-4 for v,(lo,hi) in zip(fit.x,bounds))
    return {'Pareto':{'alpha':float(alpha)},'Exponential':{'rate':float(rate)},'Lognormal':{'mu':mu,'sigma':sigma,'boundary':boundary},'tail_count':len(x)}


def tail_logpdf(values,xmin,method,parameters):
    x=np.asarray(values)
    if np.any(x<xmin):raise ValueError('tail logpdf evaluated below threshold')
    if method=='Pareto':
        a=parameters['alpha'];return np.log(a-1)+(a-1)*np.log(xmin)-a*np.log(x)
    if method=='Exponential':
        rate=parameters['rate'];return np.log(rate)-rate*(x-xmin)
    mu,sigma=parameters['mu'],parameters['sigma'];z=(np.log(x)-mu)/sigma
    return -np.log(x)-np.log(sigma)-.5*np.log(2*np.pi)-.5*z*z-special.log_ndtr((mu-np.log(xmin))/sigma)


def tail_cdf(values,xmin,method,parameters):
    x=np.maximum(np.asarray(values),xmin)
    if method=='Pareto':return -np.expm1((1-parameters['alpha'])*np.log(x/xmin))
    if method=='Exponential':return -np.expm1(-parameters['rate']*(x-xmin))
    mu,sigma=parameters['mu'],parameters['sigma']
    logsf=special.log_ndtr((mu-np.log(x))/sigma)-special.log_ndtr((mu-np.log(xmin))/sigma)
    return -np.expm1(logsf)


def ccdf_by_day(values,grid,bars_per_day=288):
    values=np.asarray(values).reshape(-1,bars_per_day)
    return np.array([np.sum(day[:,None]>=np.asarray(grid)[None,:],axis=0) for day in values])


def fixed_tail_calibration(values,xmin,method,parameters,day_weights,bars_per_day=288):
    x=np.asarray(values);tail=x[x>=xmin];grid,counts=np.unique(tail,return_counts=True);cum=np.cumsum(counts)/len(tail);before=cum-counts/len(tail)
    model=tail_cdf(grid,xmin,method,parameters);distance=float(max(np.max(cum-model),np.max(model-before)))
    daily=[]
    for day in x.reshape(-1,bars_per_day):
        part=np.sort(day[day>=xmin]);daily.append(np.searchsorted(part,grid,side='right'))
    daily=np.asarray(daily);n_tail=daily[:,-1];totals=day_weights@n_tail
    if np.any(totals<=0):raise ValueError('bootstrap contains no exceedances')
    boot=(day_weights@daily)/totals[:,None]
    null=np.max(np.abs(boot-cum),axis=1)
    p=(1+np.sum(null>=distance))/(1+len(null))
    return {'ks':distance,'calibration_p_approx':float(p),'tail_count':len(tail),'bootstrap_replicates':len(null)}
