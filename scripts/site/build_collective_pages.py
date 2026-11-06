"""Integrate the accepted study into existing pages without rebuilding prior content."""

from pathlib import Path as _ProjectPath
import sys as _project_sys
_project_sys.path.insert(0, str(_ProjectPath(__file__).resolve().parents[1]))
from _bootstrap import ROOT as PROJECT_ROOT, script_path, resolve_recorded_path
from pathlib import Path
import json,re,shutil

ROOT=PROJECT_ROOT;WEB=ROOT/'web';STUDY=ROOT/'studies/collective_dynamics_v1'

def b(en,zh):return f'<span data-en>{en}</span><span data-zh hidden>{zh}</span>'
def p(en,zh):return '<p>'+b(en,zh)+'</p>'
def insert(path,id,section,marker):
    s=path.read_text();pattern=r'<section\b[^>]*\bid="'+re.escape(id)+r'"[^>]*>.*?</section>'
    if re.search(pattern,s,flags=re.S):s=re.sub(pattern,lambda m:section,s,count=1,flags=re.S)
    else:
        assert marker in s
        s=s.replace(marker,section+marker,1)
    path.write_text(s)

def main():
    summary=json.loads((STUDY/'website-summary.json').read_text());scores=summary['primary_scores']
    for name in ['I01_information_budget.svg','I02_paired_controls.svg']:shutil.copy2(STUDY/'figures'/name,WEB/'assets/figures'/name)
    shutil.copy2(STUDY/'website-summary.json',WEB/'assets/data/collective-information-v1.json')
    section='<section class="section wrap collective-extension" id="information-efficiency"><div class="section-title"><h2>'+b('How much history does the risk estimate need?','风险估计需要多少历史信息？')+'</h2>'+p('A compact collective-pressure model is tested under four complete data budgets. Each forecast resets all calibration inside the same past window, with zero microscopic labels.','紧凑的群体方向压力模型在四种完整历史预算下接受检验。每次预测的全部校准均限制在同一过去窗口内，不使用逐笔大小标签。')+'</div>'
    section+='<figure class="collective-figure"><a href="assets/figures/I01_information_budget.svg" target="_blank"><img loading="lazy" src="assets/figures/I01_information_budget.svg" alt="Primary QLIKE under 30, 60, 120 and 240-day data budgets"></a><figcaption>'+b('183 historical target days, April–September 2026. Points are mean QLIKE; whiskers are individual 95% seven-day block intervals. Lower is better.','2026年4—9月的183个历史目标日。点表示平均QLIKE，误差线为单项95%七日分块区间；数值越低越好。')+'</figcaption></figure>'
    section+='<div class="study-table-wrap"><table class="study-table"><thead><tr><th>'+b('Past days','过去天数')+'</th><th>'+b('Return HAR','收益HAR')+'</th><th>'+b('Macro statistics','宏观统计模型')+'</th><th>'+b('Pressure AR','方向压力AR')+'</th><th>'+b('Mechanism','机理模型')+'</th></tr></thead><tbody>'
    for budget in [30,60,120,240]:
        section+=f'<tr><td>{budget}</td>'
        for model in ['ReturnHAR','MacroStat','PressureAR','MechanismSelected']:
            value=next(x['mean'] for x in scores if x['budget_days']==budget and x['model']==model and x['metric']=='qlike');section+=f'<td>{value:.6f}</td>'
        section+='</tr>'
    section+='</tbody></table></div>'
    section+=p('The selected mechanism has higher point loss than return HAR and the macro statistical model at every tested budget. At 240 days it scores 0.260805, almost the same as the equally informed pressure AR control at 0.260792. An information-efficiency or mechanism-specific prediction advantage is not established.','所选机理模型在四种预算下的点损失均高于收益HAR和宏观统计模型。240天预算下，其QLIKE为0.260805，与同信息、同风险映射的方向压力AR对照0.260792几乎相同。本轮未建立信息效率或机理约束特有的预测优势。')
    section+=p('The pressure controls use r, V and F; return HAR uses r only, while the macro model also uses K. Calibration and warm-up stay inside the declared budget. These dates were examined in previous research rounds; the comparison is historical development. The reduced pressure closure tests a hypothesis inspired by coupled dynamics, rather than recovering the network shown in the trading simulator.','方向压力模型使用r、V、F；收益HAR只使用r，宏观统计模型还使用K。校准和预热均计入声明的预算。这些日期已在前期研究中观察过，本次属于历史开发检验。低维方向压力近似检验的是耦合动力学启发的假设，并不意味着交易模拟器中的网络已由真实市场数据恢复或验证。')
    section+='<details><summary>'+b('Inspect paired controls and uncertainty','查看配对对照与不确定性')+'</summary><figure class="collective-figure"><img loading="lazy" src="assets/figures/I02_paired_controls.svg" alt="Mechanism versus matched macro and unconstrained pressure controls"><figcaption>'+b('Paired seven-day block intervals use the basic bootstrap inversion, consistent with the centred tests. Complete tables also retain labelled percentile diagnostics and Holm adjustment across twelve primary contrasts.','配对七日分块区间采用与居中检验一致的basic bootstrap反演。完整表格另保留明确标注的percentile诊断区间，并对十二项主要比较作Holm校正。')+'</figcaption></figure></details>'
    section+='<p class="study-source">'+b('Source: frozen collective-dynamics information-budget study; protocol and all model variants retained.','来源：已冻结的群体动力学信息预算研究，保留协议及全部模型变体。')+'</p><div class="collective-links"><a href="https://github.com/SAFuDarren/econophysics-risk-lab/blob/main/studies/collective_dynamics_v1/README.md">'+b('Full study and reproduction','完整研究与复现')+'</a><a href="methods.html#collective-dynamics">'+b('Mathematical connection','数学衔接')+'</a><a href="trading.html?source=model">'+b('Explore the synthetic market','体验虚拟市场')+'</a></div></section>'
    insert(WEB/'findings.html','information-efficiency',section,'<section class="closing">')
    sec='<section class="section reading" id="collective-reproduction"><h2>'+b('Reproduce collective dynamics and the trading lab','复现群体动力学与交易实验')+'</h2>'+p('The browser and Node tests use the same synthetic-market and virtual-account modules. Controlled simulations retain 32 seeds, all four scenarios, both modes and declared ablations. The information-budget study rebuilds eight numerical tables from its attributed derived market panel.','浏览器与Node检查使用同一套虚拟市场及账户模块。受控模拟保留32个种子、四类场景、两种模式及声明的机制去除对照。信息预算研究从附有来源的市场衍生数据重建八张数值表。')+'<pre><code>node tests/test_trading_engine.cjs\nnode tests/test_trading_account.cjs\nnode scripts/research/reproduce_collective_trading_engine.cjs\npython studies/collective_dynamics_v1/reproduce.py</code></pre><div class="collective-links"><a href="https://github.com/SAFuDarren/econophysics-risk-lab/blob/main/docs/COLLECTIVE_TRADING_VALIDATION_v1.md">'+b('Acceptance evidence','验收记录')+'</a><a href="trading.html">'+b('Open trading lab','打开交易实验')+'</a></div></section>'
    insert(WEB/'reproduce.html','collective-reproduction',sec,'<section class="section reading" id="sources">')
    print('Collective study pages built from accepted source data.')

if __name__=='__main__':main()
