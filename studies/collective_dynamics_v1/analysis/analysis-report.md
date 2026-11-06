# Compact collective dynamics: strict analysis

## Primary question and decision

Does a reduced, capital-weighted pressure closure with constrained reinforcement, memory and cross-scale influence improve next-day realized-variance forecasting at matched historical input budgets? It does not improve the primary accuracy/history-budget frontier here. The Q1-selected mechanism is worse than return HAR and the macro statistical model at every tested budget in point QLIKE, while its risk outputs are nearly identical to the same-map unconstrained pressure AR.

This round replaces the earlier demand for actual participant counts with an effective weighted-pressure description. That is an explicit model definition, not recovered social structure. The microscopic synthetic network used by the website is a separate controlled mechanism; this study does not validate that entire network against Bitcoin.

## Frozen design and complete information costs

The reused 663-date BTCUSDT panel has r,V,K,F at five-minute resolution. There are90 Q1 validation dates,183 Apr–Sep primary dates and25 October dates. Every forecast is fit using only30,60,120 or240 immediately preceding complete days. All state initialization, EMA lookbacks, flow fitting, price response, residual dispersion, risk calibration and statistical regression stay within that budget, with no extra warm-up days or microscopic calibration. Each fit has B−1 daily training pairs. Initial within-window features use expanding summaries before their nominal7/28-day horizon is available. This warm start is shared and explicitly counted.

ReturnHAR and persistence consume only r. The mechanism and same-map pressure/direct-flow controls consume r,V,F. MacroStat also uses K and contains the same observed pressure states. The unconstrained PressureAR is the strict mechanism-removed same-field/same-map comparator. Fewer historical days with additional fields is a tradeoff, not automatically lower total information. No universal field-cost scalar or application noninferiority threshold was invented.

All macro dates were examined before; this is historical development. Penalties {.1,10,1000} and model variants were frozen before scoring. Q1 chooses a penalty per model/budget and the Fast/Memory/CrossScale variant. selections.json was written before primary-period score analysis. Daily rolling fits update causally without reselecting hyperparameters on the primary outcomes.

## Mechanism and limits of its reduction

The daily pressure m=sumF/sumV is a volume-weighted executed-direction proxy. Slow and adaptation states are EMAs7/28, initialized inside the window. Mean-field transition is mhat=tanh(b+j*m+k*slow−a*adaptation), with nonnegative j,k,a. Fast removes slow/adaptation; Memory removes cross-scale input; CrossScale keeps both. Coefficients are regularized against observed past pressure transitions. j combines within-layer reinforcement and inertia; it does not separately identify them.

The proposed flow-energy closure multiplies predicted volume second moment by predicted squared pressure plus past within-day dispersion and transition uncertainty, with a past-flow QLIKE scale. Volume/pressure dependence means this is not an exact factorization. A past fitted r=alpha+beta F+eta response (beta>=0), trailing residual moment and positive QLIKE scale map it to expected sum of288 future bar squares. The target does not include cross-bar covariance as if daily RV equalled squared cumulative return. The conditional residual/response assumptions are not established by regression fitting.

## Full primary comparison

