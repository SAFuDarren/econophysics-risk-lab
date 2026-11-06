# Visualization labels

| Data key | Meaning | Scope/units |
|---|---|---|
|rho|future residual-innovation cross-agent correlation|dimensionless, not coordinating-person/fund fraction|
|feedback|actual calendar-return input to decision field|dimensionless coefficient on return/fit returnSD|
|liquidity|current normalized latent shock-capacity state|model units, not observed depth or dollars|
|recovery|predictable-impact subtraction coefficient|different from return-to-decision feedback|
|risk_mean|mean termwise integrated one-hour price risk|sum of12five-minute squared logreturns|
|risk_ci_low/high|marginal95%basic paired-origin bootstrap range|32origins,4999replicates; not market uncertainty|
|signal_RV_mean|mean sum(alpha+betaY)²|transmitted price component including drift; not pure identified coordination|
|noise_RV_mean|mean sum sigma²g²|activity-linked independent pricing-noise component|
|signal_share|signal_RV_mean/risk_mean|component ratio, not actual quant risk fraction|
|pressure_energy_mean|mean sum(F/V)²|12futurebars, model executed flow|
|same_prefix_range|risk range across intervened future contexts|stress assumptions, not stationary identification theorem|

Risk surfaces are simulated conditions. Use separate visual labels for empirical market forecasts and these scenario responses. The raw paths and every fixed cell are preserved; hover values should show both point estimate and uncertainty without calling a cell a real market forecast.
