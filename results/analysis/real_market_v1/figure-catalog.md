# 五张真实市场对照图

所有文件在 figures/real_market_v1，提供 PDF、SVG、600 dpi PNG。市场：Binance Vision；市场衍生图表按所取得条款标注 CC BY-NC-SA 4.0。模拟曲线明确标示 ER 条件，不能称为真实数据。五图均已检查矢量字体、面板对齐、碰撞以及可读性；检查不等于成员科学签收。

| 图号 | 输入表 | 图中展示 | 展示时可说 | 必须保留的边界 |
|---|---|---|---|---|
| F08 | daily_overview.csv；本地完整 bars.csv | 全年日收盘、全部 5 分钟收益、日量，H1/H2 分割 | 数据覆盖完整；行情保留极端变化 | 日内仅达 5 分钟；单场所单资产 |
| R01 | coupling_bins.csv；model_path_coupling_bins.csv；impact_bins.csv；impact_association.csv | 固定量箱的条件幅度；主动成交方向与收益 | 正关联在季节调整后仍存在；固定线性同根关联 R²=0.282 | 无因果或预测结论；空箱无插值；模型路径区间条件于 H1 |
| R02 | ccdf_comparison.csv；real_conditional_tail_ccdf.csv；tail_fitted_curves.csv | 市场、模型与高斯经验尾部；冻结 H1 连续尾部曲线 | 厚尾；主阈值 Pareto 相对评分较好 | 431 个 H2 尾部观测；固定 H1 校准未通过；离散模型不参加连续似然 |
| R03 | market_scaling.csv；model_scaling_summary.csv；market_acf.csv；model_acf_summary.csv | 聚合方差比；原始及季节调整后的幅度 ACF | 独立重采样模型缺少现实的幅度时间依赖 | 逐点区间；不据此估计普适临界/Hurst 指数 |
| R04 | market_metrics.csv；model_metrics_summary.csv；joint_constraint_sensitivity.csv；calibration_parameters.csv | Delta 与总体合法区间；12 月点估计 | 固定共同动作接口的联合约束与市场不相容 | 总体必要条件而非样本硬界；月点描述性；不排除全部羊群机制 |

## 图注共用细节

H2 52,992 根、184 个完整 UTC 日。市场阴影或误差线是 7 天日期块自助法的逐点 95% 区间；模型区间是每 rho 10 条独立路径的条件区间。主文点估计不因块长度改变。共同尺度为 H1 收益标准差，尾部主阈值固定 3 倍该标准差。图 R03 的模型 ACF 包络涵盖三组指定条件。

图 R02 的零经验概率和非正区间下界不画在对数坐标中，原始表不修改；理论尾部在低于显示范围的部分不继续绘制，源表仍完整。图 R04 是对预先声明 Delta 检查的后续展示组织，不增加新的选模步骤。

## 放入展示的顺序

F08 交代对象与数据；R01 说明模型抓住方向但不能直接解释执行；R02 说明宽尾不是机制证明；R03 用时间证据分辨；R04 给出一般接口约束。CD 可从五图中选择，但每张图的边界必须进入图注或讲稿，源表不可省略。