| budget_days | model | mean | sd | ci_low | ci_high |
| --- | --- | --- | --- | --- | --- |
| 30 | DirectFlow | 0.2851762 | 0.5940977 | 0.198546 | 0.4093308 |
| 60 | DirectFlow | 0.2813475 | 0.5610049 | 0.1976997 | 0.4043781 |
| 120 | DirectFlow | 0.2875194 | 0.5513338 | 0.2033887 | 0.404025 |
| 240 | DirectFlow | 0.2814571 | 0.5162381 | 0.2066168 | 0.3898808 |
| 30 | MacroStat | 0.2525102 | 0.4718985 | 0.1860059 | 0.3342115 |
| 60 | MacroStat | 0.2539056 | 0.4724554 | 0.1869976 | 0.3440897 |
| 120 | MacroStat | 0.2345791 | 0.4003197 | 0.1814751 | 0.2971316 |
| 240 | MacroStat | 0.2235958 | 0.4061741 | 0.1722631 | 0.2915379 |
| 30 | MechanismSelected | 0.2657125 | 0.5332423 | 0.1930514 | 0.3668677 |
| 60 | MechanismSelected | 0.2631771 | 0.4860156 | 0.1940237 | 0.3600924 |
| 120 | MechanismSelected | 0.2684557 | 0.4734415 | 0.1999778 | 0.3596443 |
| 240 | MechanismSelected | 0.2608053 | 0.4296659 | 0.2005812 | 0.3372649 |
| 30 | PressureAR | 0.2657487 | 0.5331492 | 0.19355 | 0.3666941 |
| 60 | PressureAR | 0.2631704 | 0.4859988 | 0.193071 | 0.3592729 |
| 120 | PressureAR | 0.2684229 | 0.4732502 | 0.1998421 | 0.359035 |
| 240 | PressureAR | 0.2607916 | 0.429663 | 0.2021678 | 0.3365572 |
| 30 | ReturnHAR | 0.2400011 | 0.4469999 | 0.1796627 | 0.3194661 |
| 60 | ReturnHAR | 0.2375262 | 0.413149 | 0.1826314 | 0.3052381 |
| 120 | ReturnHAR | 0.2375608 | 0.406466 | 0.1858874 | 0.297985 |
| 240 | ReturnHAR | 0.2281908 | 0.3857506 | 0.1870259 | 0.2789966 |

At30 days, selected Memory QLIKE is .265712 versus return HAR .240001 and MacroStat .252510. At240 days, selected CrossScale is .260805 versus .228191 and .223596. The same-map PressureAR is .260792 at240 days. Therefore no new data-efficiency or restriction-based prediction advantage is demonstrated.

The comparison is within this frozen rolling protocol. It must not be presented as an isolated improvement over the earlier .3131 standalone score, which used a different response/calibration/refit protocol. Previously viewed market paths also prevent a fresh-holdout generalization claim.

## Paired primary contrasts

| budget_days | reference | improvement_pct | pct_ci_low | pct_ci_high | basic_pct_ci_low | basic_pct_ci_high | p_holm |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 30 | MacroStat | -5.228403 | -22.30641 | 9.915902 | -20.397 | 11.9896 | 1 |
| 30 | PressureAR | 0.01363154 | -0.02572666 | 0.06814515 | -0.0342955 | 0.05546139 | 1 |
| 30 | DirectFlow | 6.825152 | 1.563949 | 12.08316 | -2.770258 | 12.45244 | 0.8052 |
| 60 | MacroStat | -3.651582 | -16.14973 | 7.428565 | -14.78386 | 8.241698 | 1 |
| 60 | PressureAR | -0.00255517 | -0.02192877 | 0.01969723 | -0.02262238 | 0.01956295 | 1 |
| 60 | DirectFlow | 6.458337 | 1.099943 | 11.99374 | -3.54552 | 12.05123 | 0.9031 |
| 120 | MacroStat | -14.44144 | -27.81295 | -0.8860427 | -28.00181 | 1.626324 | 1 |
| 120 | PressureAR | -0.01219412 | -0.03460217 | 0.01357445 | -0.036559 | 0.01379978 | 1 |
| 120 | DirectFlow | 6.630423 | 0.7743919 | 12.59896 | -3.885988 | 12.67255 | 0.9031 |
| 240 | MacroStat | -16.64138 | -29.95481 | -5.569209 | -27.83915 | -4.758209 | 1 |
| 240 | PressureAR | -0.005244727 | -0.01105554 | -0.0004402131 | -0.01002503 | -0.0001226549 | 1 |
| 240 | DirectFlow | 7.337457 | 0.6334736 | 14.67203 | -4.683036 | 14.17234 | 0.9031 |

