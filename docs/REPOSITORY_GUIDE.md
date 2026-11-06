# Repository guide

The repository separates executable models, frozen evidence, operational commands
and the published website. Start from the stable reproduction entry point; use an
individual command when working on a particular study.

## Directory roles

| Directory | Contents | Editing rule |
|---|---|---|
| `src/econophysics/` | Shared models, estimators and numerical methods | Reuse implementation rather than duplicating it in notebooks |
| `configs/` | Study parameters, seeds, splits and tuning choices | Preserve frozen versions when creating a new experiment |
| `scripts/data/` | Acquisition and data preparation | Inputs and provenance remain under `data/` |
| `scripts/research/` | Execution, summaries and isolated reconstruction | Save outcomes under a named result run |
| `scripts/figures/` | Scientific plots from numeric evidence | Preserve companion source tables |
| `scripts/site/` | Website payload and page builders | Generated content is published under `web/` |
| `scripts/checks/` | Mathematical, artifact and browser verification | Passing checks does not imply new scientific results |
| `data/manifests/` | Archive locations, checksums and provenance | Historical manifests remain unchanged |
| `data/snapshots/` | Attributed derived input snapshots | Treat as fixed inputs |
| `results/tables/` | Complete numeric tables and forecasts | Retain negative results and all declared comparisons |
| `results/analysis/` | Interpretation and statistics | Cite the corresponding tables and protocol |
| `results/checks/` | Recorded checks and historical source hashes | Preserve the original experimental record |
| `studies/` | Frozen study packages | Keep each protocol, input and manifest together |
| `figures/` | Exported research figures | Source tables and plotting code remain traceable |
| `docs/theory/` | Derivations and identification limits | Distinguish conditions from model assumptions |
| `docs/AB/` | Historical experiment protocols | Retain paths for provenance |
| `notebooks/` | Executable readers using shared model code | Re-execute with the notebook profile |
| `web/` | Public pages, tools and report downloads | Keep navigation and offline asset links valid |

Ignored `.runs/` and `.cache/` hold local verification output and runtime caches.
They are not source evidence and are not committed.

## Stable entry points

```bash
python scripts/reproduce.py --profile quick
python scripts/reproduce.py --profile theory
python scripts/reproduce.py --profile site
python scripts/reproduce.py --profile notebooks
python scripts/reproduce.py --profile forecast --destination /tmp/forecast-rerun
```

The `quick` profile checks the exact core and saved evidence. The `site` profile
checks pages, assets, preserved study packages and shared browser engines.

Individual examples:

```bash
python scripts/checks/check_repository_layout.py
python scripts/checks/check_site.py
python scripts/checks/check_collective_study.py
python scripts/research/reproduce_forecast_study.py --help
python scripts/figures/plot_forecast_study.py --help
node scripts/research/reproduce_collective_trading_engine.cjs
```

Each command retains its original arguments. Data-heavy reruns require their
documented provider archives or frozen input bundle. The historical complete
tail reconstruction explicitly checks for its unshipped prepublication
dependencies before starting; routine site/core checks do not require them.

## Relocation and historical digests

Seventy-one formerly flat command files are grouped into five families. Root
Python files are `scripts/reproduce.py` and shared `scripts/_bootstrap.py`.
No duplicate legacy wrappers or symlink farm is added.

[`repository-migration-map.json`](repository-migration-map.json) maps old paths
to new locations. `scripts/relocations.json` records exact before/after hashes,
including prior publication digests. Historical manifests under `data/`,
`results/` and `studies/` are not rewritten. Digest verification resolves an old
recorded path through that map and accepts only the recorded relocated bytes;
an arbitrary changed source or digest still fails.

The bootstrap supplies the repository root and cross-family imports. Isolated
reconstruction copies the grouped script tree and uses the same rules. The
repository-layout check exercises these rules in a temporary isolated root.

## Learning content

`docs/learning/lessons.json` is the canonical bilingual learning source. Run
`python scripts/site/build_learning_hub.py` after editing it; this creates the
browser payload and maintains site entry links. Teaching calculations live in
`web/assets/learning-math.js`, checked by `node tests/test_learning.cjs`.
