# Frozen reduced collective-dynamics and information-budget study

Frozen 6 November 2026 before new evaluation scores. All existing macro dates were examined in earlier rounds; this is retrospective historical development, not an untouched market holdout.

## Questions

Does a compact fast/slow/adaptive mean-field pressure closure improve next-day realized-variance prediction relative to an equally informed unconstrained pressure model or direct flow response? Does it use a shorter historical calibration window at comparable loss? A nonsignificant difference does not establish equivalence. No arbitrary cross-field information price or noninferiority tolerance is invented.

## Information and chronological budget

Inputs are the existing five-minute r,V,K,F for 663 UTC dates (1 Jan 2025–25 Oct 2026). No raw execution labels, participant counts, depth or external pretrained states are used. Target is RV(d+1)=sum of its 288 squared five-minute returns, not squared cumulative daily return.

At each origin, every model receives only the last B complete days, B in {30,60,120,240}. States, response, residual dispersion, calibration and risk regression all reset inside that same window. No extra warm-up history is allowed. Within-window training features use expanding summaries initially, then fixed 7/28-day summaries; B−1 daily target pairs are available. The full cost is B×288 observations per required field, with microscopic calibration zero. Models using r only are explicitly cheaper by field count than models requiring r,V,K,F. V/K are included in the same-information statistical comparator; unused fields are not charged to pressure models.

Q1 2026 (90 dates) selects penalties and which Fast/Memory/CrossScale variant is primary separately at each B. Primary evaluation is Apr–Sep 2026 (183 dates); October1–25 (25 dates) is separate. Daily fits are causal rolling refits, so each target has a B-day training window. Penalty grid {.1,10,1000} is fixed. Every candidate and budget is retained. Selection locks are written before evaluation score tables.

## Closure and controls

Daily observed pressure m=sum F/sum V; the slow state is an EMA with time constant seven days, and adaptation is an EMA with time constant28. All start from the first pressure inside the budget window. Proposed transition:

    mhat_next=tanh(b+j*m+k*slow−a*adaptation), j,k,a≥0.

Fast sets k=a=0. Memory sets k=0. CrossScale retains all. Pressure transitions are fit to past pressure targets by variance-normalized squared error and ridge, with b in [−1,1], other coefficients in [0,6]. j combines within-layer influence and inertia at this resolution; these contributions are not separately identified. This is a reduced proxy closure motivated by the coupled heat-bath model, not its exact aggregate law or graph recovery.

PressureAR uses the same m,slow,adaptation inputs without sign constraints or tanh, clipping forecasts to [−.99,.99], and the same activity/dispersion/response map. It is a mechanism-removed statistical control. DirectFlow uses trailing seven-day flow first/second moments with that same response map. Persistence uses latest RV. ReturnHAR uses log RV summaries1/7/28. MacroStat uses those plus log V and K summaries1/7 and the three pressure states (10 dimensions).

For pressure models, forecast per-bar volume second moment by trailing seven-day mean V². Within-day pressure dispersion is the V²-weighted mean of (F/V−m_day)², smoothed over seven days; add fitted pressure-transition MSE. Multiply the activity second moment by predicted squared pressure plus dispersion, then fit a nonnegative QLIKE scale to past daily mean F². This V²×pressure factorization is a working closure: volume-pressure dependence means it is not an exact identity. Enforce predicted flow second moment at least predicted mean flow squared. Mean flow uses trailing mean V times predicted pressure.

Fit r=alpha+beta F+eta on all bars inside B, beta≥0; residual second moments use the trailing seven days. Forecast daily RV from 288*(alpha²+2alpha beta E[F]+beta² E[F²]+E[eta²]). A final positive QLIKE scale is fitted to the B−1 training RV targets for all physical-map controls. It is charged as a calibrated parameter. Residual orthogonality and transfer of response are assumptions, not causal facts. Cross-time covariance is NOT added to the RV target.

ReturnHAR and MacroStat fit Gamma-log-link ridge by QLIKE on the same B−1 targets, with the same fixed penalty grid. They do not consume a microscopic prior. Stage/phase effects are represented by finite-memory pressure/adaptation state; no future-derived phase label is used.

## Primary contrasts and uncertainty

Q1 selects the primary Mechanism variant among Fast/Memory/CrossScale and its penalty. Per budget, its three primary contrasts are against MacroStat, PressureAR and DirectFlow. Holm correction spans all12 contrasts (four budgets×three controls), separately per evaluation period and metric. Main metric QLIKE; raw MSE is secondary. Seven-day circular paired blocks with19,999 draws are primary, one/fourteen-day sensitivity. Report additive/relative effect, paired SD and standardized effect, interval, day count, loss mean/SD and assumptions. Approximate one-sided centred-bootstrap tests are not exact market randomization tests.

Compare each primary Mechanism budget with ReturnHAR240 as an explicitly separate history/field tradeoff family (four contrasts). This does not demonstrate overall less information because pressure requires extra fields. Show full accuracy/budget curves, not only the favourable budget. No success claim is substituted from a secondary metric.

## Audits and outputs

Target-return perturbation and prefix invariance; pressure-fit invariance to all returns; exact B-day input provenance; finite positive forecasts; constraint/boundary and condition-number diagnostics; loss recalculation; distinct RV/cumulative-return-variance audit. Rebuild every numerical table in a fresh directory and compare. Produce strict analysis/statistics/figure catalog, actual plots and website-ready results JSON with explicit status. Previous studies and website files remain unchanged by this workstream.
