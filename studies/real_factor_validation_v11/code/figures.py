"""Two transparent figures of the frozen historical real-factor experiment."""
from pathlib import Path
import os, sys
import numpy as np
import pandas as pd
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
try:
    from audit_panel_alignment import require_matplotlib_panel_alignment
except ImportError:
    def require_matplotlib_panel_alignment(*args, **kwargs):
        import warnings
        warnings.warn('Optional panel-alignment auditor unavailable; exporting figures without rerunning that QA.')

R = Path(__file__).resolve().parents[1]
F = R/'figures'
F.mkdir(exist_ok=True)
mpl.rcParams.update({'font.family':'Arial','font.size':8,'axes.labelsize':8,
 'axes.titlesize':8,'xtick.labelsize':7,'ytick.labelsize':7,'legend.fontsize':7,
 'pdf.fonttype':42,'svg.fonttype':'none','axes.spines.top':False,
 'axes.spines.right':False,'axes.linewidth':.65,'lines.linewidth':1.2,
 'xtick.major.width':.6,'ytick.major.width':.6,'savefig.dpi':300})
navy='#164A63';teal='#167D8D';orange='#B66B24';gray='#6F7880';light='#D8DEE3'
pred = pd.read_csv(R/'tables/predictions_scored.csv')
ev = pred[pred.role=='evaluation'].copy()
ev['date'] = pd.to_datetime(ev.future_month)
contr = pd.read_csv(R/'tables/primary_contrasts.csv')
scores = pd.read_csv(R/'tables/forecast_scores.csv')
alloc = pd.read_csv(R/'tables/computed_allocations.csv')
alloc = alloc[alloc.future_month.isin(ev.future_month)].copy()
alloc['date'] = pd.to_datetime(alloc.future_month)

def letter(ax,s):
    ax.annotate(s,xy=(0,1),xycoords='axes fraction',xytext=(-31,14),
                textcoords='offset points',ha='left',va='bottom',fontsize=9,fontweight='bold')

def timeaxis(ax):
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.set_xlim(ev.date.iloc[0],ev.date.iloc[-1])
    ax.grid(axis='y',color=light,lw=.45)
    ax.set_axisbelow(True)

def finish(fig,name):
    fig.canvas.draw()
    require_matplotlib_panel_alignment(fig,json_out=str(F/(name+'.alignment.json')),
          overlay_svg=str(F/(name+'.alignment.svg')),tolerance_pt=1.5,
          gutter_tolerance_pt=1.5,require_panel_labels=True,strict=True)
    fig.savefig(F/(name+'.pdf'))
    fig.savefig(F/(name+'.svg'))
    fig.savefig(F/(name+'.png'),dpi=300)
    plt.close(fig)

fig,ax = plt.subplots(2,2,figsize=(183/25.4,145/25.4))
fig.subplots_adjust(left=.14,right=.98,bottom=.14,top=.91,wspace=.55,hspace=.72)
a,b,c,d = ax.ravel()
for z,k in zip(ax.ravel(),'abcd'):letter(z,k)
a.plot(ev.date,ev.effective_corr_modes,color=navy)
a.axhline(6,color=gray,ls='--',lw=.9)
a.set_ylim(1,6.5);a.set_yticks([2,3,4,5,6])
a.set_ylabel('Effective correlation modes')
a.set_title('Six factors, fewer return modes',pad=13,loc='left')
timeaxis(a)
b.plot(ev.date,ev.full_over_diagonal,color=teal)
b.axhline(1,color=gray,ls='--',lw=.9)
b.set_ylim(0,2.6);b.set_yticks([0,.5,1,1.5,2,2.5])
b.set_ylabel('Full / diagonal second moment')
b.set_title('Covariance can amplify or hedge',pad=13,loc='left')
timeaxis(b)
order=['HAR-Portfolio','FullCov','Diagonal','HAR-All']
q=scores.set_index('model').loc[order,'QLIKE'].to_numpy()
c.scatter(q,np.arange(4),s=26,c=[gray,navy,gray,gray],zorder=3)
for yy,xx in enumerate(q):
    c.text(.59,yy,f'{xx:.3f}',ha='right',va='center',fontsize=7)
