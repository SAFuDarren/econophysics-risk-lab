# Study configurations

Each named JSON file records parameters, observable windows, sizes, seeds, splits
and tuning choices for one study. Preserve a frozen version and create a new
name when changing an experiment.

- `foundation_v1.json`: implementation checks and explanatory figures.
- `simulation_study_v1.json`: executed primary simulation study.
- `simulation_followup_v1.json`: independent post-primary scale and interpolation diagnostics.
- `depth_study_v1.json`: finite-network recovery and identification.
- `real_market_v1.json`, `forecast_v1.json`, `state_forecast_v2.json`: market analysis and forecast comparisons.
- `us_equity_v1.json`, `tail_increment_v1.json`, `crowded_exit_v1.json`: portfolio, tail and capacity studies.
- `collective_trading_v1.json`: weighted fast/slow simulator settings.
- `figure_backend.json`: plotting conventions, not an experiment result.

These are local versioned experiment locks, not claims of external preregistration.
The [repository guide](../docs/REPOSITORY_GUIDE.md) lists commands by purpose.
