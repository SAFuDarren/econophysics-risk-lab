from pathlib import Path
import json,hashlib,platform,sys
import numpy as np
import pandas as pd
import scipy,matplotlib

R=Path(__file__).resolve().parents[1]

def md_table(frame,cols):
    text='| '+' | '.join(cols)+' |\n| '+' | '.join(['---']*len(cols))+' |\n'
    for _,r in frame.iterrows():text+='| '+' | '.join(f'{r[c]:.7g}' if isinstance(r[c],(float,np.floating)) else str(r[c]) for c in cols)+' |\n'
    return text

def main():
    scores=pd.read_csv(R/'tables/scores.csv');contrast=pd.read_csv(R/'tables/contrasts.csv');diag=pd.read_csv(R/'tables/selected_diagnostics.csv');account=pd.read_csv(R/'tables/frozen_risk_accounting.csv');selection=json.loads((R/'fits/selection.json').read_text());primary=scores[(scores.period=='primary')&(scores.metric=='qlike')];pc=contrast[(contrast.period=='primary')&(contrast.metric=='qlike')&(contrast.block_days==7)&(contrast.family=='primary_12')]
    compact=primary[primary.model.isin(['MechanismSelected','ReturnHAR','MacroStat','PressureAR','DirectFlow'])];acct=account[account.period=='primary'].groupby('budget_days').agg(directional_share=('directional_mean_flow_share','mean'),residual_share=('predicted_residual_risk_share','mean')).reset_index()
    analysis='''# Compact collective dynamics: strict analysis

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

'''+md_table(compact,['budget_days','model','mean','sd','ci_low','ci_high'])+'''
At30 days, selected Memory QLIKE is .265712 versus return HAR .240001 and MacroStat .252510. At240 days, selected CrossScale is .260805 versus .228191 and .223596. The same-map PressureAR is .260792 at240 days. Therefore no new data-efficiency or restriction-based prediction advantage is demonstrated.

The comparison is within this frozen rolling protocol. It must not be presented as an isolated improvement over the earlier .3131 standalone score, which used a different response/calibration/refit protocol. Previously viewed market paths also prevent a fresh-holdout generalization claim.

## Paired primary contrasts

'''+md_table(pc,['budget_days','reference','improvement_pct','pct_ci_low','pct_ci_high','basic_pct_ci_low','basic_pct_ci_high','p_holm'])+'''
The mechanism's point loss is6.5–7.3% below DirectFlow, but PressureAR obtains essentially the same result. That point gain cannot be credited to the nonlinear sign-constrained mechanism. The12-test Holm family supports no positive incremental claim. Individual percentile intervals and centred-bootstrap p-values use different bootstrap inversions; with skewed paired losses their boundaries need not coincide. An independent uncertainty audit added basic additive intervals compatible with the centred-null inversion; the basic percentage bounds divide those additive bounds by the fixed reference mean. Both interval types remain in the table. I02 uses the basic intervals. No equivalence claim follows from a small or nonsignificant mean-field/AR discrepancy.

## Conditioning and attenuation diagnostics

'''+md_table(diag[diag.model=='MeanFieldCrossScale'],['budget_days','condition_median','condition_max','fits_at_upper_bound','fits_at_zero'])+'''
These coefficients do not hit the upper bound, but one or more constrained coefficients often lie at zero. This is evidence about the fitted reduced representation, not proof that the real market lacks collective interaction. The finite condition numbers do not remove the nonidentification between latent graph influence, inertia and aggregation effects.

The following is a post-primary diagnostic using frozen fitted outputs, with no new model selection:

'''+md_table(acct,['budget_days','directional_share','residual_share'])+'''
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
'''
    (R/'analysis/analysis-report.md').write_text(analysis)
    (R/'analysis/stats-appendix.md').write_text('''# Statistical appendix

Primary outcome is next-day RV, sum of288 squared five-minute log returns. QLIKE y/p−log(y/p)−1 is primary; raw MSE is secondary, log MSE descriptive. The real-data uncertainty unit is the UTC target date. There is one reused Bitcoin path, no independent asset or seed replication. Model fitting randomness is absent; resampling draws are not market replications.

Each rolling total-day budget is30/60/120/240. Available training pairs are29/59/119/239. Every model/calibration and first-state initialization remains inside its window, without externally warmed EMAs or a microscopic prior. Q1 selects penalties and the primary mechanism variant independently per budget. The primary period has183 target dates; October has25. Q1 performance is selection evidence and must not be reported as an independent test.

Means and daily SDs are retained for every model, budget and period.95% intervals use19,999 circular target-day block resamples, length7 primary. Paired contrasts retain exact date alignment and use lengths1/7/14. Positive additive and relative improvement mean lower candidate loss. Paired SD, standardized paired effect, skewness and excess kurtosis are reported. Daily losses and differences are skewed, so no unqualified Gaussian paired-t claim is used. Block-bootstrap inference assumes adequate temporal stability/mixing of loss differences and finite-sample performance is not guaranteed, particularly in the25-date October period.

Approximate one-sided p-values use the centred paired bootstrap distribution. Holm adjusts all12 primary comparisons (four budgets × MacroStat/PressureAR/DirectFlow) separately per period, metric and sensitivity block. The four comparisons against ReturnHAR240 are a separate explicitly labelled history/field tradeoff family. Mean-loss score intervals are marginal. Percentile intervals and centred-bootstrap tests are different inversions and can disagree at a nominal boundary for skewed losses. Independent review therefore added basic additive intervals, 2*observed mean minus opposite bootstrap percentiles, compatible with the centred-null inversion. Their percentage display divides by the fixed observed reference mean; it is not the same as a random-denominator bootstrap ratio interval. Both are retained, and I02 uses the basic bounds. No positive claim is made from choosing the more favourable inferential output. See UNCERTAINTY_AUDIT_ADDENDUM.md.

No noninferiority margin or application loss tolerance was prespecified, so failure to detect a difference cannot establish comparable reliability or lower information. Input fields, history length, microscopic labels and external warm-up are separate cost axes; no invented scalar cost ordering is used. ReturnHAR consumes r only while pressure models require V and F, so a shorter pressure-model history is not automatically an overall information reduction.

The frozen post-primary accounting table uses existing predictions, coefficients and histories to compute directional-mean-flow and residual-risk shares; it changes no model or hyperparameter. Shares are model accounting, not causal fractions attributed to coordinating people. Simulated-network results belong to the synthetic mechanism workstream and are not empirical replications of this study.
''')
    catalog='# Figure catalog\n\n'
    for file in sorted((R/'figures').glob('*.source.json')):
        item=json.loads(file.read_text());catalog+=f"## {file.name.split('.')[0]}\n\nPurpose / observation: {item['caption']}\n\nSources: {', '.join(item['sources'])}.\n\nUncertainty:19,999 paired/circular7-day resamples; marginal percentile mean intervals in I01, basic additive intervals scaled by the fixed reference mean in I02. Both contrast interval definitions and the full Holm family remain in the table.\n\nDecision implication: no restriction-specific or information-frontier success claim; retain all controls and every budget. Do not infer observed social networks from these plots.\n\n"
    (R/'analysis/figure-catalog.md').write_text(catalog)
    provenance=dict(date='2026-11-06',scope='historical reduced closure, not full game-network validation',input_sha256=hashlib.sha256((R/'inputs/macro_observables.npz').read_bytes()).hexdigest(),prior_macro_history_viewed=True,raw_trade_labels_used=0,source='Binance Vision derived five-minute BTCUSDT panel; source licensing inherited from the prior attributed input',python=sys.version,platform=platform.platform(),packages=dict(numpy=np.__version__,pandas=pd.__version__,scipy=scipy.__version__,matplotlib=matplotlib.__version__),table_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((R/'tables').glob('*.csv'))})
    (R/'analysis/provenance.json').write_text(json.dumps(provenance,indent=2))
    summary=dict(version=1,date='2026-11-06',status='no_incremental_advantage',evidence='retrospective_historical_reduced_closure',not_full_network_validation=True,headline={'en':'No information-efficiency advantage established','zh':'尚未建立信息效率优势'},target='next_day_sum_of_288_squared_5min_returns',periods=dict(validation=['2026-01-01','2026-03-31',90],primary=['2026-04-01','2026-09-30',183],secondary=['2026-10-01','2026-10-25',25]),budget_days=[30,60,120,240],microscopic_labels=0,extra_warmup_days=0,selections=selection['budgets'],primary_scores=primary.to_dict('records'),primary_contrasts=pc.to_dict('records'),information_costs=pd.read_csv(R/'tables/input_budget.csv').to_dict('records'),sources=['PROTOCOL.md','tables/scores.csv','tables/contrasts.csv','checks/causal_audit.json'],limitations=['All macro dates were previously viewed','Pressure and activity factorization is an approximate closure','State/graph/person parameters are not identified','No equivalence or causal herding claim'])
    (R/'website-summary.json').write_text(json.dumps(summary,indent=2))

if __name__=='__main__':main()
