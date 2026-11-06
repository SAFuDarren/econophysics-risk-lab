# Weighted collective dynamics and the synthetic trading market

Version 1.0.0, 6 November 2026. Status: implemented mechanism experiment, not an empirically identified Bitcoin network. The engine is web/assets/trading-engine.js; its configuration snapshot is configs/collective_trading_v1.json. All numerical defaults are synthetic teaching choices, not fitted market parameters.

## 1. What remains from the original model

Let a decision group C carry positive trade-size weight Q_C and action xi_C. At fixed weights,

\[
F=\sum_CQ_C\xi_C,\quad
\operatorname{Var}(F\mid Q)=\sum_CQ_C^2\operatorname{Var}(\xi_C)
+2\sum_{C<D}Q_CQ_D\operatorname{Cov}(\xi_C,\xi_D).
\]

Independent symmetric actions active with probability q recover q sum_C Q_C². Equal individual size recovers the original population-size expression. This is an effective trade-weight statement, not a recovery of natural-person group sizes. Cross-group dependence can amplify or offset variance, so the independent formula is not applied unchanged to the coupled engine.

For a target horizon H, splitting also requires

\[
\operatorname{Var}\left(\sum_{t=1}^H F_t\right)
=\sum_t\operatorname{Var}(F_t)+2\sum_{t<s}\operatorname{Cov}(F_t,F_s).
\]

A common-sign 100-unit demand split into ten 10-unit child orders has cumulative-flow variance 10,000 under a symmetric parent sign. Treating the children as independent produces 1,000. The sum of squared child flows is 1,000 in both constructions: cumulative-return variance and realized-variance targets therefore must not be substituted for one another. Constant linear price response with residual orthogonality transfers the corresponding flow variance to cumulative price-return variance; it does not remove the assumptions or generate forecast evidence.

## 2. The implemented weighted network

The fixed node set has 48 effective decision units with positive capital/trade weights normalized to sum one. Default weights are lognormal draws; `weighting:'equal'` is an ablation. The weights set influence and trading contribution. Each unit has two binary states s_i^f and s_i^s, representing fast and slow decision layers, and a bounded signed trace z_i. They are simulator states, not observed investor beliefs or position holdings.

Each layer has an undirected sparse graph: nearest ring neighbors, second ring neighbors and random additional links. The graphs are fixed during a session. Node orientation can change; network rewiring is deliberately a separate, unimplemented hypothesis. Within-layer pressure at i is the capital-weighted mean direction of its neighbors:

\[
u_i^h=\frac{\sum_{j\in N_i^h}Q_js_j^h}{\sum_{j\in N_i^h}Q_j}.
\]

Fast/slow interdependence is same-node cross-layer influence. It is an opinion/decision coupling, not the functional-failure dependency of catastrophic network percolation.

Public network edges include both intralayer links and `layer:'cross'` links between the same actor's fast/slow representations, with sourceLayer/targetLayer metadata. A diagram collapsing an actor into one circle should show this as within-node coupling rather than treating a zero-length drawing as absent influence.

The fast state is sampled synchronously using p_i^f=(1+tanh(B H_i^f))/2, with

\[
H_i^f=J_fu_i^f+\kappa s_i^s+\rho_f\mu s_i^f-a_f\mu z_i+h_t.
\]

The slow state has an analogous field J_s u_i^s+0.55 kappa s_i^f+rho_s mu s_i^s−a_s mu z_i+0.25 h_exec,t, and updates with probability 0.14 each tick. The signed adaptation trace satisfies z_i'=(1−epsilon)z_i+epsilon s_i^f,new, epsilon=.055. Public `coupling` sets kappa, `memory` sets mu. Setting them to zero removes the corresponding terms without changing random-stream draw counts.

The trace term is a declared adaptive-inhibition hypothesis: long-lasting orientation can reduce its own attractiveness. It does not mean a weak minority naturally attracts everyone. Strong positive influence alone need not generate reversal; dynamics may maintain an orientation, fragment or switch depending on parameters and innovations. No periodic orbit or inevitable crash is promised.

## 3. Minimal macro closure for independent empirical testing

A possible low-dimensional closure replaces local neighbor means by observed aggregate pressure proxies and uses distinct fast/slow rates:

\[
m_f'\approx(1-\nu_f)m_f+\nu_f\tanh(J_fm_f+\kappa m_s+\rho_fm_f-a_fz+h),
\]
\[
m_s'\approx(1-\nu_s)m_s+\nu_s\tanh(J_sm_s+\kappa_sm_f+\rho_sm_s-a_sz+h_s),\qquad
z'=(1-\epsilon)z+\epsilon m_f.
\]

This is a candidate closure, not an exact inversion of graph structure or trader psychology. Its empirical parameters must be estimated within each declared information/history budget. A model may reproduce synthetic behavior and still fail held-market risk accuracy.

## 4. Order flow and accommodation

