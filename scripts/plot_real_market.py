#!/usr/bin/env python3
"""Source-backed market figures with explicit calibration and uncertainty units."""
from pathlib import Path
import argparse,csv,datetime,json,os,sys
ROOT=Path(__file__).resolve().parents[1];os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.cache/matplotlib'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy.stats import norm


def read(p):return list(csv.DictReader(p.open()))
def f(row,key):return float(row[key]) if row[key]!='' else np.nan


def main():
    p=argparse.ArgumentParser();p.add_argument('--run-id',default='real_market_v1');p.add_argument('--qa-tools',type=Path);args=p.parse_args()
    if not args.run_id.replace('_','').replace('-','').isalnum():p.error('invalid run-id')
    require_matplotlib_panel_alignment=None
    if args.qa_tools:
        sys.path.insert(0,str(args.qa_tools.resolve()));from audit_panel_alignment import require_matplotlib_panel_alignment
    cfg=json.loads((ROOT/'configs/real_market_v1.json').read_text());tables=ROOT/'results/tables'/args.run_id;out=ROOT/'figures'/args.run_id;qa=ROOT/'results/checks'/args.run_id/'figure_qa';out.mkdir(parents=True,exist_ok=True);qa.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['DejaVu Sans'],'font.size':8,'axes.labelsize':8,'axes.titlesize':9,'xtick.labelsize':8,'ytick.labelsize':8,'legend.fontsize':7.2,'pdf.fonttype':42,'svg.fonttype':'none','axes.spines.right':False,'axes.spines.top':False,'axes.linewidth':.7})
    market='#273B46';colors={'ER rho=0.6':'#78919C','ER rho=1.0':'#287DA8','ER rho=1.4':'#B16A35'};credit='Source: Binance Vision; market-derived figures CC BY-NC-SA 4.0.';catalog=[]
    def base(title,foot,height=4.,left=.13,top=.78,wspace=.43):
        fig,axes=plt.subplots(1,2,figsize=(7.2047244094,height));fig.subplots_adjust(left=left,right=.975,top=top,bottom=.25,wspace=wspace);fig.suptitle(title,y=.99,fontsize=10)
        fig.text(left,.025,foot+'\n'+credit,fontsize=7.2,va='bottom')
        for ax,letter in zip(axes,'ab'):ax.annotate(letter,(0,1),xycoords='axes fraction',xytext=(-23,12),textcoords='offset points',fontsize=10,weight='bold')
        return fig,axes
    def save(fig,name,sources,notes=None):
        fig.canvas.draw()
        if require_matplotlib_panel_alignment:require_matplotlib_panel_alignment(fig,json_out=str(qa/f'{name}.alignment.json'),tolerance_pt=1.5,gutter_tolerance_pt=1.5,require_panel_labels=True,strict=True)
        else:(qa/f'{name}.alignment.json').write_text(json.dumps({'status':'not_run','reason':'Full alignment auditor not supplied; do not reuse previous QA.','axes_bounds':[list(ax.get_window_extent().bounds) for ax in fig.axes]},indent=2)+'\n')
        fig.savefig(out/f'{name}.svg');fig.savefig(out/f'{name}.pdf');fig.savefig(out/f'{name}.png',dpi=600);plt.close(fig)
        catalog.append({'id':name,'source_paths':[str(x.relative_to(ROOT)) for x in sources],'notes':notes or []})
    # Full-year overview: daily OHLCV aggregation uses every bar; returns retain all bars.
    overview=read(tables/'daily_overview.csv');bars_path=ROOT/'data/processed'/cfg['dataset']/'bars.csv';bars=read(bars_path)
    dates=[datetime.datetime.fromisoformat(r['date_utc']) for r in overview];bar_dates=[datetime.datetime.fromisoformat(r['timestamp_utc'].replace('Z','+00:00')) for r in bars]
    fig,axes=plt.subplots(3,1,sharex=True,figsize=(7.2047244094,5.8));fig.subplots_adjust(left=.145,right=.975,top=.86,bottom=.15,hspace=.20)
    fig.suptitle('Real data | BTCUSDT spot across 2025',y=.985,fontsize=11)
    axes[0].plot(dates,[f(r,'close')/1000 for r in overview],color='#287DA8',lw=1.0);axes[0].set_ylabel('Daily close (k USDT)')
    axes[1].plot(bar_dates,[100*f(r,'return_log') for r in bars],color='#657783',alpha=.65,lw=.35,rasterized=True);axes[1].set_ylabel('5-min log return (%)')
    axes[2].bar(dates,[f(r,'volume')/1000 for r in overview],width=.8,color='#78919C',linewidth=0);axes[2].set_ylabel('Daily volume (k BTC)')
    for ax,letter in zip(axes,'abc'):
        ax.axvline(datetime.datetime(2025,7,1),color='#8A9297',linestyle='--',lw=.8);ax.annotate(letter,(0,1),xycoords='axes fraction',xytext=(-23,7),textcoords='offset points',fontsize=10,weight='bold')
    axes[0].text(.24,1.12,'H1 calibration',transform=axes[0].transAxes,ha='center',fontsize=8);axes[0].text(.76,1.12,'H2 evaluation',transform=axes[0].transAxes,ha='center',fontsize=8)
    axes[-1].xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1,4,7,10,12]));axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%b'));axes[-1].set_xlabel('2025 UTC interval date');axes[-1].set_xlim(datetime.datetime(2025,1,1),datetime.datetime(2026,1,1)-datetime.timedelta(seconds=1))
    fig.text(.145,.025,'105,120 verified 5-minute bars; 365 complete UTC days; no filling or row deletion.\nClose/volume aggregated daily; all 5-minute returns retained.\n'+credit,fontsize=7.2,va='bottom')
    save(fig,'F08',[tables/'daily_overview.csv',bars_path])
    # Conditional coupling and a separate execution-level implication.
    fig,axes=base('Held-out data | Positive coupling does not validate fixed impact',
        'H2: 52,992 bars / 184 days; market CI: 7-day block bootstrap.\nModel: 10 H2-length paths per rho, conditional on H1 moment matching.',height=4.5,top=.67)
    coupling=read(tables/'coupling_bins.csv')
    for source,color in [('Market H2',market),*colors.items()]:
        rr=sorted([r for r in coupling if r['source']==source],key=lambda r:int(r['bin']));x=np.array([int(r['bin']) for r in rr]);mean=np.array([f(r,'mean_abs_return_H1_sd') for r in rr]);lo=np.array([f(r,'ci_low') for r in rr]);hi=np.array([f(r,'ci_high') for r in rr])
        axes[0].errorbar(x,mean,yerr=[mean-lo,hi-mean],fmt='o-',color=color,lw=1.1,markersize=3,capsize=2,label=source)
    axes[0].set_xlabel('Volume bins fixed from H1 deciles');axes[0].set_ylabel('Mean absolute return / H1 SD');axes[0].set_xticks([1,3,5,7,10]);axes[0].set_title('Magnitude-volume association',pad=10)
    impact=read(tables/'impact_bins.csv');x=np.array([f(r,'mean_signed_volume_over_H1_mean') for r in impact]);mean=np.array([f(r,'mean_return_over_H1_sd') for r in impact]);lo=np.array([f(r,'ci_low') for r in impact]);hi=np.array([f(r,'ci_high') for r in impact]);line=np.array([f(r,'constant_impact_H1') for r in impact])
    axes[1].errorbar(x,mean,yerr=[mean-lo,hi-mean],fmt='o',color=market,capsize=2,markersize=3,label='H2 binned means');axes[1].plot(x,line,'--',color='#7B6996',lw=1.1,label='H1 constant-impact fit');axes[1].axhline(0,color='#AAB0B4',lw=.5);axes[1].axvline(0,color='#AAB0B4',lw=.5)
    axes[1].set_xlabel('Signed taker quantity / H1 mean volume');axes[1].set_ylabel('Mean return / H1 SD')
    impact_summary=next(row for row in read(tables/'impact_association.csv') if int(row['day_block_length'])==7)
    axes[1].set_title(f'Same-bar flow relation\nHeld-out bar R-squared = {f(impact_summary,"holdout_r_squared"):.3f}',pad=10,fontsize=8.5)
    fig.legend(*axes[0].get_legend_handles_labels(),loc='upper left',bbox_to_anchor=(.13,.93),ncol=2,frameon=False,fontsize=7)
    fig.legend(*axes[1].get_legend_handles_labels(),loc='upper left',bbox_to_anchor=(.61,.93),ncol=1,frameon=False,fontsize=7)
    save(fig,'R01',[tables/'coupling_bins.csv',tables/'impact_bins.csv',tables/'impact_association.csv'],['All bars enter fixed H1 bins; empty model bins are retained as missing, not interpolated.','Binned means do not show individual-bar scatter; R-squared is from all H2 bars.'])
    # Continuous and discrete observations share an empirical CCDF comparison, not a likelihood.
    tail_count=next(int(row['tail_count']) for row in read(tables/'tail_exponents.csv') if row['phase']=='H2' and f(row,'threshold_H1_sd')==3 and int(row['day_block_length'])==7)
    fig,axes=base('Held-out data | Broad tails do not establish a transferable power law',
        f'H1 return SD fixes units; tail threshold: 3 H1 SD; H2 exceedances: {tail_count}.\nMarket bands: 7-day blocks; model bands: independent-path bootstrap.',height=4.5,top=.67)
    ccdf=read(tables/'ccdf_comparison.csv')
    upper_grid=max(f(row,'threshold_H1_sd') for row in ccdf)
    for source,color in [('Market H2',market),*colors.items()]:
        rr=sorted([r for r in ccdf if r['source']==source],key=lambda r:f(r,'threshold_H1_sd'));x=np.array([f(r,'threshold_H1_sd') for r in rr]);y=np.array([f(r,'ccdf') for r in rr]);lo=np.array([f(r,'ci_low') for r in rr]);hi=np.array([f(r,'ci_high') for r in rr]);positive=(x>0)&(y>0)
        axes[0].loglog(x[positive],y[positive],color=color,lw=1.2,label=source);band=positive&(lo>0);axes[0].fill_between(x,lo,hi,where=band,color=color,alpha=.12,lw=0)
    xx=np.geomspace(.1,10,100);yy=2*norm.sf(xx);positive=yy>=1e-6;axes[0].loglog(xx[positive],yy[positive],':',color='#8A9297',lw=1,label='Gaussian reference');axes[0].set_ylim(1e-6,1);axes[0].set_xlim(.1,upper_grid);axes[0].set_xlabel('Absolute return / H1 SD');axes[0].set_ylabel('Exceedance probability');axes[0].set_title('Empirical tails at common scale',pad=10)
    real=read(tables/'real_conditional_tail_ccdf.csv');x=np.array([f(r,'threshold_H1_sd') for r in real]);y=np.array([f(r,'conditional_ccdf') for r in real]);lo=np.array([f(r,'ci_low') for r in real]);hi=np.array([f(r,'ci_high') for r in real]);positive=(x>0)&(y>0);axes[1].loglog(x[positive],y[positive],color=market,lw=1.3,label='H2 empirical');axes[1].fill_between(x,lo,hi,where=positive&(lo>0),color=market,alpha=.12,lw=0)
    fitted=read(tables/'tail_fitted_curves.csv')
    for method,color,style in [('Pareto','#287DA8','--'),('Exponential','#B16A35',':'),('Lognormal','#4F927C','-.')]:
        rr=[r for r in fitted if r['method']==method];x=np.array([f(r,'threshold_H1_sd') for r in rr]);y=np.array([f(r,'conditional_ccdf') for r in rr]);positive=(x>0)&(y>=1e-4);axes[1].loglog(x[positive],y[positive],style,color=color,lw=1.1,label=method+' (H1)')
    axes[1].set_ylim(1e-4,1.05);axes[1].set_xlim(3,upper_grid);axes[1].set_xlabel('Absolute return / H1 SD');axes[1].set_ylabel('Conditional exceedance probability');axes[1].set_title('Frozen H1 tail fits tested in H2',pad=10)
    fig.legend(*axes[0].get_legend_handles_labels(),loc='upper left',bbox_to_anchor=(.13,.94),ncol=2,frameon=False,fontsize=7)
    fig.legend(*axes[1].get_legend_handles_labels(),loc='upper left',bbox_to_anchor=(.61,.94),ncol=2,frameon=False,fontsize=7)
    save(fig,'R02',[tables/'ccdf_comparison.csv',tables/'real_conditional_tail_ccdf.csv',tables/'tail_fitted_curves.csv',tables/'tail_fixed_calibration.csv'],['Zero exceedance grid points and zero lower band limits are not drawn on log axes; retained in sources.','Continuous tail likelihoods are fitted only to market data.'])
    # Temporal scaling and memory are different diagnostics.
    fig,axes=base('Held-out data | Variance scaling does not imply independent fluctuations',
        'Non-overlapping UTC aggregation; market CI: 7-day date blocks.\nSeasonal profile learned only in H1; model envelope covers three fixed rho cases.',height=4.5,top=.67)
    scaling=read(tables/'market_scaling.csv');model_scale=read(tables/'model_scaling_summary.csv')
    rr=[r for r in scaling if r['metric']=='variance_ratio' and int(r['day_block_length'])==7];x=np.array([f(r,'minutes') for r in rr]);y=np.array([f(r,'estimate') for r in rr]);lo=np.array([f(r,'ci_low') for r in rr]);hi=np.array([f(r,'ci_high') for r in rr]);axes[0].errorbar(x,y,yerr=[y-lo,hi-y],fmt='o-',color=market,capsize=3,markersize=3.5,lw=1.2,label='Market H2')
    for source,color in colors.items():
        rho=float(source.split('=')[1]);rr=sorted([r for r in model_scale if f(r,'rho')==rho and r['metric']=='variance_ratio'],key=lambda r:int(r['aggregation_bars']));x=np.array([5*f(r,'aggregation_bars') for r in rr]);y=np.array([f(r,'estimate') for r in rr]);lo=np.array([f(r,'ci_low') for r in rr]);hi=np.array([f(r,'ci_high') for r in rr]);axes[0].plot(x,y,'-',color=color,lw=.9,label=source);axes[0].fill_between(x,lo,hi,color=color,alpha=.10,lw=0)
    axes[0].axhline(1,color='#9CA4A9',ls='--',lw=.7);axes[0].set_xscale('log');axes[0].set_xticks([5,15,60,240,1440],['5','15','60','240','1440']);axes[0].set_ylim(.5,1.25);axes[0].set_xlabel('Aggregation window (minutes)');axes[0].set_ylabel('Var(sum r) / [k Var(r)]');axes[0].set_title('Second-order temporal scaling',pad=10)
    acf=read(tables/'market_acf.csv');model_acf=read(tables/'model_acf_summary.csv')
    for kind,label,color,style in [('absolute_return','Raw magnitude',market,'o-'),('season_adjusted_absolute_return','Season-adjusted','#4F927C','s--')]:
        rr=[r for r in acf if r['series']==kind and int(r['day_block_length'])==7];x=np.array([f(r,'minutes') for r in rr]);y=np.array([f(r,'estimate') for r in rr]);lo=np.array([f(r,'ci_low') for r in rr]);hi=np.array([f(r,'ci_high') for r in rr]);axes[1].plot(x,y,style,color=color,markersize=3,lw=1.2,label=label);axes[1].fill_between(x,lo,hi,color=color,alpha=.10,lw=0)
    lags=cfg['acf_lags'];low=[];high=[];means=[]
    for lag in lags:
        rr=[r for r in model_acf if r['series']=='absolute_return' and int(r['lag'])==lag];low.append(min(f(r,'ci_low') for r in rr));high.append(max(f(r,'ci_high') for r in rr));means.append(np.mean([f(r,'estimate') for r in rr]))
    axes[1].plot(np.array(lags)*5,means,'-',color='#8A9297',lw=.9,label='IID model range');axes[1].fill_between(np.array(lags)*5,low,high,color='#8A9297',alpha=.22,lw=0);axes[1].axhline(0,color='#9CA4A9',ls='--',lw=.7);axes[1].set_xscale('log');axes[1].set_xticks([5,60,240,1440],['5','60','240','1440']);axes[1].set_ylim(-.025,.45);axes[1].set_xlabel('Lag (minutes)');axes[1].set_ylabel('Magnitude autocorrelation');axes[1].set_title('Persistent amplitude memory',pad=10)
    fig.legend(*axes[0].get_legend_handles_labels(),loc='upper left',bbox_to_anchor=(.13,.93),ncol=2,frameon=False,fontsize=7)
    fig.legend(*axes[1].get_legend_handles_labels(),loc='upper left',bbox_to_anchor=(.61,.93),ncol=1,frameon=False,fontsize=7)
    save(fig,'R03',[tables/'market_scaling.csv',tables/'model_scaling_summary.csv',tables/'market_acf.csv',tables/'model_acf_summary.csv'])
    # This extra figure presents the predeclared necessary bound without hiding it in a table.
    fig,axes=base('Held-out data | Joint moments challenge the fixed action interface',
        'Market: 7-day block CI; models: 10 independent paths per condition.\nMonth points are descriptive; the bound is a population statement, not a sample guarantee.',height=4.1,left=.18,wspace=.55)
    metric=read(tables/'market_metrics.csv');row=next(r for r in metric if r['metric']=='delta' and int(r['day_block_length'])==7);value=f(row,'estimate');axes[0].errorbar(value,0,xerr=[[value-f(row,'ci_low')],[f(row,'ci_high')-value]],fmt='o',color=market,capsize=4,markersize=5,lw=1.4)
    metrics=read(tables/'model_metrics_summary.csv')
    for i,(source,color) in enumerate(colors.items(),1):
        rho=float(source.split('=')[1]);row=next(r for r in metrics if f(r,'rho')==rho and r['metric']=='delta');value=f(row,'estimate');axes[0].errorbar(value,i,xerr=[[value-f(row,'ci_low')],[f(row,'ci_high')-value]],fmt='s',color=color,capsize=3,markersize=4,lw=1.1)
    axes[0].axvspan(0,1,color='#78919C',alpha=.12,lw=0);axes[0].axvline(0,color='#9CA4A9',ls='--',lw=.7);axes[0].set_yticks(range(4),['Market H2',*colors]);axes[0].set_ylim(3.6,-.6);axes[0].set_xlim(-15,2);axes[0].set_xlabel('Unit-free joint-moment Delta');axes[0].set_title('Interface requires 0 < Delta <= 1',pad=10)
    rows=[r for r in read(tables/'joint_constraint_sensitivity.csv') if r['case']=='calendar_month'];x=np.arange(1,13);y=np.array([f(r,'delta') for r in rows]);axes[1].plot(x,y,'o-',color=market,markersize=3.5,lw=1.1);axes[1].axhline(0,color='#9CA4A9',ls='--',lw=.8);axes[1].set_xlim(.6,12.4);axes[1].set_ylim(-16,1);axes[1].set_xticks([1,3,5,7,9,11],['Jan','Mar','May','Jul','Sep','Nov']);axes[1].set_ylabel('Unit-free joint-moment Delta');axes[1].set_xlabel('2025 UTC calendar month');axes[1].set_title('Negative in each calendar month',pad=10)
    save(fig,'R04',[tables/'market_metrics.csv',tables/'model_metrics_summary.csv',tables/'joint_constraint_sensitivity.csv'],['Post-analysis figure organization; the joint constraint and monthly sensitivity were already specified.','Negative Delta challenges the fixed action/execution assumptions, not all possible herding models.'])
    (qa/'figure_sources.json').write_text(json.dumps({'run_id':args.run_id,'backend':'python','figures':catalog,'license':'Market-derived outputs CC BY-NC-SA 4.0; attribution Binance Vision; source terms snapshot retained.','full_external_QA':'pending audits and visual review'},indent=2)+'\n')
    print(out)


if __name__=='__main__':main()
