# Mathematical interface and experiment units

## Weighted decisions and the original network

For positive fixed weights Q and action covariance Γ, F=Qᵀξ and
Var(F|Q)=QᵀΓQ. With fixed marginal variances, positive cross-action covariance
increases flow variance. Independent symmetric actions with activity q recover
qΣQ². Weight concentration, within-step dependence and cross-time persistence
are separate quantities.

The retained generator contains 48 effective units. Each has a normalized
positive trading weight, fast/slow binary directions and an adaptation trace.
Each layer has a fixed sparse graph, and the same unit's fast/slow states
influence one another. These are coupled decision layers, not function-failure
dependencies or empirically recovered investor relationships.

Let C=1200, activity a=.58, and t_i=tanh(1.5H_i) be the expected next fast action
in the unextended source law. Conditional on full state S and a fixed pulse d:

    E[F|S,d] = d + C a Σ_i w_i t_i
    Var(F|S,d) = C² Σ_i w_i² (a − a²t_i²).

The shared-input comparison integrates over one common Gaussian signal instead
of independent signals with identical marginals. Positive same-direction
loadings produce a nonnegative covariance increment at fixed state. Its
multi-period return effect is evaluated separately with complete stochastic
paths, accommodation and price noise.

## Propagation and interventions

D01 uses eight fixed full states, pulses −24/0/+24, 48 future steps, 512 ensemble
paths per state/dose and 4096 independent reference paths per state/dose. Saved
standard errors describe Monte Carlo estimation of conditional means. They are
not intervals for individual future realizations.

N01 compares baseline, shared signal, independent signal, positive lagged price
feedback, negative lagged price feedback and a shared activity rule. Each arm
has 128 paired independent seed units and 240 steps. The activity anchor uses
64 separate training seeds and is frozen before comparison. Paired basic
bootstrap intervals use 19,999 draws; Holm adjustment covers five interventions
and two primary metrics. The activity rule changes participation, not forced
liquidation or a strategic rush to exit.

## Observable conditioning and risk

The conditional simulation mixture uses a 2048-history bank, 32 tuning histories,
64 calibration histories and 128 independent test histories. Features use only
the 32 observed ticks 65–96 of F,V,K,r. Test hidden states and future outcomes are
validation labels. The selected mixture places equal positive weight on 128
nearest standardized observable feature vectors. It is approximate simulation
conditioning, not an exact Bayesian posterior.

All fitted risk controls share the bank's future labels. MacroGamma has the same
13 macro features; the return HAR comparator has 1/8/32-step squared-return
features. The supplied source law, priors, bank, labels and tuning are offline
information costs. Source diversity prevents one particular ancestry-collapse
mechanism; state coverage must be evaluated separately.

Each future scenario jointly generates flow, return and accommodation, preserving
compatible cross moments. The target RV is the sum of squared log returns over
the selected horizon. Cumulative-return variance additionally contains cross-time
covariance and is not substituted for RV. QLIKE is y/h − log(y/h) − 1, where
y and h are positive realized and forecast RV; smaller values are better.

For 90% split-conformal intervals, q is the 59th sorted calibration score
abs(log(y/h)) among 64 cases, and the interval is [h exp(−q), h exp(q)]. The
construction has marginal exchangeability scope over simulated cases. It does
not establish market-state conditional coverage or calibrate hidden HHI labels.

## Execution units and market transport

Raw execution B=Σv_i² and grouped B depend on the declared execution unit. The
centered amplification Var(F)/mean(B) differs from energy E[F²]/mean(B).
If an estimated and measured amplification share the same observed numerator,
their relative-error expression cancels that numerator; it does not independently
validate recovered flow variance.

The transport table compares 64 source-network blocks with 1989 blocks from
663 previously inspected Bitcoin days. Market blocks contain 96 five-minute bars.
Within-day blocks are not independent dates. The model's K counts effective
active units, while exchange K counts executions. An arrival/fragmentation and
calendar-time response layer remains necessary before freezing a new independent
market prediction test.
