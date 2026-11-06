# Research main line: macro observations, statistical structure and risk

The central task is to extract a risk-relevant statistical description from a small set of market observables, then use that description to estimate future risk. Complex-systems models provide the link between observed moments, effective trading weights, directional dependence and temporal persistence.

**Macro observations → statistical structure → risk prediction → evaluation and application.**

## The forward argument

| Stage | Question and output | Mathematical or empirical role |
|---|---|---|
| Macro observations | What do returns, volume, counts and signed aggressor flow tell us? | Define the observation interface, units, sampling horizon and available information. Detailed execution records provide reference measurements for size concentration. |
| Statistical structure | Which effective activity, weight/concentration and dependence quantities can be inferred? | Moment identities and controlled parameter recovery establish conditional inference routes. Weighted groups and fast/slow interactions explain the structure and persistence behind those moments; identification assumptions remain explicit. |
| Risk prediction | How does that estimated structure enter future risk? | Price response transfers flow means and dispersion into a return second moment, with a separate residual term. Dynamics specifies how the state evolves beyond the observation window. |
| Evaluation and application | Does the risk mapping provide useful estimates under a stated information budget? | Matched-input forecasting, direct-flow controls and risk calibration evaluate the method. Historical replay and covariance diagnostics make the statistical mechanism inspectable in concrete applications. |

## The statistical bridge

The primitive observations are r, V, K and signed aggressor flow F. Their moments support an effective description containing activity, size concentration, directional dispersion and persistence. A size baseline b separates independent-execution scale from conditional amplification G=Var(F)/b. Under specified response and residual assumptions, the risk mapping is

h=(α+βm_F)²+β²bG+σ²η.

The microscopic model explains why shared decisions and trading weights enter these moments. The inferential task is risk-relevant effective structure; it need not recover every investor or edge. A same-window bG product is exactly direct flow variance, so predictive content must come from a useful dynamic restriction, measurement economy or information-matched accuracy. Those requirements guide evaluation.

## Dynamic inference and joint future scenarios

The retained weighted fast/slow network now supplies complete stochastic future
paths. Propagating the full state distribution preserves nonlinear dynamics;
deterministic mean iteration loses that distribution and its dependencies.
Shared-input and lagged-feedback interventions test economic channels within
this same generator. They are controlled mechanism evidence.

The observable estimator conditions source-network trajectories on the past
32 bars of F, V, K and r. Its common nonnegative path weights retain coherent
joint flow, return and residual moments. A 2,048-trajectory source bank and
separate 32/64/128 selection/calibration/test units make offline information
cost and evaluation roles explicit. Diverse source states avoid static-ancestor
collapse, while HHI coverage and paired risk comparisons separately assess
inference quality and predictive value.

The original direct-map audit of 663 examined Bitcoin dates locates a market
observation gap in directional persistence, activity variation, execution units
and calendar time. Subsequent work separates effective decisions, fragmented
executions, calendar activity and price accommodation. A nominal calendar-time
extension supports the conditional studies below; this does not identify a true
Bitcoin network or complete a precise market calibration.

The [continuation evidence snapshot](../studies/collective_risk_continuation_v3/README.md)
contains the saved comparisons, definitions and numerical verification. Its
limited table-recalculation operation is distinguished from full simulation
regeneration.

## Conditional environment and effective-state diagnosis

The [state/environment study](../studies/state_environment_v9/README.md) follows
this same network mechanism. A common-input intervention has a larger paired
risk increment when simulated shock capacity is lower. Return feedback and
predictable-impact recovery alter the transmission, so a single coordination
multiplier does not describe all environments.

The inverse task now has three separate checks:

- **Precision:** independent future replications and conditional-moment labels
  separate simulation error from state variation without changing the law.
- **Information:** activity, size, latent capacity and weight concentration
  jointly improve source-model expected-risk prediction when supplied directly.
  The tested extra direction/memory block adds no established QLIKE gain.
- **Market forecast:** a past-only innovation/response closure uses the same
  F/V/K/r history as HAR. On 401 previously seen internal dates, the selected
  component readout has a 5.79% QLIKE point reduction, with uncertainty crossing
  zero. Post-run direct-moment controls nearly reproduce or exceed this score.

A positive average intervention effect compares two possible model worlds.
Additional forecast information requires observable within-world state variation
beyond the comparator. The complete-recovery local-noise limit reduces exactly
to a 20-bar return second moment; the full activity-forecast candidate is broader,
but its mechanism-specific advantage is not established. These results locate
the next inference problem: recovering useful response-environment information
at a justified measurement cost.

[Interactive study](https://safudarren.github.io/econophysics-risk-lab/risk-environment.html)
· [Saved-table verification](../studies/state_environment_v9/verify.py)

## Supporting assumption checks

Joint-moment compatibility, size distributions, fragmentation and state dependence check the assumptions used by the statistical bridge. Δ is one joint-moment diagnostic for the fixed reference interface. Its market result helps assess that interface and specify effective-weight/state extensions. It is not a separate research objective or the organising axis of the project.

Weighted fast/slow interactions model persistence and possible direction switching. The observation/participant map and the distinction between a reduced closure and the full network remain explicit. These qualifications belong with the relevant inference or dynamic model.

## Evidence and evaluation

Known-truth simulations establish parameter-recovery performance under specified scales and model assumptions. Observational-equivalence results describe the level of structure those observations determine. Bitcoin forecast comparisons test the resulting restrictions at matched information/history budgets. The current budget study has not established additional accuracy or information saving. Its full scores, controls and uncertainty remain available.

The target is reliable risk estimation with less information, or better accuracy at matched inputs. Input cost includes retained history and calibration as well as the number of output features. The replay uses directly measured execution B for explanation; macro-only estimation of that baseline retains its separate measurement and evaluation requirements.

## Application in the historical replay

The debrief follows the forward argument: inspect original observations, examine the effective amplification statistic, then compare the risk map and realized fluctuation. Response coefficients are calibrated before play and frozen. Labels distinguish observed data, model-conditioned estimates and post-hoc navigation. Its local time-scale mapping illustrates the theory while the daily forecasting study supplies the risk-performance evidence.

## Evidence map

- Observable moments, inference and identification: theory/FOUNDATIONS.md; website methods#inverse and methods#identity.
- Weighted structure and temporal dynamics: COLLECTIVE_DYNAMICS_MODEL_v1.md and COLLECTIVE_SIMULATION_RESULTS_v1.md.
- Risk mapping and replay information contract: REPLAY_THEORY_BRIDGE_v1.md; website methods#execution-risk-bridge.
- Matched-budget forecast evaluation: studies/collective_dynamics_v1/README.md and tables/scores.csv.
- Historical observations and selection: studies/historical_replay_v1/README.md.
- Supporting joint-moment diagnostic: website methods#delta and findings#market.
