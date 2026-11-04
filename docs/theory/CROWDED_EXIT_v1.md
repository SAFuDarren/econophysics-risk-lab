# 有限账户退出模型：现金守恒与反馈不激活的充分条件

这份解释性推导在固定参数结果产生后补充，不改变运行前契约或材料性门槛。它用于解释为什么输出为零增量，不是市场安全定理，也不宣称新理论。

令参考资本A、净敞口z_i、初始持仓X_i=A z_i、累计减仓q、深度D_i>0。价格路径p_i(s)=exp(−A z_i s/D_i)，I_i(q)=∫0^q p_i(s)ds。费用率c满足0≤c<1。

\[
L(A,q)=\sum_i z_i[1-I_i(q)-(1-q)p_i(q)]
+c\sum_i|z_i|I_i(q).
\]

该式包含已成交现金、剩余头寸标记和费用。卖出长仓与回补空仓都能造成损失；先净额后的相反订单不再产生交易。它不包括外生价格新闻、外部机构或冲击恢复。

对q求导：

\[
\frac{\partial L}{\partial q}
=(1-q)\sum_i\frac{A z_i^2}{D_i}p_i(q)
+c\sum_i|z_i|p_i(q)\ge0.
\]

对A求导（z_i=0的项按连续极限为零）：

\[
\frac{\partial L}{\partial A}=
\sum_i\frac{z_i^2}{D_i}\left[
(1-c\operatorname{sgn}z_i)\int_0^q s p_i(s)ds
+(1-q)q p_i(q)\right]\ge0.
\]

因此，在固定持仓、深度、减仓比例下，资金越大，损失不会变小。

令成交额约束给出的资本上界为

\[
A_V=\min_{i:z_i\ne0}\frac{H\alpha ADV_i}{f|z_i|}.
\]

若L(A_V,f)<b，其中b为损失反馈触发阈值，则所有A≤A_V都有L(A,f)<b。由q0=f以及

\[
q_{k+1}=\max\{q_k,\min[1,f+\beta(L(A,q_k)-b)_+]\}
\]

可知q_k始终等于f。再若L(A_V,f)≤l_max，则一次冲击的损失约束也不绑定，于是

\[
\boxed{A_{cap}^{Volume}=A_{cap}^{OneRound}=A_{cap}^{Feedback}=A_V.}
\]

这将“程序算出三条重合曲线”加强为一个可逐状态检查的充分条件。当前2,280个持仓/深度状态中，L(A_V,f)最大为1.79158%，低于b=2%且低于l_max=5%；主深度所有配置最大为0.89633%。来源为[完整容量表](../../results/tables/crowded_exit_v1/capacities.csv)，核对记录在[方法检查](../../results/checks/crowded_exit_v1/method_checks.json)。

局部活动区间的反馈增益是beta*∂L/∂q，若小于1则该局部光滑迭代稳定；未激活、饱和及全局状态须另外处理，不能把它当ER平均度或真实市场临界分数。当前可行容量区间中反馈未被激活，无需用临界放大解释它。

结论仅针对固定2%阈值、给定深度代理和没有外生冲击的计划减仓自冲击实验。不推断别的风险规则、低流动性资产或完整危机中的反馈也不重要；本轮停止，不调整规则寻找正结果。
