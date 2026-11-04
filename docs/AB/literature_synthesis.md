# 文献如何改变本项目：来源—分析—结论映射


本稿把原始论文的结果与本项目推论分开。公开材料仅保留链接与引用，不打包论文全文。数值对照属于后续 SIMULATION，不能归给这些论文。

| 来源 | 原文支持什么 | 本项目据此增加什么 |
|---|---|---|
| Cont–Bouchaud：群体协调 | 以随机沟通群体解释聚合波动，讨论截断幂律与活动率 | 明确群体／收益尾部区别，保留固定活动率下的负拟合结果 |
| Gilbert：有限图连通概率 | 连通概率递推及两节点连接概率 | 计算有限 N 的 E S2、E S3，建立不使用监督标签的物理反演 |
| Platt–Gebbie：校准问题 | 在具体金融 ABM 中展示风格化事实与校准退化可以并存 | 不把“图像像市场”当作机制验证；增加边际保真联合对照 |
| Platt：校准方法比较 | 用已知参数的计算实验比较估计方法与误差 | 加强经典参照，重新生成训练／验证／测试并重复 10 次 |
| Clauset–Shalizi–Newman：尾部统计 | 极大似然、拟合优度和替代分布比较 | 不凭 log-log 直线宣布幂律；相对拟合更好不等于充分 |
| Lux–Marchesi：动态适应 | 策略转换与交互可产生内生波动及时间结构 | 解释静态基线缺少的反馈，把涌现与适应区分开 |
| Johansen–Ledoit–Sornette：泡沫／崩盘 | 模仿、崩盘风险率与条件价格增长的模型联系 | 区分静态渗流临界性、动态风险和随机崩盘时间 |

## R1. Cont–Bouchaud：我们保留了什么、增加了什么

Cont, R.; Bouchaud, J.-P. *Herd behavior and aggregate fluctuations in financial markets*. 核对 [arXiv cond-mat/9712318v2](https://arxiv.org/html/cond-mat/9712318v2)，Section 4、Appendix 4。

原文以随机群体和共同动作连接微观协调与宏观波动；其渐近处理明确考虑 2aN 有限。本组保持群体动作骨架，新增量与单位订单执行，并固定 q=2a 进行有限规模实验。不能把原文在其他极限中的收益尾部结论直接作为本组模拟的必然结果。

## R2. Gilbert：让“可识别”成为可计算的估计器

Gilbert, E. N. (1959). *Random Graphs*. Annals of Mathematical Statistics 30(4), 1141–1144. [原论文扫描，大学公开副本](https://www.stat.cmu.edu/~brian/780/bibliography/09%20Other%20Models/Gilbert%20-%201959%20-%20Random%20graphs.pdf)；重点为印刷页 1142，式 (4)–(5)。

已查看扫描原页。我们采用连通概率递推，推得有限 N 随机节点群体分布及其矩；不再依赖临界点附近发散的亚临界近似。递推本身是经典结果，本组贡献是把它接到已有量价矩反演、边界记录与学习比较。

## R3. Platt–Gebbie：看起来像市场，不等于已经识别机制

Platt, D. F.; Gebbie, T. J. *The Problem of Calibrating an Agent-Based Model of High-Frequency Trading*. 核对 [arXiv:1606.01495v4](https://arxiv.org/html/1606.01495v4)，Section 6E、7–8；全文已读相关段落。

该文在一个高低频交易 ABM 上观察到：若干收益风格化事实可以复现，但校准仍可能退化。它是具体模型中的证据，不是全部 ABM 必然不可识别的定理。本组用严格等价反例处理结构边界，再用量置换对照展示边际统计遗漏的联合信息；两类证据不混为一谈。

## R4. Platt：基准比较必须检验参数恢复本身

Platt, D. *A Comparison of Economic Agent-Based Model Calibration Methods*. 核对 [arXiv:1902.05938v1（2019）](https://arxiv.org/html/1902.05938v1)，Section 3、5；已核对全文方法与结论。

该文以已知参数的计算实验比较不同校准方法，并强调估计质量和不确定性。它在所研究的场景中发现 Bayesian 方法有优势；本项目没有复制其方法集，也不据此声称 Bayesian 一定优于本组 RBF。我们采纳的是同条件比较、强参照和重复制样原则。

## R5. Clauset–Shalizi–Newman：幂律是可拒绝的统计假设

Clauset, A.; Shalizi, C. R.; Newman, M. E. J. *Power-law distributions in empirical data*. 核对 [arXiv:0706.1062v2](https://arxiv.org/html/0706.1062v2)，Sections 3–5。

原文给出极大似然、KS 拟合优度与分布比较的统计框架。本组尾部为有限整数支持，具体实现与论文的标准无界设定有别，因此不称“完全复现论文检验”。保留区间、支持、bootstrap 分辨率和多重比较口径。

## R6. Lux–Marchesi：适应性为什么会带来时间结构

Lux, T.; Marchesi, M. (1999). *Scaling and criticality in a stochastic multi-agent model of a financial market*. Nature 397, 498–500. [出版页](https://www.nature.com/articles/17290)，[所核对的三页原文副本](http://finance.martinsewell.com/stylized-facts/scaling/LuxMarchesi1999.pdf)。出版页直接抓取受登录跳转限制；已读取原论文副本并核对标题、作者和页码。

模型区分基本面交易者与乐观／悲观的噪声交易者，意见和策略转换受趋势、群体意见及相对利润驱动；论文讨论内生厚尾、波动时间依赖和暂时失稳。我们据此说明当前逐期独立模型为何没有适应反馈。没有运行 Lux–Marchesi 复现，也不把其经验结果作为本组结果。

## R7. Johansen–Ledoit–Sornette：静态临界点不能直接变成崩盘日期

Johansen, A.; Ledoit, O.; Sornette, D. *Crashes as Critical Points*. 核对 [arXiv cond-mat/9810071v2（1998）](https://arxiv.org/abs/cond-mat/9810071v2)，Section 2.1、式 (2)–(3)，PDF 第 6 页。引用按已核对版本，不补写存在元数据差异的出版期号。

原文将自增强模仿与崩盘风险率联系，并在简化鞅条件下导出未崩盘路径的价格增长。崩盘是随机事件，不能把临界时间当作确定崩盘日。本文属于泡沫／崩盘机制应用综述；我们没有拟合 LPPL、验证真实危机预测或把 ER rho 当作该模型风险率。

## 综合后的科学问题

**在指定模型内估计一个连接参数，与判断该机制是否得到数据支持，是两项不同任务。** 本组用有限规模理论做前者，用联合约束与替代耦合做后一项的受控检验，并用观测等价证明识别的最终边界。
