from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from audit_panel_alignment import require_matplotlib_panel_alignment

R=Path(__file__).resolve().parents[1];F=R/'figures'
NAVY='#234E70';TEAL='#267A74';ORANGE='#BA6A3C';GREY='#7B858F'
plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','DejaVu Sans'],'font.size':9,'axes.labelsize':9,'xtick.labelsize':9,'ytick.labelsize':9,'legend.fontsize':8.5,'legend.frameon':False,'axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.8,'pdf.fonttype':42,'svg.fonttype':'none'})

def save(fig,name,sources,caption):
    fig.canvas.draw();require_matplotlib_panel_alignment(fig,json_out=R/'checks'/f'{name}-alignment.json')
    fig.savefig(F/f'{name}.pdf',facecolor='white');fig.savefig(F/f'{name}.svg',facecolor='white');fig.savefig(F/f'{name}.png',dpi=600,facecolor='white')
    (F/f'{name}.source.json').write_text(json.dumps(dict(sources=sources,caption=caption),indent=2));plt.close(fig)

def budgets():
    a=pd.read_csv(R/'tables/scores.csv');a=a[(a.period=='primary')&(a.metric=='qlike')];fig,ax=plt.subplots(figsize=(7.2,4.6));fig.subplots_adjust(left=.13,right=.97,bottom=.24,top=.76)
    fig.text(.055,.96,'No accuracy/history advantage is established for the compact closure',fontsize=11.4,fontweight='bold',va='top');fig.text(.055,.895,'183 historical target days, April-September 2026; every calibration stays inside its stated budget',fontsize=8.4,color=GREY,va='top')
    for name,color,marker,label in [('MechanismSelected',ORANGE,'o','Selected mechanism'),('ReturnHAR',NAVY,'s','Return HAR (price only)'),('MacroStat',TEAL,'^','Macro statistical')]:
        g=a[a.model==name].sort_values('budget_days');x=np.arange(4);y=g['mean'].to_numpy();ax.errorbar(x,y,yerr=[y-g.ci_low.to_numpy(),g.ci_high.to_numpy()-y],fmt=marker+'-',color=color,ms=5,capsize=3,lw=1.3,label=label)
    ax.set(xticks=range(4),xticklabels=['30','60','120','240'],xlabel='Available past days (including every calibration)',ylabel='Mean next-day RV QLIKE');ax.legend(loc='lower left',bbox_to_anchor=(0,1.025),ncol=3,fontsize=8.1)
    fig.text(.13,.105,'Whiskers: 95% circular seven-day intervals for mean loss. Lower is better; intervals are not equivalence tests.',fontsize=8.1,color=GREY)
    fig.text(.13,.055,'Return HAR requires fewer input fields. All models use zero microscopic calibration labels and no extra warm-up.',fontsize=8.1,color=GREY)
    save(fig,'I01_information_budget',['tables/scores.csv','tables/input_budget.csv','fits/selection.json'],'All four historical data budgets with zero microscopic calibration. The selected reduced mechanism has no accuracy/history-budget advantage over retained statistical references.')

def paired():
    a=pd.read_csv(R/'tables/contrasts.csv');a=a[(a.period=='primary')&(a.metric=='qlike')&(a.block_days==7)&(a.family=='primary_12')];fig,axes=plt.subplots(1,2,figsize=(7.2,4.5));fig.subplots_adjust(left=.13,right=.97,bottom=.25,top=.73,wspace=.38)
    fig.text(.055,.96,'The restriction adds no benefit over the same-map pressure control',fontsize=11.4,fontweight='bold',va='top');fig.text(.055,.89,'Paired relative loss reduction; the full primary family contains 12 budget/control contrasts',fontsize=8.4,color=GREY,va='top')
    for ax,reference,title,letter in zip(axes,['PressureAR','DirectFlow'],['Unconstrained pressure AR','Direct flow response'],['a','b']):
        g=a[a.reference==reference].sort_values('budget_days');x=g.improvement_pct.to_numpy();y=np.arange(4);ax.errorbar(x,y,xerr=[x-g.basic_pct_ci_low.to_numpy(),g.basic_pct_ci_high.to_numpy()-x],fmt='o',color=ORANGE,capsize=3,ms=5);ax.axvline(0,color=GREY,ls=':',lw=1);ax.set(yticks=range(4),yticklabels=['30','60','120','240'],ylabel='Past-day budget',xlabel='Relative QLIKE reduction (%)',title=title);ax.invert_yaxis();ax.text(-.18,1.08,letter,transform=ax.transAxes,fontweight='bold',fontsize=10)
    fig.text(.08,.105,'Whiskers: individual 95% basic paired block intervals, scaled by reference mean. Holm tests remain in the tables.',fontsize=8.1,color=GREY)
    fig.text(.08,.055,'A better point score against direct flow does not establish a benefit from the nonlinear, sign-constrained mechanism.',fontsize=8.1,color=GREY)
    save(fig,'I02_paired_controls',['tables/contrasts.csv'],'All four budgets versus same-map unrestricted pressure and direct-flow controls. Basic95% additive intervals are scaled by the fixed observed reference mean; the12-comparison Holm family remains distinct.')

if __name__=='__main__':budgets();paired()
