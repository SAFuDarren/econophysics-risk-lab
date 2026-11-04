"""Causal state features, channel shrinkage and Gamma quasi-likelihood forecasts."""
import datetime
import numpy as np
from scipy.stats import spearmanr
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from .forecasting import daily_features


def correlation(x,y):
    x=np.asarray(x);y=np.asarray(y)
    return float(np.corrcoef(x,y)[0,1]) if x.std()>0 and y.std()>0 else 0.


def state_daily(bars):
    result=daily_features(bars)
    assert len(bars)==288*len(result)
    for d,row in enumerate(result):
        part=bars[d*288:(d+1)*288];r=np.array([float(v['return_log']) for v in part]);v=np.array([float(v['volume']) for v in part]);trades=np.array([float(v['trades']) for v in part]);flow=np.array([float(v['signed_taker_volume']) for v in part]);imbalance=np.divide(flow,v,out=np.zeros_like(flow),where=v>0)
        if trades.sum()<=0 or np.dot(flow,flow)<=0:raise ValueError('degenerate trade/flow observation')
        row.update(trades=float(trades.sum()),average_trade=float(v.sum()/trades.sum()),recent4h_rv=float(r[-48:]@r[-48:]),recent4h_volume_share=float(v[-48:].sum()/v.sum()),downside_variance_share=float((r[r<0]**2).sum()/row['rv']),standardized_day_return=float(r.sum()/np.sqrt(row['rv'])),flow_persistence=correlation(imbalance[1:],imbalance[:-1]),activity_persistence=correlation(np.log1p(trades[1:]),np.log1p(trades[:-1])),response_slope=float((r@flow)/(flow@flow)))
    return result


def state_samples(days):
    samples=[]
    for i in range(27,len(days)-1):
        d=days[i];past=days[i-27:i+1];rv28=np.mean([r['rv'] for r in past]);v28=np.mean([r['volume'] for r in past]);n28=np.mean([r['trades'] for r in past]);size28=np.mean([r['average_trade'] for r in past]);v7=np.mean([r['volume'] for r in past[-7:]])
        sample={'origin_date':d['date'],'target_date':days[i+1]['date'],'target_rv':days[i+1]['rv'],'target_day_return':days[i+1]['day_return'],
                'log_rv_1':np.log(d['rv']),'log_rv_7':np.log(np.mean([r['rv'] for r in past[-7:]])),'log_rv_28':np.log(rv28),'log_recent4h_rv':np.log(d['recent4h_rv']),
                'log_volume':np.log(d['volume']),'log_relative_volume':np.log(d['volume']/v7),'log_relative_volume28':np.log(d['volume']/v28),'log_relative_trades28':np.log(d['trades']/n28),'log_relative_average_trade28':np.log(d['average_trade']/size28),'flow_response_proxy':np.arcsinh(d['response_slope']*v28/np.sqrt(rv28))}
        for key in ['downside_variance_share','log_quarticity_ratio','max_variance_share','standardized_day_return','recent4h_volume_share','absolute_taker_imbalance','flow_persistence','activity_persistence','rank_abs_volume','normalized_squared_coupling']:sample[key]=d[key]
        samples.append({k:float(v) if isinstance(v,(np.floating,np.integer)) else v for k,v in sample.items()})
    return samples


class ChannelRegressor:
    """Convex Gamma QLIKE with unpenalized intercept and separate channel penalties."""
    def __init__(self,kind='gamma',return_penalty=10.,volume_penalty='off',return_dim=8):
        self.kind=kind;self.return_penalty=return_penalty;self.volume_penalty=volume_penalty;self.return_dim=return_dim
    def fit(self,x,y):
        x=np.asarray(x,dtype=float);y=np.asarray(y,dtype=float)
        self.used_dim=self.return_dim if self.volume_penalty=='off' else x.shape[1];x=x[:,:self.used_dim]
        if not np.all(np.isfinite(x)) or not np.all(y>0):raise ValueError('invalid features/target')
        self.scaler=StandardScaler().fit(x);z=self.scaler.transform(x);self.target_scale=float(y.mean());self.iterations=0
        if self.kind=='log':
            self.target_mean=float(np.log(y).mean());self.model=Ridge(alpha=self.return_penalty,fit_intercept=False).fit(z,np.log(y)-self.target_mean);return self
        design=np.c_[np.ones(len(z)),z];penalty=np.r_[0.,np.full(min(self.return_dim,self.used_dim),self.return_penalty),np.full(max(0,self.used_dim-self.return_dim),float(self.volume_penalty) if self.volume_penalty!='off' else self.return_penalty)];logy=np.log(y/self.target_scale);b=np.zeros(design.shape[1])
        def objective(beta):
            error=logy-design@beta
            with np.errstate(over='ignore',invalid='ignore'):
                return float(np.sum(np.expm1(error)-error)+.5*np.dot(penalty*beta,beta))
        old=objective(b)
        for iteration in range(100):
            ratio=np.exp(logy-design@b);gradient=design.T@(1-ratio)+penalty*b;hessian=design.T@(ratio[:,None]*design)+np.diag(penalty);step=np.linalg.solve(hessian,gradient);decrement=float(gradient@step)
            if decrement<1e-10 or np.max(np.abs(gradient))/len(y)<1e-9:break
            rate=1.
            while rate>2**-35:
                candidate=b-rate*step;value=objective(candidate)
                if np.isfinite(value) and value<=old-1e-4*rate*decrement:break
                rate*=.5
            if rate<=2**-35:
                if decrement<1e-7:break
                raise RuntimeError('Gamma Newton line search failed')
            b=candidate;old=value
        self.coef=b;self.iterations=iteration+1;self.objective=old;self.gradient_per_sample=float(np.max(np.abs(design.T@(1-np.exp(logy-design@b))+penalty*b))/len(y))
        if self.gradient_per_sample>1e-5:raise RuntimeError('Gamma solver did not converge')
        return self
    def predict_log(self,x):
        z=self.scaler.transform(np.asarray(x)[:,:self.used_dim])
        if self.kind=='log':return self.target_mean+self.model.predict(z)
        return np.log(self.target_scale)+self.coef[0]+z@self.coef[1:]


def walk_forward(samples,feature_names,kind,alpha,beta,start,end,adaptive,window=365,min_targets=250):
    dates=np.array([r['target_date'] for r in samples]);x=np.array([[r[k] for k in feature_names] for r in samples]);y=np.array([r['target_rv'] for r in samples]);selected=np.flatnonzero((dates>=start)&(dates<end));pred=[];records=[];current=None
    for counter,index in enumerate(selected):
        if current is None or (adaptive and counter%7==0):
            cutoff=dates[index];lower=(datetime.date.fromisoformat(cutoff)-datetime.timedelta(days=window)).isoformat();train=(dates<cutoff)&(dates>=lower)
            if train.sum()<min_targets:raise ValueError('insufficient causal training targets')
            current=ChannelRegressor(kind,alpha,beta,return_dim=3 if len(feature_names)==3 else 8).fit(x[train],y[train]);records.append({'refit_target_date':cutoff,'training_first_target':str(dates[train][0]),'training_last_target':str(dates[train][-1]),'training_targets':int(train.sum()),'used_dim':current.used_dim,'solver_iterations':current.iterations,'solver_gradient_per_sample':getattr(current,'gradient_per_sample',None),'return_penalty':alpha,'volume_penalty':beta})
        pred.append(float(current.predict_log(x[index:index+1])[0]))
    return selected,np.array(pred),records
