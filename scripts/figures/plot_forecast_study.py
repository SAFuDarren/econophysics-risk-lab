#!/usr/bin/env python3
"""Five evidence-led forecast figures; source tables remain authoritative."""

from pathlib import Path as _ProjectPath
import sys as _project_sys
_project_sys.path.insert(0, str(_ProjectPath(__file__).resolve().parents[1]))
from _bootstrap import ROOT as PROJECT_ROOT, script_path, resolve_recorded_path
from pathlib import Path
import argparse,csv,datetime,json,os,sys
ROOT=PROJECT_ROOT;os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.cache/matplotlib'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import NullFormatter
from matplotlib.colors import TwoSlopeNorm


def read(p):return list(csv.DictReader(p.open()))
def f(r,k):return float(r[k])


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run-id',default='forecast_v1');parser.add_argument('--qa-tools',type=Path);args=parser.parse_args();require_matplotlib_panel_alignment=None
    if args.qa_tools:
        sys.path.insert(0,str(args.qa_tools));from audit_panel_alignment import require_matplotlib_panel_alignment
    tables=ROOT/'results/tables'/args.run_id;out=ROOT/'figures'/args.run_id;qa=ROOT/'results/checks'/args.run_id/'figure_qa';out.mkdir(parents=True,exist_ok=True);qa.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['DejaVu Sans'],'font.size':8,'axes.labelsize':8,'axes.titlesize':9,'xtick.labelsize':7.5,'ytick.labelsize':8,'legend.fontsize':7.2,'pdf.fonttype':42,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.7})
    dark='#263C49';grey='#84939C';blue='#267DA5';orange='#B7753D';green='#3E8A77';credit='Source: Binance Vision; market-derived outputs CC BY-NC-SA 4.0.';registry=[]
    pred=read(tables/'test_predictions.csv');contrasts=read(tables/'regression_contrasts.csv');primary=[r for r in contrasts if r['model']=='HAR+All' and r['baseline']=='HAR' and r['metric']=='log_mse' and r['day_block_length']=='7'][0]
    def rows(name):return [r for r in pred if r['model']==name]
    def frame(title,height=4.4,left=.13,bottom=.22,top=.8):
        fig=plt.figure(figsize=(7.2047244094,height));fig.subplots_adjust(left=left,right=.97,bottom=bottom,top=top);fig.suptitle(title,y=.985,fontsize=10);return fig
    def footer(fig,content,left=.13):fig.text(left,.025,content+'\n'+credit,fontsize=7.2,va='bottom')
    def save(fig,name,sources,note):
        fig.canvas.draw()
        if require_matplotlib_panel_alignment:require_matplotlib_panel_alignment(fig,json_out=str(qa/f'{name}.alignment.json'),strict=True,tolerance_pt=1.5,gutter_tolerance_pt=1.5,require_panel_labels=len(fig.axes)>1)
        else:(qa/f'{name}.alignment.json').write_text(json.dumps({'status':'not_run','reason':'External alignment auditor not supplied; do not inherit delivered QA.'},indent=2)+'\n')
        fig.savefig(out/f'{name}.pdf');fig.savefig(out/f'{name}.svg');fig.savefig(out/f'{name}.png',dpi=600);plt.close(fig);registry.append({'id':name,'sources':[str((tables/s).relative_to(ROOT)) for s in sources],'interpretation':note})
    # P01: complete held-out chronology and paired loss accumulation.
    fig=frame('Forecast validation | A small average gain varies over time',height=5.25,top=.85,bottom=.2);axes=fig.subplots(2,1,sharex=True);fig.subplots_adjust(hspace=.33)
    real=rows('HAR');allrows=rows('HAR+All');dates=[datetime.datetime.fromisoformat(r['target_date']) for r in real]
    axes[0].plot(dates,[f(r,'actual_volatility_pct') for r in real],color=dark,lw=1,label='Realised')
    axes[0].plot(dates,[f(r,'prediction_volatility_pct') for r in real],color=grey,lw=1,label='HAR')
    axes[0].plot(dates,[f(r,'prediction_volatility_pct') for r in allrows],color=blue,lw=1.1,label='HAR+All');axes[0].set_ylabel('Daily realised volatility (%)');axes[0].legend(loc='lower left',bbox_to_anchor=(0,1.03),ncol=3,frameon=False)
    advantage=np.cumsum(np.array([f(r,'log_mse') for r in real])-np.array([f(r,'log_mse') for r in allrows]));axes[1].plot(dates,advantage,color=blue,lw=1.3);axes[1].axhline(0,color=grey,lw=.7,ls='--');axes[1].set_ylabel('Cumulative advantage\n(log-loss units)');axes[1].set_xlabel('2026 held-out target day (UTC)');axes[1].xaxis.set_major_locator(mdates.MonthLocator());axes[1].xaxis.set_major_formatter(mdates.DateFormatter('%b'));axes[1].set_xlim(dates[0],dates[-1])
    for ax,label in zip(axes,'ab'):ax.annotate(label,(0,1),xycoords='axes fraction',xytext=(-27,10),textcoords='offset points',weight='bold',fontsize=10)
    footer(fig,'All 183 test days retained; positive cumulative advantage favours HAR+All.\n2025 train / 2026 Q1 selection / Q2-Q3 test; coefficients frozen after Q1.')
    save(fig,'P01',['test_predictions.csv'],'Forecasts are point predictions, not intervals or price-direction forecasts. All final dates retained.')
    # P02: paired gain intervals, including nonlinear same-view control.
    names=['HAR+Activity','HAR+Coupling','HAR+Tail','HAR+All','RBF-HAR','RBF-All'];items=[next(r for r in contrasts if r['model']==m and r['baseline']=='HAR' and r['metric']=='log_mse' and r['day_block_length']=='7') for m in names];items.append(next(r for r in contrasts if r['model']=='RBF-All' and r['baseline']=='RBF-HAR' and r['metric']=='log_mse' and r['day_block_length']=='7'))
    fig=frame('Incremental value | The primary 95% interval includes zero',height=4.55,left=.28,top=.83);ax=fig.add_subplot();labels=names+['RBF-All vs RBF-HAR'];ys=np.arange(len(items))[::-1]
    for y,r in zip(ys,items):
        color=blue if r['model']=='HAR+All' else grey;v=f(r,'improvement_pct');lo=f(r,'improvement_ci_low');hi=f(r,'improvement_ci_high');ax.errorbar(v,y,xerr=[[v-lo],[hi-v]],fmt='D' if r['model']=='HAR+All' else 'o',color=color,capsize=3,ms=5,lw=1.2)
    ax.axvline(0,color=grey,ls='--',lw=.8);ax.set_yticks(ys,labels);ax.set_ylim(-.6,len(items)-.4);ax.set_xlabel('Log-MSE reduction versus stated baseline (%)');ax.set_xlim(-6.5,10.3)
    fig.text(.28,.88,f"Primary: {f(primary,'improvement_pct'):.2f}%  [{f(primary,'improvement_ci_low'):.2f}, {f(primary,'improvement_ci_high'):.2f}]",color=blue,fontsize=9,weight='bold')
    footer(fig,'Paired 95% intervals: circular 7-day blocks, 4,999 replicates, 183 days.\nHAR is the baseline except the last row; naive baselines remain in source tables.',left=.28)
    save(fig,'P02',['regression_contrasts.csv'],'All declared feature/nonlinear variants retained; Persistence/EWMA are baseline benchmarks documented in tables and report. No winner selected from test.')
    # P03: all incremental variants by complete calendar month, descriptive.
    monthly=read(tables/'monthly_metrics.csv');months=sorted({r['month'] for r in monthly});values=np.array([[f(next(r for r in monthly if r['model']==m and r['month']==month),'improvement_vs_HAR_pct') for month in months] for m in names]);fig=frame('Temporal robustness | Gains do not persist in every month',height=4.65,left=.23,top=.73);ax=fig.add_subplot();bound=float(np.ceil(np.max(np.abs(values))/5)*5);im=ax.imshow(values,cmap='BrBG',norm=TwoSlopeNorm(vmin=-bound,vcenter=0,vmax=bound),aspect='auto');ax.set_yticks(np.arange(len(names)),names);ax.set_xticks(np.arange(6),['Apr\n30 days','May\n31 days','Jun\n30 days','Jul\n31 days','Aug\n31 days','Sep\n30 days']);ax.tick_params(length=0)
    for i in range(len(names)):
        for j in range(6):ax.text(j,i,f'{values[i,j]:+.1f}',ha='center',va='center',fontsize=8,color='white' if abs(values[i,j])>.65*bound else dark)
    # Dedicated horizontal colour scale preserves the main plot geometry.
    cax=fig.add_axes([.34,.80,.48,.025]);cax.set_label('<colorbar>');fig.colorbar(im,cax=cax,orientation='horizontal');cax.xaxis.set_ticks_position('top');fig.text(.23,.91,'Cell values: log-MSE reduction vs HAR (%)',fontsize=7.2)
    footer(fig,'Each cell uses all days in that month; no month-wise significance claim.\nAll feature/nonlinear variants shown; colour scale is symmetric around zero.',left=.23)
    save(fig,'P03',['monthly_metrics.csv'],'Monthly results describe temporal heterogeneity; small monthly samples and shared fitted models are not independent replications.')
    # P04: identical coordinate systems, every held-out day, no forecast-envelope claim.
    fig=frame('Prediction limits | Large realised moves remain difficult',height=4.35,left=.12,top=.79,bottom=.24);axes=fig.subplots(1,2);fig.subplots_adjust(wspace=.43);realvol=np.array([f(r,'actual_volatility_pct') for r in real]);hi=np.array([int(r['high_volatility_day']) for r in real]).astype(bool);allvalues=realvol.tolist()+[f(r,'prediction_volatility_pct') for m in ['HAR','HAR+All'] for r in rows(m)];low=min(allvalues)*.8;high=max(allvalues)*1.15
    assert low>0
    for ax,m,letter in zip(axes,['HAR','HAR+All'],'ab'):
        pv=np.array([f(r,'prediction_volatility_pct') for r in rows(m)]);ax.scatter(realvol[~hi],pv[~hi],s=13,color=grey,alpha=.7);ax.scatter(realvol[hi],pv[hi],s=30,color=orange,marker='D');ax.plot([low,high],[low,high],color=dark,lw=.7,ls='--');ax.set_xscale('log');ax.set_yscale('log');ax.set_xlim(low,high);ax.set_ylim(low,high);ax.set_xticks([.5,1,2,4,6],['0.5','1','2','4','6']);ax.set_yticks([.5,1,2,4,6],['0.5','1','2','4','6']);ax.xaxis.set_minor_formatter(NullFormatter());ax.yaxis.set_minor_formatter(NullFormatter());ax.set_title(m);ax.set_xlabel('Realised daily volatility (%)');ax.set_ylabel('Forecast daily volatility (%)');ax.annotate(letter,(0,1),xycoords='axes fraction',xytext=(-23,12),textcoords='offset points',weight='bold',fontsize=10)
    footer(fig,'Every point is one of 183 test days; orange diamonds: 8 high-volatility days.\nIdentical log axes; dashed identity is a reference, not a prediction interval.',left=.12)
    save(fig,'P04',['test_predictions.csv'],'Point forecasts cannot reproduce every realised shock; this scatter alone is not evidence of biased conditional forecasts.')
    # P05: score comparison and empirical calibration have distinct roles.
    pc=read(tables/'probability_contrasts.csv');cal=read(tables/'probability_calibration.csv');pc=[r for r in pc if r['day_block_length']=='7'];fig=frame('Risk probabilities | Baseline choice changes the improvement claim',height=4.65,left=.13,top=.79,bottom=.24);axes=fig.subplots(1,2);fig.subplots_adjust(wspace=.52)
    for i,r in enumerate(pc):
        y=2-i;v=f(r,'improvement_pct');lo=f(r,'improvement_ci_low');hi=f(r,'improvement_ci_high');axes[0].errorbar(v,y,xerr=[[v-lo],[hi-v]],fmt='o',color=blue if i==2 else grey,capsize=3,ms=4)
    axes[0].set_yticks([2,1,0],['HAR vs\nConstant','All vs\nConstant','All vs\nHAR']);axes[0].set_ylim(-.6,2.6);axes[0].axvline(0,color=grey,lw=.7,ls='--');axes[0].set_xlabel('Brier score reduction (%)');axes[0].set_title('Paired score evidence')
    for m,color,marker in [('Logit-HAR',grey,'o'),('Logit-All',blue,'D')]:
        cr=[r for r in cal if r['model']==m and int(r['days'])>0];axes[1].scatter([f(r,'mean_probability') for r in cr],[f(r,'event_frequency') for r in cr],s=[10+2*int(r['days']) for r in cr],color=color,marker=marker,alpha=.7,label=m)
    axes[1].plot([0,1],[0,1],color=dark,lw=.7,ls='--');axes[1].set_xlim(-.04,1.04);axes[1].set_ylim(-.04,1.04);axes[1].set_xlabel('Mean predicted probability');axes[1].set_ylabel('Observed event frequency');axes[1].set_title('Descriptive calibration');axes[1].legend(loc='lower left',bbox_to_anchor=(0,1.13),frameon=False,ncol=2,markerscale=.4,handletextpad=.3,columnspacing=.6)
    for ax,letter in zip(axes,'ab'):ax.annotate(letter,(0,1),xycoords='axes fraction',xytext=(-23,12),textcoords='offset points',weight='bold',fontsize=10)
    footer(fig,'183 test days, only 8 events; high volatility exceeds the frozen 2025 Q90.\nLeft: 7-day block 95% intervals. Right: fixed bins, marker area reflects count; no CI.',left=.13)
    save(fig,'P05',['probability_contrasts.csv','probability_calibration.csv'],'Large reductions versus a frozen historical event rate are not the incremental gain from volume. Sparse calibration bins cannot establish stable rare-event probabilities.')
    (qa/'figure_sources.json').write_text(json.dumps(registry,indent=2)+'\n');print('Five forecast figures exported.')


if __name__=='__main__':main()
