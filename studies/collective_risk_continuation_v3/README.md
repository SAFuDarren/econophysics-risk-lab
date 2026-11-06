# Collective structure, observable inference and risk

This evidence snapshot connects weighted coordination, a fast/slow decision
network, observable-prefix state inference and coherent future risk scenarios.
It accompanies the research report and the Explore research workbench.

## Research findings

- Effective trading weights and cross-action covariance determine flow variance.
  A shared signal changes covariance even when each unit's marginal signal law
  is held fixed. The paired economic-channel experiment retains all six arms,
  128 seed units per arm and both prespecified primary metrics.
- Complete stochastic state propagation tracks independent large-ensemble
  references. Repeated substitution of state means loses distributional
  information in the nonlinear network.
- Observable histories condition a simulation-bank mixture over 128 source
  trajectories. Slow-state estimates improve relative to the unconditional
  prior, while the direct pressure proxy is more accurate for fast direction.
  HHI interval coverage and the matched-feature risk comparison delimit what
  the available macro interface identifies.
- Direct Bitcoin transport reveals excess model persistence and insufficient
  activity variation. Market execution counts, effective active units and model
  time require an explicit observation map.

All network effects are controlled-model findings. The market comparison is a
descriptive check on existing Bitcoin history. The 8-step risk horizon is primary;
1 and 48 steps are retained as secondary results. The conditional ensemble has
no established risk advantage over the same-feature MacroGamma or supplied
network prior in this test.

## Evidence and checking

- `tables/`: complete selected source tables, including all simulated test cases.
- `evidence.json`: browser-oriented data with units, scopes and source hashes.
- `source-manifest.json`: exact byte hashes and derivation records.
- `METHODS.md`: mathematical interface and experiment units.
- `code/check_evidence.py`: independently recalculates saved losses, state errors,
  interval coverage, finite-sample calibration ranks and paired mean contrasts.
- `code/source_network_kernel.py`: unchanged source-law snapshot for inspection.
- `code/export_evidence.py`: transforms the original study snapshots into this
  release; it requires the separately retained source study directories and NumPy.

Run the self-contained numerical audit from the repository root:

```bash
python studies/collective_risk_continuation_v3/code/check_evidence.py
```

In the downloaded standalone evidence bundle, enter its top-level directory and
run `python code/check_evidence.py`. The bundle also contains the four final
figures in `figures/`; the repository website serves those same files from its
figure assets directory.

This is a source-table audit package. Large simulation-bank arrays and raw market
archives are excluded; the package does not claim a self-contained reconstruction
of every original simulation or an independent replication of the market study.
Original graph/weight laws, simulation labels, tuning and calibration histories
are counted as information, alongside the online 32-bar observation prefix.

## Observation and validation separation

The inference viewer first exposes ticks 65–96 of each of the 128 fixed test
cases. Latent-state labels are separately exported for optional validation
reveal. They were never inputs to the saved estimator. Downloaded source tables
also retain calibration cases and all selected experimental conditions.

The website distinguishes observed market statistics, model-conditioned
estimates and known simulated truth. The figures and tables describe the fixed
experiments; selecting a state, dose or horizon does not fit a new model.
