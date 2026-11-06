#!/usr/bin/env python3
"""Traceable sector-risk and strategy-P&L figures, retaining negative results."""

from pathlib import Path as _ProjectPath
import sys as _project_sys
_project_sys.path.insert(0, str(_ProjectPath(__file__).resolve().parents[1]))
from _bootstrap import ROOT as PROJECT_ROOT, script_path, resolve_recorded_path
from pathlib import Path
import argparse,csv,datetime as dt,json,os,sys
ROOT=PROJECT_ROOT;os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.cache/matplotlib'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.colors import LogNorm

def read(name):return list(csv.DictReader((ROOT/f'results/tables/us_equity_v1/{name}.csv').open()))
def f(r,k):return float(r[k])
def date(x):return dt.datetime.fromisoformat(x)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--qa-tools',type=Path);args=parser.parse_args();require_matplotlib_panel_alignment=None
    if args.qa_tools:sys.path.insert(0,str(args.qa_tools));from audit_panel_alignment import require_matplotlib_panel_alignment
    out=ROOT/'figures/us_equity_v1';qa=ROOT/'results/checks/us_equity_v1/figure_qa';out.mkdir(parents=True,exist_ok=True);qa.mkdir(parents=True,exist_ok=True);sources=[]
    plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['DejaVu Sans'],'font.size':8,'axes.labelsize':8,'axes.titlesize':9,'xtick.labelsize':7.2,'ytick.labelsize':7.2,'legend.fontsize':7.2,'pdf.fonttype':42,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.7})
    blue='#287EA6';orange='#B6763C';green='#428675';red='#9F5A63';dark='#293F4B';grey='#86969F';palette=[blue,orange,green,red,dark,grey];credit='Data: Yahoo Finance daily ETF panel. Fixed research rules; no live trading claim.'
    def base(title,height=4.5,left=.13,right=.97,top=.78,bottom=.24):
        fig=plt.figure(figsize=(7.2047244094,height));fig.subplots_adjust(left=left,right=right,top=top,bottom=bottom);fig.suptitle(title,y=.985,fontsize=10);return fig
    def label(axes):
        for ax,c in zip(axes,'abcdef'):ax.annotate(c,(0,1),xycoords='axes fraction',xytext=(-19,13),textcoords='offset points',fontsize=10,weight='bold')
    def foot(fig,text,left=.13):fig.text(left,.025,text+'\n'+credit,fontsize=7.2,va='bottom')
    def save(fig,name,tables,interpretation):
        fig.canvas.draw()
        if require_matplotlib_panel_alignment:require_matplotlib_panel_alignment(fig,json_out=str(qa/f'{name}.alignment.json'),strict=True,tolerance_pt=1.5,gutter_tolerance_pt=1.5,require_panel_labels=len([a for a in fig.axes if not a.get_label().startswith('<colorbar')])>1)
        else:(qa/f'{name}.alignment.json').write_text(json.dumps({'status':'not_run','reason':'External auditor not supplied'})+'\n')
        fig.savefig(out/f'{name}.pdf');fig.savefig(out/f'{name}.svg');fig.savefig(out/f'{name}.png',dpi=600);plt.close(fig);sources.append({'id':name,'sources':[f'results/tables/us_equity_v1/{t}.csv' for t in tables],'interpretation':interpretation})
    # U01: fixed historical windows, comparable node placement and edge rule.
    rows=read('snapshot_correlations');windows=list(dict.fromkeys(r['requested_date'] for r in rows));symbols=list(dict.fromkeys(r['row'] for r in rows));angle=np.pi/2+np.arange(9)*2*np.pi/9;positions=np.c_[np.cos(angle),np.sin(angle)];fig=base('Industry co-movement | The observed graph changes with the window',3.65,left=.055,right=.965,top=.77,bottom=.28);axes=fig.subplots(1,3);fig.subplots_adjust(wspace=.18)
    for ax,window in zip(axes,windows):
        matrix=np.array([[f(next(r for r in rows if r['requested_date']==window and r['row']==a and r['column']==b),'correlation') for b in symbols] for a in symbols]);edges=0
        for i in range(9):
            for j in range(i+1,9):
                if matrix[i,j]>=.6:ax.plot(positions[[i,j],0],positions[[i,j],1],color=blue,lw=.5+3*(matrix[i,j]-.6),alpha=.55,zorder=1);edges+=1
        ax.scatter(positions[:,0],positions[:,1],s=27,color=dark,zorder=2)
        for name,xy in zip(symbols,positions):ax.text(*(1.4*xy),name,ha='center',va='center',fontsize=7.2)
        ax.set(xlim=(-1.75,1.75),ylim=(-1.75,1.75));ax.set_aspect('equal');ax.set_axis_off();ax.set_title(window);ax.text(.5,-.08,f'{edges} / 36 edges',transform=ax.transAxes,ha='center',fontsize=7.2)
    label(axes);foot(fig,'63-session sample correlations; fixed nodes, positive-correlation edge threshold 0.60.\nThree preselected historical examples; an observed correlation graph is not a trader network.',left=.055)
    save(fig,'U01',['snapshot_correlations'],'Historical association structure only. Nine nodes and an edge threshold do not demonstrate thermodynamic criticality or causal transmission.')
    # U02: same-window risk estimates and an explicit alignment ablation play different roles.
    daily=[r for r in read('daily_risk') if r['date']>='2020-01-01'];surrogate=[r for r in read('surrogate_summary') if r['metric']=='basket_variance'];fig=base('Collective risk | Marginal volatility misses aligned fluctuations',5.5,left=.14,top=.83,bottom=.22);axes=fig.subplots(2,1);fig.subplots_adjust(hspace=.6);x=[date(r['date']) for r in daily]
    axes[0].plot(x,[100*np.sqrt(252*f(r,'variance_total')) for r in daily],color=blue,lw=.8,label='Full covariance');axes[0].plot(x,[100*np.sqrt(252*f(r,'variance_self')) for r in daily],color=grey,lw=.8,label='Diagonal only');axes[0].set_ylabel('Annualised volatility (%)');axes[0].legend(loc='lower left',bbox_to_anchor=(0,1.08),ncol=2,frameon=False);axes[0].xaxis.set_major_locator(mdates.YearLocator(2));axes[0].xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    years=np.array([int(r['year']) for r in surrogate]);obs=np.array([f(r,'observed') for r in surrogate]);null=np.array([f(r,'surrogate_mean') for r in surrogate]);lo=np.array([f(r,'surrogate_low') for r in surrogate]);hi=np.array([f(r,'surrogate_high') for r in surrogate]);axes[1].plot(years,obs,'o-',color=blue,lw=.8,label='Aligned observations');axes[1].errorbar(years+.1,null,yerr=[null-lo,hi-null],fmt='s',color=orange,capsize=3,label='Shifted alignment');axes[1].set_ylabel('Standardised basket variance');axes[1].set_xticks(years);axes[1].legend(loc='lower left',bbox_to_anchor=(0,1.06),ncol=2,frameon=False);label(axes)
    foot(fig,'a: Rolling 63-session estimates, descriptive. b: Per-asset trailing-scale standardisation.\n499 within-year shifts; bars show central 95% of surrogates, not a sampling CI or causal test.',left=.14)
    save(fig,'U02',['daily_risk','surrogate_summary'],'Cross-sector alignment materially changes the basket distribution. This is not a causal herding identification or a forecast performance result.')
    # U03: the new representation must face both its matched model and the strong risk baseline.
    contrasts=read('risk_contrasts');selected=json.loads((ROOT/'results/checks/us_equity_v1/selection_freeze.json').read_text());strong=selected['risk_reference'];cases=[('NetworkGamma','ReturnGamma','Added network features'),('ReturnGamma',strong,'Return calibration vs EWMA')];splitnames=['Historical test\n301 targets','2026 confirmation\n40 targets'];fig=base('Held-out risk forecasts | More network features do not improve calibration',4.35,left=.24,top=.77,bottom=.26);axes=fig.subplots(1,2,sharey=True);fig.subplots_adjust(wspace=.25);allrows=[]
    for ax,(model,baseline,title) in zip(axes,cases):
        rr=[next(r for r in contrasts if r['split']==split and r['model']==model and r['baseline']==baseline and r['metric']=='QLIKE' and r['block_length']=='4') for split in ['historical_test','confirmation']];allrows+=rr
        for y,row in zip([1,0],rr):
            v=f(row,'improvement_pct');ax.errorbar(v,y,xerr=[[v-f(row,'ci_low')],[f(row,'ci_high')-v]],fmt='D',ms=5,color=red if v<0 else blue,capsize=3)
        ax.axvline(0,color=grey,lw=.8,ls='--');ax.set_title(title);ax.set_ylim(-.5,1.5);ax.set_xlabel('QLIKE loss reduction (%)')
    low=np.floor(min(f(r,'ci_low') for r in allrows)/10)*10-5;high=np.ceil(max(f(r,'ci_high') for r in allrows)/10)*10+5
    for ax in axes:ax.set_xlim(low,high)
    axes[0].set_yticks([1,0],splitnames);label(axes);foot(fig,'Paired circular bootstrap: 4 nonoverlapping five-session target blocks, 4,999 resamples.\nApproximate 95% intervals; positive is better. All 14 controls and yearly scores appear in U07.',left=.24)
    save(fig,'U03',['risk_contrasts'],'The frozen network representation fails the predictive improvement claim, including on confirmation. Conventional EWMA remains essential.')
    # U04: curves display money paths, increment correlations measure contemporaneous dependence.
    sr=read('strategy_daily');names=list(dict.fromkeys(r['strategy'] for r in sr));short=['Mom 63','Mom 126','Rev 5','Rev 21','LowVol 21','LowVol 63'];dates=sorted(set(r['date'] for r in sr if '2020-01-01'<=r['date']<'2026-01-01'));look={(r['date'],r['strategy']):f(r,'net_5bp') for r in sr};pnl=np.array([[look[d,n] for n in names] for d in dates]);fig=base('Strategy P&L | Different recipes can share the same risk',5.15,left=.1,top=.73,bottom=.26);axes=fig.subplots(1,2);fig.subplots_adjust(wspace=.6)
    for i,name in enumerate(short):axes[0].plot([date(d) for d in dates],100*np.cumsum(pnl[:,i]),color=palette[i],lw=.85,label=name)
    axes[0].axhline(0,color=grey,lw=.6);axes[0].set_ylabel('Cumulative P&L (% fixed capital)');axes[0].xaxis.set_major_locator(mdates.YearLocator(2));axes[0].xaxis.set_major_formatter(mdates.DateFormatter('%Y'));axes[0].set_title('All six fixed recipes');axes[0].legend(loc='lower left',bbox_to_anchor=(-.14,1.12),ncol=3,frameon=False,handlelength=1.3,columnspacing=.65)
    c=np.corrcoef(pnl,rowvar=False);im=axes[1].imshow(c,vmin=-1,vmax=1,cmap='BrBG',aspect='auto');axes[1].set_xticks(range(6),['M63','M126','R5','R21','L21','L63'],rotation=0);axes[1].set_yticks(range(6),short);axes[1].tick_params(length=0);axes[1].set_title('Daily net P&L correlation')
    for i in range(6):
        for j in range(6):axes[1].text(j,i,f'{c[i,j]:.2f}',ha='center',va='center',fontsize=7.2,color='white' if abs(c[i,j])>.7 else dark)
    cax=fig.add_axes([.65,.135,.25,.017]);cax.set_label('<colorbar>');fig.colorbar(im,cax=cax,orientation='horizontal',ticks=[-1,0,1]);label(axes);foot(fig,'2020-2025, 1,508 sessions. Daily increments drive dependence; curves are display only.\nFixed capital, one-session execution delay; 5 bp one-way turnover and 100 bp annual short fee.',left=.1)
    save(fig,'U04',['strategy_daily'],'All fixed strategy recipes are shown, including losses. Cumulative-curve correlation must not substitute for increment correlation or alpha testing.')
    # U05: a real held-out redundancy example, with a bounded exposure explanation.
    redundant=read('redundancy_diagnostic');exposure=read('exposure_decomposition');fig=base('Factor redundancy | Two low-volatility versions provide little diversification',4.65,left=.19,top=.78,bottom=.27);axes=fig.subplots(1,2);fig.subplots_adjust(wspace=.95)
    for y,row in zip([1,0],redundant):
        v=f(row,'daily_net_correlation');axes[0].errorbar(v,y,xerr=[[v-f(row,'corr_ci_low')],[f(row,'corr_ci_high')-v]],fmt='o',ms=5,color=blue,capsize=3)
    axes[0].set(xlim=(.5,1),ylim=(-.5,1.5),xlabel='Daily net increment correlation');axes[0].set_yticks([1,0],['2020-2025','2026']);axes[0].set_title('LowVol 21 vs LowVol 63')
    xx=np.array([0,1]);contrib=[]
    for split in ['historical_test','confirmation']:
        row=next(r for r in exposure if r['split']==split and r['strategy_a']=='LowVol-21' and r['strategy_b']=='LowVol-63');contrib.append([1e4*f(row,'shared_exposure_covariance'),1e4*f(row,'cross_asset_covariance')])
    v=np.array(contrib);axes[1].bar(xx-.16,v[:,0],width=.29,color=grey,label='Shared holdings');axes[1].bar(xx+.16,v[:,1],width=.29,color=orange,label='Asset co-movement');axes[1].axhline(0,color=dark,lw=.7);axes[1].set_xticks(xx,['2020-2025','2026']);axes[1].set_ylabel('Conditional covariance (% points squared)');axes[1].set_title('Exposure projection');axes[1].legend(loc='lower left',bbox_to_anchor=(-.15,1.11),frameon=False);label(axes)
    foot(fig,'a: 20-session paired blocks, 4,999 resamples; post-analysis descriptive pair diagnostic.\nb: Average past-covariance projection, no causal partition. Equal-risk effective count: 1.04 / 1.11.',left=.19)
    save(fig,'U05',['redundancy_diagnostic','exposure_decomposition'],'The example supports parameter-version redundancy, not lack of all alpha. Shared holdings and cross-asset terms can offset; projections do not identify microscopic causes.')
    # U06: preserve all four allocation methods and both evaluation periods.
    ar=read('allocation_daily');methods=['Equal','InverseVol','LW-MinVariance','HRP'];fig=base('Allocating P&L streams | No profitable network-allocation advantage established',4.4,left=.13,top=.76,bottom=.25);axes=fig.subplots(1,2);fig.subplots_adjust(wspace=.3)
    for ax,(lo,hi,title) in zip(axes,[('2020-01-01','2026-01-01','Historical test'),('2026-01-01','2026-10-24','2026 confirmation')]):
        for i,name in enumerate(methods):
            rr=[r for r in ar if r['method']==name and lo<=r['date']<hi];ax.plot([date(r['date']) for r in rr],100*np.cumsum([f(r,'net_5bp') for r in rr]),color=palette[i],lw=1.1 if name=='HRP' else .85,label=name)
        ax.axhline(0,color=grey,lw=.6);ax.set_title(title);ax.xaxis.set_major_locator(mdates.YearLocator(2) if lo.startswith('2020') else mdates.MonthLocator(interval=3));ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y') if lo.startswith('2020') else mdates.DateFormatter('%b'))
    axes[0].set_ylabel('Cumulative P&L (% fixed capital)');axes[0].legend(loc='lower left',bbox_to_anchor=(-.05,1.13),ncol=4,frameon=False,handlelength=1.4,columnspacing=.9);label(axes);foot(fig,'Net underlying trades aggregated before costs; all four existing allocation rules retained.\n5 bp one-way cost, 100 bp annual short fee. Read risk, return and exposure together.',left=.13)
    save(fig,'U06',['allocation_daily'],'All allocation curves are negative under declared costs. Any isolated risk decrease does not establish profitable factor discovery or allocator superiority.')
    # U07: complete score matrix, with no truncation of poor diagonal controls.
    yearly=read('risk_yearly');modelnames=list(dict.fromkeys(r['model'] for r in yearly));years=sorted(set(r['year'] for r in yearly));grid=np.array([[f(next(r for r in yearly if r['model']==name and r['year']==year),'qlike') for year in years] for name in modelnames]);assert np.isfinite(grid).all() and np.all(grid>0);fig=base('Full risk controls | All methods and all evaluation years',5.8,left=.3,top=.86,bottom=.21);ax=fig.subplots();im=ax.imshow(grid,cmap='viridis',norm=LogNorm(vmin=grid.min(),vmax=grid.max()),aspect='auto');ax.set_yticks(range(len(modelnames)),[s.replace('FixedCorrelation','Fixed corr').replace('LedoitWolf','LW') for s in modelnames]);ax.set_xticks(range(len(years)),years);ax.tick_params(length=0)
    for i in range(len(modelnames)):
        for j in range(len(years)):ax.text(j,i,f'{grid[i,j]:.2f}',ha='center',va='center',fontsize=7.2,color='white' if im.norm(grid[i,j])<.6 else dark)
    cax=fig.add_axes([.39,.135,.48,.02]);cax.set_label('<colorbar>');cb=fig.colorbar(im,cax=cax,orientation='horizontal',ticks=[.2,.5,1,2,5]);cb.ax.minorticks_off();cb.ax.set_xticklabels(['0.2','0.5','1','2','5']);fig.text(.3,.92,'Mean QLIKE; log colour scale, lower is better',fontsize=7.2);foot(fig,'All 14 methods; 2026 contains Jan 2-Oct 23. Cells are descriptive annual scores.\nNo rescaling, cell clipping or post-test winner selection; the primary contrast is in U03.',left=.3)
    save(fig,'U07',['risk_yearly'],'Complete controls expose whether complexity dominates standard risk methods. Annual means alone do not provide a new multiple-comparison-corrected claim.')
    (qa/'figure_sources.json').write_text(json.dumps(sources,indent=2)+'\n');print('Seven US-equity and P&L figures exported.')

if __name__=='__main__':main()
