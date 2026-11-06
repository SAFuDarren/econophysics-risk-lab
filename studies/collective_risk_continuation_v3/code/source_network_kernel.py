"""Full stochastic decision-network kernel; distribution-equivalent Python law.

The frozen JavaScript generator is the source of numerical rules. NumPy RNG
paths differ; no bit-identical path claim is made. No teacher state enters an
observable estimator through this module unless its caller explicitly passes it.
"""
from dataclasses import dataclass
import hashlib,copy
import numpy as np

N=48
DEFAULTS=dict(coupling=.55,memory=.75,weighting='heterogeneous',active_probability=.58)

def seed_rng(seed):
    return np.random.default_rng(int.from_bytes(hashlib.sha256(str(seed).encode()).digest()[:16],'little'))

def _topology(rng,n):
    a=np.zeros((n,n),dtype=bool)
    for i in range(n):
        for j in [(i+1)%n,(i+2)%n,int(rng.integers(n))]:
            if i!=j:a[i,j]=a[j,i]=True
    return a

def _weighted_graph(a,w):
    v=a*w[None,:]
    return v/v.sum(1)[:,None]

@dataclass
class NetworkBatch:
    weights:np.ndarray
    wf:np.ndarray
    ws:np.ndarray
    fast:np.ndarray
    slow:np.ndarray
    trace:np.ndarray
    liquidity:np.ndarray
    price:np.ndarray
    last_return:np.ndarray
    rv_ema:np.ndarray
    tick:int
    params:dict

    @classmethod
    def initialize(cls,n,seed,params=None):
        p={**DEFAULTS,**(params or {})}
        if p['weighting'] not in ['heterogeneous','equal']:raise ValueError('weighting')
        rg=seed_rng(str(seed)+'-graph');rs=seed_rng(str(seed)+'-state')
        norm=rg.standard_normal((n,N));w=np.exp(.65*norm) if p['weighting']=='heterogeneous' else np.ones((n,N))
        w/=w.sum(1)[:,None];wf=np.empty((n,N,N));ws=np.empty_like(wf)
        for i in range(n):
            wf[i]=_weighted_graph(_topology(rg,N),w[i]);ws[i]=_weighted_graph(_topology(rg,N),w[i])
        fast=np.where(rs.random((n,N))<.5,-1.,1.);slow=np.where(rs.random((n,N))<.5,-1.,1.)
        return cls(w,wf,ws,fast,slow,np.zeros((n,N)),np.ones(n),np.full(n,100.),np.zeros(n),np.zeros(n),0,p)

    @classmethod
    def from_js_state(cls,state,params=None):
        nodes=state['nodes'];w=np.array([x['weight'] for x in nodes]);graphs=[]
        for key in ['fastGraph','slowGraph']:
            a=np.zeros((N,N),bool)
            for i,neighbors in enumerate(state[key]['neighbors']):a[i,neighbors]=True
            graphs.append(_weighted_graph(a,w)[None])
        return cls(w[None],graphs[0],graphs[1],*[np.array([[x[k] for x in nodes]],float) for k in ['fast','slow','trace']],np.array([state['liquidity']]),np.array([state['price']]),np.zeros(1),np.zeros(1),state['tick'],{**DEFAULTS,**(params or {})})

    def __len__(self):return len(self.weights)

    def subset(self,indices):
        ii=np.asarray(indices,dtype=int)
        return NetworkBatch(*[getattr(self,k)[ii].copy() for k in ['weights','wf','ws','fast','slow','trace','liquidity','price','last_return','rv_ema']],self.tick,copy.deepcopy(self.params))

    def clone(self):return self.subset(np.arange(len(self)))

    def repeat(self,n):
        if len(self)!=1:raise ValueError('repeat needs a single latent state')
        return self.subset(np.zeros(n,dtype=int))

    def _fields(self,dose=0,common_signal=0,signal_loading=0,price_feedback=0,extra_fast=0,extra_slow=0):
        d=np.broadcast_to(np.asarray(dose,float),(len(self),))
        ex=.85*d/(1200+abs(d));mu=self.params['memory'];k=self.params['coupling']
        lf=np.einsum('bij,bj->bi',self.wf,self.fast,optimize=False)
        ls=np.einsum('bij,bj->bi',self.ws,self.slow,optimize=False)
        signal=np.asarray(common_signal,float)
        if signal.ndim<=1:signal=np.broadcast_to(signal,(len(self),))[:,None]
        else:signal=np.broadcast_to(signal,(len(self),N))
        feedback=price_feedback*self.last_return[:,None]
        def field_shape(v):
            v=np.asarray(v,float)
            return np.broadcast_to(v,(len(self),))[:,None] if v.ndim<=1 else np.broadcast_to(v,(len(self),N))
        hf=.72*lf+k*self.slow+.24*mu*self.fast-.95*mu*self.trace+ex[:,None]+signal_loading*signal+feedback+field_shape(extra_fast)
        hs=.65*ls+.55*k*self.fast+.32*mu*self.slow-.35*mu*self.trace+.25*ex[:,None]+.25*signal_loading*signal+.25*feedback+field_shape(extra_slow)
        return np.tanh(1.5*hf),np.tanh(1.5*hs),d

    def activity_probability(self,risk_anchor=None):
        a=np.full(len(self),self.params['active_probability'])
        if risk_anchor is not None:
            if np.any(np.asarray(risk_anchor)<=0):raise ValueError('positive risk anchor required')
            a/=1+np.maximum(0,self.rv_ema/risk_anchor-1)
        return a

    def conditional_moments(self,dose=0,common_signal=0,signal_loading=0,price_feedback=0,risk_anchor=None,extra_fast=0,extra_slow=0,active_probability=None):
        tf,ts,d=self._fields(dose,common_signal,signal_loading,price_feedback,extra_fast,extra_slow)
        a=self.activity_probability(risk_anchor) if active_probability is None else np.broadcast_to(np.asarray(active_probability,float),(len(self),))
        if np.any((a<0)|(a>1)|~np.isfinite(a)):raise ValueError('activity probability outside [0,1]')
        m=d+1200*a*np.sum(self.weights*tf,1)
        var=1200**2*np.sum(self.weights**2*(a[:,None]-a[:,None]**2*tf**2),1)
        return {'mean':m,'variance':var,'second':var+m*m,'fast_mean':tf,'slow_mean':.86*self.slow+.14*ts,'trace_mean':.945*self.trace+.055*tf,'activity_probability':a}

    def step(self,rng,dose=0,common_signal=0,signal_loading=0,price_feedback=0,risk_anchor=None,extra_fast=0,extra_slow=0,active_probability=None):
        tf,ts,d=self._fields(dose,common_signal,signal_loading,price_feedback,extra_fast,extra_slow)
        a=self.activity_probability(risk_anchor) if active_probability is None else np.broadcast_to(np.asarray(active_probability,float),(len(self),))
        if np.any((a<0)|(a>1)|~np.isfinite(a)):raise ValueError('activity probability outside [0,1]')
        # Four uniforms per node plus two independent Gaussian noise channels.
        u=rng.random((len(self),N,4));noise=rng.standard_normal((len(self),2))
        self.fast=np.where(u[:,:,0]<.5*(1+tf),1.,-1.)
        self.slow=np.where(u[:,:,1]<.14,np.where(u[:,:,2]<.5*(1+ts),1.,-1.),self.slow)
        active=u[:,:,3]<a[:,None]
        self.trace=.945*self.trace+.055*self.fast
        V=abs(d)+1200*np.sum(self.weights*active,1)
        F=d+1200*np.sum(self.weights*active*self.fast,1)
        pressure=np.divide(F,V,out=np.zeros_like(F),where=V>0)
        self.liquidity=np.clip(self.liquidity+.075*(1.3-self.liquidity)-.065*abs(pressure)+.04*noise[:,0],.35,1.8)
        impact=.009*np.tanh(.34*(F/1200)/self.liquidity)
        ret=np.clip(impact+.00115*noise[:,1],-.018,.018)
        self.price=np.maximum(.01,self.price*np.exp(ret));self.last_return=ret
        ea=1-np.exp(-1/16);self.rv_ema=(1-ea)*self.rv_ema+ea*ret**2
        self.tick+=1
        return {'F':F,'V':V,'K':active.sum(1),'r':ret,'pressure':pressure,'liquidity':self.liquidity.copy(),'fast':np.sum(self.weights*self.fast,1),'slow':np.sum(self.weights*self.slow,1),'trace':np.sum(self.weights*self.trace,1),'activeProbability':a}

    def hidden_summary(self):
        return {'fast':np.sum(self.weights*self.fast,1),'slow':np.sum(self.weights*self.slow,1),'trace':np.sum(self.weights*self.trace,1),'liquidity':self.liquidity.copy(),'effective_weight_concentration':np.sum(self.weights**2,1)}

    def save(self,path):
        np.savez_compressed(path,**{k:getattr(self,k) for k in ['weights','wf','ws','fast','slow','trace','liquidity','price','last_return','rv_ema']},tick=self.tick,params=np.array([__import__('json').dumps(self.params)]))

    @classmethod
    def load(cls,path):
        z=np.load(path,allow_pickle=False)
        return cls(*[z[k] for k in ['weights','wf','ws','fast','slow','trace','liquidity','price','last_return','rv_ema']],int(z['tick']),__import__('json').loads(str(z['params'][0])))

def observable_only(step_output):
    return {k:step_output[k].copy() for k in ['F','V','K','r']}
