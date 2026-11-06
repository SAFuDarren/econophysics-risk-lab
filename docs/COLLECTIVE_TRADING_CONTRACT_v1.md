# Collective dynamics and trading lab: implementation contract

Frozen 6 November 2026 before new scoring. Workstreams implement the nine tasks in COLLECTIVE_TRADING_VALIDATION_v1.md. This file defines dependencies and public interfaces; it is not empirical evidence.

## Ownership and sequence

1. Root owns this contract, account/scoring module, integration, independent acceptance and release.
2. Mechanism workstream owns assets/trading-engine.js, controlled simulation tests, mechanism mathematics and configuration. Publish the API below before polishing numerical scenarios.
3. Frontend workstream owns trading.html, assets/trading.css and assets/trading-ui.js. Build against the fixed API; no changes to engine/account modules or existing main navigation pages.
4. Empirical workstream owns the new isolated Collective_Dynamics_Information_Study_v1 numerical study. Freeze model/protocol before evaluation; no old study edits or silent use of hidden microscopic calibration.
5. Independent review follows functioning engine, UI and numerical outputs. Root integrates only reviewed results and tests the complete page on desktop/mobile.

## Mechanism and evidence boundary

Weighted directional units, node-state changes and coupled fast/slow opinion dynamics form a candidate mechanism. Cross-layer influence is not physical node-failure percolation. The trading market is synthetic and must not be labelled an identified Bitcoin network or a validated forecast. Preserve original fixed-model evidence. No future target returns may enter a risk predictor or an advance scenario signal.

For H bars, variance of cumulative return includes cross-time covariance; next-day realized variance is a sum of squared bar returns and has a different target. Do not add covariance terms to realized variance as if the targets were equal. Known-weight group variance laws require stated independence/symmetry; coupled models need cross-covariances.

## Browser module interfaces (UMD: window globals and CommonJS)

`TradingEngine` exports:
- `version`, `scenarios`: array of {id,title:{en,zh},description:{en,zh}}. IDs: `buy`, `sell`, `split`, `turn`.
- `create({seed=...,scenario='buy',mode='guided',steps=180, coupling=...,memory=...})`: returns {step(), snapshot(), reset(), config}. Mode is guided or experiment. Unknown scenario/invalid options rejected.
- `step()`: advance exactly one tick, return a public snapshot. At end, return the same last snapshot without extra noise/trades.
- `snapshot()`: deep copy with {tick,totalSteps,done,price,bars,events,metrics,network}. Each bar: {tick,open,high,low,close,volume,flow,pressure,phase}. Events: {id,tick,type,title:{en,zh},body:{en,zh}}. Events include only information available by current tick; never include future path/outcomes.
- `metrics`: {pressure,coherence,liquidity,phase,fastAlignment,slowAlignment}, finite bounded values; phase in forming/holding/fragmenting/mixed. These are simulator states/proxies, not observed market beliefs.
- `network`: {nodes:[{id,x,y,weight,fast,slow,active}],edges:[{source,target,layer,weight}]}. May be used for an optional small mechanism view. No DOM dependency.
- `simulate(config)`: complete path, for controls/replay, same generator as create; preserve chronology and deterministic seeds.

Return price starts at 100, remains strictly positive, bars always satisfy OHLC bounds, synthetic volume nonnegative and |flow|<=volume. Guided mode implements explicit teaching conditions with advance intent events; experiment mode uses only current intent and stochastic model response. Same seed/config produces identical paths, independent of snapshot reads or playback speed. Different scenarios use isolated RNG state. Optional coupling/memory off settings are controlled ablations. Player is a price taker in first version.

`TradingAccount` exports:
- `create({initialCash=100000,feeBps=5,slippageBps=2,maxLeverage=1})`: stateful portfolio.
- `trade({side:'buy'|'sell'|'short'|'cover'|'close',fraction:0.25|0.5|1,price,tick})`: execute from current known price; returns {ok,message,trade?,state}. Root owns exact accounting/rules.
- `mark(price,tick)`: update equity/drawdown and return summary.
- `snapshot()`: {initialCash,cash,quantity,averageEntry,equity,unrealizedPnl,realizedPnl,totalFees,returnPct,maxDrawdownPct,grossExposure,history,trades}.
- `close({price,tick})`: settle long/short consistently.
- `review({bars,events})`: costed results, fixed transparent grade and same-path passive/cash benchmark, replay notes; no model-prediction-success claim.

Final account clarification: trade.realizedPnl is the additive change in portfolio realized P&L; trade.roundTripPnl separately allocates entry costs to closing trades. review({bars,events,done}) marks the passive benchmark during the round and closes it with exit costs when done=true.

## UI design and execution rules

Read frontend-design skill and produce a compact design plan before code. Reuse the existing site's bundled fonts and navigation/language behaviour. A restrained market workbench, clear candle chart, meaningful buy/sell colours and visible virtual account are the subject-specific focus. Default page uses Chinese or English consistent with existing language choice. Keep supported user-facing labels concise. Use fictional instrument name and a small synthetic-market indicator.

User can choose scenario/mode, start/pause/step/retry, select 25/50/100% trade size, buy/sell or short/cover, close position and inspect a review. Auto-pause before end is unnecessary; settle all positions at the final bar with costs. Opening review pauses playback. Scenario changes reset both engine and account; confirm only if needed for actual action semantics (no browser confirmation dialogs for routine reset). Avoid stale charts, hidden oversize mobile controls and leaked future data in public events.

Guided-mode refinement: playback pauses when a new intent is revealed, giving the learner time to decide before the announced execution begins. Experiment mode continues normally. Account insolvency disables new orders but leaves the remaining market observable.

## Acceptance gates

- Reproduce analytical independent/coherent weight cases; include splitting temporal dependence and no-automatic-cycle controls.
- Engine deterministic, finite/bounded OHLC, chronological events, prefix invariance and completed-path stability.
- Account: long and short cash/equity identities, partial closing/reversal rules, fees/slippage, mark-to-market, exposure rejection, insolvency handling, exact end settlement, fixed scoring rules.
- Empirical: frozen protocol, matched information/history, all calibration charged, causal features, primary QLIKE and paired date-block uncertainty, complete negative results, no test-period model selection.
- Browser: keyboard and mobile taps, start/pause/step/reset/scenario/mode/trading/review, no uncaught console errors, no horizontal overflow; bilingual labels consistent.
- Existing navigation and preview remain intact; all local links work; source-derived charts and simulated plots labelled accurately.
- Final release: nine-item checklist with evidence paths, known limitations, isolated reproduction, reviewed desktop/mobile screenshots and deployment verification if published.
