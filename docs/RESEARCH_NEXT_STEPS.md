# Next research priorities

The objective remains a risk-relevant effective state inferred from a small
observable market interface. The interdependent network supplies directional
dependence and memory; the observation model must explain how those decisions
appear as real executions and calendar-time risk. The published market benchmark
has not established an accuracy or information-cost advantage.

## Use direct information where it is already visible

Start with observed pressure F/V as a fast-direction measurement or proxy, with
explicit activity/selection error. Ask the network model to explain hidden slow
state, adaptation, weight concentration and accommodation. Evaluate whether those
latent quantities add useful future-flow information beyond the direct proxy.
Do not credit information already contained in F/V to structural recovery.

## Preserve uncertainty over risk-relevant structure

Static graph/weight parameters should not be repeatedly resampled without a
correct uncertainty mechanism. Candidate routes include conditional ensembles
drawn from the same full-network simulation law and properly accepted
resample-move or particle-MCMC steps. Positive scenario weights preserve joint
moments, but diverse samples alone do not establish a calibrated posterior.
Prefer a small identifiable risk state or partial bounds to recovering every edge.

## Separate the event clock, execution layer and direction network

An effective decision is not a raw exchange execution. A proposed observation
layer should distinguish internal decision events, child executions and
calendar windows. Directional dynamics stay on the original fast/slow network;
arrival intensity and fragmentation describe when and how they are observed.

[Russell and Engle's 1998 ACM manuscript](https://eml.berkeley.edu/symposia/nsf98/engle_russell.pdf)
models transaction arrivals jointly with price marks. It motivates this separation;
it is not validation of our mechanism. A low-order stochastic activity process,
seasonality and an explicit size/fragmentation model are hypotheses to test,
rather than assuming that count overdispersion is a coordination parameter.

Check pressure correlations, activity variation, execution-size concentration
and joint flow/return moments at 5, 15 and 60 minutes together. A fitted time multiplier
that matches one correlation is insufficient. Preserve uncertainty from existing
microscopic calibration and count its offline information cost.

## Carry response and tail uncertainty into the same risk scenarios

Calibrate calendar-time volume and price response jointly with the state model.
Retain conditional flow/residual dependence and parameter uncertainty; avoid
incompatible separately predicted cross moments or scalar risk clipping. Evaluate
tail support and proper interval scores, not coverage alone. Add at most one
clearly justified new observable when current information is inadequate, and
give the same observable to every comparator.

## Freeze the market test after the observation map passes

Use the already examined histories for model development and posterior-predictive
checks. Compare with direct-flow, prior-only, return-HAR and macro-statistical
controls under explicit raw fields, history, offline labels, supplied model law
and tuning costs. Only then freeze candidate, budget, precision objective and
independent dates/assets. Reduced total information at comparable reliability or
improved equal-information accuracy remains the acceptance criterion.
