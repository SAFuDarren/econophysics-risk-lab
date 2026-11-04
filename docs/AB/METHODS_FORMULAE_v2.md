# AB方法、公式与符号：机制研究＋下一日波动预测

以[项目概览](../../README.md)为内容入口。本表解释已经执行的分析，不预设预测优势、普适幂律或真实市场rho。源码、原配置和冻结报告仍是计算依据。

## 1. 术语与单位先固定

|符号/术语|统一含义|边界|
|---|---|---|
|r_t^model|模型一期归一收益|不是某个真实账户收益|
|r_dj|真实第d日第j根5分钟log收益|来自已保存return_log，跨日边界沿用原数据处理|
|V_t^model、v_dj、V_d|模型活动量；真实BTC根成交量；日总量|成交量不是净资金流，BTC/USDT单位不混用|
|N、s_C、S_j|模型人数、群体大小、群体j阶和|真实市场没有这些真值标签|
|p、rho|ER边概率、有效平均度rho=p(N−1)|不等于真实市场相关系数或危机概率|
|q、a|总活动概率q；旧代码单方向概率a=q/2|不是旧稿中的边保留率|
|lambda、u|模型价格响应、单位订单数量|不是已估计真实盘口深度和订单量|
|RV_d、z_d|日内5分钟收益平方和；其log|RV是方差代理，100√RV为波动强度|
|HAR|Heterogeneous Autoregressive表示，此处用1/7/28日|7/28是24/7市场改编，不是原文逐项复刻|
|alpha_R|岭回归惩罚|不与尾部指数混用|
|Skill_B|相对明确参照B的损失下降百分比|不是涨跌正确率、年化收益或因果贡献|

## 2. 羊群模型与矩关系

群体动作跨群体独立、对称，P(xi_C=±1)=q/2，P(xi_C=0)=1−q；固定N≥2、0<q<1、lambda>0、u>0，动作独立于当期图。

\[
r=\frac{\lambda}{N}\sum_Cs_C\xi_C,\quad
V=u\sum_Cs_C|\xi_C|,\quad S_j=\sum_Cs_C^j.
\]
\[
E[V]=quN,\quad \operatorname{Var}(r)=q(\lambda/N)^2E[S_2],\quad
\operatorname{Var}(V)=q(1-q)u^2E[S_2].
\]

用途：检验代码、说明同均量不固定风险、连接协调群体与宏观统计。原观测接口为外部对手方简化全成交，不是实际订单簿清算。

若每期图与动作独立重采样、参数固定，则E[r_{t+1}²|F_t]=q(lambda/N)²E S₂为常数。时间预测需要额外时间结构；不能把固定ER基线当作现成的波动预测器。

## 3. 渗流、临界、尾部与标度

\[
\rho=p(N-1),\quad P_\infty=s_{max}/N,\quad
\chi_f=\frac{\sum_{C\ne C_{max}}s_C^2}{\sum_{C\ne C_{max}}s_C}.
\]

chi_f排除一个最大分量，与包含全部群体的S₂不同；如没有剩余分量，沿用原源表的缺失口径，不编造有限值。N=128/256/512、9rho、40图/点，共1,080图。rho=1为无限稀疏ER阈值，有限系统曲线非奇点。

均场临界群体数密度n_s∝s^(−5/2)。如连续密度f(x)∝x^(−alpha)，相应CCDF尾指数为alpha−1；不能把群体密度、收益密度和收益CCDF混成同一指数。多群体加和、活动、符号抵消、有限支持均影响收益尾部。

实际手法：群体/收益CCDF、有限范围离散纯幂律拟合与拟合优度、替代分布、系统规模和采样聚合对照。当前有限范围纯幂律被拒绝；没有普适收益指数、SOC或市场阈值结论。

## 4. 条件反演与结构等价

定义有限ER A_N(rho)=E[S₂]，严格递增。已知N/u并维持模型前提：

\[
q=E[V]/(uN),\quad A_N(\rho)=\operatorname{Var}(V)/[q(1-q)u^2],\quad
\lambda^2=N^2u^2(1-q)\operatorname{Var}(r)/\operatorname{Var}(V).
\]

有限图递推与物理矩估计器提供反演参照；经典回归用相同窗口/划分比较收益、量、联合及尺度不变表示，训练数据不含标签元信息。10次独立重训报告跨研究误差，不把同一路径窗口当独立训练研究。

链边{12,23,34}与星边{12,13,14}都形成一个大小4的群体，因此当前接口有完全相同联合量价分布。它证明内部边不可识别，不是只用某分类器失败作推断。有限样本误差与总体不可识别分开。

## 5. 市场联合约束与时间统计

对模型图分布不作ER限制，固定观察接口要求

