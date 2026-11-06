# Coordination, market accommodation and forecast information

This release connects the existing weighted decision network to a conditional
risk question: when does the same common signal have a larger price-risk effect,
and can the effective state improve a forecast from observed macro history?

[Interactive instrument](https://safudarren.github.io/econophysics-risk-lab/risk-environment.html)
· [Explore entry](https://safudarren.github.io/econophysics-risk-lab/lab.html#risk-environment)
· [Mathematical diagnosis](MATHEMATICAL_DIAGNOSIS.md)
· [Variables and units](VARIABLES.md)

## Results and evidence scopes

1. **Controlled model response.** At return feedback 0.15, changing future
   innovation correlation from 0 to 0.65 adds 3.306, 2.230 and 1.639 × 10⁻⁶
   to mean one-hour risk at normalized capacity 0.5, 1 and 1.5. Those increments
   equal 7.44%, 6.42% and 5.42% of the corresponding common-signal-arm risk.
   The effect weakens as
   capacity rises. These are 32-origin, 128-branch paired scenarios, not measured
   Bitcoin order-book depths or observed quant-fund risk shares. The tested
   feedback interaction is subadditive; its sign need not hold outside this grid.
2. **Estimation precision.** Barwise conditional second-moment integration keeps
   the original stochastic paths and improves effect precision. Across 256
   origins, common-input and feedback effects remain heterogeneous. A positive
   mean intervention effect concerns two model worlds; a forecast advantage
   concerns differences between states within the observed world.
3. **Information diagnosis in the source model.** Adding the hidden environment
   block (activity, size, capacity and weight concentration) to 32-bar macro
   histories improves expected-risk QLIKE from 0.036879 to 0.008413 on 64 test
   origins. This is a privileged-information diagnostic. Adding the tested
   direction/memory block gives 0.008519, without an established improvement.
4. **Bitcoin comparison with the same empirical input budget.** From the past
   32 five-minute bars of signed flow, volume, counts and returns, forecast the
   next 12 squared log returns. On 401 previously seen internal dates,
   development-selected HAR+Components scores 0.501501 versus 0.532309 for
   HAR-All. The 5.79% point reduction has a paired loss-difference interval
   [-0.078475, 0.017982] and Holm p=0.33. Structural priors, representations and
   computation differ despite shared fields/history/calibration. This is no
   accepted additional forecasting advantage or external confirmation.
5. **A diagnostic control.** In the complete-recovery, constant-local-noise,
   activity-forecast-off, no-fallback limit, the closure equals a 20-bar return
   second moment. Post-run HAR+RV20 and HAR+RawMoments20 score 0.502745 and
   0.499219. These descriptive controls explain why a point gain alone does not
   identify new coordination information. They did not replace the primary
   selection. The identity does not apply to the full activity-forecast model.

The contribution is a tested conditional mechanism, a separation of estimation
and information bottlenecks, and a concrete interpretation of the empirical
closure. It does not identify real coordinating participants from aggregate data.

## Files and verification

`tables/` preserves numerical tables and saved predictions byte-for-byte from the
sealed `Collective_Risk_State_Diagnosis_v9` experiment. `checks/` contains the
scoped outcomes; `SOURCE_PROVENANCE.json` records source paths and SHA-256 hashes.
`MANIFEST.json` covers this curated release, including the verification program.

```bash
python studies/state_environment_v9/verify.py
```

This standard-library check reconstructs response effects, component accounting,
precision means and source/market QLIKE values from saved data. It verifies file
integrity and interpretation labels. It does **not** regenerate the network
paths, fit the observable closure or rebuild market archives. Bootstrap intervals
are retained experiment outputs, not recomputed by this saved-table check.
Historical study packages elsewhere in `studies/` remain unchanged and keep
their own reproduction commands and evidence scopes.

`rho` in the response tables denotes future innovation correlation, displayed as
rho_c on the website. It is distinct from the original ER mean-degree parameter.
`liquidity` denotes normalized latent capacity. Signal/noise components include
conditional drift/impact energy and activity-scaled pricing noise; they are not
identified coordination shares. Risk units are sums of squared log returns.

The market tables derive from Binance Vision BTCUSDT aggregates and retain
CC BY-NC-SA 4.0 attribution and applicable source terms in [DATA_LICENSES.md](../../DATA_LICENSES.md).
The model tables are original project simulations under [LICENSE.md](../../LICENSE.md).
