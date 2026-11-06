# Strategy diversity, trading scale and accommodation

This saved-evidence release extends the existing weighted fast/slow herding
network with multiple input factors and lagged performance allocation. It asks
when larger collective trading weight raises risk and when genuine signal
diversity or stronger accommodation offsets that effect.

**These are controlled model scenarios, not observed quant institutions.** The
scale parameter multiplies network transaction sizes; it does not measure the
number of firms or their assets. Capacity is a latent normalized response state,
not observed exchange depth. Independent group inputs still interact through
peers, the two network layers and price feedback.

## Evidence

- 56 short-horizon cells: 45 main grid cells, two cloned-factor controls, six
  network ablations and three volume-only controls. Each uses 32 source origins,
  128 future branches and twelve five-minute bars.
- At high scale and middle capacity, twelve independent group inputs reduce
  expected one-hour risk by 9.95% relative to one common input. Adding a shared
  component raises it by 7.65%. Low rather than high capacity raises risk by
  57.40% in the retained high-scale, diverse-input comparison.
- The matched-volume experiment holds volume, count and pricing-noise paths
  fixed; directional scale raises expected risk by 17.23% over that control.
- Eight allocation cells use 32 origins, eight branches and 192 bars. Performance
  feedback raises terminal group concentration, including relative to the
  score-identity-permuted control. All four primary 16-hour risk-difference
  intervals cross zero. Terminal weights affect the following bar; prebar paths
  separately show concentration within the tested window.

The one-event monotonicity result assumes fixed marginals, fixed state and
positive exposures. The full feedback system is evaluated by simulation. Its
price-risk decomposition includes drift/impact energy and a pricing-noise term;
the signal component is not a pure coordination share.

## Verify and inspect

Run `python studies/strategy_ecology_v10/verify.py` from the repository root.
It checks file hashes, reconstructs cell and allocation means from saved origin
statistics, and checks primary differences. It does not regenerate stochastic
paths, recalibrate the model or reproduce bootstrap intervals from branch-level
paths. Source path hashes identify the separately sealed full experiment.

`tables/` contains all 56 cells, 16 model contrasts, 1,792 origin means, eight
allocation contrasts and the saved allocation trajectories. `methods/` gives
the mathematical bridge, restricted monotonicity result and literature
interface. `SOURCE_PROVENANCE.json` records the original source hashes.

[Interactive instrument](../../web/strategy-ecology.html) ·
[Real research-factor application](../real_factor_validation_v11/README.md)

Original model outputs retain the project license. No institutional positions,
participant identities, real fund migrations or causal market-impact estimates
are contained in this package.