\[
\Delta=\frac{\operatorname{Cov}(r^2,V)/\operatorname{Var}(r)-\kappa_3(V)/\operatorname{Var}(V)}{E[V]}
=\frac{E[S_3]}{N E[S_2]}\in[1/N,1].
\]

实际r去样本常数漂移后计算；总体模型均值为0。BTC H1校准/H2留出，7日循环日期块区间，月度与极端日敏感性。负Delta挑战固定N/q/u/lambda、对称独立动作、简化执行/冲击这一组前提；不是所有羊群机制的否证。

时间分析保留有符号/幅度相关、季节调整和时间聚合方差比。H2 |r|一期相关0.344说明时间结构；与n_s群体标度不是同一对象，也不是SOC证明。

## 6. 预测输入的精确定义：源代码一致的10项

每天M=288，真实根收益r_j、BTC成交量v_j，记rc_j=r_j−bar r、vc_j=v_j−bar v，sigma_r²=mean(rc²)，V_d=Σv_j，F_d=Σ signed_taker_volume_j。

|输入组|公式/定义|项数|
|---|---|---:|
|HAR|log RV_d；log(mean(RV_{d−6:d}))；log(mean(RV_{d−27:d}))|3|
|Activity|log V_d；log[V_d/mean(V_{d−6:d})]|2|
|Coupling|Spearman(|r_j|,v_j)；mean(rc_j² vc_j)/(sigma_r² mean(v_j))；|F_d|/V_d|3|
|Tail|log[M Σr_j⁴/(Σr_j²)²]；max(r_j²)/Σr_j²|2|

主动成交方向是交易场所字段派生量，不是盘口OFI或市场全部买量减全部卖量。Tail项是有限样本形状/集中度，不是已估计幂律指数。HAR+All同时增加成交与收益形状，不能将其增量全部归给成交量。

## 7. 预测器、时间协议与参照

\[
RV_d=\sum_j r_{d,j}^2,\quad z_{d+1}=\log RV_{d+1},\quad
\widehat z_{d+1}=\bar z_{fit}+\widehat w^T\widetilde x_d,
\]
\[
\widehat w=\arg\min_w\sum_{d\in fit}(z_{d+1}-\bar z_{fit}-w^T\widetilde x_d)^2+\alpha_R\|w\|^2.
\]

tilde x由拟合期均值/标准差得到。原模型使用中心化目标、无额外岭截距的实现；推断时加回目标均值。alpha在2026Q1选定，之后用427日拟合一次；最终183日系数固定。已有测试日的观测可作为之后预测日的过去输入，不进入重新拟合。

参照保留：原拟合目标的固定log均值；昨日RV延续；验证选EWMA；HAR；Activity/Coupling/Tail消融；RBF同输入对照。模型/特征/预算以原forecast_v1契约和源码为准。本次收敛不重做训练。

## 8. 损失、技能与区间

\[
L_{\log}=\frac1D\sum_d(\log RV_d-\widehat z_d)^2,
\]
\[
L_Q=\frac1D\sum_d\left(RV_d/\widehat{RV}_d-\log(RV_d/\widehat{RV}_d)-1\right),\quad
L_\sigma=\frac{100}D\sum_d|\sqrt{RV_d}-\sqrt{\widehat{RV}_d}|,
\]
\[
Skill_B=100\left(1-\overline L_{model}/\overline L_B\right),\quad
\widehat{RV}_d=\exp(\widehat z_d).
\]

日期为配对单位，4,999次循环1/7/14日块，7日为主口径。新增整体技能复核的区间未经多重性调整且为事后描述；原增量族的Holm结果继续保留。相对HAR的原主族p≈0.3948，未确认稳定新增优势；跨零不是统计等效证明。指数变换不保证条件算术均值或风险资本校准。

## 9. 方法—证据—主张边界索引

|分析|入口/结果|可支持|
|---|---|---|
|网络与动作|src/econophysics/model.py；simulation_study_v1|群体协调的模型机制|
|有限图反演|src/econophysics/physics_inference.py；depth_study_v1|限定家族的模型内参数恢复|
|真实量价|real_market_v1；REAL_MARKET_BOUND|联合相容性与时间结构|
|下一日预测|src/econophysics/forecasting.py；forecast_v1|原历史留出的整体技能与增量区分|
|目标重评|predictive_utility_v1|固定均值/简单参照与强HAR完整对照；不是新训练/新验证|
|后续扩展|state_forecast_v2、tail_increment_v1、crowded_exit_v1|保留边界/阴性证据，不宣称实用增量|

当前没有真实网络标签、涨跌预测成果、已校准极端概率、实盘收益或量子优势。成员科学复核仍需独立完成。
