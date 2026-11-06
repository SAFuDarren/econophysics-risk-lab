# Economics learning source audit

Checked 2026-11-06. Thirteen bilingual project-linked economics modules, one three-option self-test each. This is an educational content packet, not new research evidence or a statement that market prediction has been validated. No source quotations or source figures are reproduced.

## Source-to-claim map

| Primary source | Lesson IDs | Supported content and boundary |
|---|---|---|
| [SEC Investor.gov: Types of Orders](https://www.investor.gov/introduction-investing/investing-basics/how-stock-markets-work/types-orders) | price-and-value; liquidity-and-orders; signed-flow | Market/limit execution and execution-price uncertainty. Does not supply a theory that price always returns to value or identify participant positions. |
| [Shiller, NBER w0456](https://www.nber.org/papers/w0456) | price-and-value | Equity dividend-discount model and volatility analysis. Working paper is 1980; published AER version is 1981. We do not present its findings as a universal mispricing theorem or apply the dividend claim to Bitcoin. |
| [Cont, Kukanov & Stoikov, arXiv1011.6402](https://arxiv.org/abs/1011.6402) | liquidity-and-orders; signed-flow; price-impact | Source studies 50 US stocks and order-book OFI, including limit orders/cancellations. The module explicitly distinguishes that OFI from the project's signed executed-volume F. Published DOI10.1093/jjfinec/nbt003, 2014. |
| [Tóth et al., arXiv1108.1632](https://arxiv.org/abs/1108.1632) | herding-and-splitting | Membership-labelled LSE evidence separates splitting from herding, with splitting dominance on that paper's short scales. Not a universal conclusion about Bitcoin or five-minute bars. |
| [Khandani & Lo, NBER w14465](https://www.nber.org/papers/w14465) | common-factors | 2007 quant-event evidence consistent with deleveraging and temporary market-making capital withdrawal. It motivates shared-exposure questions, not causal identification of our parameters or Bitcoin institutions. NBER version2008; journal version2011. |
| [Hendershott, Jones & Menkveld](https://doi.org/10.1111/j.1540-6261.2010.01624.x) | common-factors | NYSE instrumental-variable study supports a liquidity-improvement channel, countering a blanket claim that algorithms only amplify risk. Publisher page accessible in search/open excerpts. |
| [Brunnermeier & Pedersen, NBER w12939](https://www.nber.org/papers/w12939) | feedback-and-liquidity | Conditional theoretical feedback between funding and market liquidity. NBER2007; journal2009. Project activity-throttle is explicitly not forced liquidation or strategic exit. |
| [Basel Committee market-risk framework2019](https://www.bis.org/publications/201901-standards-minimum-capital-requirements-market-risk) | tail-risk | Official context for expected shortfall and tail-risk distinction. Quantile formula is a mathematical definition; no capital-rule recommendation is made. |
| [SEC Investor.gov: Asset Allocation and Diversification](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) | diversification | Underlying exposures matter; several narrowly focused funds need not give broad diversification. Covariance formula is the project's mathematical identity, not a promised future risk estimate. |
| [Corsi, DOI10.1093/jjfinec/nbp001](https://doi.org/10.1093/jjfinec/nbp001) | volatility-and-rv; forecast-comparison | HAR-RV combines different volatility horizons. Journal metadata verified via institutional record and original paper PDF at [WU university](https://statmath.wu.ac.at/~hauser/LVs/FinEtricsQF/References/Corsi2009JFinEtrics_LMmodelRealizedVola.pdf). Publisher fetch returned an inaccessible redirect, so no claim that its page was fully read. Our1/7/28-day choice is named as a project variant. |
| [Alvarez-Zuzek et al., PLOS ONE](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0163593) | networks-and-identification | Interacting decision processes on interconnected networks; not financial-market model validation. |
| [Russell & Engle, UCSD98-10 ACM author manuscript](https://eml.berkeley.edu/symposia/nsf98/engle_russell.pdf) | event-and-calendar-time | Models transaction arrivals and price marks jointly. Supports the event/calendar-time distinction, not validation of our network or an inferred market clock. This is distinct from their ACD paper. |
| [Angelopoulos & Bates, arXiv2107.07511](https://arxiv.org/abs/2107.07511) | networks-and-identification | Calibration concerns uncertainty, not identification. Exchangeability gives marginal conformal coverage; not guaranteed market/state-conditional coverage. |
| Project methods.html#identity | networks-and-identification | Project-specific conditional finite-ER identification and exact observation-equivalence examples. This is internal mathematical evidence, not external empirical replication. |

## Content checks

- All price/value descriptions separate transaction prices, information and model-based cash-flow valuation. No assertion that fundamentals never matter or that all assets necessarily revert.
- Signed flow describes aggressive executed size; every trade has counterparties. K is not a count of people. Large execution does not identify a new long/short position.
- Liquidity, funding, common-factor, order splitting and feedback are separate mechanisms. Experimental positive/negative channels do not imply universal effects.
- Returns, squared returns, RV, cumulative return square, drawdown, VaR and ES are separate targets; units/horizon are named.
- Conditional moment identities and working response/valuation models have explicit assumptions. Every equation has a symbol/unit glossary.
- Project identification, model calibration, prediction and causal claims are distinguished. Current particle collapse is named as uncertainty failure, not unique graph recovery.
- Educational example numbers are arithmetic examples, not invented data or research results.
- All thirteen economics three-option self-tests were checked for one intended correct answer; indices are zero-based. JSON schema/bilingual keys and LaTeX control-character checks pass.

## Internal entry links

All try_href targets were inspected in the current source pages: trading.html, trading.html?source=model; methods.html#execution-risk-bridge, #collective-dynamics, #covariance, #forecast; lab.html#memory, #risk, #identity. File reorganisation may require a fresh site link audit, but no lesson references a moved script path.

## Extended project foundations

The combined learning source adds conditional moments, group generating functions,
finite ER/percolation, effective weights, execution baselines, averaging and
dependence, temporal risk, observation equivalence, nonlinear state propagation,
Monte Carlo error, joint moments, filtering, evaluation and calibration. Project
derivations remain model-conditioned. All formula and symbol strings are checked
with the bundled KaTeX. The event-time module uses the original Russell and Engle
1998 ACM manuscript and distinguishes its time-aggregation identity from a
calibrated market clock. Controlled interval-demo scores are documented in
`calibration-demo.json`.