c.set_yticks(np.arange(4),order);c.invert_yaxis();c.set_ylim(3.6,-.6)
c.set_xlim(0,.63);c.set_xticks([0,.2,.4])
c.set_xlabel('Mean QLIKE (lower is better)')
c.set_title('Frozen evaluation forecasts',pad=13,loc='left')
c.grid(axis='x',color=light,lw=.45);c.set_axisbelow(True)
for block,offset,color,marker in [(3,-.10,navy,'o'),(6,.10,gray,'^')]:
    rows=contr[(contr.metric=='QLIKE')&(contr.block_months==block)]
    for i,(_,r) in enumerate(rows.iterrows()):
        d.errorbar(r.mean_difference,i+offset,
          xerr=np.array([[r.mean_difference-r.CI_low],[r.CI_high-r.mean_difference]]),
          color=color,fmt=marker,ms=4,capsize=2,lw=1,
          label=f'{block}-month blocks' if i==0 else None)
d.axvline(0,color=gray,ls='--',lw=.8)
d.set_yticks([0,1],['vs Diagonal','vs HAR-All']);d.invert_yaxis();d.set_ylim(1.6,-.6)
d.set_xlabel('Paired QLIKE: FullCov − reference')
d.set_title('Paired prediction differences',pad=13,loc='left')
d.set_xticks([-.4,-.2,0]);d.set_xlim(-.45,.12)
d.legend(loc='upper center',bbox_to_anchor=(.45,-.28),frameon=False,ncol=2,
          handletextpad=.4,columnspacing=1.1)
finish(fig,'RF1_signed_covariance_and_forecasts')

fig = plt.figure(figsize=(183/25.4,143/25.4))
gs = fig.add_gridspec(2,2,height_ratios=[1,1])
a=fig.add_subplot(gs[0,:]);b=fig.add_subplot(gs[1,0]);c=fig.add_subplot(gs[1,1])
fig.subplots_adjust(left=.125,right=.98,bottom=.15,top=.91,wspace=.57,hspace=.76)
for z,k in zip([a,b,c],'abc'):letter(z,k)
for mode,color,ls in [('Fixed',gray,'--'),('Performance',navy,'-'),('Permuted',orange,':')]:
    s=alloc[alloc['mode']==mode]
    a.plot(s.date,s.HHI,color=color,ls=ls,label=mode)
a.set_ylabel('Held coefficient HHI');a.set_ylim(.15,.39);a.set_yticks([.15,.2,.25,.3,.35])
a.set_title('Computed allocation on observed returns',pad=13,loc='left')
timeaxis(a)
a.legend(loc='upper right',bbox_to_anchor=(1,1.30),frameon=False,ncol=3,
         handlelength=2,columnspacing=1.4)
for ax,metric,mult,title,xlab in [
 (b,'held_HHI',1,'Concentration and return timing differ','Paired HHI: Performance − reference'),
 (c,'realized_risk',1e6,'Next-month risk increment is uncertain','Risk difference (units: $10^{-6}$)')]:
    for block,offset,color,marker in [(3,-.1,navy,'o'),(6,.1,gray,'^')]:
        rows=contr[(contr.metric==metric)&(contr.block_months==block)]
        for i,(_,r) in enumerate(rows.iterrows()):
            mean=r.mean_difference*mult;lo=r.CI_low*mult;hi=r.CI_high*mult
            ax.errorbar(mean,i+offset,xerr=np.array([[mean-lo],[hi-mean]]),
              color=color,fmt=marker,ms=4,capsize=2,lw=1,
              label=f'{block}-month blocks' if i==0 else None)
    ax.axvline(0,color=gray,ls='--',lw=.8)
    ax.set_yticks([0,1],['vs Fixed','vs Permuted']);ax.invert_yaxis();ax.set_ylim(1.6,-.6)
    ax.set_xlabel(xlab);ax.set_title(title,pad=13,loc='left')
b.set_xlim(-.057,.038);b.set_xticks([-.05,-.025,0,.025])
c.set_xlim(-6.2,9.8);c.set_xticks([-5,0,5])
c.legend(loc='upper center',bbox_to_anchor=(-.06,-.30),frameon=False,ncol=2,
          handletextpad=.4,columnspacing=1.1)
finish(fig,'RF2_allocation_and_next_month_risk')
print('Created two complete vector/PNG scientific figure bundles')
