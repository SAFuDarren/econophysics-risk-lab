# Learning-room content and illustrations

The learning room contains 27 English/Chinese concepts: 13 economics topics,
10 mathematical foundations and 4 inference/risk topics. It follows the project's
research line and links to the existing experiments and methods.

## Edit and build

- `lessons.json` is the canonical lesson source: questions, intuition, LaTeX,
  assumptions, symbol units, project links, sources and quizzes.
- `calibration-demo.json` contains 64 calibration scores and 128 evaluation ratios
  from the project's fixed controlled-network experiment. It is synthetic research
  output, not market data. Source-table hashes are retained in the file. All cases
  are used; changing the selected coverage level changes only the prescribed rank.
- `web/learn.html` and `web/assets/learning.css` define the reading layout.
- `web/assets/learning.js` implements navigation, search, quizzes and local marks.
- `web/assets/learning-math.js` holds the tested mathematical teaching models.

From the repository root:

```bash
python scripts/site/build_learning_hub.py
node tests/test_learning.cjs
python scripts/reproduce.py --profile site
```

The builder produces `web/assets/data/learning-content.js`, maintains topic
anchors and adds one learning entry to existing navigation. It also keeps active
website command examples aligned with the script migration map. No internet
request is needed at runtime.

## Illustration contracts

1. **Liquidity:** hypothetical ask prices 100.02+0.02i; visible level sizes 20 or 80;
   buy sizes 10–160. The display computes VWAP and execution slippage relative to
   the original best ask. It does not estimate permanent market impact.
2. **Aggressor flow:** fixed total executed quantity 200, split by initiating side;
   F=V_buy−V_sell. Every execution has counterparties.
3. **Covariance:**20 positive weights summing to 1, fixed unit marginal variance,
   common pair correlation 0–1. Correlation is not graph-edge probability.
4. **Fragmentation:** a 100-unit parent, symmetric random sign, equal children all
   inside one bar. Raw B changes with size partition; parent flow second moment
   remains10,000. Amplification is not a follower fraction.
5. **Temporal blocks:**8 equal steps, independent symmetric block signs, block
   sizes 1/2/4/8 and linear response. Expected flow RV is 8; cumulative-flow variance
   is 8 times block length. All sign patterns are enumerated in the math test.
6. **State uncertainty:**two possible flow means −2/+2, each within-state variance 1.
   The exact total-variance/mean-energy decomposition is displayed.
7. **Calibration:**fixed observed outputs of controlled simulations, with
   split-conformal ranks at 80/90/95% nominal marginal coverage. Exchangeability
   assumptions, sample counts and the difference from market coverage are explicit.

Some topics use a direct link to an existing, specifically relevant experiment
instead of repeating an unrelated generic widget. The conceptual source map is
in [source-audit.md](source-audit.md). The event-time module cites Russell and
Engle's 1998 UCSD98-10 ACM manuscript; it is not labelled as their separate ACD
paper. Classical mathematical identities and project-conditioned derivations are
distinguished from empirical source findings.

Sources remain accessible per lesson. No source quotations or figures are
reproduced. The website preserves keyboard controls, reduced motion and local
language/progress preferences; it does not collect reader progress remotely.
