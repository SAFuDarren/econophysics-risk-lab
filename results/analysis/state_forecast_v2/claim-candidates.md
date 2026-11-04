# v2主张账本

- Claim: 状态量价在新BTC窗口有小点增量。
  - Source evidence: primary_contrasts.csv、predictions.csv；V02/V04。
  - Allowed wording: 主QLIKE2.476%，区间跨零；补充log-MSE3.170%，仅25日。
  - Forbidden stronger wording: 稳定显著跨市场改善，或实际投资效益已验证。
  - Uncertainty: 主[-0.407%,4.815%]；日期块近似、短窗口。
  - Next check: 新冻结、更多未用日期；保留简单HAR和匹配return基线。
  - Decision: weaken。

- Claim: ETH验证选择关闭新成交状态通道。
  - Source evidence: validation_grid.csv、selected_models.json、逐日恒等检查。
  - Allowed wording: 此算法在ETH Q1验证选择Off，后续预测等同基线。
  - Forbidden stronger wording: 成交量没有任何预测信息，或[0,0]是一般等价证明。
  - Uncertainty: 模型/表示/网格有限，单一资产环境。
  - Next check: 独立问题下的信息时距与更直接的微观观测。
  - Decision: keep。

- Claim: 同根经验联合分布和时序结构携带不同信息。
  - Source evidence: 受控完整对置换、path_acf.csv、STATE_MECHANISM_v2.md。
  - Allowed wording: 此构造中量价对完全保留，幅度记忆显著改变；不等于过程律相同。
  - Forbidden stronger wording: 已唯一识别真实协调机制。
  - Uncertainty: 假设模型、10路径、固定参数，未拟合市场。
  - Next check: 新条件可辨识预测与更多实证接口。
  - Decision: keep bounded。

- Claim: 固定接口的正Delta不能扩展到全部状态羊群模型。
  - Source evidence: compensation_theory.json、小图精确枚举、有限N递推。
  - Allowed wording: 补偿构造保持指定低阶量但给负Delta；为事后解释性理论。
  - Forbidden stronger wording: 已解释真实-8.18或证明文献首创/新预测优势。
  - Uncertainty: 依赖明确补偿规则和状态假设。
  - Next check: 未确立真实机制时维持条件性结论。
  - Decision: keep bounded。
