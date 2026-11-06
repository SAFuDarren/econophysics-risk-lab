# Data and figure terms

## Project simulation results

Model-generated tables, exact examples and figures are credited to the Econophysics Risk Lab
Project Team. Research code and original materials retain the terms in LICENSE.md.

## Binance Vision

The Bitcoin and Ethereum market-derived results use Binance Vision archives.
Their source terms are retained under data/manifests/. Dataset-derived charts,
indicators and numerical outputs retain **CC BY-NC-SA 4.0** attribution to Binance
Vision and the applicable dataset terms.

Current source: https://github.com/binance/binance-public-data/blob/master/TERMS_AND_CONDITIONS.md

The repository includes derived research tables, documented download routes and
checksums. Complete raw and processed market archives are rebuilt locally by the
research scripts rather than included in the public snapshot.

The market fields in `web/assets/data/research-depth.json` replay the existing
Binance-derived model-restriction tables and retain those attribution terms.
The remaining simulation fields, the ten browser path payloads and
`data/snapshots/state-mechanism-series.csv.gz` are project-generated model results.

## Yahoo Finance-derived ETF diagnostics

The covariance and strategy results derive from the project's fixed Yahoo
Finance research snapshot. They are descriptive project outputs. Full supplier
OHLCV, adjusted-price and corporate-action histories are excluded from this
repository. No additional rights over the underlying supplier data are granted.
Source and adjustment-drift records are in data/manifests/us_equity_v1/.

## Third-party web assets

KaTeX 0.19.1 uses MIT. Source Sans 3 and Source Serif 4 use SIL OFL.
The exact source URLs and hashes are in web/assets/vendor/sources.json; licenses
are included beside the assets. The site makes no external runtime font or script
requests.


## Collective-dynamics information-budget study

`studies/collective_dynamics_v1/inputs/macro_observables.npz` is the inherited derived BTCUSDT five-minute panel. Source hashes, attribution and the Binance Vision terms snapshot accompany the study. It contains market aggregates and no raw execution archive or participant identities. Dataset-derived tables and figures retain the source terms described in the study attribution. The new trading-market paths and interface preview are project-generated synthetic outputs and an actual screenshot; they are separate from observed-market evidence.

## State and response-environment diagnosis

`studies/state_environment_v9/tables/market_*` and the corresponding files in
`web/downloads/state-environment/` are derived BTCUSDT research results from
Binance Vision. They retain the Binance attribution, CC BY-NC-SA 4.0 and source
terms described above. These tables contain aggregate model predictions and
realized-risk summaries, with no participant identities or full raw executions.

The response surfaces, source-state tests and simulation-precision tables are
original model results under LICENSE.md. The interactive instrument explicitly
separates those model scenarios from market-derived observations and fitted
estimates. A model capacity state is not observed exchange depth.

## Research-factor return application

`studies/real_factor_validation_v11/` and `web/downloads/real-factors/`
contain derived monthly research results based on the Kenneth R. French Data
Library five-factor and momentum daily files. The download URLs, current-vintage
dates and SHA-256 hashes are retained in the study source manifest. Original
daily archives and the daily return panel are excluded. Factor definitions and
source data retain their original owners' rights; LICENSE.md does not relicense
them. See the [official data library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html)
and the study's `SOURCES_AND_TERMS.md`.

The displayed factor returns are observations of constructed research
portfolios. Allocation coefficients, covariance estimates and forecasts are
project computations, separate from actual institutional orders or funds.
The `strategy_ecology_v10` scenario tables and trajectories are original
model-generated results under the project license.
