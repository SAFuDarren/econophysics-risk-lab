"""Causal daily features and fixed-origin next-day forecast baselines."""
import datetime
from itertools import groupby
import numpy as np
from scipy.stats import spearmanr
from sklearn.linear_model import Ridge,LogisticRegression
from sklearn.kernel_ridge import KernelRidge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


def daily_features(bars,bars_per_day=288):
    days=[]
    for date,items in groupby(bars,lambda r:r['date_utc']):
        rows=list(items)
        if len(rows)!=bars_per_day:raise ValueError('incomplete UTC day')
        r=np.array([float(x['return_log']) for x in rows]);v=np.array([float(x['volume']) for x in rows]);flow=np.array([float(x['signed_taker_volume']) for x in rows])
        rv=float(r@r);rc=r-r.mean();vc=v-v.mean();variance=float(rc@rc/len(r))
        if rv<=0 or variance<=0 or v.sum()<=0 or v.std()==0:raise ValueError('degenerate daily feature; no silent imputation')
        days.append({'date':date,'rv':rv,'volume':float(v.sum()),'close':float(rows[-1]['close']),'day_return':float(r.sum()),'rank_abs_volume':float(spearmanr(np.abs(r),v).statistic),
                     'normalized_squared_coupling':float(np.mean(rc*rc*vc)/(variance*v.mean())),'absolute_taker_imbalance':float(abs(flow.sum())/v.sum()),
                     'log_quarticity_ratio':float(np.log(len(r)*np.sum(r**4)/(rv*rv))),'max_variance_share':float(np.max(r*r)/rv)})
    for a,b in zip(days,days[1:]):
        if datetime.date.fromisoformat(b['date'])-datetime.date.fromisoformat(a['date'])!=datetime.timedelta(days=1):raise ValueError('daily grid gap')
    return days


def forecast_samples(days):
    result=[]
    for t in range(27,len(days)-1):
        row=days[t];future=days[t+1];past=days[t-27:t+1]
        result.append({'origin_date':row['date'],'target_date':future['date'],'target_rv':future['rv'],'log_rv_1':float(np.log(row['rv'])),
                       'log_rv_7':float(np.log(np.mean([x['rv'] for x in past[-7:]]))),'log_rv_28':float(np.log(np.mean([x['rv'] for x in past]))),
                       'log_volume':float(np.log(row['volume'])),'log_relative_volume':float(np.log(row['volume']/np.mean([x['volume'] for x in past[-7:]]))),
                       **{k:row[k] for k in ['rank_abs_volume','normalized_squared_coupling','absolute_taker_imbalance','log_quarticity_ratio','max_variance_share']}})
    return result


def feature_names(name,groups):
    base=groups['HAR']
    if name in ['HAR','RBF-HAR','Logit-HAR']:return base
    if name in ['HAR+All','RBF-All','Logit-All']:return base+groups['Activity']+groups['Coupling']+groups['Tail']
    return base+groups[name.split('+')[1]]


class LogRegressor:
    def __init__(self,kind,spec):
        estimator=Ridge(alpha=spec['alpha'],fit_intercept=False) if kind=='ridge' else KernelRidge(kernel='rbf',**spec)
        self.pipeline=make_pipeline(StandardScaler(),estimator)
    def fit(self,x,y):
        self.mean=float(np.mean(y));self.pipeline.fit(x,y-self.mean);return self
    def predict(self,x):return self.mean+self.pipeline.predict(x)


def fit_logit(x,y,C):
    return make_pipeline(StandardScaler(),LogisticRegression(C=C,solver='lbfgs',max_iter=4000)).fit(x,y)


def daily_losses(actual_rv,log_prediction):
    actual_rv=np.asarray(actual_rv);log_prediction=np.asarray(log_prediction);difference=np.log(actual_rv)-log_prediction
    result={'log_mse':difference**2,'qlike':np.expm1(difference)-difference,'volatility_mae':100*np.abs(np.sqrt(actual_rv)-np.exp(log_prediction/2))}
    if not all(np.all(np.isfinite(x)) for x in result.values()):raise ValueError('invalid forecast loss')
    return result


def ewma_at_origin(days,alpha):
    value=days[0]['rv'];result={days[0]['date']:value}
    for row in days[1:]:
        value=alpha*row['rv']+(1-alpha)*value;result[row['date']]=value
    return result