The mechanism's point loss is6.5–7.3% below DirectFlow, but PressureAR obtains essentially the same result. That point gain cannot be credited to the nonlinear sign-constrained mechanism. The12-test Holm family supports no positive incremental claim. Individual percentile intervals and centred-bootstrap p-values use different bootstrap inversions; with skewed paired losses their boundaries need not coincide. An independent uncertainty audit added basic additive intervals compatible with the centred-null inversion; the basic percentage bounds divide those additive bounds by the fixed reference mean. Both interval types remain in the table. I02 uses the basic intervals. No equivalence claim follows from a small or nonsignificant mean-field/AR discrepancy.

## Conditioning and attenuation diagnostics

| budget_days | condition_median | condition_max | fits_at_upper_bound | fits_at_zero |
| --- | --- | --- | --- | --- |
| 30 | 5.478911 | 18.17422 | 0 | 250 |
| 60 | 4.174913 | 8.660617 | 0 | 229 |
| 120 | 3.216509 | 10.18371 | 0 | 203 |
| 240 | 3.50177 | 5.226908 | 0 | 169 |

These coefficients do not hit the upper bound, but one or more constrained coefficients often lie at zero. This is evidence about the fitted reduced representation, not proof that the real market lacks collective interaction. The finite condition numbers do not remove the nonidentification between latent graph influence, inertia and aggregation effects.

The following is a post-primary diagnostic using frozen fitted outputs, with no new model selection:

| budget_days | directional_share | residual_share |
| --- | --- | --- |
| 30 | 0.001289354 | 0.733903 |
| 60 | 0.0008055046 | 0.7428736 |
| 120 | 0.0006410086 | 0.7359141 |
| 240 | 0.0007180948 | 0.7117625 |

The directional-mean contribution to the predicted flow second moment is small; the risk mapping is dominated by within-day dispersion and residual price-risk components. This helps explain why pressure-transition restrictions barely change the risk forecast. These are model accounting quantities, not causal fractions of market herding.

## Audit and reproduction scope

Target/future-return perturbations leave target forecasts unchanged; every-return perturbation leaves pressure fits unchanged; truncated-prefix forecasts agree exactly; all input windows match the exact B-day budget and end before the target; all risk forecasts are positive/finite. Losses are independently recalculated. The cumulative-return square identity is checked explicitly, and it differs from the RV target as expected. Fresh-directory reproduction rebuilds all numerical outputs from the packaged derived panel; it is a numerical check, not new market evidence.

## Claim Candidates

- Claim: The new model offers more accurate or lower-information risk estimates.
  - Source evidence: predictions.csv; scores.csv; input_budget.csv; contrasts.csv.
  - Allowed wording: No advantage is established in this historical matched-budget comparison.
  - Forbidden wording: A validated low-information Bitcoin risk sensor or superior predictor.
  - Uncertainty: One reused path, approximate macro closure, multiple budgets/variants and four input-cost axes.
  - Next check: A revised, separately frozen mechanism justified by independent evidence and an untouched final sample.
  - Decision: discard positive claim.
- Claim: A coupled fast/slow network has been empirically recovered.
  - Source evidence: protocol, constrained fit diagnostics and independent synthetic engine.
  - Allowed wording: A compact proxy closure motivated by coupled dynamics was tested.
  - Forbidden wording: The Bitcoin graph, psychological consensus or actual coordinating people were identified.
  - Uncertainty: Macro aggregation and parameter correspondence are not unique.
  - Next check: Independent observables or restricted identifiability conditions.
  - Decision: retain only as model hypothesis.
- Claim: Pressure persistence beats direct-flow risk.
  - Source evidence: full12-contrast family; same-map PressureAR.
  - Allowed wording: The reduced pressure mapping improves point loss over DirectFlow but the same-input unconstrained mapping performs similarly; family-corrected incremental evidence is absent.
  - Forbidden wording: Mean-field coupling or consensus stages caused a verified prediction gain.
  - Uncertainty: Bootstrap assumptions, reused history and small field differences in MacroStat.
  - Next check: Separate stage information from the activity/dispersion factorization under a future frozen design.
  - Decision: weaken.
