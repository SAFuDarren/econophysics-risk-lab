#!/usr/bin/env python3
"""Mechanism interventions, fresh-test skills, full controls and budget diagnostics."""

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
from matplotlib.colors import TwoSlopeNorm


def read(p):return list(csv.DictReader(p.open()))
def f(r,k):return float(r[k])


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run-id',default='state_forecast_v2');parser.add_argument('--mechanism-run-id',default='state_mechanism_v2');parser.add_argument('--qa-tools',type=Path);args=parser.parse_args();require_matplotlib_panel_alignment=None
    if args.qa_tools:sys.path.insert(0,str(args.qa_tools));from audit_panel_alignment import require_matplotlib_panel_alignment
    tables=ROOT/'results/tables'/args.run_id;out=ROOT/'figures'/args.run_id;qa=ROOT/'results/checks'/args.run_id/'figure_qa';out.mkdir(parents=True,exist_ok=True);qa.mkdir(parents=True,exist_ok=True);plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['DejaVu Sans'],'font.size':8,'axes.labelsize':8,'axes.titlesize':9,'xtick.labelsize':7.5,'ytick.labelsize':7.5,'legend.fontsize':7.2,'pdf.fonttype':42,'svg.fonttype':'none','axes.spines.right':False,'axes.spines.top':False,'axes.linewidth':.7})
    dark='#293F4B';grey='#86969F';blue='#287EA6';orange='#B6763C';green='#428675';credit='Market data: Binance Vision; market-derived outputs CC BY-NC-SA 4.0.';sources=[]
    def base(title,height=4.6,left=.23,top=.79,bottom=.25):
        fig=plt.figure(figsize=(7.2047244094,height));fig.subplots_adjust(left=left,right=.97,top=top,bottom=bottom);fig.suptitle(title,y=.985,fontsize=10);return fig
    def foot(fig,text,left=.13,source_credit=None):fig.text(left,.025,text+'\n'+(credit if source_credit is None else source_credit),fontsize=7.2,va='bottom')
    def labels(axes):
        for ax,letter in zip(axes,'ab'):ax.annotate(letter,(0,1),xycoords='axes fraction',xytext=(-23,12),textcoords='offset points',weight='bold',fontsize=10)
    def save(fig,name,paths,notes):
        fig.canvas.draw()
        if require_matplotlib_panel_alignment:require_matplotlib_panel_alignment(fig,json_out=str(qa/f'{name}.alignment.json'),strict=True,tolerance_pt=1.5,gutter_tolerance_pt=1.5,require_panel_labels=sum(not ax.get_label().startswith('<colorbar') for ax in fig.axes)>1)
        else:(qa/f'{name}.alignment.json').write_text(json.dumps({'status':'not_run','reason':'External auditor not supplied; previous QA does not transfer.'})+'\n')
        fig.savefig(out/f'{name}.pdf');fig.savefig(out/f'{name}.svg')
        fig.savefig(out/f'{name}.png',dpi=600);plt.close(fig);paths=[p.replace('results/tables/state_forecast_v2/',f'results/tables/{args.run_id}/') for p in paths];sources.append({'id':name,'sources':paths,'interpretation':notes})
    # V01: memory intervention and marginal joint constraint have different roles.
    mechanism_path=ROOT/'results/tables'/args.mechanism_run_id/'summary.csv';mechanism=read(mechanism_path);arms=['Constant','PersistentActivity','ShuffledActivity','PersistentImpact'];names=['Constant','Activity state','Shuffled pairs','Impact state'];theory=json.loads((ROOT/'results/checks'/args.run_id/'compensation_theory.json').read_text());fig=base('Mechanism controls | Time order and joint moments carry different information',height=4.6,left=.19,top=.77);axes=fig.subplots(1,2);fig.subplots_adjust(wspace=.7);ys=np.arange(4)[::-1]
    for metric,offset,color,marker,lab in [('magnitude_acf1',.11,blue,'o','Return magnitude'),('volume_acf1',-.11,orange,'s','Volume')]:
        for y,arm in zip(ys,arms):
            r=next(r for r in mechanism if r['arm']==arm and r['metric']==metric);v=f(r,'estimate');axes[0].errorbar(v,y+offset,xerr=[[v-f(r,'ci_low')],[f(r,'ci_high')-v]],color=color,fmt=marker,capsize=2,ms=4,label=lab if y==ys[0] else None)
    axes[0].set_yticks(ys,names);axes[0].set_ylim(-.6,3.6);axes[0].set_xlim(-.07,.97);axes[0].axvline(0,color=grey,lw=.7,ls='--');axes[0].set_xlabel('Lag-one correlation');axes[0].set_title('Controlled persistence');axes[0].legend(loc='lower left',bbox_to_anchor=(-.1,1.14),ncol=2,frameon=False,handletextpad=.3,columnspacing=.6)
    for i,arm in enumerate(arms):
        r=next(r for r in mechanism if r['arm']==arm and r['metric']=='delta');v=f(r,'estimate');axes[1].errorbar(v,4-i,xerr=[[v-f(r,'ci_low')],[f(r,'ci_high')-v]],color=green if arm=='ShuffledActivity' else grey,fmt='o',capsize=3,ms=4)
    axes[1].plot(theory['compensated_delta'],0,marker='^',color=blue,ms=6);axes[1].axvline(0,color=grey,lw=.7,ls='--');axes[1].set_yticks([4,3,2,1,0],names+['Compensated\n(theory only)']);axes[1].set_ylim(-.65,4.65);axes[1].set_xlim(-2.6,1.1);axes[1].set_xlabel('Joint-moment Delta');axes[1].set_title('Fixed graph law, changing states');labels(axes)
    foot(fig,'SIMULATION: 10 paths x 8,192 bars; intervals resample independent paths.\nShuffling retains exact observed (r,V) pairs; triangle is an added analytic construction.\nState models are hypothetical, with no real-market calibration.',left=.19,source_credit='Source: original controlled simulation and analytic construction; no market data.')
    save(fig,'V01',[str(mechanism_path.relative_to(ROOT)),str((ROOT/'results/checks'/args.run_id/'compensation_theory.json').relative_to(ROOT))],'Compensation construction is post-analysis theory, not a fifth predictive model. Changing memory does not establish market mechanism truth.')
    # V02: predeclared three fresh comparisons. Off is exact model identity.
    primary=read(tables/'primary_contrasts.csv');cases=[('ETHUSDT','external_asset'),('BTCUSDT','new_time'),('ETHUSDT','new_time')];case_names=['ETH external\n183 days · Off','BTC new time\n25 days','ETH new time\n25 days · Off'];fig=base('Fresh tests | A stable volume increment is not established',height=4.35,left=.23,top=.79);axes=fig.subplots(1,2,sharey=True);fig.subplots_adjust(wspace=.38)
    for ax,metric,title in zip(axes,['qlike','log_mse'],['Primary: QLIKE','Secondary: log-MSE']):
        for y,(asset,tag) in zip([2,1,0],cases):
            r=next(r for r in primary if r['asset']==asset and r['evaluation']==tag and r['metric']==metric and r['day_block_length']=='7');v=f(r,'improvement_pct');ax.errorbar(v,y,xerr=[[v-f(r,'ci_low')],[f(r,'ci_high')-v]],fmt='D' if asset=='BTCUSDT' else 'o',mfc=blue if asset=='BTCUSDT' else 'white',mec=blue if asset=='BTCUSDT' else grey,ecolor=blue if asset=='BTCUSDT' else grey,capsize=3,ms=5)
        ax.axvline(0,color=grey,lw=.8,ls='--');ax.set_xlim(-1.5,6);ax.set_ylim(-.65,2.65);ax.set_title(title);ax.set_xlabel('Loss reduction (%)')
    axes[0].set_yticks([2,1,0],case_names);labels(axes);foot(fig,'Matched baseline: updating return-only Gamma model. Paired 7-day blocks, 4,999 draws.\nOff = validation selected exact return-only fallback; it is not an information theorem.\nTwo October assets share only 25 distinct dates.',left=.23)
    save(fig,'V02',['results/tables/state_forecast_v2/primary_contrasts.csv'],'QLIKE is the frozen v2 primary. A positive secondary BTC log-MSE result cannot replace external-asset or primary-objective checks.')
    # V03: all controls against the simple retained baseline, both compulsory losses.
    control=read(tables/'legacy_control_summary.csv');models=['LegacyHAR-Static','ReturnLog-Adaptive','ReturnGamma-Static','ReturnGamma-Adaptive','LegacyVolumeGamma-Adaptive','StateVolumeGamma-Adaptive','StateVolumeGamma-Static'];display=['HAR log · Fixed','Return log · Updating','Return Gamma · Fixed','Return Gamma · Updating','Legacy V · Updating','State V · Updating','State V · Fixed'];grids=[np.array([[f(next(r for r in control if r['asset']==asset and r['evaluation']==tag and r['model']==m and r['metric']==metric),'improvement_vs_legacy_HAR_pct') for asset,tag in cases] for m in models]) for metric in ['qlike','log_mse']];bound=float(np.ceil(max(np.abs(g).max() for g in grids)/10)*10);fig=base('Full controls | More complexity does not dominate the simple baseline',height=4.9,left=.26,top=.8,bottom=.3);axes=fig.subplots(1,2,sharey=True);fig.subplots_adjust(wspace=.18)
    for ax,g,title in zip(axes,grids,['QLIKE','Log-MSE']):
        im=ax.imshow(g,cmap='BrBG',norm=TwoSlopeNorm(vmin=-bound,vcenter=0,vmax=bound),aspect='auto');ax.set_title(title);ax.set_xticks([0,1,2],['ETH ext.\nn=183','BTC Oct\nn=25','ETH Oct\nn=25']);ax.tick_params(length=0)
        for i in range(7):
            for j in range(3):ax.text(j,i,f'{g[i,j]:+.1f}',ha='center',va='center',fontsize=7.5,color='white' if abs(g[i,j])>.65*bound else dark)
    axes[0].set_yticks(np.arange(7),display);labels(axes);cax=fig.add_axes([.36,.145,.48,.022]);cax.set_label('<colorbar>');cb=fig.colorbar(im,cax=cax,orientation='horizontal',ticks=[-bound,0,bound]);cb.ax.tick_params(labelsize=7)
    fig.text(.26,.89,'Cells: loss reduction vs the retained HAR log baseline (%)',fontsize=7.2);foot(fig,'All 7 frozen model controls shown; cell values are descriptive, not new winner tests.\nThe matched volume comparison is in V02. Shared colour scale; no cell truncation.',left=.26)
    save(fig,'V03',['results/tables/state_forecast_v2/legacy_control_summary.csv'],'Separate loss functions reveal trade-offs. Good mean-variance calibration does not imply smaller log prediction error or dominance over LegacyHAR.')
    # V04: every new BTC date, no cherry-picked large-return window.
    predictions=read(tables/'predictions.csv');base_rows=[r for r in predictions if r['asset']=='BTCUSDT' and r['evaluation']=='new_time' and r['model']=='ReturnGamma-Adaptive'];state_rows=[r for r in predictions if r['asset']=='BTCUSDT' and r['evaluation']=='new_time' and r['model']=='StateVolumeGamma-Adaptive'];dates=[datetime.datetime.fromisoformat(r['target_date']) for r in base_rows];fig=base('New BTC time | Small forecast gain, limited budget change',height=5.2,left=.14,top=.84,bottom=.21);axes=fig.subplots(2,1,sharex=True);fig.subplots_adjust(hspace=.32)
    axes[0].plot(dates,[f(r,'actual_volatility_pct') for r in base_rows],color=dark,lw=1.1,label='Realised');axes[0].plot(dates,[f(r,'forecast_volatility_pct') for r in base_rows],color=grey,lw=1.1,label='Return Gamma');axes[0].plot(dates,[f(r,'forecast_volatility_pct') for r in state_rows],color=blue,lw=1.1,label='State + Volume');axes[0].legend(loc='lower left',bbox_to_anchor=(0,1.04),ncol=3,frameon=False);axes[0].set_ylabel('Daily realised volatility (%)')
    for rr,col,lab in [(base_rows,grey,'Return Gamma'),(state_rows,blue,'State + Volume')]:axes[1].plot(dates,[f(r,'actual_rv')/f(r,'forecast_rv') for r in rr],color=col,lw=1.1,label=lab)
    axes[1].axhline(1,color=grey,lw=.7,ls='--');axes[1].axhline(2,color=orange,lw=.7,ls=':');axes[1].set_ylabel('Realised variance / forecast');axes[1].set_xlabel('October 2026 target day (UTC)');axes[1].set_xlim(dates[0],dates[-1]);axes[1].xaxis.set_major_locator(mdates.DayLocator(interval=4));axes[1].xaxis.set_major_formatter(mdates.DateFormatter('%d'));labels(axes)
    foot(fig,'All 25 new dates retained. Reference ratios: 1 = budget, 2 = twice budget.\nThis is an uncapped theoretical risk diagnostic, not a trading strategy or a guarantee.',left=.14)
    save(fig,'V04',['results/tables/state_forecast_v2/predictions.csv'],'The two volume-channel forecasts are close. A short-period point improvement cannot establish practical risk reduction or stable deployment value.')
    (qa/'figure_sources.json').write_text(json.dumps(sources,indent=2)+'\n');print('Four state-mechanism forecast figures exported.')


if __name__=='__main__':main()
