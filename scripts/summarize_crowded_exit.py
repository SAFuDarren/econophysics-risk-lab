#!/usr/bin/env python3
"""Strict descriptive report for the fixed crowded-exit feasibility run."""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--root",type=Path,default=ROOT); args=parser.parse_args()
    root=args.root; table=root/"results/tables/crowded_exit_v1"; check=root/"results/checks/crowded_exit_v1"
    out=root/"results/analysis/crowded_exit_v1"; out.mkdir(parents=True,exist_ok=True)
    def read(name): return list(csv.DictReader((table/f"{name}.csv").open()))
    caps,pairs,summary,replay=map(read,["capacities","paired_capacity","summary_metrics","volume_replay_summary"])
    cfg=json.loads((root/"configs/crowded_exit_v1.json").read_text()); gate=json.loads((check/"gate.json").read_text())
    ones=[r for r in caps if r["method"]=="OneRound"]
    highest=max(ones,key=lambda r:float(r["nav_loss_fraction"]))
    primarydepth=max([r for r in ones if r["depth_multiplier"]=="1.0"],key=lambda r:float(r["nav_loss_fraction"]))
    vloss=max(float(r["nav_loss_fraction"]) for r in ones)
    certificate={"status":"pass" if vloss<cfg["loss_buffer"] else "not_satisfied",
                 "scope":"Sufficient model condition, conditional on fixed z/D and no exogenous shock; not market validation",
                 "states":len(ones),"max_initial_loss_fraction":vloss,"response_buffer":cfg["loss_buffer"],
                 "loss_budget":cfg["max_nav_loss"],"source_sha256":hashlib.sha256((table/"capacities.csv").read_bytes()).hexdigest(),
                 "all_volume_equal_one_round_equal_feedback":all(float(r["volume_cap_usd"])==float(r["one_round_cap_usd"])==float(r["feedback_cap_usd"]) for r in pairs),
                 "derivation":"docs/theory/CROWDED_EXIT_v1.md; monotone L(A,f) and L(A_V,f)<buffer imply q_k=f below the volume ceiling"}
    (check/"capacity_certificate.json").write_text(json.dumps(certificate,ensure_ascii=False,indent=2)+'\n')
    eq=next(r for r in replay if r['allocation']=='Equal' and r['method']=='VolumeOnly')
    conservative=next(r for r in replay if r['allocation']=='Equal' and r['method']=='ConservativeVolume')
    text=f'''# 拥挤退出最小检验：未发现额外容量增量，停止扩展

**固定参数下，190个月度截面×4种原配置×3档深度的2,280个状态，成交量约束、一次冲击和多轮反馈的资本上界完全相同。新增反馈的容量折减为0%，未通过运行前材料性门槛。按用户要求，停止这一应用扩展，保留原羊群—渗流—临界性课程主线。**

## 1. 比较了什么

只使用已有六策略/九ETF和四种原配置，2011-01至2026-10-23共190个最后可用月度截面；最后一月不完整。一次账户先净额，未虚构六家独立基金。计划减仓25%，3交易日、每日10%成交额参与率，费用5bp；过去20日成交额和63日波动代理深度，d=1为主，0.5/2为敏感性。统一2%损失触发线、响应斜率5、5%NAV损失上限。

本轮是**计划减仓的自冲击**，没有叠加外生价格冲击、外部基金交易或冲击恢复。真实持仓代理和行情只提供条件输入，冲击/响应规则未被执行数据校准。

## 2. 容量结果

|配置|深度d|状态数|平均额外容量折减|最大额外容量折减|达到10%的状态|
|---|---:|---:|---:|---:|---:|
'''
    for r in summary:
        text+=f"|{r['allocation']}|{float(r['depth_multiplier']):g}|{r['snapshots']}|{float(r['mean_haircut_pct']):.3f}%|{float(r['max_haircut_pct']):.3f}%|{r['material_snapshots']}|\n"
    text+='''
固定案例：资金按十亿美元计，数值是成交额代理下的上界，不是实际可部署资金建议；损失是模型内标记/成交费用损失。

|日期|成交量上界|一次冲击上界|反馈上界|一次冲击NAV损失|
|---|---:|---:|---:|---:|
'''
    for day in ['2019-12-31','2020-02-28','2020-03-31','2022-12-30','2026-10-23']:
        r=next(x for x in pairs if x['date']==day and x['allocation']=='Equal' and x['depth_multiplier']=='1.0')
        c=next(x for x in caps if x['date']==day and x['allocation']=='Equal' and x['depth_multiplier']=='1.0' and x['method']=='OneRound')
        text+=f"|{day}|{float(r['volume_cap_usd'])/1e9:.3f}|{float(r['one_round_cap_usd'])/1e9:.3f}|{float(r['feedback_cap_usd'])/1e9:.3f}|{100*float(c['nav_loss_fraction']):.3f}%|\n"
    text+=f'''
## 3. 为什么为零：可检查的充分条件

三者相同不是因为代码禁用了反馈。独立合成测试可触发反馈并收紧容量，只用于核验实现，不作为本组市场成果。

实际2,280个状态在成交量上界的一次冲击损失，最大为{100*vloss:.5f}%（{highest['date']}、{highest['allocation']}、d={highest['depth_multiplier']}），低于固定2%触发线；主深度所有配置最大为{100*float(primarydepth['nav_loss_fraction']):.5f}%。因此，在满足成交量约束的资金区间，反馈不会启动，5%损失上限也不绑定。

损失随资金规模单调增加，使这个结果可由充分条件核对：若在成交量上界仍未触发反馈，较小资金也不会触发。[推导](../../../docs/theory/CROWDED_EXIT_v1.md)与[证书](../../checks/crowded_exit_v1/capacity_certificate.json)给出条件和全部状态检查。不能据此推断其他风控规则或完整危机中的反馈没有价值。

## 4. 普通成交量不确定性比新增反馈更直接

按每个模型给出的资金上界、下一3日等速执行，使用已发生的美元成交额代理检查每日参与率。189个截面有完整未来3日，末端1个截面记缺失；所有历史已查看，属于回顾性重放。

Equal主配置：三个模型均有{eq['volume_breaches']}/{eq['origins_with_future']}={100*float(eq['volume_breach_fraction']):.2f}%截面超过参与率代理。简单改用过去20日美元成交额的20%分位作基线，则为{conservative['volume_breaches']}/{conservative['origins_with_future']}={100*float(conservative['volume_breach_fraction']):.2f}%，但平均部署资本只剩{100*float(conservative['mean_relative_capital']):.2f}%。

这表明按均值成交额将资金推到理论上界并不能保证未来每日成交量足够；保守成交量基线改变了超限/资金利用的取舍。不能将其称作最优规则、实际成交失败、滑点预测或物理增量，也不能隐去较少资金这一代价。

## 5. 停止决定与可允许主张

- 保留：本参数/资产/账户设定中，成交量约束先绑定；新增自冲击反馈没有改变容量，主门槛失败，停止应用扩展。
- 保留：普通成交量代理也有未来变化风险，需要连同资金利用率解释；原固定六策略、四配置及所有负结果不删。
- 不允许：羊群/反馈永远无用、ETF真实安全容量已测准、市场没有临界性、成功避免X%损失、风险预测优于统计基线、分枝/ER临界指数已经在六策略中测得。
- 不追加：调低2%阈值、扩大杠杆/规模、换资产、加机构或新模型寻找正结果。原课程理论、模拟、识别边界和真实量价检验继续作为正文。

所有数值源于固定情景的确定性计算，无p值或置信区间。历史状态与参数敏感性不是独立试验或抽样区间。成员科学签收仍not_run。

## 图与复算

- [C01 容量重合与配对零增量](../../../figures/crowded_exit_v1/C01_capacity.png)
- [C02 为什么反馈未激活](../../../figures/crowded_exit_v1/C02_activation.png)
- [C03 成交量约束与资金利用](../../../figures/crowded_exit_v1/C03_volume_replay.png)
- 配置/契约、九张CSV、冻结SHA、方法核验和独立目录复算共同形成证据链；最终PPT和成员验收不由本报告自动完成。
'''
    (out/'analysis-report.md').write_text(text)
    stats='''# 统计与计算口径

1. 估计对象是固定账户/持仓、资金与深度条件下的资本上界。方法为精确解析成交额界、连续执行价格现金积分、单调反馈迭代和可行性二分，不训练ML。
2. 190个月度状态、四配置、三深度均完整报告；2,280为配对情景数而非独立市场样本数。原价格与事件早已查看，未新增盲测。
3. 主比较Feedback vs OneRound，指标100*(1−A_feedback/A_one_round)，单位百分比；正值表示模型要求更低资本，不是收益改善。VolumeOnly是成交额参照，同深度行重复是为了配对，不重复算样本。
4. 主门槛在结果前冻结：Equal、d=1、容量折减≥10%且至少涉及两个不同自然年。没有显著性检验，不把人为10%门槛当行业标准。敏感性不能救活失败的主门槛。
5. 这些是确定性条件结果，p值/置信区间不适用；均值、标准差、分位数是全体所选历史状态的描述。三档深度不是概率区间，也未形成市场参数后验。
6. 未来成交额重放只用当时可用持仓与先前20日成交额：下一3日按等速退出，检查压力前数量计价的美元成交额代理。未模拟日内调度、ETF额外流动性渠道、真实订单簿或因果冲击。末端缺失保留。
7. 重放的超限率与部署资本必须同时报告；ConservativeVolume是过去20日成交额20%分位的简单强参照。没有新规则的盲测优势声明。
8. 现金数值积分与解析式独立核对；合成正例仅证实反馈代码可工作。输入和源代码结果前SHA冻结；旧协议/交接包保留。解释性单调充分条件为结果后分析，未用于改参数。
9. 不能把净额后的一个账户解释成六家外部机构，不能将新反馈增益等同原ER平均度rho，不能由无外生冲击的实验否定完整危机传染。
'''
    (out/'stats-appendix.md').write_text(stats)
    (out/'summary.json').write_text(json.dumps({'status':'stop_expansion','gate':gate,'certificate':certificate,'primary_replay':{'mean_volume':eq,'conservative_volume':conservative},'member_review':'not_run'},ensure_ascii=False,indent=2)+'\n')
    print('Wrote analysis report, statistics appendix and sufficient-condition certificate; decision: stop expansion.')


if __name__=='__main__':main()
