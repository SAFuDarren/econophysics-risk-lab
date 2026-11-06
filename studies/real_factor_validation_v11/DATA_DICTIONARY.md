# Observation and estimation dictionary

| Object | Evidence type | Definition / unit | Interpretation |
|---|---|---|---|
| MktRF, SMB, HML, RMW, CMA, Mom | Observed published research-portfolio returns | Daily arithmetic return, original percent divided by 100 | Named factor payoffs, not observed trading flows |
| MktRF | Observed published excess return | Market minus risk-free rate | The market research factor |
| SMB / HML / RMW / CMA / Mom | Observed published spread returns | Size / value / profitability / investment / momentum factor | Long–short research returns; coefficient sum 1 is not underlying gross 1 |
| `origin` | Calendar/index metadata | Last available observation of completed month | All decisions use observations no later than this date |
| `future_month` | Calendar/index metadata | Immediately following calendar month | Nonoverlapping risk target window |
| `role` | Frozen selection rule | fit / development / evaluation | Determined by target year, never by outcome |
| Past scale | Estimated state | Previous 252 daily sample SD, ddof 1 | Used for current coefficients and completed-month score |
| `budget_*` | Computed allocation state | Positive risk-budget coefficients summing to 1 | Equal, lagged-score update, or score-permuted update |
| Factor columns in `computed_allocations.csv` | Computed held allocation | `budget / past_scale`, normalized to sum to 1 | Next-month factor-sleeve payoff coefficients |
| `HHI` | Computed concentration | Sum of squared held coefficients | Range 1/6–1; not trader concentration or security-level ownership |
| `risk_budget_HHI` | Computed concentration | Sum of squared risk-budget coefficients | Distinct from held HHI |
| `turnover` | Computed proxy | Half the absolute change in held coefficients | Monthly coefficient turnover; ignores underlying factor turnover |
| `assumed_1bp_turnover_charge` | Assumed scenario quantity | 0.0001 × coefficient turnover | Illustrative charge, not measured transaction costs |
| `FullCov` | Estimated forecast | Past 63 mean squared fixed-weight payoff | Centered covariance plus squared mean |
| `Diagonal` | Estimated counterfactual forecast | Same mean/marginal variances, cross-covariances set to zero | Isolates signed covariance contribution |
| `cross_term` | Estimated signed state | FullCov−Diagonal | Can be negative; no assumption that all commonality amplifies |
| `full_over_diagonal` | Estimated ratio | FullCov/Diagonal | <1 net hedging; >1 net amplification under current coefficients |
| `effective_corr_modes` | Estimated structural summary | `(trace C)^2 / trace(C@C)`, C = past 63 correlation matrix | Effective return dimensions; loses correlation signs, not a monotone risk index |
| `HAR-Portfolio` | Estimated forecast | Three log second-moment features, positive Gamma mean | Fixed-allocation 22/66/252-day HAR-style baseline |
| `HAR-All` | Estimated forecast | Same portfolio HAR plus six-series second moments/means/correlations | Same six raw series, 252-day history, larger fixed feature family |
| `realized_Fixed/Performance/Permuted` | Computed outcome from observed returns | Mean of squared next-month daily `r @ w`, coefficients held fixed | Daily return², not intraday RV, log-return variance or funded NAV |
| `QLIKE` | Computed evaluation loss | `y/p − log(y/p) −1` | Positive target and forecast; lower is better; scale invariant |
| `mean_difference` | Paired evaluation effect | Model minusreference calendar-month mean | Direction retained; risk increments can be negative |
| `CI_low/high` | Estimated sampling uncertainty | 95% basic circular paired-block interval | Primary 3 months, sensitivity 6 months, 4,999 draws |
| `p_raw/p_holm` | Computed test summaries | Two-sided centered-block null, add-one / Holm 6 | Corrected across locked six primary contrasts at each block size |

## Table scope and redistribution

- `tables/observed_factor_returns.csv` and `inputs/`: **local source-data cache only**, excluded from public release.
- `tables/predictions_scored.csv`: all 429 eligible target months; use `role=evaluation` for claims above.
- `tables/computed_allocations.csv`: three computed rules for all 429 months; this is not actual fund flow.
- `tables/development_grid.csv`: the full frozen penalty menu, no evaluation optimization.
- `tables/forecast_scores.csv` and `tables/primary_contrasts.csv`: evaluation aggregates and locked inference.
- `tables/past_features.npz`: derived 252-day features and weights, not raw daily returns; optional audit artifact.

All return-squared numbers are specific to this research-factor payoff normalization. They must not be compared numerically with Bitcoin squared log-return targets as if those targets were interchangeable.
