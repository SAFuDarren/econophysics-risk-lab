# Controlled collective-dynamics simulation

6 November 2026. Evidence type: exact mathematical controls and synthetic mechanism simulations. The engine's parameters are teaching choices. No real-market fitting, empirical prediction advantage or investor-count recovery is claimed here.

## Test object and outputs

Run `node tests/test_trading_engine.cjs` from the repository root. Eleven compound acceptance gates cover exact weighted-action enumeration, common-parent temporal covariance, the distinction between cumulative variance and RV, a scalar no-cycle control, options, deterministic replay, snapshot isolation, resets, horizon prefixes, completed paths, causal events and market bounds. The command also writes four CSV tables under results/tables/collective_trading_v1/ and the audit results/checks/collective_trading_engine_v1.json.

There are 32 independent seed values. Four scenarios in two modes contribute 256 complete runs. Four additional ablations of the turn/experiment case contribute 128 runs, for 384 runs total. Ablations share innovation streams within a seed; they are paired comparisons, not independent replications of a market.

## Exact controls

| Construction | Cumulative signed-flow variance | Sum of per-child squared flows |
|---|---:|---:|
| Independent symmetric units with weights 1,2,3,4 | 30 | 30 |
| One coherent symmetric 10-unit block | 100 | 100 |
| Ten same-parent, same-sign 10-unit children | 10,000 | 1,000 |
| Ten independent-sign 10-unit children | 1,000 | 1,000 |

The last two rows directly demonstrate why cross-time covariance belongs to cumulative-flow/cumulative-return variance and must not be inserted into an RV target without changing the estimand. The independent weighted law is also enumerated with activation probabilities .1,.5,1. A one-dimensional monotone reinforcement map approaches consensus without sign cycles; reinforcement alone therefore does not automatically implement recurring boom/bust behavior.

## Conditional scenario behavior

Whole-session percentage returns, mean ± between-seed SD:

| Scenario | Guided conditions | Experiment conditions |
|---|---:|---:|
| Buy program | 23.67 ± 10.64 | 11.49 ± 8.91 |
| Sell program | −16.91 ± 6.77 | −8.90 ± 6.25 |
| Small persistent buy children | 23.23 ± 11.70 | 11.20 ± 7.44 |
| Initially buying, then a new sell program | −3.13 ± 8.05 | −0.73 ± 5.92 |

Guided mode has steadier execution and a stronger reaction to announced intent; experiment mode has incomplete/random fills and weaker intent response. These are distinct conditions, not a performance contest. All cases, seeds, realized variance, maximum drawdown and phase counts are retained in the run table.

For the default teaching seed 5253, the buy path rises from 101.997 at tick 24 to 125.032 at tick 60. The sell path moves from 100.655 to 84.098 over those ticks. In turn, price is 127.751 at tick 75 and 105.509 at tick 120, after a new sell program is announced at 75 and starts at 82. These are generated signed-flow responses under declared synthetic conditions. No future price tape or rule assigns these closing prices. The turn example is not evidence of an unannounced endogenous crash prediction.

## Ablations retain non-universal effects

Turn/experiment mean realized variance, with 32 seeds each:

| Variant | Mean RV | Between-seed SD |
|---|---:|---:|
| Full mechanism | .00090522 | .00023753 |
| Cross-layer coupling off | .00090828 | .00020308 |
| Memory/adaptation off | .00103182 | .00029984 |
| Equal capital weights | .00098029 | .00026271 |
| Announced parent programs off | .00035738 | .00006463 |

The cross-layer RV difference is close to zero at these parameters, and memory/adaptation dampens the mean RV relative to its removal. Neither coupling nor heterogeneous weights universally raises total price risk in this interacting, adapting construction. The independent-group square-weight theorem remains a special-case result. The order-free run retains stochastic network dynamics without a predetermined program, and its mean percentage return is .25 with a wide between-seed SD of 6.59.

Mean intervals in simulation_summary.csv use a pointwise approximate 95% t interval over independent seeds. simulation_paired_ablations.csv retains paired differences and paired SD. These descriptive intervals do not receive a familywise significance interpretation, and a zero-spanning interval is not proof of equality. The ensemble is one fixed parameter configuration, not a parameter-space phase diagram or a population sample of financial markets.

## Causal and engineering acceptance

Every public event is generated at its reveal tick or earlier. Intent appears before its execution, while the later opposing program is absent from earlier snapshots. No snapshot consumes random numbers or contains future prices. Different session lengths have identical overlapping prefixes. All 384 paths have positive finite prices, consistent OHLC bounds, nonnegative volume and absolute flow no larger than volume; cross-layer and memory-off settings actually change paths.

Repeat the complete ensemble in an isolated directory with `node scripts/research/reproduce_collective_trading_engine.cjs`. All four tables must match byte-for-byte. The browser uses this same engine rather than an independent decorative price generator. The separately frozen empirical study must establish whether a low-information macro closure adds any market-risk advantage.