Each node independently becomes active with probability .58 per tick. Active background quantity is 1,200 Q_i, with sign s_i^f. A separately declared parent-order program contributes child quantity P_t and sign d_t. Hence

\[
V_t=1200\sum_iQ_iA_{it}+P_t,\quad
F_t=1200\sum_iQ_iA_{it}s_i^f+d_tP_t,\quad |F_t|\le V_t.
\]

The order plan is announced before execution; current signed execution and revealed intent feed the decision field. Guided mode increases the reliability and steadiness of the declared execution conditions. Experiment mode allows skipped/smaller fills and weaker reaction to intent. No future price is assigned from the plan.

Positive accommodation L_t mean-reverts with depletion from absolute current pressure and independent noise, constrained to [.35,1.8]. It is a simulated response state, not observed order-book depth. Price log return is

\[
r_t=\operatorname{clip}\left(.009\tanh\left[.34(F_t/1200)/L_t\right]+\eta_t,-.018,.018\right),
\qquad \eta_t\sim N(0,.00115^2).
\]

The synthetic OHLC bar has current opening and closing prices, with independently generated small positive upper/lower wicks. Starting price is 100. Player trades do not alter this background market in version 1, making same-path score and benchmark comparisons well-defined.

## 5. Causal, reproducible scenarios

All event times are absolute ticks, independent of the requested total session length. `buy` and `sell` announce at tick 18 and execute from tick 24 to 59; `split` has smaller children from tick 24 to 107; `turn` begins with buying and announces a new sell program at tick 75, executing from 82 to 119. These are synthetic conditional experiments. A reversal after an opposing program is not labelled an endogenous prediction of a crash.

The `externalOrders:false` control removes all announced parent programs and their intent fields. It isolates the interacting-node background dynamics; its stochastic alignment changes are retained without claiming a periodic endogenous boom/bust law.

Only events at the current or an earlier tick are generated. Event bodies describe revealed intent, current execution/completion or current alignment change. They do not disclose a future closing price, guaranteed profitable direction or a future event list. Guided and experiment mode are visibly distinguished. Plans and simulation code are public; this is not a secure competitive trading game.

Independent PRNG streams handle initial topology, node state updates, price/accommodation noise, order fills and OHLC wicks. Snapshot reads consume no randomness. Updates consume a fixed draw pattern for ablations. Same seed/config gives the same path; extending steps preserves the path prefix; stepping after completion does not alter state. `reset` recreates the original session.

## 6. Observable phases and their limits

Let M_f=sum_i Q_i s_i^f and A=|M_f|. The simulator reports forming when A>=.22 and its one-tick increase exceeds .025; fragmenting when the previous A>=.22 and the decline exceeds .025; holding when A>=.42 otherwise; mixed for remaining states. These are fixed display definitions from current/past simulator states. They are not an inferred real-market stage or a retrospective pre-crash label.

`pressure` is F/V, `coherence` is |M_f|, `fastAlignment` and `slowAlignment` are signed weighted state means. `switching` is the total weight whose fast state changed on the current tick. Actual market F/V is only an executed-pressure proxy; it does not identify M_f, real network edges or investor positions without additional assumptions.

## 7. Controlled tests and interpretation

tests/test_trading_engine.cjs independently enumerates the original weighted law, a coherent-block comparison and the split-parent covariance example. It checks a monotone scalar consensus map as a no-automatic-cycle control. Engine checks cover deterministic replay, reset, mutation isolation, OHLC/flow bounds, event chronology, horizon prefix invariance, parameter ablations and completed-path stability.

The same test command writes an ensemble of synthetic runs and all declared ablations, with seed as the independent simulation unit. The resulting intervals concern this chosen simulator/configuration only. They do not establish a universal network law, real-market crash predictability, profitability or an information-efficient risk advantage. Those claims require the separately frozen empirical study.

## 8. Model precedents

- Alvarez-Zuzek et al., *Interacting Social Processes on Interconnected Networks* (2016), https://doi.org/10.1371/journal.pone.0163593 : opinion/decision dynamics on coupled networks can coexist or one orientation can dominate. Our weighted financial interpretation is a separate hypothesis.
- Iñiguez et al., *Opinion and community formation in coevolving networks* (2009), https://arxiv.org/abs/0908.1068 : opinion and relation dynamics with different time scales. This engine keeps graph links fixed and varies node states instead of claiming that all features of that model are implemented.
- Sato and Kanazawa, *Inferring Microscopic Financial Information from the Long Memory in Market-Order Flow* (2023), https://doi.org/10.1103/PhysRevLett.131.197401 : account-resolved order-splitting evidence motivates retaining temporal direction dependence, not identifying real parent orders in this synthetic game.
- Cont, Kukanov and Stoikov, *The Price Impact of Order Book Events* (2014), https://arxiv.org/abs/1011.6402 : order-book imbalance and depth motivate a separate response/accommodation stage. The engine uses signed traded flow and a synthetic response state, not the paper's measured full order-book imbalance.
