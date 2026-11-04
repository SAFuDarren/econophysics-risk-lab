"""Finite-grid uncertainty and bounded discrete-tail diagnostics."""

import numpy as np
from scipy.optimize import minimize_scalar
from scipy.special import logsumexp


def stratified_bootstrap_mean(values, groups, rng, repetitions=4999):
    values = np.asarray(values, dtype=float)
    groups = np.asarray(groups)
    if not np.all(np.isfinite(values)):
        raise ValueError('bootstrap values must be finite')
    result = np.zeros(repetitions)
    for group in np.unique(groups):
        subset = values[groups == group]
        indices = rng.integers(0, len(subset), size=(repetitions, len(subset)))
        result += subset[indices].sum(axis=1) / len(values)
    return result


def interval(samples):
    return [float(x) for x in np.quantile(samples, [.025, .975])]


def holm_adjust(pvalues):
    pvalues = np.asarray(pvalues, dtype=float)
    order = np.argsort(pvalues)
    adjusted = np.empty(len(pvalues))
    maximum = 0.0
    for rank, index in enumerate(order):
        maximum = max(maximum, (len(order)-rank)*pvalues[index])
        adjusted[index] = min(1.0, maximum)
    return adjusted.tolist()


def finite_tail_fit(counts, support, kind, bounds):
    counts = np.asarray(counts, dtype=float)
    support = np.asarray(support, dtype=float)
    statistic = np.log(support) if kind == 'power' else support
    def objective(parameter):
        logp = -parameter*statistic - logsumexp(-parameter*statistic)
        return -float(np.dot(counts, logp))
    optimum = minimize_scalar(objective, bounds=bounds, method='bounded', options={'xatol':1e-9})
    candidates = [float(optimum.x), float(bounds[0]), float(bounds[1])]
    parameter = min(candidates, key=objective)
    logp = -parameter*statistic - logsumexp(-parameter*statistic)
    probabilities = np.exp(logp)
    ks = float(np.max(np.abs(np.cumsum(counts)/counts.sum() - np.cumsum(probabilities))))
    return {'parameter':parameter, 'log_likelihood':-objective(parameter), 'aic':2+2*objective(parameter), 'ks':ks, 'probabilities':probabilities}


def tail_diagnostic(order_magnitudes, upper, xmin, config, rng):
    values = np.asarray(order_magnitudes, dtype=int)
    support = np.arange(xmin, upper+1)
    counts = np.bincount(values, minlength=upper+1)[xmin:upper+1]
    if counts.sum() < 50:
        raise ValueError('too few observations above the prespecified tail threshold')
    power = finite_tail_fit(counts, support, 'power', config['power_exponent_bounds'])
    exponential = finite_tail_fit(counts, support, 'exponential', config['exponential_rate_bounds'])
    ks_null, exponent_samples = [], []
    for _ in range(config['bootstrap_replicates']):
        generated = rng.multinomial(int(counts.sum()), power['probabilities'])
        fitted = finite_tail_fit(generated, support, 'power', config['power_exponent_bounds'])
        ks_null.append(fitted['ks'])
        empirical = rng.multinomial(int(counts.sum()), counts/counts.sum())
        exponent_samples.append(finite_tail_fit(empirical, support, 'power', config['power_exponent_bounds'])['parameter'])
    pvalue = (1+sum(d >= power['ks'] for d in ks_null))/(len(ks_null)+1)
    summary = {'tail_count':int(counts.sum()), 'total_count':len(values), 'xmin':xmin, 'upper_support':upper,
               'power_exponent':power['parameter'], 'exponent_ci_low':interval(exponent_samples)[0], 'exponent_ci_high':interval(exponent_samples)[1],
               'power_ks':power['ks'], 'power_gof_p':pvalue, 'gof_mc_se':float(np.sqrt(pvalue*(1-pvalue)/(len(ks_null)+1))),
               'power_aic':power['aic'], 'exponential_rate':exponential['parameter'], 'exponential_aic':exponential['aic'],
               'delta_aic_exp_minus_power':exponential['aic']-power['aic'], 'bootstrap_replicates':len(ks_null)}
    return summary, [{'m':int(m), 'count':int(count), 'power_probability':float(pp), 'exponential_probability':float(ep)} for m,count,pp,ep in zip(support,counts,power['probabilities'],exponential['probabilities'])]
