# Signed covariance and allocation in observed research-factor returns

Six nominal factors do not provide six independent risks. This application
checks the statistical bridge of the collective-risk project using the official
Kenneth R. French daily five-factor and momentum series. Observed factor
portfolio returns, computed allocation coefficients and estimated future risk
are distinct objects throughout.

The current data vintage contains 9,254 daily observations from 2 January 1990
to 30 September 2026. A past-only monthly protocol has 228 fit, 120 development
and 81 evaluation origins. The evaluation covers January 2020–September 2026.
All comparators can use the same six series and previous 252 days, plus the
same fit/development sample; their representations and model capacity differ.
Parameters are fit only before 2010, with the ridge penalty selected only on
2010–2019. Evaluation targets are joined after predictions are hash-frozen.
This is a historical evaluation using a revised current vintage, not a
point-in-time or prospective trading test.

## Findings

- Effective correlation modes have median 3.23. Net covariance hedges risk in
  36 evaluation months and amplifies it in 45. The full/diagonal second-moment
  ratio ranges from 0.355 to 2.301. A positive common-input scenario is one
  branch of the signed covariance mechanism, not a universal market rule.
- QLIKE (lower is better): FullCov 0.24266, diagonal 0.34974, HAR-Portfolio
  0.19341 and HAR-All 0.48843. FullCov has lower point loss than the diagonal
  and high-dimensional HAR-All models, but neither primary comparison passes
  the six-comparison Holm correction. The simple portfolio HAR has the best
  point score. No forecasting superiority is established.
- Lagged performance allocation raises mean held coefficient HHI by 9.15%
  versus the fixed risk-budget allocation. Holm p is 0.0036 for the primary
  three-month block and 0.054 for the six-month sensitivity. Performance HHI is
  lower than the score-identity-permuted control, so this pattern is not unique
  evidence for performance-specific concentration.
- Mean future risk is 34.8% higher than the fixed allocation, but its paired
  interval crosses zero (Holm p=0.2562). Neither the model's 16-hour experiment
  nor this monthly application establishes a risk increment from migration.

The coefficients normalize factor sleeves after inverse-volatility scaling;
they are not underlying-stock gross exposures or observed institutional capital.
Monthly risk is the mean squared arithmetic research-factor combination,
not intraday Bitcoin squared log returns. Risk results are gross; an illustrative
one-basis-point coefficient-turnover charge does not identify implementation costs.

## Scope and reproduction

Run `python studies/real_factor_validation_v11/verify.py` from the repository
root for standard-library hash and saved-table reconstruction. This does not
refit forecasts or regenerate uncertainty. The full local independent checker
also reparsed the official archives, reconstructed all 429 monthly decisions,
checked fit/development separation, and recomputed paired block bootstraps.

`code/study.py`, `code/check_saved.py` and `PROTOCOL.json` provide the complete
analysis specification. To regenerate in a separate copy, install NumPy and
pandas, create `inputs/`, then run `code/study.py freeze`, `download`, `predict`
and `score` in that order. The download can return a later vintage; compare
its SHA-256 with `checks/download_manifest.json` before claiming exact
reproduction. `check_saved.py` deliberately checks the archived sample and
requires the regenerated daily panel and feature file.

`code/figures.py` can regenerate the two figures from the saved monthly tables
with NumPy, pandas and Matplotlib. The publication copy makes the author's
optional panel-alignment auditor nonessential and emits a warning if it is
unavailable; it does not claim to rerun layout QA in that case. This adaptation
does not change plotted data or calculations. Original and public file hashes
are distinguished in `SOURCE_PROVENANCE.json` and `MANIFEST.json`.

Source archives and daily returns are omitted from this public package.
Only derived monthly tables, forecast parameters, code, figures, original
download routes and hashes are distributed. Source data retain their owners'
rights; the project license grants no additional rights to them.

This application supports signed covariance as a risk-relevant representation.
It does not calibrate the nonlinear fast/slow network, identify coordinated
Bitcoin investors or measure the causal market impact of quant funds.

[Official data library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html) ·
[Model scenarios](../strategy_ecology_v10/README.md) ·
[Interactive instrument](../../web/strategy-ecology.html)
