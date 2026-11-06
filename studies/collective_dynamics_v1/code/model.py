from pathlib import Path
import numpy as np
from scipy.optimize import least_squares

R=Path(__file__).resolve().parents[1]
BUDGETS=[30,60,120,240]
PENALTIES=[.1,10.,1000.]
PRESSURE_MODELS=['MeanFieldFast','MeanFieldMemory','MeanFieldCrossScale','PressureAR']

def load():
    with np.load(R/'inputs/macro_observables.npz') as z:return {k:z[k] for k in z.files}

def rolling(x,k):
    c=np.r_[0.,np.cumsum(x)];i=np.arange(len(x));s=np.maximum(0,i-k+1)
    return (c[i+1]-c[s])/(i-s+1)

def ema(x,k):
    out=np.empty(len(x));out[0]=x[0];a=1-np.exp(-1/k)
    for i in range(1,len(x)):out[i]=(1-a)*out[i-1]+a*x[i]
    return out

def summaries(data):
    r=data['returns'];v=data['volume'];f=data['flow'];k=data['trades'];p=f/v;m=f.sum(1)/v.sum(1);v2=np.mean(v*v,axis=1)
    return dict(dates=data['dates'],rv=np.sum(r*r,axis=1),V=v.sum(1),K=k.sum(1),Vmean=v.mean(1),V2=v2,F=f.mean(1),F2=np.mean(f*f,axis=1),r=r.mean(1),rF=np.mean(r*f,axis=1),r2=np.mean(r*r,axis=1),pressure=m,
        pressureDispersion=np.sum(v*v*(p-m[:,None])**2,axis=1)/np.sum(v*v,axis=1))

def window(a,start,end):
    w={k:x[start:end] for k,x in a.items()};m=w['pressure'];s=ema(m,7);adapt=ema(m,28)
    w['slow']=s;w['adaptation']=adapt
    w['ReturnHAR']=np.column_stack([np.log(rolling(w['rv'],k)) for k in [1,7,28]])
    w['MacroStat']=np.column_stack([w['ReturnHAR'],*[np.log(rolling(w['V'],k)) for k in [1,7]],*[np.log(rolling(w['K'],k)) for k in [1,7]],m,s,adapt])
    meanf=w['F'].mean();meanr=w['r'].mean();varf=w['F2'].mean()-meanf**2
    beta=max(0.,float((w['rF'].mean()-meanf*meanr)/max(varf,1e-20)));alpha=float(meanr-beta*meanf)
    eta=np.maximum(w['r2']-2*alpha*w['r']-2*beta*w['rF']+alpha**2+2*alpha*beta*w['F']+beta**2*w['F2'],1e-16)
    w['alpha']=alpha;w['beta']=beta;w['eta7']=rolling(eta,7)
    w['V2forecast']=rolling(w['V2'],7);w['Vforecast']=rolling(w['Vmean'],7);w['dispersion7']=rolling(w['pressureDispersion'],7)
    return w

class GammaRidge:
    def fit(self,x,y,penalty):
        self.mean=x.mean(0);self.sd=x.std(0);self.sd[self.sd<1e-14]=1.;z=(x-self.mean)/self.sd;D=np.c_[np.ones(len(x)),z];self.scale=float(y.mean());ly=np.log(y/self.scale);pen=np.r_[0.,np.full(x.shape[1],penalty)];b=np.zeros(D.shape[1])
        def objective(p):
            with np.errstate(over='ignore'):e=ly-D@p;return float(np.sum(np.expm1(e)-e)+.5*np.dot(pen*p,p))
        old=objective(b)
        for it in range(100):
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
        self.b=b;self.gradient=float(np.max(abs(D.T@(1-np.exp(ly-D@b))+pen*b))/len(y));self.iterations=it+1
        if self.gradient>1e-5:raise ArithmeticError('Gamma gradient '+str(self.gradient))
        return self
    def predict(self,x):return self.scale*np.exp(self.b[0]+((x-self.mean)/self.sd)@self.b[1:])

