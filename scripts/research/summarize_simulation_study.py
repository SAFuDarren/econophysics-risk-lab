"""Recompute saved prediction statistics and write a bounded analysis bundle."""

from pathlib import Path as _ProjectPath
import sys as _project_sys
_project_sys.path.insert(0, str(_ProjectPath(__file__).resolve().parents[1]))
from _bootstrap import ROOT as PROJECT_ROOT, script_path, resolve_recorded_path

from pathlib import Path
import csv,hashlib,json,os,sys
ROOT=PROJECT_ROOT
sys.path.insert(0,str(ROOT/'src'))
import numpy as np
from econophysics.study_statistics import interval,stratified_bootstrap_mean


def read(path):
    with path.open() as f:return list(csv.DictReader(f))


def main():
    source=ROOT/'results/tables/simulation_study_v1';extra=ROOT/'results/tables/simulation_followup_v1'
    output=ROOT/'results/analysis/simulation_study_v1'
    output.mkdir(parents=True,exist_ok=True)
    (ROOT/'figures/captions').mkdir(parents=True,exist_ok=True)
    metrics=[r for r in read(source/'learning_metrics.csv') if float(r['training_fraction'])==1]
    contrasts=read(source/'view_contrasts.csv');tails=read(source/'tail_diagnostics.csv')
    interpolation=read(extra/'unseen_rho_metrics.csv');stress=read(extra/'stress_control_metrics.csv')
    predictions=read(ROOT/'results/predictions/simulation_study_v1/test_predictions.csv')
    validations=[]
    for row in metrics:
        matched=[r for r in predictions if r['method']==row['method'] and r['view']==row['view']]
        error=np.array([abs(float(r['prediction'])-float(r['rho'])) for r in matched])
        assert len(matched)==84 and abs(float(error.mean())-float(row['mae']))<1e-12
        assert all(abs(float(r['absolute_error'])-e)<1e-12 for r,e in zip(matched,error))
        validations.append({'method':row['method'],'view':row['view'],'prediction_rows':len(matched),'recomputed_mae':float(error.mean()),'status':'pass'})
    supplemental=[]
    aux=read(ROOT/'results/predictions/simulation_followup_v1/stress_control_predictions.csv')
    new=read(ROOT/'results/predictions/simulation_followup_v1/unseen_rho_predictions.csv')
    for label,rows,first,second in [('in-grid joint minus volume', [r for r in aux if float(r['lambda_multiplier'])==1], 'Return + volume','Volume-only control'),('unseen joint minus return',new,'Return + volume','Return only'),('unseen joint minus volume',new,'Return + volume','Volume-only control')]:
        a={r['window_id']:r for r in rows if r['view']==first};b={r['window_id']:r for r in rows if r['view']==second};ids=sorted(a)
        difference=np.array([float(a[i]['absolute_error'])-float(b[i]['absolute_error']) for i in ids])
        groups=np.array(['_'.join(i.split('_')[:-1]) for i in ids])
        boot=stratified_bootstrap_mean(difference,groups,np.random.default_rng(52532500),4999)
        lo,hi=interval(boot)
        supplemental.append({'contrast':label,'mean_difference':float(difference.mean()),'ci_low':lo,'ci_high':hi,'base_windows':len(ids),'status':'supplementary descriptive interval; no new primary p-value'})
    def metric(method,view):return next(r for r in metrics if r['method']==method and r['view']==view)
    primary=next(r for r in contrasts if r['method']=='RBF')
    def table(rows,fields):
        header='| '+' | '.join(label for _,label in fields)+' |\n| '+' | '.join('---' for _ in fields)+' |\n'
        return header+'\n'.join('| '+' | '.join(str(r[key]) for key,_ in fields)+' |' for r in rows)+'\n'
    exact=[]
    for row in metrics:
        exact.append({'method':row['method'],'view':row['view'],'mae':f"{float(row['mae']):.6f}",'sd':f"{float(row['loss_sd']):.6f}",'ci':f"[{float(row['ci_low']):.6f}, {float(row['ci_high']):.6f}]"})
    metric_table=table(exact,[('method','方法'),('view','输入'),('mae','测试 MAE'),('sd','窗口损失 SD'),('ci','条件 95% CI')])
    supplemental_table=table([{'contrast':r['contrast'],'difference':f"{r['mean_difference']:.6f}",'ci':f"[{r['ci_low']:.6f}, {r['ci_high']:.6f}]",'n':r['base_windows']} for r in supplemental],[('contrast','补充比较'),('difference','平均损失差'),('ci','条件 95% CI'),('n','独立基础窗口')])
    phase=read(source/'phase_summary.csv');peaks=[]
    for n in [128,256,512]:
        row=max([r for r in phase if int(r['n'])==n],key=lambda r:float(r['finite_chi_mean']))
        peaks.append({'n':n,'sampled_peak_rho':float(row['rho'])})
    (output/'analysis-report.md').write_text(f'''# 模拟研究分析：已完成计算，待成员科学复核

**核心观察：在既定 ER 羊群模型、参数网格和一次训练划分中，加入成交量降低了收益特征的连接程度恢复误差；仅成交量参照也已很强。价格尺度漂移造成的是当前拟合器的失效，不能据此声称信息在数学上不可识别。**

## 范围与实际工作

- 物理扫描：N=128／256／512，9 个 rho，每格 40 个独立图，共 1,080 个网络。
- 分布与尺度：5 个条件各 8,192 个独立模拟区间，共 40,960；时间聚合用非重叠区间。
- 主逆问题：420 个独立窗口，每窗 256 区间；252 训练、84 验证、84 测试；a 在三个值之间变化但不作为输入，lambda=0.02 固定。
- 补充插值：6 个训练未见 rho 值、3 个 a、每格 4 窗，共 72 个新独立窗口；原模型不重新调参。
- F03／F04／F05／F06／F10／F11 已生成 PNG／SVG／PDF。没有真实行情或量子结果；不是完整项目已验收。

## 1. 主比较：同样窗口，收益 vs 收益＋量

{metric_table}
主要指标越低越好，单位为 rho。SD 描述测试窗口损失差异，不是重训 SD。CI 条件于当前拟合器和固定参数网格，采用 4,999 次按 rho／a 分层的独立窗口 bootstrap；不含换训练集的不确定性。

预设主方法 RBF：MAE 从 {float(metric('RBF','Return only')['mae']):.6f} 到 {float(metric('RBF','Return + volume')['mae']):.6f}，相对下降 {float(primary['relative_mae_reduction_percent']):.2f}%。配对损失差（joint − return）为 {float(primary['difference_joint_minus_return']):.6f}，条件区间 [{float(primary['ci_low']):.6f}, {float(primary['ci_high']):.6f}]。三项同方法输入对比的 Holm 调整后近似 bootstrap p={float(primary['p_holm']):.4g}。这是一次有限模拟实验，不是市场预测优势。

![F10](figures/F10.png)

## 2. 重要对照：成交量本身已经很有信息

主结果后明确追加的 volume-only RBF 在原网格 MAE 为 {float(next(r for r in stress if r['view']=='Volume-only control')['mae']):.6f}；joint 与它的差区间包含零。因此不能写“量价组合显著优于所有单一观察”。这个接口固定了人数与单位订单，成交量均值／波动能约束活动和群体结构，结果与模型关系相容。

{supplemental_table}
补充对照是事后诊断，不冒充最初预设主比较；区间仅作条件性分析，不新增一组显著性赢家主张。

## 3. 未见 rho 的插值与价格尺度压力

在训练未见的 rho=0.5／0.7／0.9／1.1／1.3／1.5 上，冻结 RBF 的收益／joint MAE 分别为 {float(next(r for r in interpolation if r['view']=='Return only')['mae']):.6f}／{float(next(r for r in interpolation if r['view']=='Return + volume')['mae']):.6f}。这是训练范围内插值，a 的取值与模型机制仍已见，不能推广为任意网络或市场机制识别。

lambda 从训练的 0.02 改为 0.01／0.04 后，joint MAE 为 0.149826／0.242402，高于原条件 0.025593。只看量的对照不依赖 lambda，误差保持 0.023433。这说明混合特征拟合器没有自动取得尺度稳健性；当前观测仍可能含有足够信息，不是不可识别证明。

![F11](figures/F11.png)

## 4. 物理机制：有限规模过渡与尾部边界

最大群体比例随 rho 增加，有限群体统计在临界附近出现峰；三个 N 的采样网格峰分别为 {', '.join('N='+str(r['n'])+' -> rho='+str(r['sampled_peak_rho']) for r in peaks)}。网格较粗且 CI 重叠，不能将这些位置称为精确阈值估计。

![F03](figures/F03.png)

收益是离散的绝对净订单单位，m 最大为 128。预设范围 m=4...128 的简单有限支持幂律，在三个 rho 条件下均被 parametric-bootstrap KS 检查拒绝：原始 p=0.005（199 次 bootstrap 的分辨率下限），三项 Holm 后 p=0.015。rho=1.4 时幂律的 AIC 比指数低，但仍未通过拟合优度；相对更好不等于绝对充分。不能声称“所有范围都不可能有幂律”，也不能声称完成了真实市场尾部验证。

![F05](figures/F05.png)

F04 展示有限群体密度，F06 分开比较人数与时间聚合后的标准化形状。没有拟合临界指数或证明普适标度；曲线外观相近不足以完成这些主张。

## Claim Candidates

- Claim: 成交量改善收益特征的恢复。
  - Source evidence: learning_metrics.csv、view_contrasts.csv、test_predictions.csv；F10。
  - Allowed wording: 在此固定模型／网格／一次训练划分下，RBF joint 相对 return-only MAE 下降约 37%。
  - Forbidden stronger wording: 对真实市场或所有机制普遍有效；joint 必然优于 volume-only。
  - Uncertainty: 条件窗口 bootstrap，不含重训；主测试 84 窗。
  - Next check: 成员复跑与额外独立训练重复。
  - Decision: keep, scoped.
- Claim: 价格尺度漂移会破坏当前拟合器。
  - Source evidence: stress_control_metrics.csv；F11。
  - Allowed wording: 冻结 joint RBF 对 lambda 漂移敏感，volume-only 诊断在该变换下不变。
  - Forbidden stronger wording: 观测数学上不可识别；真实市场无法推断。
  - Uncertainty: 同 84 个基础测试窗的重复条件，不是 252 个独立窗。
  - Next check: 成员复核后决定是否研究显式尺度稳健的估计器。
  - Decision: keep, scoped.
- Claim: 选定范围的简单幂律不充分。
  - Source evidence: tail_diagnostics.csv、tail_probabilities.csv；F05。
  - Allowed wording: 在有限 N、指定阈值和分布族下，拟合优度未支持该幂律。
  - Forbidden stronger wording: 羊群不能产生幂律；所有阈值都被排除；指数已充分解释全部收益。
  - Uncertainty: 固定 xmin；有限支持；Monte Carlo 分辨率有限。
  - Next check: 真实尾部和独立声明的范围敏感性分析由接续成员处理。
  - Decision: keep, scoped.

## 下一位成员仍需完成

真实行情的完整获取与质量、F08 真实量价、真实尾部与尺度对照；独立复跑和科学复核；三份讲解 notebook、最终 GitHub 与 CD 的展示整合。成员复核仍为 not_run。当前所有数字均来自模拟，不得写成市场实证。
''')
    statrows=[{'method':r['method'],'delta':f"{float(r['difference_joint_minus_return']):.6f}",'ci':f"[{float(r['ci_low']):.6f}, {float(r['ci_high']):.6f}]",'effect':f"{float(r['paired_standardized_effect']):.4f}",'p':f"{float(r['bootstrap_p_approx']):.4g}",'holm':f"{float(r['p_holm']):.4g}"} for r in contrasts]
    tailrows=[{'rho':r['rho'],'n':r['tail_count'],'alpha':f"{float(r['power_exponent']):.4f}",'ci':f"[{float(r['exponent_ci_low']):.4f}, {float(r['exponent_ci_high']):.4f}]",'ks':f"{float(r['power_ks']):.4f}",'p':r['power_gof_p_holm'],'delta':f"{float(r['delta_aic_exp_minus_power']):.2f}"} for r in tails]
    (output/'stats-appendix.md').write_text('''# 统计口径与可核对数字

## 单位、依赖与不确定性

主比较以独立母种子窗口为单位，同窗两种输入配对。每个 rho／a 格固定 12／4／4 训练／验证／测试。预处理只拟合训练集；目标减均值也只用训练目标，RBF 在原目标尺度加回训练均值。所有调参只用验证损失，不裁剪预测，不在测试结果后重选主特征或主方法。

一次训练划分意味着所有 MAE CI 条件于该拟合器；84 窗不是 84 次训练。采用预先选择的非参数分层 bootstrap，无须以正态性“未拒绝”决定切换检验；不能将未拒绝当作接受正态。每格只有 4 测试窗，有限样本区间覆盖与重训稳健性仍有限。

配对均值差的近似双侧 p 由中心化分层 bootstrap 分布估计；不是精确置换检验。效应量为平均配对损失差除以其样本 SD，仅描述当前窗口损失。Holm 家族为 Dummy／Ridge／RBF 三个同方法输入对比；学习曲线与补充对照不额外声称显著性。

''' + table(statrows,[('method','方法'),('delta','joint − return'),('ci','95% 条件 CI'),('effect','配对标准化效应'),('p','近似 bootstrap p'),('holm','Holm p')]) + '''
## 尾部：先声明支持与范围

绝对净订单 m 是 0...128 的整数。固定 xmin=4，条件于 4...128，拟合归一化 p(m) ∝ m^(-alpha)，alpha∈[0,8]；指数候选 p(m) ∝ exp(-rate*m)，rate∈[0,2]。均用精确有限求和与极大似然，两者各 1 参数，AIC 同样本同范围。199 次参数 bootstrap 生成候选分布并重新拟合，计算离散 CDF 最大差；幂律参数 CI 用条件尾部样本的非参数 bootstrap。拟合不通过时 alpha 仅是指定拟合的参数估计，不是已确认的普适临界指数。

''' + table(tailrows,[('rho','rho'),('n','尾部样本'),('alpha','幂律参数'),('ci','参数区间'),('ks','KS'),('p','GOF Holm p'),('delta','AIC(exp) − AIC(power)')]) + '''
KS bootstrap p 的最小分辨率是 1/200；不能把这些值写成精确的更小 p。AIC 为相对比较，未对指数分布做充分性结论。范围未做系统敏感性研究。

尾部检验采用离散、MLE、拟合优度和替代分布的基本方法原则，参考 [Clauset–Shalizi–Newman](https://arxiv.org/html/0706.1062v2)；本组有限支持和固定阈值是明确改写，不是声称复现其全部算法。训练器与填补行为分别核对 [KernelRidge 官方说明](https://scikit-learn.org/stable/modules/generated/sklearn.kernel_ridge.KernelRidge.html)和 [SimpleImputer 官方说明](https://scikit-learn.org/stable/modules/generated/sklearn.impute.SimpleImputer.html)。

## 网络与尺度

每格 40 个独立图。M2 全体和有限群体统计分开；有限统计排除一个最大分量，无剩余时记缺失，不记零。图内所有群体不是独立重复，F04 的 CI 以整图重采样。所有图的 CI 为点态，非同时置信带。

时间聚合非重叠，8192 可被 1／4／16／64 整除，无丢弃尾段。先将收益核对并恢复为整数净订单，精确求和再映射为 log 收益，防止抵消产生浮点近零伪影。F06 仅描述形状与方差比例，未作普适指数检验。

## 补充控制

volume-only 和未见 rho 测试是在主结果后明确追加，先锁定新的诊断配置再生成。原主比较保持不变，补充测试不用于重新选择原模型。lambda 压力条件共用同 84 个基础窗口；统计按基础窗口分层，不能把三个尺度当独立样本。插值有 72 个新独立窗口，仅在原 rho 范围内、既有 a 与机制条件下评价。

''' + supplemental_table + '''
## 证据状态

源表、预测、配置、种子、划分、源码哈希与命令已经保存；自动检查与人类科学复核分别记录。真实数据、量子、订单簿、动态适应、独立重训均没有在本轮完成。
''')
    descriptions={
      'F03':('连接与有限规模过渡','最大群体占比增大，有限群体统计在临界附近有峰；精确位置未估计。','每格 40 图，点态 95% graph-bootstrap；虚线为无限规模参考。'),
      'F04':('群体分布','比较相同 N 下排除最大群体后的密度；长尾外观不等于收益幂律。','N=512；每条件40图；按每节点群体数；log零计数与零下界带不绘但源表保留。'),
      'F05':('收益尾部充分性','指定有限幂律均未通过 GOF；不能只读双对数外观。','各8192期；离散 m=4...128；虚点线为条件拟合；替代分布与检验见表。'),
      'F06':('人数和采样尺度','分开看 N 与非重叠聚合的形状变化；曲线接近不证明普适标度。','各8192期；样本SD／sqrt(k)标准化；重复聚合有依赖；整数求和避免近零残差。'),
      'F10':('成交量增益','同方法同测试窗比较；RBF joint 比 return-only MAE低约37%，非所有输入组合的赢家证明。','252训练/84验证/84测试；曲线训练预算63/126/252；条件分层bootstrap95%CI。'),
      'F11':('拟合器边界','lambda漂移使混合模型失效，volume-only控制不变；不能推出结构不可识别。','84基础测试窗；volume-only事后追加；分组图每格4窗，均值描述、SD在源表。')}
    catalog=['# 图目录与讲解检查\n\n所有图为 SIMULATION，PNG 预览、SVG/PDF 矢量，科学成员复核 not_run。\n']
    for fid,(purpose,observation,caption) in descriptions.items():
        catalog.append(f'## {fid}：{purpose}\n\n- Purpose：{purpose}。\n- Observation：{observation}\n- Implication：按上述范围解释，不能推广为市场机制识别或幂律证明。\n- Caption requirements：{caption}\n- Interpretation check：说明单位、重复单位和条件；将观察、推断与边界分开。\n\n![{fid}](figures/{fid}.png)\n')
        (ROOT/f'figures/captions/{fid}_simulation.md').write_text(f'# {fid} | {purpose}\n\n状态：ready_for_review；证据：SIMULATION。\n\n{observation}\n\n{caption}\n\n源表由 results/checks/simulation_study_v1/figure_qa/simulation_study_v2/render_record.json 登记；输出 figures/simulation_study_v2/{fid}.png／.svg／.pdf。科学成员复核：not_run。\n')
    (output/'figure-catalog.md').write_text('\n'.join(catalog))
    link=output/'figures'
    if not link.exists():link.symlink_to(os.path.relpath(ROOT/'figures/simulation_study_v2',output),target_is_directory=True)
    summary={'scope':'simulation only; ready for member review','primary_model':'RBF','main_test_windows':84,'training_splits':1,'main':{r['view']:float(r['mae']) for r in metrics if r['method']=='RBF'},
             'view_contrasts':contrasts,'supplementary_interpolation':interpolation,'supplementary_paired_differences':supplemental,
             'phase_graphs':1080,'series_periods':40960,'learning_windows':420,'unseen_rho_windows':72,'figures':list(descriptions),'latest_figure_set':'figures/simulation_study_v2','member_review':'not_run'}
    (output/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    record={'status':'pass','primary_metric_recomputations':validations,'supplementary_intervals':supplemental,
            'analysis_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'member_scientific_review':'not_run'}
    (ROOT/'results/checks/simulation_study_v1/analysis_validation.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
    print(str(output.relative_to(ROOT)))


if __name__=='__main__':main()
