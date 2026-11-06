#!/usr/bin/env python3
"""Covariance-controlled figures: synthetic mechanisms and external market tests.

Slide/report canvas 10.5 inches wide; not a journal-size submission claim.
"""

from pathlib import Path as _ProjectPath
import sys as _project_sys
_project_sys.path.insert(0, str(_ProjectPath(__file__).resolve().parents[1]))
from _bootstrap import ROOT as PROJECT_ROOT, script_path, resolve_recorded_path
from pathlib import Path
import csv,datetime as dt,json,os,sys
ROOT=PROJECT_ROOT;os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.cache/matplotlib'));sys.path.insert(0,str(ROOT/'scripts/figure_audit'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from audit_panel_alignment import require_matplotlib_panel_alignment

BLUE='#24647D';TEAL='#3D8274';GOLD='#B18A42';GRAY='#8E9CA5';INK='#263D49';RED='#9C515E'

def read(name):return list(csv.DictReader((ROOT/f'results/tables/tail_increment_v1/{name}.csv').open()))
def f(row,key):return float(row[key])
def date(value):return dt.datetime.fromisoformat(value)

def main():
    out=ROOT/'figures/tail_increment_v1';qa=ROOT/'results/checks/tail_increment_v1/figure_qa';out.mkdir(parents=True,exist_ok=True);qa.mkdir(parents=True,exist_ok=True);registry=[]
    plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['DejaVu Sans'],'font.size':9.5,'axes.titlesize':11,'axes.labelsize':10,'xtick.labelsize':9,'ytick.labelsize':9,'legend.fontsize':9,'axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.7,'pdf.fonttype':42,'svg.fonttype':'none'})
    def base(title,height=5.8,left=.10,right=.96,wspace=.46,bottom=.20,top=.80):
        fig,axes=plt.subplots(1,2,figsize=(10.5,height));fig.subplots_adjust(left=left,right=right,top=top,bottom=bottom,wspace=wspace);fig.suptitle(title,x=.5,y=.97,fontsize=14,fontweight='semibold')
        for ax,letter in zip(axes,'ab'):ax.annotate(letter,(0,1),xycoords='axes fraction',xytext=(-22,16),textcoords='offset points',fontsize=12,fontweight='bold');ax.grid(axis='x',color='#E6ECEF',linewidth=.7);ax.set_axisbelow(True)
        return fig,axes
    def foot(fig,text):fig.text(.10,.035,text,fontsize=8.8,va='bottom',linespacing=1.6,color=INK)
    def save(fig,identifier,sources,interpretation,notes):
        fig.canvas.draw();require_matplotlib_panel_alignment(fig,json_out=str(qa/f'{identifier}.alignment.json'),strict=True,tolerance_pt=1.5,gutter_tolerance_pt=1.5,require_panel_labels=True)
        fig.savefig(out/f'{identifier}.pdf');fig.savefig(out/f'{identifier}.svg');fig.savefig(out/f'{identifier}.png',dpi=300);plt.close(fig)
        registry.append({'id':identifier,'sources':[f'results/tables/tail_increment_v1/{s}.csv' for s in sources],'interpretation':interpretation,'notes':notes,'formats':['pdf','svg','png'],'canvas_width_in':10.5})
    def error(ax,row,y,color,marker='o'):
        mid,lo,hi=[f(row,k) for k in ['improvement_pct','ci_low','ci_high']];assert lo<=mid<=hi
        ax.errorbar(mid,y,xerr=[[mid-lo],[hi-mid]],fmt=marker,color=color,ecolor=color,capsize=3,markersize=5.5,lw=1.4)
    truth_names={'Gaussian':'Gaussian','StudentT-5':'Student-t (5)','FactorMixture-p0.05-ratio6-k0.75':'Volatility mixture','Herding-rho0.6-q0.05-k0.75':'Herding ρ = 0.6','Herding-rho1.0-q0.05-k0.75':'Herding ρ = 1.0','Herding-rho1.4-q0.05-k0.75':'Herding ρ = 1.4'}
    # T01: the variance control does not fix extreme loss severity.
    ccdf=read('synthetic_ccdf');truth=read('synthetic_truth');fig,ax=base('The same covariance can hide different tail risks',left=.10,wspace=.58)
    styles=[(INK,'-'),(GRAY,'--'),(TEAL,'-'),(BLUE,':'),(BLUE,'-'),(BLUE,'--')]
    for row,(color,style) in zip(truth,styles):
        points=[r for r in ccdf if r['truth']==row['truth'] and 1<=f(r,'loss_threshold_sigma')<=7 and 1e-4<=f(r,'exceedance_probability')<=.2];ax[0].semilogy([f(r,'loss_threshold_sigma') for r in points],[f(r,'exceedance_probability') for r in points],color=color,ls=style,lw=1.7,label=truth_names[row['truth']])
    ax[0].set(xlim=(1,7),ylim=(1e-4,.2),xlabel='Equal-weight loss / portfolio σ',ylabel='Probability of a larger loss',title='A shared covariance; six known data generators');handles,legend_labels=ax[0].get_legend_handles_labels();fig.legend(handles,legend_labels,loc='upper center',bbox_to_anchor=(.30,.935),ncol=2,frameon=False,fontsize=8.2)
    ys=np.arange(len(truth));ax[1].plot([-f(r,'q05') for r in truth],ys,'o',color=INK,label='95% VaR magnitude');ax[1].plot([-f(r,'es01') for r in truth],ys,'s',color=BLUE,label='99% expected shortfall')
    ax[1].set(yticks=ys,yticklabels=[truth_names[r['truth']] for r in truth],xlabel='Loss in portfolio σ units',title='Moderate quantiles and extreme losses differ',ylim=(5.5,-.5),xlim=(0,5.4));fig.legend(handles=[plt.Line2D([],[],marker='o',ls='none',color=INK,label='95% VaR'),plt.Line2D([],[],marker='s',ls='none',color=BLUE,label='99% expected shortfall')],loc='upper center',bbox_to_anchor=(.75,.91),ncol=2,frameon=False,fontsize=8.5)
    foot(fig,'MODEL-ONLY: 50,000 scenarios per truth; all six scenario covariances match numerically.\nMonte Carlo point estimates; CCDF display: 1–7σ, probability ≥ 0.0001. Full threshold grid is retained.')
    save(fig,'T01_same_covariance',['synthetic_ccdf','synthetic_truth'],'同协方差下尾部仍不同；波动混合也能产生类似极端尾部。','完整81阈值保留于源表；log轴不画零频率，不暗示尾部概率精确为零。')
    # T02: do not show only a herding-generated positive example.
    effects=read('synthetic_paired_effects');truth_order=list(truth_names);fig,ax=base('Known mechanisms: compare physics with statistical alternatives',left=.18,right=.97,wspace=.25)
    models=[('Herding',BLUE,-.20,'o'),('FactorMixture',TEAL,0,'s'),('FHS',GRAY,.20,'D')]
    for axis,metric,title in zip(ax,['pinball05','brier'],['5% tail quantile loss','Co-crash Brier loss']):
        for model,color,offset,marker in models:
            for j,name in enumerate(truth_order):
                row=next(r for r in effects if r['truth']==name and r['model']==model and r['metric']==metric);error(axis,row,j+offset,color,marker)
        axis.axvline(0,color=INK,lw=.8);axis.set(ylim=(5.6,-.6),yticks=range(6),xlabel='Loss reduction vs Gaussian (%)',title=title)
    ax[0].set_yticklabels([truth_names[t] for t in truth_order]);ax[1].set_yticklabels([])
    handles=[plt.Line2D([],[],color=c,marker=m,ls='none',label=n) for n,c,_,m in models];fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.57,.91),ncol=3,frameon=False)
    foot(fig,'MODEL-ONLY: 20 independent fits per truth, 504 observations per fit. Bars: paired 95% training-run bootstrap intervals.\nShared 50,000-scenario test laws condition these results. All nine methods, including Student-t controls, remain in the tables.')
    save(fig,'T02_synthetic_increment',['synthetic_paired_effects','synthetic_repetitions'],'正确生成模型并不自动带来相对通用重尾/经验法的大幅优势。','图展示3个指定代表方法，完整九方法均有源表；区间不是市场证据或测试库抽样区间。')
    # T03: quantitative real-data effects, with rare/absent events stated visibly.
    contrast=read('contrasts');fig,ax=base('External market test: no stable incremental tail-risk gain',left=.25,right=.97,wspace=.22,bottom=.24)
    groups=[('external','historical_test','New stocks · 2020–25'),('external','confirmation','New stocks · 2026'),('sector','historical_test','Sector ETFs · 2020–25'),('sector','confirmation','Sector ETFs · 2026')]
    for axis,metric,title in zip(ax,['pinball05','brier'],['5% tail loss vs Gaussian','Co-crash loss vs FHS']):
        for j,(panel,period,label) in enumerate(groups):
            row=next(r for r in contrast if r['panel']==panel and r['period']==period and r['model']=='Herding' and r['covariance']=='EWMA-126-0.94' and r['block_sessions']=='20' and r['metric']==metric)
            if metric=='brier' and int(row['co_events'])<3:
                note='0 events: false alarms only' if int(row['co_events'])==0 else '2 events: estimate unstable'
                axis.text(.04,j,note,transform=axis.get_yaxis_transform(),color=GRAY,fontsize=8.8,va='center')
            else:error(axis,row,j,BLUE if panel=='external' else GRAY,'o' if panel=='external' else '^')
        
        if metric=='brier':
            axis.grid(False);axis.vlines([0,0],[-.4,1.6],[.4,2.4],color=INK,lw=.8)
        else:axis.axvline(0,color=INK,lw=.8)
        axis.set(yticks=range(4),ylim=(3.6,-.6),xlabel='Herding loss reduction (%)',title=title)
    ax[0].set_yticklabels([x[2] for x in groups]);ax[1].set_yticklabels([]);ax[0].set_xlim(-5.5,2.5);ax[1].set_xlim(-3,3)
    foot(fig,'REAL DATA: 1,508 historical / 204 confirmation days per panel; 20-day paired-block, unadjusted 95% intervals.\nPrimary external historical tail gain +0.56%; Holm p = 0.077. External co-events: 32 historical, 0 in 2026.\nRare-event 2026 Brier ratios and full intervals remain in the source table; no crash-detection claim is available there.')
    save(fig,'T03_market_increment',['contrasts','metrics'],'外部历史增益很小且未通过主族校正，2026尾部反向；零事件不能验证抓暴跌。','旧行业分析为回顾性；未校正CI不替代Holm主检验。0/2事件段未画误导性大相对增益，完整值保留。')
    # T04: precision, covariance and equal-budget criticality restrictions.
    high=read('mc_full_contrasts');analytic=read('analytic_tail_contrasts');ablation=read('critical_ablation');fig,ax=base('Small historical gains do not establish a criticality advantage',left=.23,right=.97,wspace=.55)
    labels=['EWMA · 8,192 draws','EWMA · 16,384 draws','EWMA · integrated tail','Shrinkage · 8,192 draws']
    for period,color,offset in [('historical_test',BLUE,-.13),('confirmation',GOLD,.13)]:
        source=[next(r for r in contrast if r['panel']=='external' and r['period']==period and r['model']=='Herding' and r['covariance']=='EWMA-126-0.94' and r['block_sessions']=='20' and r['metric']=='pinball05'),next(r for r in high if r['period']==period and r['metric']=='pinball05'),next(r for r in analytic if r['panel']=='external' and r['period']==period and r['model']=='Herding' and r['baseline']=='Gaussian'),next(r for r in contrast if r['panel']=='external' and r['period']==period and r['model']=='Herding' and r['covariance']=='LedoitWolf-126' and r['block_sessions']=='20' and r['metric']=='pinball05')]
        for j,row in enumerate(source):error(ax[0],row,j+offset,color)
    ax[0].set(yticks=range(4),yticklabels=labels,ylim=(3.6,-.6),xlabel='Tail loss reduction vs Gaussian (%)',title='Sensitivity: external stocks')
    for j,(period,label) in enumerate([('historical_test','2020–25 · MC'),('historical_test','2020–25 · integrated'),('confirmation','2026 · MC'),('confirmation','2026 · integrated')]):
        if j%2==0:row=next(r for r in ablation if r['panel']=='external' and r['period']==period and r['metric']=='pinball05')
        else:row=next(r for r in analytic if r['panel']=='external' and r['period']==period and r['model']=='HerdingCritical')
        error(ax[1],row,j,BLUE if period=='historical_test' else GOLD)
    ax[1].set(yticks=range(4),yticklabels=['2020–25 · MC','2020–25 · integrated','2026 · MC','2026 · integrated'],ylim=(3.6,-.6),xlabel='Tail loss reduction: ρ = 1 vs ρ = 0.6 (%)',title='Same-budget criticality ablation')
    for axis in ax:axis.axvline(0,color=INK,lw=.8)
    fig.legend(handles=[plt.Line2D([],[],marker='o',ls='none',color=BLUE,label='2020–2025'),plt.Line2D([],[],marker='o',ls='none',color=GOLD,label='2026')],loc='upper center',bbox_to_anchor=(.60,.91),ncol=2,frameon=False)
    foot(fig,'REAL DATA / SENSITIVITY: same information and fitted laws; 20-day paired-block 95% intervals.\nNumerical audits do not replace the frozen primary test. Fitted ρ is a model-shape parameter, not observed market criticality.')
    save(fig,'T04_robustness_and_criticality',['contrasts','mc_full_contrasts','analytic_tail_contrasts','critical_ablation'],'控制协方差、积分误差及固定rho后，没有跨时段的临界性优势。','完整积分只针对标量组合尾部；图/动作有限库仍是数值近似，未新增市场信息。')
    # T05: visible probability paths; event-free confirmation cannot validate detection.
    daily=read('external_daily');fig,ax=base('What the co-crash forecasts looked like in real market data',left=.09,right=.97,wspace=.25,top=.73)
    for axis,lo,hi,title in [(ax[0],'2020-01-01','2021-01-01','2020: a known stress-year illustration'),(ax[1],'2026-01-01','2026-10-24','2026: no events under the frozen definition')]:
        subset={m:[r for r in daily if r['covariance']=='EWMA-126-0.94' and r['method']==m and lo<=r['date']<hi] for m in ['Herding','FHS']};events=[r for r in subset['Herding'] if int(r['co3'])];maxp=max(f(r,'p_co3') for rows in subset.values() for r in rows)*100
        for r in events:axis.axvline(date(r['date']),color=RED,alpha=.28,lw=.8)
        for m,color in [('FHS',GRAY),('Herding',BLUE)]:axis.plot([date(r['date']) for r in subset[m]],[100*f(r,'p_co3') for r in subset[m]],color=color,lw=1.3,label=m)
        axis.set(title=title+'\n'+f'{len(events)} event days / {len(subset["Herding"])} sessions',ylabel='Next-day co-crash probability (%)',ylim=(0,max(2,maxp*1.12)));axis.xaxis.set_major_locator(mdates.MonthLocator(interval=3));axis.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
    fig.legend(handles=[plt.Line2D([],[],color=BLUE,lw=1.5,label='Herding'),plt.Line2D([],[],color=GRAY,lw=1.5,label='FHS'),plt.Line2D([],[],color=RED,alpha=.6,lw=1,label='Realized event day')],loc='upper center',bbox_to_anchor=(.55,.91),ncol=3,frameon=False)
    foot(fig,'REAL DATA: at least 3/9 next-day returns below −2 forecast marginal standard deviations; identical covariance.\nVertical red rules mark realized events, not forecast probabilities. Full 2020–2025 data, not this illustration alone, determine scores.')
    save(fig,'T05_actual_probability_paths',['external_daily'],'真实逐日概率与事件对照，直观展示2026只能评价误报。','2020为预先已知危机示例，非从最佳表现区间择优；不以例图替代完整评分。')
    (out/'registry.json').write_text(json.dumps({'batch':'tail_increment_v1','backend':'Python/matplotlib','figures':registry},ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':'rendered_alignment_pass','figures':len(registry),'rendered_pdf_qa_pending':True},indent=2))

if __name__=='__main__':main()
