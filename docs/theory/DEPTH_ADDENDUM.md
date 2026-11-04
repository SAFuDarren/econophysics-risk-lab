# 理论深化：可识别参数、有限规模校准与可检验机制

证据类型：下列推导为 CONCEPTUAL／MODEL_CHECK；数值表现另见深化分析。它们补充 [理论基础 v1](FOUNDATIONS.md)，不改旧模型，也不声明文献首创。

## 1. 从无穷极限走到有限 N 的可计算反演

令 C_s(p) 为 G(s,p) 连通的概率。包含指定节点的分量大小必为某个 k；先选其余 k−1 个节点，再要求内部连通、没有跨分量边，得到

$$C_1(p)=1,\qquad
C_s(p)=1-\sum_{k=1}^{s-1}\binom{s-1}{k-1}C_k(p)(1-p)^{k(s-k)}.$$

这是 [Gilbert（1959），式 (4)、印刷页 1142](https://www.stat.cmu.edu/~brian/780/bibliography/09%20Other%20Models/Gilbert%20-%201959%20-%20Random%20graphs.pdf) 的连通概率递推。固定有限 N 时，随机节点所属分量的精确概率为

$$\pi_{N,s}(p)=\binom{N-1}{s-1}C_s(p)(1-p)^{s(N-s)}.$$

因此不必把亚临界近似 1/(1−rho) 硬套到临界点，而可直接计算

$$A_N(\rho)=\mathbb E S_2=N\sum_{s=1}^N s\pi_{N,s}(\rho/(N-1)),$$
$$B_N(\rho)=\mathbb E S_3=N\sum_{s=1}^N s^2\pi_{N,s}(\rho/(N-1)).$$

有限图概率公式是精确的；本实现是 380 位十进制数值求值，不能称为符号精确运算。另用 460 位复算部分点，并用小图全枚举核对 S2、S3。低 p 时递推发生严重相消，普通双精度直接相减会失真。

物理估计器以样本均值和无偏样本方差构造

$$\widehat q=\overline V/(uN),\quad
\widehat A=s_V^2/[\widehat q(1-\widehat q)u^2],\quad
\widehat\rho=A_N^{-1}(\widehat A).$$

价格响应再由

$$\widehat\lambda=Nu\sqrt{(1-\widehat q)s_r^2/s_V^2}$$

得到。求逆使用密集网格插值，并记录合法矩域边界；它不是监督学习，不使用训练标签。在有限窗口里有插值误差、矩估计误差和模型假设误差；可识别性不保证无偏或最优。

## 2. 一个与网络分布无关的联合矩约束

沿用 Q、M、q、S_j；q∈(0,1)，图可以逐期按任意分布抽取，群体动作规则保持不变。因为 E[M|H]=qN 不随图改变，三阶全累积量没有额外的条件均值项，故

$$\kappa_3(M)=q(1-q)(1-2q)\mathbb E S_3,$$
$$\operatorname{Cov}(Q^2,M)=q(1-q)\mathbb E S_3.$$

第一式也可直接展开 M−qN=Σs_i(I_i−q)：不同指标交叉项因独立、零均值消失；Bernoulli 的三阶中心矩为 q(1−q)(1−2q)。第二式已在基础稿中证明。

消去 E S3，并使用 Var(Q)=q E S2、Var(M)=q(1−q) E S2，回到观测单位后得到

$$\boxed{(1-q)\kappa_3(V)\operatorname{Var}(r)
-(1-2q)\operatorname{Cov}(r^2,V)\operatorname{Var}(V)=0.}$$

可写成无量纲残差

$$\mathcal Z=(1-q)\frac{\kappa_3(V)}{uN\operatorname{Var}(V)}
-(1-2q)\frac{\operatorname{Cov}(r^2,V)}{uN\operatorname{Var}(r)}=0.$$

它不含 lambda、不要求 ER，也没有临界近似。图族参数拟合之前，就能检查共同动作／聚合接口是否与数据相容。实际计算以模型已知的零收益均值构造二阶矩，并在每次 bootstrap 中重新估计 q。

边界必须明确：这是必要条件，不是充分条件；满足它不能唯一证明羊群或 ER。q=1/2 时三阶条件退化，不适合单独检验耦合。真实市场的 N、u 未知时，也不能直接把模拟标准化搬过去。

## 3. 严格尺度不变性可以作为设计条件

若一个窗口的收益统一乘以 b>0，收益标准差、平均绝对值和分位数都乘以 b；零收益比例和 corr(V,|r|) 不变。因此以

$$\Phi(r,V)=\left(\frac{\overline{|r|}}{s_r},\frac{Q_{.95}(|r|)}{s_r},
\frac{Q_{.99}(|r|)}{s_r},\Pr_T(r=0),\overline V,s_V,Q_{.95}(V),\operatorname{corr}(V,|r|)\right)$$

作为输入，就有 Phi(br,V)=Phi(r,V)。任何固定学习器在该表示上的输出也不变。要删除尺度坐标 s_r，而不是保留它并希望模型自己学会忽略。

这个性质只处理窗口内共同的正尺度因子；不保证处理逐期变化的冲击、非线性价格影响或真实制度变化。丢弃尺度也会丢失有用信息，因此无漂移时可能降低预测精度。尺度稳健与统计效率是两个需要分别验证的目标。

## 4. “临界”必须注明是哪一种

本组 ER 临界性是静态群体几何：N→∞ 时巨型分量出现。它不自动包含策略适应、时间记忆或泡沫积累。

[Lux–Marchesi（1999）](https://www.nature.com/articles/17290)通过趋势、群体意见及策略利润驱动的交易者转换，研究内生波动与暂时失稳；其动态稳定性问题不同于静态 ER 渗流。

[Johansen–Ledoit–Sornette，arXiv v2](https://arxiv.org/abs/cond-mat/9810071v2) Section 2.1、式 (2)–(3) 使用跳跃风险过程。在其简化鞅条件下，dp/p=mu(t)dt−kappa dj、E[dj]=h(t)dt，故 mu=kappa h。未崩盘路径上

$$\log p(t)-\log p(t_0)=\kappa\int_{t_0}^t h(s)ds.$$

若额外假设 h(t)∝(t_c−t)^(−alpha)、0<alpha<1，积分给出 log p=A−B(t_c−t)^(1−alpha)。这将随时间增长的风险与条件价格增长联系起来；临界时间不是确定的崩盘日期。

这是对文献机制的比较与条件推导，本项目没有实现该动态模型或验证其预测能力。不能把 ER 的 rho=1、动态失稳阈值和拟合出的 t_c 当作同一个量。

## 5. 三层结论

1. **机制相容性：**联合矩与边际保真对照可排除某些替代耦合；不等于确定真实机制。
2. **模型内校准：**接受 ER 和已知 N、u 后，可恢复参数并检验有限样本精度。
3. **结构识别边界：**放宽到一般图分布，基础稿的精确观测等价仍成立；再强的拟合器也不能越过该边界。

因而“参数估得准”和“机制解释正确”是不同成果，需要不同证据。
