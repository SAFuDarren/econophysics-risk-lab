"""Finite-N ER moment inversion and scale-invariant features; no fitted rho labels."""
from decimal import Decimal, localcontext
import math


def finite_er_moments(n, rho, precision=380):
    """Connectedness recurrence; high precision avoids catastrophic cancellation.

    This is a finite graph probability calculation, not a large-N branching approximation.
    Return expectations of sum(size**j), j=2,3, and the root-component PMF mass.
    """
    if n < 2 or not 0 <= rho <= n-1:
        raise ValueError('invalid N or rho')
    if rho == 0:
        return {'s2':float(n),'s3':float(n),'probability_mass':1.0}
    if rho == n-1:
        return {'s2':float(n*n),'s3':float(n**3),'probability_mass':1.0}
    with localcontext() as ctx:
        ctx.prec=precision
        p=Decimal(str(rho))/Decimal(n-1);absence=1-p
        powers=[Decimal(1)]
        for _ in range(n*n//4):powers.append(powers[-1]*absence)
        connected=[Decimal(0),Decimal(1)]
        for size in range(2,n+1):
            probability=1-sum(Decimal(math.comb(size-1,k-1))*connected[k]*powers[k*(size-k)] for k in range(1,size))
            if probability < 0 or probability > 1:
                raise ArithmeticError('connectedness recurrence lost precision')
            connected.append(probability)
        root=[Decimal(math.comb(n-1,s-1))*connected[s]*powers[s*(n-s)] for s in range(1,n+1)]
        mass=sum(root)
        if abs(mass-1)>Decimal('1e-80'):
            raise ArithmeticError('root component distribution not normalized')
        return {'s2':float(n*sum(Decimal(s)*v for s,v in enumerate(root,1))),
                's3':float(n*sum(Decimal(s*s)*v for s,v in enumerate(root,1))),
                'probability_mass':float(mass)}


def scale_invariant_joint(features):
    """Quotient a positive return-scale action; discard the scale coordinate."""
    scale=features['return_std']
    if scale <= 0:
        return [None,None,None,features['zero_return_fraction'],features['volume_mean'],
                features['volume_std'],features['volume_q95'],features['corr_volume_abs_return']]
    return [features[k]/scale for k in ('mean_abs_return','abs_return_q95','abs_return_q99')]+[
        features[k] for k in ('zero_return_fraction','volume_mean','volume_std','volume_q95','corr_volume_abs_return')]


def volume_moment_estimate(features, curve, n=128, unit_order=1.):
    """Return a physical-domain estimate plus explicit boundary/calibration flags."""
    import numpy as np
    q=features['volume_mean']/(unit_order*n)
    if not 0 < q < 1:
        return {'rho':None,'q':q,'s2':None,'flag':'degenerate_activity'}
    s2=features['volume_std']**2/(q*(1-q)*unit_order**2)
    values=np.asarray([r['s2'] for r in curve]);rhos=np.asarray([r['rho'] for r in curve])
    flag='interior'
    if s2<values[0]:flag='below_physical_moment_domain'
    elif s2>values[-1]:flag='above_physical_moment_domain'
    estimate=float(np.interp(s2,values,rhos))
    if flag=='interior' and estimate>2.5:flag='outside_dense_calibration_region'
    return {'rho':estimate,'q':q,'s2':s2,'flag':flag}
