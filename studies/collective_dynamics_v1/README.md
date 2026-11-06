# Reduced collective dynamics under matched information budgets

This study tests a compact mean-field pressure model motivated by weighted fast/slow interacting groups, with memory and adaptation. It evaluates next-day realized variance on reused historical Bitcoin observations; it does not recover a real graph or empirically validate the full synthetic trading-game network.

The study finds no information-efficiency or restriction-specific predictive advantage. At 30 days, the Q1-selected mechanism scores QLIKE 0.265712 versus price-only HAR 0.240001. At 240 days, it scores0.260805 versus HAR 0.228191 and MacroStat0.223596. The same-map unconstrained PressureAR is0.260792. All budgets, controls, uncertainty and unsuccessful outcomes are retained.

## Budget and evidence

Rolling total-input budgets are 30/60/120/240 days, each with 288 bars/day and B−1 training target pairs. All calibration, state initialization and feature lookback fit inside that window; there is no additional warm-up, microscopic label or pretrained state. ReturnHAR needs only price returns; pressure models additionally need V,F. Fewer days plus more input fields is not automatically lower total information.

Q1-2026 selects penalties and mechanism variant; Apr–Sep 2026 supplies 183 primary dates and October 1–25 supplies 25 secondary dates. All macro dates were viewed in prior rounds, so this is historical development. Primary QLIKE contrasts use paired seven-day circular blocks and Holm over12 budget/control comparisons. The selection lock precedes primary scoring.

## Artifacts

- PROTOCOL.md: exact frozen model, chronology, budgets and comparison families.
- code/model.py: compact pressure transitions, response/dispersion map and statistical controls.
- tables/: full predictions, selected/candidate fits, costs, score uncertainty and contrasts.
- analysis/: strict analysis, statistical appendix, figure catalog and provenance.
- figures/: actual data figures in PDF, editable SVG and 600 dpi PNG, with source metadata.
- website-summary.json: compact presentation data with evidence boundaries.
- checks/: chronological/invariance audits, reproduction and figure QA.

## Reproduce

Use Python with NumPy, pandas, SciPy and Matplotlib; versions are recorded in analysis/provenance.json. From this directory:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python reproduce.py
```

The script rebuilds every numerical table in a fresh temporary directory from the attributed derived macro input, checks all columns and model selections, and writes checks/reproduction.json. It does not download or reaggregate raw source records; that provenance belongs to the preceding data audit. Code/run.py performs fitting and Q1 selection, code/evaluate.py performs frozen scoring/audits, code/accounting.py provides a labelled post-primary diagnostic, and code/figures.py regenerates actual plots.

The source is Binance Vision's public historical BTCUSDT data. The inherited derived input is identical to the preceding audited panel. See DATA_ATTRIBUTION.md and the accompanying terms snapshot. No prior research result or website file is modified by this study directory.
