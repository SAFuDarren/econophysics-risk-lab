# Validation record

Checked on 5 November 2026 (Singapore time).

| Check | Result | Entry point |
|---|---|---|
| Original exact theory checks | 480 passed | `python scripts/reproduce.py --profile quick` |
| Model and frozen-evidence tests | 9 passed | Same quick profile |
| Browser mathematics against Python fixtures | 82 passed | `node tests/test_web_math.cjs` |
| Main website resources and anchors | 5 pages, 150 local links passed | `python scripts/reproduce.py --profile site` |
| Research Markdown links | 99 local links resolved | Public snapshot packaging check |
| Retained original research artifacts | 341 SHA-256 hashes matched | `data/frozen_source_manifest.json` |
| Research notebooks | 3 executed, 16 code cells, 4 plot outputs, zero errors | `python scripts/reproduce.py --profile notebooks` |
| Fresh forecast reconstruction | 699 method checks passed; all 16 CSV tables byte-identical | `python scripts/reproduce.py --profile forecast --destination /tmp/forecast-rerun` |

The numerical reconstruction used Python 3.14.4 and the versions recorded in
`requirements-study.txt`. It downloaded the documented market archives anew and
reconstructed all 183 held-out forecast dates.

Browser review covered both languages, navigation, mathematical typesetting,
mobile layouts, grouping controls, one-period model actions, population and
finite-window inversion, chain–star equivalence, covariance controls, forecast
date selection and experiment-record downloads. The retained four-module
laboratory was also opened and its four tabs checked.

The workflow definitions in `.github/workflows/` run the quick checks and website
checks on subsequent repository changes.
