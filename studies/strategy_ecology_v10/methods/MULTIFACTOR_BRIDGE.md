# Multifactor strategy ecology: mathematical bridge and interpretation contract

This extension retains the 48-unit weighted fast/slow decision network. The
unit is an effective trading unit, not an observed firm, account or person.
The new factor labels specify shared input exposure; peer influence remains in
the original graph fields. They are separate causal channels.

## 1. Input covariance, held fixed at each node's marginal variance

Let unit i have positive weight w_i, with sum_i w_i=1, and factor-group label
g(i). Let z_0, z_1,...,z_M and e_i be mutually independent unit-variance Gaussian
innovations. The standardized signal is

u_i = sqrt(rho_0)[sqrt(c) z_0 + sqrt(1-c) z_{g(i)}]
      + sqrt(1-rho_0)e_i.

Multiplication by the fixed signal amplitude sigma_s supplies the decision-field
signal. Its marginal variance is sigma_s^2 for every i, independent of M and c.
For distinct i,j,

Cov(sigma_s u_i, sigma_s u_j)
 = sigma_s^2 rho_0[c+(1-c) 1{g(i)=g(j)}].

Here rho_0 is the fixed fraction of input variance allocated to factor exposure;
c is correlation between different factor inputs. Neither is the fraction of
coordinating people, funds or observed risk. Let P_g=sum_{i:g(i)=g} w_i. Then

Var(sum_i w_i sigma_s u_i)
 = sigma_s^2[(1-rho_0)sum_i w_i^2
              +rho_0{c+(1-c)sum_g P_g^2}].

The weight-adjusted factor count is M_w=1/sum_g P_g^2. Balanced *node counts*
do not imply equal P_g under heterogeneous capital weights. At c=1 all factor
labels are perfect clones, and the formula is independent of M. At c=0,
diversification lowers the factor component through sum_g P_g^2, conditional on
the unchanged node weights. This is an input-variance result. The nonlinear
tanh decisions, network feedback and price transmission must still be simulated;
the equation does not assert monotonic one-hour price RV in every state.

## 2. Persistent factors and same-origin interventions

All factor and idiosyncratic states use the retained AR coefficient phi. A new
factor assignment can preserve the initial complete node signal by remapping the
initial idiosyncratic state. Since all components use the same phi, their initial
signal contribution to the conditional mean remains phi^h times the original
signal at horizon h. The conditional innovation variance at h multiplies the
one-step stationary expression above by (1-phi^(2h)).

Remapping generally changes the distribution of initial idiosyncratic states.
The resulting experiment is therefore a fixed-initial-state comparison of
future innovation covariance, not a comparison of stationary market ecologies.
Long-run migration experiments need their own warm-up, estimand and controls.

## 3. Volume, quant scale and accommodation

Let A scale the signed and unsigned trading quantities supplied by the retained
network, while the independent background quantity is not multiplied by A.
At A=1 the original market law must be recovered. An increase of A changes both
signed pressure and total volume, so part of risk may come from the retained
activity-scaled price noise. A matched-volume/signed-flow control is needed to
separate these channels; one must not call the entire A effect coordination.

The predictable-impact recovery calculation must use the same A and background
law as realized orders. The capacity target must enter both predicted and actual
capacity updates. Otherwise a change in the intervention also creates an
unintended error in impact recovery.

The capacity state is a normalized latent response condition. Its target is not
measured exchange depth, funding availability or a monetary regulatory limit.
Price parameters stay fixed within a counterfactual pair; their inherited
calibration uncertainty is not removed by a precise Monte Carlo comparison.

## 4. What migration can and cannot establish

A specified redistribution rule may move normalized capital/trading weights
between strategies based only on information available before the next trade.
It can test a mechanism under that rule. The original nodes do not contain an
observed position ledger, balance sheet or full strategy return series; a proxy
performance measure must not be relabeled as actual fund wealth or liquidation.

If node weights change, three separate objects may change: own traded quantity,
neighbor influence (requiring graph renormalization), and group exposure P_g.
Every comparison must state which are allowed to move. Total-weight conservation
does not make realized per-bar V constant because heterogeneous node activity
still interacts with weights. Separate a free endogenous-capacity experiment
from capacity-held controls.

## 5. Scientific boundary

The study can establish conditional model mechanisms and counterfactual risk
responses. It does not identify actual quant institutions, observed factor
exposures or a real-market coordination-risk share. It also does not establish
forecast superiority over HAR without a new matched-information empirical test.
No threshold found in a finite grid is a universal phase transition or optimal
regulatory limit. A failed intervention or sign reversal is retained evidence.

## 6. A restricted nonlinear one-event bridge

For one network event at a fixed complete state, write the new fast sign as s_i
and its conditional mean given Gaussian input U_i as

    t_i(U_i)=tanh[1.5(H_i+sigma_s U_i)].

The fixed field H_i includes the known old neighbor/slow/memory state and known
calendar feedback. Independent transition uniforms and independent activity
draws A_i~Bernoulli(a) give, for xi_i=A_i s_i,

    Var(xi_i)=a-a^2 (E t_i)^2,
    Cov(xi_i,xi_j)=a^2 Cov(t_i(U_i),t_j(U_j)), i!=j.

If Gaussian marginal means/variances stay fixed, E t_i and each diagonal
variance stay fixed. For standard bivariate Gaussian inputs with correlation q,
Gaussian differentiation/integration by parts gives

    d/dq E[f(U_i)g(U_j)] = E[f'(U_i)g'(U_j)].

For these bounded smooth increasing tanh functions the right side is
nonnegative. Therefore lowering every pairwise input correlation, while
preserving marginals and positive trading weights, weakly lowers one-event flow
variance. The M=4 to M=12 assignment is a nested group refinement because 4
divides 12; pairwise input covariance cannot increase in that refinement at fixed
c. Lowering c at a fixed partition also cannot increase pairwise covariance.
The initial-signal remap keeps the conditional node input means fixed, so the
same statement applies to the first event after the next Gaussian innovation.

The differentiation formula is a standard Price identity, not a new theorem
claimed by this project. A primary mathematical treatment is F. Voigtlaender,
"A general version of Price's theorem", arXiv:1710.03576,
https://arxiv.org/abs/1710.03576 (Journal of Theoretical Probability,
doi:10.1007/s10959-020-01017-w). This project applies its smooth bounded
bivariate special case.

This result is deliberately restricted to one event with fixed prior fields.
After repeated events, inhibitory adaptation, changing states, impact recovery
and actual-return feedback change the relevant marginal laws and fields. The
one-event ordering does not prove monotonic 12-bar price RV, cumulative-return
variance, a stationary market ordering or any real quant-fund effect. Formal
multi-event results remain the saved conditional simulations.
