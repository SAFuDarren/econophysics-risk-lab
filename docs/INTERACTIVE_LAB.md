# Interactive research laboratory

The public laboratory connects the model's mathematical quantities with exact calculations, live simulations and saved research evidence. The established entry point remains `web/lab.html`.

## Navigation

The global website navigation remains Research, Explore, Findings, Mathematics and Reproduce. The Explore page groups six experiments into mathematical foundations, inference and discoveries, and applications. Each experiment has a stable URL fragment, a mathematics link, an implementation link and a source-results link. Desktop uses one experiment rail; mobile uses one grouped selector. The existing strategy and allocation laboratory remains at `web/advanced/index.html`, reached from the shared-risk experiment, with a return link.

| Fragment | Interaction | Evidence |
| --- | --- | --- |
| `#mechanism` | Compare independent traders, constructed groups and an ER graph; inspect a group's squared-size contribution | Exact conditional moments; live model draw |
| `#network` | Vary connectivity and population size; compare a seeded graph with the saved ensemble curve | Original phase summary, 40 draws per setting |
| `#inference` | Follow the moment inversion and compare five sampled windows | Saved finite-ER interpolation curve; live model windows; separate recovery benchmark |
| `#identity` | Edit all six possible four-node edges; enumerate every one-period outcome | Exact action probabilities, aggregated over component sizes |
| `#memory` | Replay a complete saved path; shuffle whole observation pairs; inspect time correlations | Replication 0 from the four-arm temporal-state experiment |
| `#risk` | Adjust historical covariance treatment and holdings; inspect paired variance contributions | Saved sector covariance matrices, matched holdings and window |

The homepage research map connects each research question to its experiment, mathematics, code and source results. The report and README website preview remain available.

## Saved temporal paths

`data/snapshots/state-mechanism-series.csv.gz` preserves the original controlled-simulation series, including all ten paths and four arms. `web/assets/data/memory-path.json` contains the complete 8,192-pair replication 0 from each arm, the original mechanism configuration and the source SHA-256. It loads only when the temporal-memory experiment is opened.

The first shuffle of persistent activity replays the original saved shuffle. Further shuffles, and shuffles of other arms, use a reproducible browser permutation of the original pairs. Every pair is retained exactly. Histograms and lag-one correlations use all 8,192 observations; the time trace shows a movable 512-observation segment. The report's ten-path summary remains a separate research result.

Exports include settings, displayed results and source references. A temporal-memory export also includes the current ordered observation pairs. Calculations and exports stay in the visitor's browser.

## Validation

Run `python scripts/reproduce.py --profile site`. It checks nested-page links and anchors, duplicate IDs, self-hosted resources, saved-path and source-figure parity, JavaScript syntax, exact enumeration against analytical moments, path correlations against the saved Python metrics, and pair-preserving deterministic shuffles. The laboratory supports both interface languages, narrow screens, keyboard navigation and reduced-motion preferences.