def pressure_fit(w,model,penalty):
    m=w['pressure'];s=w['slow'];a=w['adaptation'];y=m[1:];ysd=max(float(y.std()),1e-4)
    if model=='MeanFieldFast':X=np.c_[np.ones(len(m)),m]
    elif model=='MeanFieldMemory':X=np.c_[np.ones(len(m)),m,-a]
    else:X=np.c_[np.ones(len(m)),m,s,-a]
    T=X[:-1]
    if model=='PressureAR':
        pp=np.diag(np.r_[0.,np.full(T.shape[1]-1,penalty*ysd**2)]);theta=np.linalg.solve(T.T@T+pp,T.T@y);pred=np.clip(X@theta,-.99,.99);grad=0.;iters=1;success=True
    else:
        def residual(theta):return np.r_[(np.tanh(T@theta)-y)/ysd,np.sqrt(penalty)*theta[1:]]
        def jacobian(theta):
            p=np.tanh(T@theta);reg=np.c_[np.zeros(T.shape[1]-1),np.eye(T.shape[1]-1)*np.sqrt(penalty)]
            return np.r_[T*((1-p*p)/ysd)[:,None],reg]
        opt=least_squares(residual,np.r_[0.,np.full(T.shape[1]-1,.01)],jac=jacobian,bounds=(np.r_[-1.,np.zeros(T.shape[1]-1)],np.r_[1.,np.full(T.shape[1]-1,6.)]),max_nfev=300,ftol=1e-10,xtol=1e-10,gtol=1e-10)
        theta=opt.x;pred=np.tanh(X@theta);grad=float(opt.optimality);iters=int(opt.nfev);success=bool(opt.success)
        if not success:raise ArithmeticError(model+' pressure fit '+opt.message)
    centred=T[:,1:]-T[:,1:].mean(0);sd=centred.std(0);sd[sd<1e-12]=1;condition=float(np.linalg.cond(np.c_[np.ones(len(T)),centred/sd]))
    return pred,dict(coefficients=theta.tolist(),transition_mse=float(np.mean((y-pred[:-1])**2)),condition=condition,at_upper_bound=int(np.sum(theta[1:]>=5.999)) if model!='PressureAR' else 0,at_zero=int(np.sum(theta[1:]<=1e-7)) if model!='PressureAR' else 0,gradient=grad,iterations=iters,success=success)

def flow_risk(w,meanf,secondf):
    secondf=np.maximum(secondf,meanf**2);varf=np.maximum(secondf-meanf**2,0)
    return 288*((w['alpha']+w['beta']*meanf)**2+w['beta']**2*varf+w['eta7'])

def forecast(w,model,penalty):
    y=w['rv'][1:];meta=dict(alpha=w['alpha'],beta=w['beta'],pressure_condition=0.,at_upper_bound=0,at_zero=0,gradient=0.,iterations=0,transition_mse=0.,flow_scale=1.,risk_scale=1.,coefficients='')
    if model=='Persistence':return float(w['rv'][-1]),meta
    if model in ['ReturnHAR','MacroStat']:
        fit=GammaRidge().fit(w[model][:-1],y,penalty);meta.update(gradient=fit.gradient,iterations=fit.iterations,coefficients=fit.b.tolist());return float(fit.predict(w[model][-1:])[0]),meta
    if model=='DirectFlow':
        means=rolling(w['F'],7);seconds=rolling(w['F2'],7)
    else:
        mhat,diag=pressure_fit(w,model,penalty);raw=w['V2forecast']*(mhat*mhat+w['dispersion7']+diag['transition_mse']);scale=float(np.mean(w['F2'][1:]/np.maximum(raw[:-1],1e-20)));means=w['Vforecast']*mhat;seconds=raw*scale
        meta.update(pressure_condition=diag['condition'],at_upper_bound=diag['at_upper_bound'],at_zero=diag['at_zero'],gradient=diag['gradient'],iterations=diag['iterations'],transition_mse=diag['transition_mse'],flow_scale=scale,coefficients=diag['coefficients'])
    rawrisk=flow_risk(w,means,seconds);scale=float(np.mean(y/rawrisk[:-1]));meta['risk_scale']=scale
    return float(rawrisk[-1]*scale),meta

def losses(y,p):
    d=np.log(y)-np.log(p);return dict(qlike=np.expm1(d)-d,mse=(y-p)**2,log_mse=d*d)
