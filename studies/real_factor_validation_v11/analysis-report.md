# Effective factor diversity, signed covariance and risk

Six named research factors represented a median **3.23 effective correlation modes** in the 2020–September 2026 evaluation. Their cross-covariances increased the estimated risk in 45 months and reduced it in 36. A rule that shifted allocation toward past winners changed concentration, but the resulting increase in next-month risk was not statistically established. The real-data extension therefore supports a **signed, state-dependent** interpretation of common exposure. It does not identify actual quantitative trading or calibrate the nonlinear network.

## Connection to the main research line

The network model asks how common actions and limited absorption can convert coordination into risk. The extension below tests an observable implication at the research-factor-return level: nominal strategy labels are not independent return directions, and the risk contribution depends on the sign and magnitude of the covariance at the current allocation. This refines the path from observables to effective state to risk without treating a new dataset as evidence for the entire network mechanism.

The empirical state is an estimated return covariance matrix and a computed allocation. It is not a count of coordinated traders. The experiment does not measure the absorption environment, trading flows or the causal effect of quant scale; those remain distinct model mechanisms. It also does not resolve the Bitcoin macro-to-coordination inverse problem.

## Data and chronological design

We downloaded the official Kenneth R. French daily five-factor and momentum archives after freezing `PROTOCOL.json` and `code/study.py`. All six series—MktRF, SMB, HML, RMW, CMA and Mom—were fixed before download and retained. The aligned panel contains 9,254 common daily observations from 2 January 1990 through 30 September 2026. The pre-specified cap was 31 October 2026; no unavailable October observations were added. Source percentage returns were divided by 100.

This is a historical study with a protocol frozen before this dataset was retrieved. It is not an externally registered, prospective experiment. The files are the current September 2026 CRSP vintage. The official library states that CIZ files replaced FIZ production beginning with the January 2025 release. Current-vintage historical returns can incorporate revisions, so this is not a point-in-time trading backtest. Archive checksums, retrieval times, original headers, copyright and routes are retained in the local provenance bundle.

Each origin is a month end. The previous 252 daily observations determine scale and features; coefficients are fixed for the entire next calendar month. The risk target is the mean squared daily arithmetic research-factor payoff in that next month. It is neither intraday realized variance nor the return of a funded investment account. The first eligible target month is January 1991: there are 228 fitting months in 1991–2009, 120 development months in 2010–2019 and 81 evaluation months in January 2020–September 2026. Evaluation predictions and allocations were hashed before joining their next-month targets.

## Signed covariance and prediction

For the fixed allocation, each factor receives equal risk budget, transformed to held coefficients by inverse past volatility and normalized to sum to one. At each origin, the previous 63 observations give the mean vector μ and covariance Σ. The full second-moment estimate is

\[
\widehat v_{\mathrm{full}}=w^\top\widehat\Sigma w+(w^\top\widehat\mu)^2.
\]

The diagonal counterfactual retains the same means and marginal variances, setting only the cross-covariances to zero. Their difference is the signed covariance contribution. Positive common exposure can amplify the payoff variance; opposing return directions can hedge it. The correlation participation ratio, \((\operatorname{tr} C)^2/\operatorname{tr}(C^2)\), summarizes effective return modes. Because squaring correlations discards their signs, that mode count alone is not a directional risk index.

Across the 81 evaluation months, the full/diagonal second-moment ratio ranged from **0.355 to 2.301**, with median **1.021**. Effective correlation modes ranged from **1.900 to 4.448**, with median **3.228**, despite the fixed six-factor universe. These are historical state estimates, not six observed firms or a measured degree of behavioral coordination.

Forecasts were assessed on the same fixed-allocation target. A positive Gamma mean model with ridge regularization implements two HAR-style benchmarks: HAR-Portfolio uses three portfolio second-moment averages over 22, 66 and 252 days; HAR-All additionally uses the six factor second moments on those windows, six past-63-day means and all 15 correlations. Both are afforded the same six-series, 252-day information set and the same fit/development periods. Their representations and capacities differ. The penalty menu was 0.1, 10 and 1,000, selected only on development QLIKE; selected penalties were 10 for HAR-Portfolio and 1,000 for HAR-All. No evaluation refit was performed.

| Forecast | Evaluation mean QLIKE, lower is better |
|---|---:|
| HAR-Portfolio | 0.1934 |
| Full covariance | 0.2427 |
| Diagonal | 0.3497 |
| HAR-All | 0.4884 |

