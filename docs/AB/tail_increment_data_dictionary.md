# 尾部增量批次的数据接口

所有路径相对project根目录。数据源是当前供应商复权快照，原始报价/公司行动JSON在data/raw/tail_increment_v1，处理后价格在data/processed/tail_increment_v1/external.csv；公开仓库不自动包含它们。

|文件|实验单位与用途|
|---|---|
|select_daily.csv|旧行业验证期的日×方法×协方差；只用于冻结统计参照|
|sector_daily.csv|已看行业ETF的日预测/评分，回顾性|
|external_daily.csv|规则冻结后下载的九股票外部资产留出，日预测/评分|
|*_law_choices.csv|每21日拟合时的选择、拟合窗口和形状，不是市场临界真值|
|*_causal_arrays.npz|dates/returns/covariances/z/h；协方差与创新可复核，前126个创新NaN为预热，不参与拟合|
|metrics.csv|分资产池/协方差/时期/方法汇总；事件数不可省略|
|contrasts.csv|相对验证参照的配对日块效应、区间和主族标记|
|secondary_metrics.csv / secondary_contrasts.csv|1%尾部与FZ联合评分；次要探索，不另选主赢家|
|critical_ablation.csv|相同六候选+off预算，rho1对rho0.6|
|synthetic_truth.csv / synthetic_ccdf.csv|六个已知真分布、相同协方差，50000场景；不是市场数据|
|synthetic_repetitions.csv / synthetic_metrics.csv / synthetic_paired_effects.csv|每真值20独立训练重复；CI条件于共享测试律|
|mc_daily.csv / mc_sensitivity.csv|每21个评价日的8192/16384场景比较；不是新增市场日|
|mc_full_daily.csv / mc_full_contrasts.csv|追加全部外部日的积分分辨率核验，原模型选择未变|
|analytic_tail_daily.csv / analytic_tail_contrasts.csv|原已选形状的标量尾部积分；不重选参照或替换主检验|
|reliability.csv|固定概率桶的样本数/事件数/均值，仅作描述|
|law_bank_diagnostics.csv|模型图与动作库的S2/S4、最大群体、活动零频率等|

## 逐日字段

- date：被预测收益的交易日。fit_end：参数最近一次更新时可用的最后日期，严格早于date；预测协方差每日只取date之前126个收益。
- y：实际等权组合收益除以预测前组合标准差；actual_basket_return是原始算术日收益，0.01表示1%。
- q05/q01：标准化收益的5%/1%下分位；es05/es01：相应标准化下尾均值，通常比相应分位更负。
- portfolio_sigma：预测前组合的每日标准差，不是未来真实风险。co_count/co3：实际低于各自−2预测标准差的资产数量/是否至少3只。
- p_co3：共同下跌场景概率。p_co3_smoothed只用于次要log-score的有限计数平滑；Brier用原p_co3。scenario_count是数值场景数，不是市场样本量。
- pinball05/pinball01：标准化分位损失；brier：概率平方误差；fz05/fz01：联合VaR/ES分数。FZ可能为负，不做百分比改善；日度主表只有fz05，fz01在次要分析中由固定预测重算。
- covariance_relative_error：预测场景经验协方差相对共同目标的Frobenius误差；不衡量对未来真实协方差的准确度。
- rho/q/kappa/nu等：已选分布的模型参数。q为活动率，kappa为第一模式非高斯份额。空值表示不适用于该方法；不是缺失数据插补。
- *_law_choices.csv中的fitted_scalar_nll沿用实现字段名：共同模式法是标量NLL，椭圆StudentT是完整向量NLL；不能把该列跨模型直接当性能排名。StudentT与Gaussian off选择时使用匹配的全向量Gaussian项，单元审计和源实现保留。

## 效应与边界

improvement_pct=100×(1−平均模型损失/平均参照损失)，正值较好；不是投资收益百分比。CI为相同日块下的未校正分位区间；主p值另做Holm。FZ用mean_loss_difference，负值偏向模型。2026外部0事件时，Brier仅比较误报；不能从该表计算有意义的暴跌召回率。
