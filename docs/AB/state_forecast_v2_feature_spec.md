# v2实现定义（先于预测结果）

最近4小时为UTC日末48根5分钟；负向半方差占比为sum(r²*1[r<0])/RV；标准化日收益为sum(r)/sqrt(RV)。HAR均值用RV的算术均值后取log，不是log均值。

成交状态分别为V_d/mean28(V)、Ntrades_d/mean28(Ntrades)，以及(V_d/Ntrades_d)/mean28(V/Ntrades)。第三项是逐日平均单笔规模的自身28日均值归一化，不是前两项之比；避免把精确共线特征误称新增信息。日末4小时量为其占全日量的份额。

有符号主动成交量I=2*taker_buy_volume-V。flow_persistence是日内I/V的滞后一期Pearson相关；activity_persistence是日内log(1+trades)的滞后一期相关。退化相关定义0并在实现检查中覆盖，不删行。流量响应代理为asinh[(sum(rI)/sum(I²))*mean28(V)/sqrt(mean28(RV))]，单位不变、仅为同根关联代理，不等同盘口冲击或因果弹性。

独立价格/量通道惩罚的Gamma目标为sum[RV/mu-log(RV/mu)-1]+(alpha_R||beta||²+alpha_V||gamma||²)/2，log(mu)=b+beta*x_R+gamma*x_V。标准化仅用当次训练窗口；intercept不惩罚。成交off时精确使用相应return-only模型，不能以极大有限数近似后声称零通道。

为数值稳定，仅把y除以当次训练均值，预测再乘回；不改损失、不截断实现值。Newton解析梯度/海森矩阵、回溯线搜索，记录梯度与收敛；没有用测试标签确定尺度或参数。
