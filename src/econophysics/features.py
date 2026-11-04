"""One shared feature definition for paired return-only and return/volume views."""

import math
import statistics

PRICE_FEATURES = ('return_std', 'mean_abs_return', 'abs_return_q95', 'abs_return_q99', 'zero_return_fraction')
VOLUME_FEATURES = ('volume_mean', 'volume_std', 'volume_q95', 'corr_volume_abs_return')


def quantile_linear(values, probability):
    data = sorted(values)
    if not data or not 0 <= probability <= 1:
        raise ValueError('invalid quantile input')
    h = (len(data) - 1) * probability
    lo = math.floor(h)
    return data[lo] + (h - lo) * (data[min(lo + 1, len(data) - 1)] - data[lo])


def window_features(observations):
    if len(observations) < 2:
        raise ValueError('at least two observations required')
    ret = [float(row['r']) for row in observations]
    vol = [float(row['V']) for row in observations]
    if not all(math.isfinite(x) for x in ret + vol) or any(x < 0 for x in vol):
        raise ValueError('non-finite return/volume or negative volume')
    absolute = [abs(x) for x in ret]
    mv, ma = statistics.fmean(vol), statistics.fmean(absolute)
    sv, sa = statistics.stdev(vol), statistics.stdev(absolute)
    corr = (math.fsum((v - mv) * (a - ma) for v, a in zip(vol, absolute)) /
            ((len(vol) - 1) * sv * sa)) if sv and sa else None
    return dict(zip(PRICE_FEATURES + VOLUME_FEATURES,
                    [statistics.stdev(ret), ma, quantile_linear(absolute, .95),
                     quantile_linear(absolute, .99), sum(x == 0 for x in ret) / len(ret),
                     mv, sv, quantile_linear(vol, .95), corr]))
