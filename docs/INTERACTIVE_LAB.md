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

`data/snapshots/state-mechanism-series.csv.gz` preserves the original controlled-simulation series, including all ten paths and four arms. `web/assets/data/memory-path.json` contains replication 0; `web/assets/data/memory/path-01.json` through `path-09.json` contain the other nine complete 8,192-pair paths. Every payload retains the original mechanism configuration and source SHA-256. Paths load individually when selected. The existing replication-0 URL is retained.

The first shuffle of persistent activity replays the original saved shuffle. Further shuffles, and shuffles of other arms, use a reproducible browser permutation of the original pairs. Every pair is retained exactly. Histograms and lag-one correlations use all 8,192 observations; the time trace shows a movable 512-observation segment. The report's ten-path summary remains a separate research result.

Exports include settings, displayed results and source references. A temporal-memory export also includes the current ordered observation pairs. Calculations and exports stay in the visitor's browser.

## Research detail

Five experiments have a local Explore / Research detail switch. The six experiment routes and global navigation are unchanged. `lab.html?view=research#network` opens the research view directly; the corresponding fragments are `inference`, `identity`, `memory` and `risk`.

| Experiment | Research interaction | Basis |
| --- | --- | --- |
| Finite networks | Vary N and edge probability p, select a rooted group size, and compare the finite-graph recurrence with complete enumeration | Exact browser sums for N = 2–5; independent Python Fraction/BFS fixtures |
| Parameter recovery | Compare five methods at three return scales on the original and unseen parameter grids; retain all ten study pairs | All 300 rows of the original scale-control table; no additional fitting |
| Identification | Filter all 64 labelled four-node graphs into five size profiles, inspect every observation probability and open a graph in the original editor | Complete finite enumeration and the existing observation-law argument |
| Temporal memory | Inspect ten-path means and saved intervals; compare V-only and whole-pair permutations of a selected path | Saved path statistics and summaries; deterministic browser transformations |
| Shared risk | Compare six fixed-portfolio, covariance-matched synthetic distributions, exceedance frequencies, VaR and ES | Original 50,000-scenario estimates and all 486 saved CCDF rows |

The findings page adds a market-restriction workbench at `findings.html#market`: the primary BTC H2 estimate, both saved interval choices, twelve monthly estimates and three exclusion cases. Point-only cases retain that status. Five mathematical steps explain how the fixed-interface scales cancel from Delta. The positive envelope across finite N is shown separately from the tighter bound for a specified N.

`scripts/site/build_research_payload.py` builds the shared research payload from the saved CSVs and extracts the remaining nine path payloads from the original compressed snapshot. It preserves the existing replication-0 payload. The shared JSON records each input table's SHA-256. SVG exports embed source metadata; JSON exports identify the research view and its selected settings.

## Validation

Run `python scripts/reproduce.py --profile site`. It checks nested-page links and anchors, duplicate IDs, self-hosted resources, full table/path parity, source figures, JavaScript syntax, exact enumeration against independent rational fixtures, all ten paths against the saved Python correlations, scale controls and both permutation invariants. The laboratory supports both interface languages, narrow screens, keyboard navigation and reduced-motion preferences.
