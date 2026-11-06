# Real-market replay: large executed flow before substantial price moves

Nine BTC/USDT excerpts use original Binance one-minute OHLC candles and independently aggregated executed-order flow. Four primary alerts are followed by an upward close-price excursion; five by a downward excursion. The same-direction move reaches 2.09–6.52% within 90 minutes. Excerpts include genuine pullbacks and secondary, potentially competing alerts. These are retrospectively selected teaching excerpts, not a strategy backtest.

The full source pool contains 26 UTC days in 2025: the previously audited 5th and 20th of each month, plus March 2 and April 9. Fifty-two official archives provide 37,440 one-minute bars and the corresponding aggregate executions. Every archive has a recorded exchange SHA-256 check. Reaggregated total quote volume, taker-buy quote volume and raw fill counts reconcile with the official candles. All selected OHLC values match the original candle archives exactly.

## Observable signal

A large execution is one aggregate trade with price × quantity at least 100,000 USDT. Buyer-maker=false is aggressive buying; true is aggressive selling. Aggregate fills can belong to the same taking order at the same price and time. They do not identify beneficial owners, complete parent orders or whether a trader opens a long/short position.

After a minute closes, sum large buying and selling over the last three minutes. An alert requires the dominant side to carry at least 70% of large directional flow and exceed both 1 million USDT and its own preceding 120-window 90th percentile. The threshold excludes the current window. Alerts are separated by a 12-minute cooldown. Future prices never enter alert generation.

Each primary excerpt is selected **after** observing at least a 2% same-direction close-price excursion in the next 90 minutes, whose maximum occurs at least five minutes later. A direction-alternating, date-diversifying selector prioritises actual adverse moves and excludes excerpts whose primary alerts are within 180 minutes on the same date. It produces nine excerpts, rather than inventing more qualifying cases. See tables/all-alerts.csv, eligible-candidates.csv and selected-cases.csv for the complete selection trail.

## Replay contract

The playable round lasts 120 real minutes, with 40 preceding candles plus the completed starting candle visible as context. The original price scale, candles and volume are retained. Each step reveals the next completed minute; no future OHLC or outcome appears in the replay snapshot. All qualifying alerts inside an excerpt are displayed at their actual close time. A primary alert is not given special visual status.

Excerpt labels conceal the selected outcome during play. The UTC date and outcome summary are revealed after the last candle. This is an open-source classroom interaction, not a secure competition: the underlying static library and source are public. Turning hints off suppresses large-flow messages and their guided pauses, without altering the path. Speed and signal controls remain available.

The account is virtual and accepts the historical completed-bar price with the declared fees/slippage. Virtual short exposure uses the same spot price path; it is not a reconstruction of a futures position or borrowing market. Passive comparison begins at the playable starting close, excluding warm-up candles. Real replay does not display invented network nodes as historical observations. The separate mechanism tab retains the synthetic model and its controls.

## Reproduce

Use Python with NumPy and pandas, and Node.js for the replay/account tests.

```sh
python studies/historical_replay_v1/verify.py
python studies/historical_replay_v1/reproduce.py
node tests/test_trading_history.cjs
```

The first command independently checks signal thresholds, timing and every selected candle against the complete derived pool. The second rebuilds all selection tables and the browser JSON in a fresh directory, requiring byte equality. Neither command silently downloads data.

To rebuild the complete input from official archives, use:

```sh
python studies/historical_replay_v1/code/acquire.py \
  --cache /tmp/binance-replay-cache \
  --output /tmp/replay-input-rebuild
```

Repeated `--reuse-cache /path/to/existing/archives` options avoid downloading known official archives. Acquisition checks each archive against the recorded exchange SHA-256. Run verify.py with `--raw-kline-cache /path/to/candle/archives` to compare every selected OHLC value directly with original Kline files. The executed raw rebuild reproduced the complete derived input byte-for-byte.

Browser acceptance uses tests/test_historical_browser.cjs and the same Playwright environment variables as the original trading browser tests. Source and data verification, raw reproduction and the 59-check browser record are retained in checks/. The model-tab regression also passed all 51 checks.

## Sources and attribution

- [Binance public-data specification](https://github.com/binance/binance-public-data): archive routes, aggregate trades, Kline fields and the 2025 microsecond timestamp change.
- [Binance Spot market-data documentation](https://developers.binance.com/en/docs/catalog/core-trading-spot-trading/api/rest-api/market): aggregate execution and buyer-maker semantics.
- Exact source URLs, sizes and exchange checksums: inputs/source-manifest.json.
- Binance Vision terms snapshot: inputs/Binance_Vision_Terms_Snapshot.md. Derived data retain the source attribution and noncommercial share-alike scope described there. No exchange affiliation is implied.

## Mechanism debrief, revision 1.3

Completed rounds now expose observed signed base flow and the measured sum of squared aggregate base sizes, a centred 15-minute execution-amplification proxy, and a local conditional risk map. The source pool and per-candle payload include `flowBase` and `squaredSizeBase`. Signed base flow reconciles to official taker-buy base volume; squared sizes are reaggregated from the original executions. The nine case selections and original prices are unchanged.

The shared timeline labels observed versus model-conditioned quantities, keeps the response calibration strictly before play, retains the exact same-window baseline/amplification cancellation, and compares model risk with a G=1 reference and already realized RMS. The complete view opens after play, including for hint-disabled rounds. It uses richer execution data than the macro-only research target and is not a new strategy or daily-risk validation result.

See [the mathematical and information contract](../../docs/REPLAY_THEORY_BRIDGE_v1.md) and [the research main line](../../docs/RESEARCH_MAINLINE_v1.md). `node tests/test_trading_debrief.cjs` rebuilds all 1,089 conditional origins and tests chronology/invariance. `python studies/historical_replay_v1/verify_debrief.py` independently recalculates the numerical map. `reproduce.py` also rebuilds the debrief trace in a new directory and requires byte equality. Numerical, independent and browser checks are retained under checks/.
