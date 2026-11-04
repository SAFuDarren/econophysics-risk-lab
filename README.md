# Econophysics Risk Lab

**How do shared decisions change market fluctuations, and what can price and volume reveal about the hidden structure?**

[![Research checks](https://github.com/SAFuDarren/econophysics-risk-lab/actions/workflows/checks.yml/badge.svg)](https://github.com/SAFuDarren/econophysics-risk-lab/actions/workflows/checks.yml)
[![Website deployment](https://github.com/SAFuDarren/econophysics-risk-lab/actions/workflows/pages.yml/badge.svg)](https://github.com/SAFuDarren/econophysics-risk-lab/actions/workflows/pages.yml)

A computational PC5253 research project connecting herding, finite-network moments,
conditional parameter inference, identification limits and historical risk applications.

![Interactive research homepage](web/assets/social-preview.jpg)

## Explore

[**Open the research website →**](https://safudarren.github.io/econophysics-risk-lab/) · [Research repository](https://github.com/SAFuDarren/econophysics-risk-lab)

Run a local preview:

```bash
python -m http.server 8000 --directory web
```

Open **http://localhost:8000**. The five-page website is available in English and
Chinese. Its fonts, mathematical typesetting, figures and numerical data load
locally.

- **Coordination:** inspect group contributions to squared-size risk and simulate a shared action.
- **Inference:** compare population inversion with finite-window estimates, then switch a four-node chain into a star while its observation law remains fixed.
- **Portfolio risk:** compare full covariance, retained co-movement and diagonal variances for the same historical holdings.
- **Forecast record:** inspect every one of the original 183 held-out dates and change the displayed baseline.
- **Extended laboratory:** the original Chinese four-module workspace retains strategy screening, all 63 nonempty subsets and transaction-cost comparisons.

## Research findings

| Question | Finding | Evidence |
|---|---|---|
| How does coordination enter risk? | Group-size power sums connect local shared actions to aggregate price–volume moments. | Exact identities and 1,080 finite-size graph draws |
| What can observations recover? | Selected ER parameters are identifiable under the stated interface; internal edges can remain observationally identical. | Finite-ER inversion, ten independent studies and an exact chain–star example |
| Does the fixed interface fit market data? | The BTC H2 joint-moment statistic lies outside the model's necessary positive range. | Original market tables and block intervals |
| What do forecasts add? | HAR+All reduces historical log-MSE by 31.20% relative to persistence; its additional 2.26% reduction over HAR has an interval crossing zero. | All 183 test dates and paired comparisons |
| What can covariance analysis show? | Shared movements account for much of the same-window sector basket variance; similar strategy variants can repeat exposure. | Fixed ETF covariance and daily P&L diagnostics |

## Run the checks

The core model and exact theory verification use only the Python standard library.

```bash
python scripts/reproduce.py --profile quick
```

The numerical studies use the tested versions in `requirements-study.txt`.
The notebook environment can be installed with:

```bash
python -m pip install -e ".[analysis,notebooks]"
python scripts/reproduce.py --profile notebooks
python scripts/reproduce.py --profile site
```

The full forecast reconstruction downloads the documented archives into a fresh
location, repeats the frozen experiment and compares its CSVs with the saved tables:

```bash
python -m pip install -r requirements-study.txt
python scripts/reproduce.py --profile forecast --destination /tmp/forecast-rerun
```

See the [validation record](docs/VALIDATION.md) for the executed checks and fresh forecast reconstruction.

## Learn through the project

1. [Groups, moments and finite-size networks](notebooks/01_model_and_moments.ipynb)
2. [Inversion and identification limits](notebooks/02_inference_and_identity.ipynb)
3. [Market tests and historical forecasting](notebooks/03_market_and_forecasting.ipynb)

The notebooks call the shared implementation and frozen source tables. The course
mean-degree symbol `c` maps to `rho` in the original Python API; activity `q` maps
to twice the directional action probability `a`.

## Repository map

- [`src/econophysics/`](src/econophysics/): shared model, inference, statistics and application code.
- [`configs/`](configs/): frozen research configurations.
- [`results/tables/`](results/tables/): compact source tables and complete original forecast outputs.
- [`data/manifests/`](data/manifests/): archive locations, checksums, provenance and retained source terms.
- [`web/`](web/): website, interactive experiments and original scientific figures.
- [`docs/theory/FOUNDATIONS.md`](docs/theory/FOUNDATIONS.md): theory and identification arguments.
- [`tests/`](tests/): cross-language fixtures, exact enumeration and evidence checks.

The complete [English report](web/downloads/research-report-en.pdf) and
[Chinese report](web/downloads/research-report-zh.pdf) retain 19 figures, eight tables
and the subsequent control studies.

## Credits and reuse

Scientific work is credited to the **PC5253 Project Team**. Website and repository
maintained by **Darren Fu Shiang**. See [AUTHORS.md](AUTHORS.md).

Code, original research materials, dataset-derived results and third-party web
assets have separate terms. See [LICENSE.md](LICENSE.md) and
[DATA_LICENSES.md](DATA_LICENSES.md). Full raw market archives, complete supplier
price histories and course lecture PDFs are excluded from this public snapshot.