Full covariance had 30.6% lower mean QLIKE than the diagonal counterfactual and 50.3% lower than HAR-All. These two locked comparisons did not survive the six-comparison Holm correction: adjusted p = 0.2562 and 0.0810 with three-month blocks. HAR-Portfolio had the lowest descriptive loss. The result is therefore useful for interpreting covariance, while a robust predictive advantage over HAR is not established. No new tuning was performed after seeing evaluation outcomes.

## Lagged performance allocation and next-month risk

We compared three allocation rules on the same observed factor payoffs. Fixed uses an equal risk budget at every origin. Performance applies a multiplicative update to the preceding budget using only the just-completed calendar month's volatility-scaled factor returns, a fixed gain of 0.1, clipping at ±2, and 2% reinjection toward equal budget. Permuted applies the same update after a deterministic date-seeded permutation of the completed factor scores. All budgets are converted to inverse-volatility held coefficients before the next month begins.

The held-coefficient HHI is \(\sum_i w_i^2\). It differs from risk-budget HHI: the fixed baseline's held coefficients are inverse-volatility weights, not equal 1/6 weights. Consequently its HHI is not mechanically the minimum. A coefficient sum of one is a normalization over research-factor sleeves; it does not specify the underlying long/short gross exposure, funded capital, financing or security-level turnover. Budgets carry a persistent state from preceding origins; that allocation experiment is separate from the matched 252-day forecast interface.

| Rule | Mean held HHI | Mean next-month daily second moment |
|---|---:|---:|
| Fixed | 0.1897 | 1.1916 × 10⁻⁵ |
| Performance | 0.2070 | 1.6065 × 10⁻⁵ |
| Permuted | 0.2299 | 1.3223 × 10⁻⁵ |

Performance increased held HHI by 9.15% relative to Fixed. The paired difference was 0.01736, with a three-month-block 95% basic interval of [0.00701, 0.02713] and Holm-adjusted p = 0.0036. The six-month-block sensitivity gave adjusted p = 0.0540, so the statistical strength depends on the dependence assumption. Performance had **lower**, not higher, concentration than Permuted: the adjusted p values were 0.1624 and 0.3168. The comparison therefore does not make concentration unique evidence for economically aligned performance chasing.

Performance's mean next-month risk was 34.8% above Fixed, but the paired difference interval included zero (−2.93 to 8.25 × 10⁻⁶; adjusted p = 0.2562). Against Permuted, the mean increment was 21.5%, also not established (−5.00 to 7.49 × 10⁻⁶; adjusted p = 0.4844). Gross risk is the primary outcome. A descriptive 1 bp charge per unit of monthly coefficient turnover is saved for inspection; it is an assumed coefficient-level charge, not an estimate of full factor implementation costs.

## What changed in the scientific conclusion

The observable extension establishes a concrete empirical distinction between **factor names, effective return dimensions, held concentration and future risk**. Those quantities cannot be substituted for one another. Signed covariance supplies both amplification and hedging examples in the complete evaluation sequence. The allocation control shows why greater concentration, by itself, cannot establish stronger risk or an identified flow mechanism.

For the network argument, this makes the next empirical requirement sharper: measure or credibly proxy directional common exposure together with available absorption, and then test whether the resulting effective state improves risk estimates under the same information budget. These factor data supply the covariance side of that bridge. They do not observe liquidity or show the feedback from allocation into prices, and they do not turn the model's market-impact scenario into a causal market measurement.

## Verification and artifacts

`code/check_saved.py` does not import the frozen study implementation. It reparses the official archives and independently reconstructs all 429 origins, scales, coefficients, HHI, turnover, target alignment, covariance estimates, HAR features, predictions, fit-only Gamma gradients, development selection, evaluation scores and both bootstrap/Holm families. **12,082 checks passed**; all protocol, code and prediction hashes were unchanged. This is independent implementation QA on the same inputs, not independent empirical replication.

The two scientific figures use all 81 evaluation months and the locked contrasts. Derived monthly tables, protocol, code, source routes and provenance hashes are suitable for the project release. Raw official archives and the full daily source panel remain local; no new license over those source returns is asserted.

Sources: [French Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html), [five-factor construction](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/f-f_5_factors_2x3.html), [daily momentum construction](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_mom_factor_daily.html).
