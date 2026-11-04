"""Joint constraints of the action/aggregation interface, independent of graph family."""
import numpy as np


def joint_diagnostics(returns,volumes,n=128,unit_order=1.,q=None):
    r=np.asarray(returns,dtype=float);v=np.asarray(volumes,dtype=float)
    if r.shape!=v.shape or r.ndim!=1 or len(r)<3:
        raise ValueError('paired one-dimensional observations required')
    q_hat=float(v.mean()/(n*unit_order)) if q is None else float(q)
    if not 0<q_hat<1:raise ValueError('activity outside nondegenerate model domain')
    dc=v-v.mean();r2=r*r
    # Model E[r]=0 is used; this second raw moment consistently estimates Var(r).
    r_second=float(r2.mean());v_variance=float(np.mean(dc*dc));v_third=float(np.mean(dc**3))
    if min(r_second,v_variance)<=0:raise ValueError('degenerate variances')
    cross=float(np.mean((r2-r_second)*dc))
    normalized_cross=cross/(r_second*n*unit_order)
    constraint=(1-q_hat)*v_third/(v_variance*n*unit_order)-(1-2*q_hat)*normalized_cross
    return {'q':q_hat,'normalized_coupling':normalized_cross,'constraint_residual':constraint,
            'volume_variance':v_variance,'volume_third_central':v_third,'return_second':r_second,'cross_r2_volume':cross}
