# 证据与允许主张

- Claim: 完整表示相对历史多尺度波动产生小的平均点改善。
  - Source evidence: regression_metrics.csv、regression_contrasts.csv；P01/P02。
  - Allowed wording: 最终183日主损失点下降2.263%，7日块区间跨零。
  - Forbidden stronger wording: 已证明稳定显著胜出；2.263%全由成交量造成。
  - Uncertainty: [-0.115%,4.559%]，条件块近似；训练参数不确定性未纳入。
  - Next check: 新冻结、此前未用时间；保留收益形状嵌套参照。
  - Decision: weaken。

- Claim: 风险概率相对固定历史发生率的评分较低。
  - Source evidence: probability_metrics.csv、probability_contrasts.csv；P05。
  - Allowed wording: Brier相对常数点下降38.35%，但相对Logit-HAR增量5.24%不确定。
  - Forbidden stronger wording: 量价提高38%；已校准崩盘概率或可保证降低投资损失。
  - Uncertainty: 最终8个事件；常数发生率失配；高概率箱样本少。
  - Next check: 动态发生率控制与新时间段概率校准。
  - Decision: keep bounded comparison。

- Claim: 方法增量随月份和实现波动状态变化。
  - Source evidence: monthly_metrics.csv、regime_metrics.csv；P03/P04。
  - Allowed wording: 主方法四个月点改善为正，两个月为负；高波动8日组未改善。
  - Forbidden stronger wording: 已定位因果机制；已验证能提前选择获益状态。
  - Uncertainty: 月度和状态均为描述性，目标状态使用事后实现值。
  - Next check: 预先定义可观测状态并在新留出检验交互预测。
  - Decision: keep descriptive。
