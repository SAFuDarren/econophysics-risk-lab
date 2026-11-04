# 图目录与图注

所有图同时导出PNG/PDF/SVG，使用同一Python后端。T01/T02为模型内证据；T03–T05为真实数据，不能互相替代。

## T01_same_covariance

- 目的/读者应注意：同协方差下尾部仍不同；波动混合也能产生类似极端尾部。
- 源表：results/tables/tail_increment_v1/synthetic_ccdf.csv、results/tables/tail_increment_v1/synthetic_truth.csv
- 图注必含：完整81阈值保留于源表；log轴不画零频率，不暗示尾部概率精确为零。
- 如何改变判断：不能仅凭相同协方差假定相同尾部，也不能据尾部差异唯一选定物理机制。
- 复核：分清模型/市场；检查n、单位、参照、区间与非独立性；逐面板检查图例、裁切和PDF文字。

## T02_synthetic_increment

- 目的/读者应注意：正确生成模型并不自动带来相对通用重尾/经验法的大幅优势。
- 源表：results/tables/tail_increment_v1/synthetic_paired_effects.csv、results/tables/tail_increment_v1/synthetic_repetitions.csv
- 图注必含：图展示3个指定代表方法，完整九方法均有源表；区间不是市场证据或测试库抽样区间。
- 如何改变判断：生成真值正确不自动意味着胜过灵活统计替代，必须保留非羊群负对照。
- 复核：分清模型/市场；检查n、单位、参照、区间与非独立性；逐面板检查图例、裁切和PDF文字。

## T03_market_increment

- 目的/读者应注意：外部历史增益很小且未通过主族校正，2026尾部反向；零事件不能验证抓暴跌。
- 源表：results/tables/tail_increment_v1/contrasts.csv、results/tables/tail_increment_v1/metrics.csv
- 图注必含：旧行业分析为回顾性；未校正CI不替代Holm主检验。0/2事件段未画误导性大相对增益，完整值保留。
- 如何改变判断：主结果未通过校正且2026反向，不能把诊断用途包装为稳定预测增益。
- 复核：分清模型/市场；检查n、单位、参照、区间与非独立性；逐面板检查图例、裁切和PDF文字。

## T04_robustness_and_criticality

- 目的/读者应注意：控制协方差、积分误差及固定rho后，没有跨时段的临界性优势。
- 源表：results/tables/tail_increment_v1/contrasts.csv、results/tables/tail_increment_v1/mc_full_contrasts.csv、results/tables/tail_increment_v1/analytic_tail_contrasts.csv、results/tables/tail_increment_v1/critical_ablation.csv
- 图注必含：完整积分只针对标量组合尾部；图/动作有限库仍是数值近似，未新增市场信息。
- 如何改变判断：小幅历史效果与数值分辨率/协方差/时段有关，不能声明真实临界性优势。
- 复核：分清模型/市场；检查n、单位、参照、区间与非独立性；逐面板检查图例、裁切和PDF文字。

## T05_actual_probability_paths

- 目的/读者应注意：真实逐日概率与事件对照，直观展示2026只能评价误报。
- 源表：results/tables/tail_increment_v1/external_daily.csv
- 图注必含：2020为预先已知危机示例，非从最佳表现区间择优；不以例图替代完整评分。
- 如何改变判断：零事件只能比较误报，示例曲线不能替代全样本正确评分。
- 复核：分清模型/市场；检查n、单位、参照、区间与非独立性；逐面板检查图例、裁切和PDF文字。

图形处理：T01的CCDF展示1–7σ、概率≥1e-4；所有81阈值留在源表，零频率不画在对数轴。T02只画物理、同模式混合、FHS三个指定代表，完整九方法均在表中。T03对0/2事件的2026 Brier不画容易误导的百分比森林点，改为状态说明，完整值/区间仍在源表。T05只把预先已知的2020作为例图，主评分使用全2020—2025，不是择优危机窗口。
