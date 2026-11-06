#!/usr/bin/env python3
"""Evidence-first US sector/P&L analysis bundle and human reading copy source."""

from pathlib import Path as _ProjectPath
import sys as _project_sys
_project_sys.path.insert(0, str(_ProjectPath(__file__).resolve().parents[1]))
from _bootstrap import ROOT as PROJECT_ROOT, script_path, resolve_recorded_path
from pathlib import Path
import csv,json,numpy as np
ROOT=PROJECT_ROOT

def read(n):return list(csv.DictReader((ROOT/f'results/tables/us_equity_v1/{n}.csv').open()))
def f(r,k):return float(r[k])

def main():
    out=ROOT/'results/analysis/us_equity_v1';out.mkdir(parents=True,exist_ok=True);check=ROOT/'results/checks/us_equity_v1';run=json.loads((check/'run_record.json').read_text());selection=run['selection'];primary=read('risk_primary');metrics=read('risk_metrics');redundancy=read('redundancy_diagnostic');pairs=read('strategy_pairs');alloc=read('allocation_metrics');ac=read('allocation_contrasts');daily=read('daily_risk');hist=next(r for r in primary if r['split']=='historical_test');conf=next(r for r in primary if r['split']=='confirmation');strong=selection['risk_reference']
    def met(split,name):return next(r for r in metrics if r['split']==split and r['model']==name)
    diagnostic={}
    for split,lo,hi in [('historical_test','2020-01-01','2026-01-01'),('confirmation','2026-01-01','2026-10-24')]:
        rows=[r for r in daily if lo<=r['date']<hi];diagonal=met(split,'Diagonal-63');reference=met(split,strong);diagnostic[split]={'rolling_collective_fraction_mean':float(np.mean([f(r,'collective_fraction') for r in rows])),'rolling_full_diagonal_volatility_ratio_median':float(np.median([f(r,'volatility_ratio_full_to_diagonal') for r in rows])),'EWMA_qlike_gain_over_diagonal_pct':100*(1-f(reference,'qlike')/f(diagonal,'qlike'))}
    main_table='\n'.join(f"| {'2020–2025' if r['split']=='historical_test' else '2026确认'} | {r['n']} | {f(r,'improvement_pct'):.2f}% | [{f(r,'ci_low'):.2f}%, {f(r,'ci_high'):.2f}%] |" for r in primary)
    risk_table='\n'.join(f"| {'2020–2025' if split=='historical_test' else '2026确认'} | {f(met(split,'Diagonal-63'),'qlike'):.4f} | {f(met(split,strong),'qlike'):.4f} | {f(met(split,'ReturnGamma'),'qlike'):.4f} | {f(met(split,'NetworkGamma'),'qlike'):.4f} |" for split in ['historical_test','confirmation'])
    allocation_table='\n'.join(f"| {'历史' if r['split']=='historical_test' else '确认'} | {r['method']} | {f(r,'cumulative_pnl_pct'):.2f}% | {f(r,'annual_sigma_pnl_pct'):.2f}% | {f(r,'mean_underlying_gross_exposure'):.3f} |" for r in alloc if r['cost_bps']=='5' and r['split'] in ['historical_test','confirmation'])
    a0=next(r for r in ac if r['split']=='historical_test' and r['block_sessions']=='20');a1=next(r for r in ac if r['split']=='confirmation' and r['block_sessions']=='20');d0=diagnostic['historical_test'];d1=diagnostic['confirmation'];rr0,rr1=redundancy
    report=rf'''# 群体波动、行业联动与策略P&L

Econophysics Risk Lab · 2026-10-27 · AB · 美股应用分析，待成员科学复核

## 1. 结论：量化了遗漏与冗余，未得到新预测或盈利优势

本批完成十一ETF日线、九行业相关网络、组合风险分解、六条固定策略P&L和四种既有配置方法。新增网络特征的风险预测不优于匹配收益模型；HRP也未建立稳定配置优势。保留全部控制和成本敏感性，不继续用当前留出调参。

**支持的实际用途是风险模型审计和因子冗余筛查。** 历史期逐日63日估计中，行业联动方差占比均值为{100*d0['rolling_collective_fraction_mean']:.2f}%，完整/对角波动之比的中位数为{d0['rolling_full_diagonal_volatility_ratio_median']:.2f}。两个低波动参数版本的每日净P&L相关为{f(rr0,'daily_net_correlation'):.3f}，等风险两策略的有效数量约{f(rr0,'equal_risk_two_sleeve_effective_count'):.2f}。这些不是新alpha或可实现收益。

| 评价区间 | 五日目标数 | QLIKE改善 | 近似95%区间 |
|---|---:|---:|---:|
{main_table}

负改善表示误差增加；2026只含40个非重叠目标，长期稳定性不能由此保证。历史主区间跨零；确认区间完全为负。预设研究门槛未达。

新数据共46,530行、4,230个收盘日期（含2009年末两日参考），研究日期2010年至2026-10-23共4,228日。原始字段逐条重建核对；全部交易日对齐，无填补或删除。时间留出不是对已知历史事件的盲测。

<!-- pagebreak -->

## 2. 保留物理主线：群体放大到观测投影

![既有F03：羊群网络的有限规模连通过渡](../../../figures/simulation_study_v2/F03.png)

上图为既有模拟证据，并非本批美股估计。研究主体仍是羊群交互、群体连通、渗流/临界、收益尾部和时间标度；泡沫/崩盘与适应机制由原始文献综述说明，不把静态基线称为已实现的适应市场。

原模型群体二阶矩控制波动：

$$r=\frac{{\lambda}}{{N}}\sum_Cs_C\xi_C,\qquad \operatorname{{Var}}(r)=q(\lambda/N)^2 E S_2,\quad S_2=\sum_Cs_C^2.$$

作为明确条件下的观测扩展，设多维观测$Z=\sum_Cb_C\xi_C+\epsilon$，策略权重$W$在动作前已确定，则

$$\operatorname{{Cov}}(WZ)=q\sum_C(Wb_C)(Wb_C)^T+WDW^T.$$

共同载荷会通过策略暴露投影成共同P&L风险。该补充推导在主结果后提出，81状态有理数枚举通过；未用作预测方法或市场拟合。详见[完整条件与证明](../../../docs/theory/COLLECTIVE_PNL_v1.md)。真实相关矩阵没有微观群体标签，不能识别真实羊群/临界点。

<!-- pagebreak -->

## 3. 数据与行业联动：观察结构，不制造真实网络

![U01：预设历史窗口的行业相关图](../../../figures/us_equity_v1/U01.png)

九行业为XLB/XLE/XLF/XLI/XLK/XLP/XLU/XLV/XLY，SPY/QQQ只作参照；ETF持仓与行业定义随历史改变，不代表完整美股。供应商复权收盘构造总回报代理，原始OHLCV、分红和拆股同时保存；当前复权历史不是历史时点数据版本。

2010–2017训练，2018–2019选参，2020–2025历史留出。验证选择及代码哈希锁定后才获取2026年1月2日至10月23日的204日确认数据。确认期与既有加密研究共享部分市场背景，不是所有意义上的独立复现。

U01采用相同节点位置和0.60正相关阈值，相关窗口为63个交易日；三个历史日期事先指定。它展示收益关联，不是交易者、持股或因果传播网络。九节点图不能证明热力学临界性。

美股日线与加密5分钟数据不直接横比尾指数、原始成交量或不同目标的损失。本批未把成交量加入预测：检验的是横截面联动信息，不能称量价增益。

<!-- pagebreak -->

## 4. 联动风险与对齐信息：有数值，解释有边界

![U02：风险估计及保边际的移位对照](../../../figures/us_equity_v1/U02.png)

$$\hat v_p=w^T\hat\Sigma w=\sum_iw_i^2\hat\sigma_i^2+2\sum_{{i<j}}w_iw_j\hat\sigma_{{ij}},\qquad w_i=1/9.$$

2020–2025逐日滚动估计中，联动项占比均值{100*d0['rolling_collective_fraction_mean']:.2f}%；2026为{100*d1['rolling_collective_fraction_mean']:.2f}%。完整/对角波动比中位数分别{d0['rolling_full_diagonal_volatility_ratio_median']:.2f}、{d1['rolling_full_diagonal_volatility_ratio_median']:.2f}。这是一项同窗估计分解，不是真实条件方差或样本外预测增益。

每资产先按此前63日标准差标准化，再在每年内各自循环移位。每年的各资产经验边际值不变，而跨资产日期对齐改变。图中移位范围来自499次条件移位，不是抽样CI或因果p值；非平稳性/循环接缝限制其解释。完整逐年统计和全部重复均保留。

<!-- pagebreak -->

## 5. 未来风险：强参照有效，新增网络校准未通过

![U03：冻结比较的留出增量](../../../figures/us_equity_v1/U03.png)

$$Y_{{t,5}}=\frac15\sum_{{h=1}}^5(w^TR_{{t+h}})^2,\qquad L(Y,v)=Y/v-\log(Y/v)-1.$$

Y是未来五日平均平方收益，不是日内RV或可观察的真实条件方差。五类控制、两种窗口、EWMA两个衰减及两种Gamma校准全部保留。验证选择的强参照为EWMA-126-0.94；Gamma用$v_0$作offset，收益形状三项进入两模型，相关谱三项仅进入网络模型。

| 评价 | 对角63 | 强EWMA | 收益Gamma | 网络Gamma |
|---|---:|---:|---:|---:|
{risk_table}

常规EWMA相对对角控制的QLIKE分别下降{d0['EWMA_qlike_gain_over_diagonal_pct']:.2f}%、{d1['EWMA_qlike_gain_over_diagonal_pct']:.2f}%。它说明不能忽略联动及时间更新，**不是我们的新方法超过常规风险模型**；两种方法还同时具有估计/更新差别，不能把全部改善归因于相关性。

<!-- pagebreak -->

## 6. P&L：每日增量才是主要依赖对象

![U04：六条规则、全部曲线与增量相关](../../../figures/us_equity_v1/U04.png)

固定规则为动量63/126日（跳过21日）、反转5/21日、低波动21/63日。每次在九ETF中多3空3，目标gross=1。每周最后交易日收盘执行，用前一日及以前信号；持仓从下一交易日赚取盈亏，周内固定总回报指数单位。

$$p_{{s,t}}=\sum_iq_{{s,i,t-1}}(T_{{i,t}}-T_{{i,t-1}})-c\sum_i|\Delta q_{{s,i,t}}|T_{{i,t}}-b_t.$$

主成本为每单边成交额5bp、空头100bp假设年借券费；另保留0/10/25bp。不是实际成交/券源数据。盈亏按固定参考资本相加，不报CAGR或可实现收益。

低波动两版本在2026的每日净P&L相关{f(rr1,'daily_net_correlation'):.3f}，累计曲线相关约{f(next(r for r in pairs if r['split']=='confirmation' and r['strategy_a']=='LowVol-21' and r['strategy_b']=='LowVol-63'),'cumulative_pnl_correlation_warning_only'):.3f}。累计曲线会改变依赖度量；不能用它代替每日增量来判断独立性。

<!-- pagebreak -->

## 7. 因子挖掘的正向作用：识别冗余及暴露来源

![U05：低波动参数版本的冗余与条件风险分解](../../../figures/us_equity_v1/U05.png)

训练期最高正相关规则选出LowVol-21/63。这个解释性诊断是在主结果之后追加，不能冒称新的预注册检验。历史每日相关{f(rr0,'daily_net_correlation'):.3f}，20日块区间[{f(rr0,'corr_ci_low'):.3f},{f(rr0,'corr_ci_high'):.3f}]；确认相关{f(rr1,'daily_net_correlation'):.3f}，区间[{f(rr1,'corr_ci_low'):.3f},{f(rr1,'corr_ci_high'):.3f}]。

若两条策略作等风险配置，其有效独立风险来源数$2/(1+\rho)$约为{f(rr0,'equal_risk_two_sleeve_effective_count'):.2f}、{f(rr1,'equal_risk_two_sleeve_effective_count'):.2f}；它不是独立alpha数量。参数数量增加不能直接算作分散化增加。

$$\hat\Sigma^{{PL}}=W\hat\Sigma W^T=W\operatorname{{diag}}(\hat\Sigma)W^T+W[\hat\Sigma-\operatorname{{diag}}(\hat\Sigma)]W^T.$$

共享持仓和资产协方差项可正可负。该低波动例子的历史交叉资产项抵消部分共享暴露项；不能把所有市场共同波动都描述成增加长短策略风险。这是当前暴露下的风险候选，不是未来P&L精确分解或唯一因果来源。用途是候选筛查/暴露审计，低相关或高相关均不能单独证明alpha。

<!-- pagebreak -->

## 8. 配置实际例子：全部成本后曲线为负

![U06：四种既有配置方法的净P&L](../../../figures/us_equity_v1/U06.png)

Equal、InverseVol、LW-MinVariance及HRP使用过去126日净增量，调仓保留一交易日信号延迟；组合先聚合底层持仓再扣成本，避免重复计费。验证选择强配置参照为LW-MinVariance。

| 评价 | 方法 | 累计净P&L | 年化波动 | 平均底层gross |
|---|---|---:|---:|---:|
{allocation_table}

HRP相对强参照的波动下降为历史{f(a0,'sigma_reduction_pct'):.2f}%（区间[{f(a0,'sigma_ci_low'):.2f}%,{f(a0,'sigma_ci_high'):.2f}%]）、确认{f(a1,'sigma_reduction_pct'):.2f}%（[{f(a1,'sigma_ci_low'):.2f}%,{f(a1,'sigma_ci_high'):.2f}%]）。均未建立稳定优势；全部曲线亏损，不称有效因子发现。结果仅限这些九ETF样例，不否定全部学术动量/防御因子。

<!-- pagebreak -->

## 9. 全部风险控制与年份

![U07：全部模型与所有评价年份](../../../figures/us_equity_v1/U07.png)

矩阵保留14种方法；颜色为正QLIKE的对数尺度，数值没有截断。逐年点估计只作稳定性描述，不能事后挑最佳年份或追加赢家检验。

主不确定性为配对的4个五日目标块，4999次循环bootstrap，另1/13块敏感性。历史301个目标、确认40个目标；后者主块只有约10个块长度，依赖/非平稳使区间近似。主两项Holm已保留；原始重采样尾比例为0时代表分辨率下限，不是概率为0。

网络指标由同一相关矩阵计算，没有增加原始信息。此结果限制本次特征/估计器的预测主张，不能推出所有结构信息或所有学习器无用。

<!-- pagebreak -->

## 10. 复现、方法与汇报的主张范围

先读[冻结契约](../../../docs/AB/us_equity_v1_contract.md)、[统计附录](stats-appendix.md)、[图源/图注](figure-catalog.md)与[AB交接](../../../docs/AB/US_EQUITY_HANDOFF_v1.md)。运行入口和完整表随交接包提供，真实行情通过来源记录重建；公开访问不自动等于再分发授权。

复现区分两种口径：固定首次数据快照在独立目录重建19张CSV和15个持仓数组，全部精确一致；重新下载时仅复权收盘字段出现最大约1.10e-6的相对差异，主增量点估计改变不足0.0011个百分点，方向未变。完整原始收盘/成交量/分红拆股未变，供应商计算差异来源不确定；保留两份来源并明确外部下载不能逐字节复现。

方法包括：交易日历/公司行动检查、滚动协方差与相关谱、保边际的移位对照、Gamma准似然条件均值、训练/验证/历史/确认四段、块bootstrap、固定规则P&L与费用、既有HRP/收缩配置、已知暴露的矩阵投影。未使用真实潜在网络标签、盘口订单流、因子大搜索或量子优势结论。

原始研究连接：

- [Mantegna：金融收益的层级结构](https://arxiv.org/pdf/cond-mat/9802256)：收益相关网络的研究基础，不是微观网络恢复证明。
- [Ledoit–Wolf：协方差收缩](https://econ-papers.upf.edu/papers/691.pdf)：强风险参照的动机；本代码用sklearn scaled-identity目标，与该文constant-correlation目标有别。
- [López de Prado：HRP作者算法入口](https://www.quantresearch.org/Software.htm)：层次配置的既有参照，独立实现，未宣称原创或稳定超额收益。
- [Moskowitz–Grinblatt：行业动量](https://www.aqr.com/insights/research/journal-article/do-industries-explain-momentum)：经济背景，本六条ETF规则不是该论文的严格复制。
- [Bailey等：回测过拟合](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf)、[Harvey等：因子多重检验](https://people.duke.edu/~charvey/Research/Published_Papers/P118_and_the_cross.PDF)：固定候选、保留试验范围与不事后筛赢家的依据；没有声称已执行其PBO或发现新alpha。

本批可用于汇报的贡献：保留物理机制机制，量化哪些风险会被简化假设遗漏，展示如何筛查冗余因子，并用新确认期检验应用边界。成员科学签收、最终PPT、交互诊断器和公开GitHub仍待完成。
'''
    (out/'analysis-report.md').write_text(report)
    (out/'stats-appendix.md').write_text('''# 统计与执行附录

实验单位：风险为不重叠五交易日目标，P&L为日期；多资产/多策略不是独立市场重复。2010–2017训练、2018–2019选择、2020–2025历史测试，2026-01-02至10-23确认。历史事件已知，当前复权历史不是point-in-time版本。

QLIKE和log-MSE均保留。主Family为NetworkGamma vs ReturnGamma的历史/确认两项QLIKE，Holm；其他方法、指标、配置为完整探索性对照。主块4个五日目标，敏感1/13；4999次、固定seed。P&L比较用20日块、5/63敏感，波动下降与年化均值差/敞口同报。非参数块重采样不依赖高斯假设，但不保证非平稳下精确覆盖。原始bootstrap p=0不视作精确概率0，报告低于有限重复分辨率约0.0004。没有将重采样尾比例称作精确null test。

网络校准为Gamma准似然而非严格Gamma分布假设：mu=v0 exp(b+beta*xR+gamma*xC)，目标Y/v0，训练集标准化、独立L2、网络Off选项；验证后train+val重拟合一次、未来系数固定。保留逐目标预测、损失和全部选择网格。强参照只按验证选，固定相关控制的训练期矩阵仅在训练结束后用于评价，不用于训练期强参照或网络特征。

策略为固定指数单位，目标gross1、前日信号、当日收盘执行、次日起P&L；每单边5bp及年借券100bp是假设，另0/10/25bp。净额合并后扣费，不把gross降低自动计作配置优势。累计净P&L是固定资本加性量、非CAGR；Sharpe为零现金收益参照的描述量，未校正全部潜在试验选择或验证实盘可达性。

移位对照先按此前63日波动标准化，再逐年独立循环移位各资产；499次，偏移至少20日。保留该年的每列经验值，但接缝/非平稳/周期影响解释；范围是条件移位中央95%，不是真实重复抽样CI或因果p值。

事后辅助：LowVol参数冗余例子按2011–2017最高相关规则选，但诊断规则在主结果后提出，明确探索性；20日配对块区间。等风险Neff=2/(1+rho)不是独立alpha数量。W Sigma W分解是条件候选的恒等关系，不是整个未来P&L的精确协方差或唯一因果归因。条件羊群多观测推导以81个动作状态精确枚举，未拟合市场也未改变主方法。

完整数量与区间见risk_primary、risk_contrasts、risk_metrics、risk_yearly、strategy_metrics、allocation_metrics、allocation_contrasts、redundancy_diagnostic等源表。当前所有评价已被查看，后续调参需新协议和新增检验，不重写当前冻结。
''')
    sources=json.loads((check/'figure_qa/figure_sources.json').read_text());catalog=['# 图表目录与解释\n\n所有图是研究输出，成员科学签收未完成。\n']
    for item in sources:
        catalog.append(f"## {item['id']}\n\n文件：figures/us_equity_v1/{item['id']}.pdf/.svg/.png。\n\n源表："+'、'.join(item['sources'])+'。\n\n应注意：'+item['interpretation']+'\n\n检查：阅读完整图与所有控制；区分同窗描述、条件模型、移位范围和真正留出；不把历史波动/相关直接写成临界、预警或盈利。\n')
    (out/'figure-catalog.md').write_text('\n'.join(catalog))
    (out/'claim-candidates.md').write_text('''# 主张账本

| 主张 | 证据 | 可用措辞 | 禁止升级 | 状态 |
|---|---|---|---|---|
| 行业联动不可在该篮子描述中忽略 | daily_risk、surrogate_summary、U01/U02 | 同窗候选与保边际对照显示明显联动贡献 | 因果羊群/真实临界/预测胜利 | 保留描述 |
| 新网络校准未改善 | risk_primary、全部risk_metrics、U03/U07 | 本特征/估计器未确认增量，确认期更差 | 所有网络信息都无用 | 保留有范围结论 |
| 参数版本可能冗余 | strategy_pairs、redundancy_diagnostic、U04/U05 | LowVol21/63在两期具有较高每日相关 | 独立alpha数量精确恢复/所有防御因子无效 | 事后解释性 |
| 条件风险可由暴露与资产协方差投影 | exposure_decomposition、COLLECTIVE_PNL_v1 | 条件代数机制及81状态核验成立 | 唯一真实微观原因 | 条件成立 |
| HRP未建立实用优越性 | allocation_metrics/contrasts、U06 | 该固定规则/成本下无稳定优势、全部配置净亏损 | 全部HRP/全部量化因子无效 | 保留有范围结论 |
| 已解决真实交易盈利 | 无 | 无 | 不得宣称 | 不支持 |
''')
    summary={'status':'pass','main_predictive_gate_met':False,'new_profitable_factor_or_allocator_established':False,'diagnostic':diagnostic,'primary':primary,'redundancy':redundancy,'allocation_primary_exploratory':[a0,a1],'member_scientific_review':'not_run'};(out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':'pass','analysis_pages_planned':10,'forecast_gate':False,'profitable_factor_claim':False},indent=2))

if __name__=='__main__':main()
