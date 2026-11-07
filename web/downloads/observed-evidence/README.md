# Observed evidence for market accommodation and fund demand

The source tables and figures accompany the findings on state estimation, price response and forecast evaluation. The ledger gives the corresponding files in the saved research studies.

## Bitcoin executions and visible depth

The observation panel covers 90 Bybit BTCUSDT spot dates from 1 May to 29 July 2025. The five-minute endpoints use strict publication-aware quotes. Top-20 visible depth measures displayed inventory. The conditional response table uses the current realized flow. The separate next-hour forecast comparison uses information available at each origin, with 30 evaluation dates and 600 queries. QLIKE is averaged over dates and lower values indicate lower forecast loss.

[Bybit historical data](https://www.bybit.com/en/derivative-activity/history-data) · [Orderbook field definitions](https://bybit-exchange.github.io/docs/v5/websocket/public/orderbook)

## Fund demand and forecast diagnostics

The study covers 28 SEC N-PORT filing quarters from 2019 Q4 through 2026 Q3. The cohort contains MTUM, QUAL, VLUE, USMV and SIZE, with IVV as a broad-market reference. Holdings, assets and reported sales minus redemptions enter according to conservative public availability. Reported fund flow is mapped proportionally through holdings to a conditional demand moment. The signed static decomposition covers 73 historical origins.

The scale correction reuses earlier historical data. It checks 30 target-month flow realizations and 33 monthly NAV-risk targets with origins and inputs as recorded in the saved design. The source risk table reports observed divided by forecast for its calibration ratio. Paired intervals are in the contrast table. The subset links on the findings page identify the evidence used there.

[SEC Form N-PORT data sets](https://www.sec.gov/data-research/sec-markets-data/form-n-port-data-sets)

## Source ledger

| Published file | Saved study source | SHA-256 |
|---|---|---|
| bitcoin-current-response.csv | Observed_Accommodation_and_Fund_Network_v14/bitcoin/tables/conditional_current_flow_response_fit.csv | `9548452aeb154c096046d0d6b662ee45a4b8a3ffea2728cc9a43d6070c46e8a6` |
| bitcoin-risk-scores.csv | Observed_Accommodation_and_Fund_Network_v14/bitcoin/tables/risk_summary.csv | `0521da309677d8d7f2362a0628c535d9fcbcd340d0f2db4effca6acc6727acae` |
| bitcoin-risk-contrasts.csv | Observed_Accommodation_and_Fund_Network_v14/bitcoin/tables/primary_contrasts.csv | `9b179f5233d1b3eb02198f526ae3d71abaf5c380549f406495a72f261866dff7` |
| fund-demand-decomposition.csv | Observed_Accommodation_and_Fund_Network_v14/funds/tables/demand_decomposition_summary.csv | `7783916cf653a6817a8dea75704608f3ba920ab249956f828cf1c93b9e938b1b` |
| bitcoin-risk-forecasts.svg | Observed_Accommodation_and_Fund_Network_v14/figures/B1_bitcoin_risk_forecasts.svg | `d67c215e29f1d69cd3b8eae174f54508bcd47331a0acbc5ffa6651d72d32595c` |
| fund-flow-scores.csv | Scale_Aware_Fund_Dynamics_v15/model/tables/flow_score_summary.csv | `a7d62d4c6da18aef70ce943efdeef0c5ff1203a56b7ed01253744cabc2aa7b70` |
| fund-risk-scores.csv | Scale_Aware_Fund_Dynamics_v15/model/tables/risk_scores.csv | `a402bdad7779248845df6c12388acf8a1c203fdea7b9467d8122b03b4a8c8b20` |
| fund-contrasts.csv | Scale_Aware_Fund_Dynamics_v15/model/tables/primary_contrasts.csv | `f0c258b9a4969fb42e183a784c40f9c00c9e6dea9d7828d53b8f45928053bd87` |
| fund-flow-and-risk.svg | Scale_Aware_Fund_Dynamics_v15/figures/S2_state_and_risk_comparison.svg | `4d5170e4619eb652965f3f5d0b4397ff66902aac2b60f17d90cc7a4c11eed3a1` |
