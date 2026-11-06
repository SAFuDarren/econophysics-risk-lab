# One-event covariance ordering under multifactor input

## Claim and exact scope

At a fixed complete pre-event state, hold every node's input marginal law,
positive trading weight and activity probability fixed. Lowering every pairwise
Gaussian input correlation weakly lowers the variance of the next event's
signed weighted flow. This includes refining the present balanced factor
partition from four groups to twelve, or lowering between-factor correlation.

This is a restricted application of a standard Gaussian covariance identity,
not a new mathematical theorem. It does not order a complete eight-event bar,
one-hour price RV, cumulative-return risk, equilibrium behavior or market data.

## Derivation

The known prior-state field H_i contains neighbor influence, fast/slow coupling,
inertia/adaptation and the already observed calendar return. The factor remap
preserves the complete current residual signal u_i0. At the next bar's factor
innovation, the first-event conditional mean of the new fast sign is

    t_i(X_i)=tanh(1.5[H_i + sigma_s phi u_i0
                                 + sigma_s sqrt(1-phi^2) X_i]),

where X is standard multivariate Gaussian and

    Corr(X_i,X_j)=rho_0[c+(1-c)1{g(i)=g(j)}], i!=j.

Thus all single-node t_i marginal laws remain fixed. Independent transition
uniforms and independent Bernoulli(a) activity yield, for xi_i=A_i s_i,

    E xi_i = a E t_i,
    Var(xi_i)=a-a^2(E t_i)^2,
    Cov(xi_i,xi_j)=a^2 Cov(t_i(X_i),t_j(X_j)), i!=j.

For jointly standard Gaussian (X,Y) with correlation q and bounded smooth f,g,
Gaussian differentiation and two integrations by parts give

    d/dq E[f(X)g(Y)] = E[f'(X)g'(Y)].

In the present case,

    t_i'(x)=1.5 sigma_s sqrt(1-phi^2) sech^2(1.5[...]) >= 0.

The derivative of each cross expectation, and hence covariance, is nonnegative;
the separate marginal means do not depend on q. The diagonal action variances
are constant. Finally,

    Var(F)=1200^2[sum_i w_i^2 Var(xi_i)
                       +2 sum_{i<j} w_i w_j Cov(xi_i,xi_j)],

with w_i>0, so entrywise reductions in pair correlations weakly lower Var(F).

The implemented factor grouping uses a fixed permutation rank modulo M. Since
four divides twelve, equality modulo twelve implies equality modulo four.
Twelve groups therefore refine four groups: no pairwise Gaussian correlation
increases. Increasing only the number of labels at c=1 changes no correlation
and must leave both this result and complete paths unchanged.

## Why this does not prove multistep price-risk monotonicity

Within subsequent events, the prior fast/slow states and inhibitory traces
change. Price impact is nonlinear, predictable impact is partially recovered,
and later decisions use actual noisy calendar returns. Those operations do not
satisfy the fixed-field/fixed-marginal comparison above. The 12-bar primary
metric is expected sum of squared returns, not this one-event flow variance.
Its ordering must come from the separately frozen paired simulations.

The remap also means that the intervention preserves the current complete input
and changes the future innovation covariance law. It is not a claim that the
different factor ecologies were each sampled from their own stationary law.

## Independent numerical check and provenance

`audit/check_one_event_quadrature.py` reconstructs the known fields directly from
the sealed source NPZ, without importing production code. It uses bivariate
Gauss-Hermite integration, reconstructs all off-diagonal action covariances and
the full weighted flow variance for M=1,4,12 and c=0,.6,1 on eight fixed origins.
It compares 48-node and 96-node integration, checks Price derivatives against
centered finite differences, and preserves full numerical values in CSV/JSON.

Reference: Felix Voigtlaender, *A general version of Price's theorem*,
https://arxiv.org/abs/1710.03576 (v2, 2020; accepted in Journal of Theoretical
Probability), doi:10.1007/s10959-020-01017-w. The bounded tanh special case here
requires no generalized-distribution extension.
