#!/usr/bin/env python3
"""Three claim-based scientific figures for the literature-informed depth study."""
from pathlib import Path
import argparse,csv,json,os,sys
ROOT=Path(__file__).resolve().parents[1]
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.cache/matplotlib'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import NullFormatter


def read(p):return list(csv.DictReader(p.open()))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--qa-tools',type=Path);parser.add_argument('--run-id',default='depth_study_v1');args=parser.parse_args()
    if not args.run_id.replace('_','').replace('-','').isalnum():parser.error('invalid run ID')
    require_matplotlib_panel_alignment=None
    if args.qa_tools:
        sys.path.insert(0,str(args.qa_tools.resolve()))
        from audit_panel_alignment import require_matplotlib_panel_alignment
    source=ROOT/'results/tables'/args.run_id;analysis=ROOT/'results/analysis'/args.run_id;out=ROOT/'figures'/args.run_id;qa=ROOT/'results/checks'/args.run_id/'figure_qa'
    out.mkdir(parents=True,exist_ok=True);qa.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['DejaVu Sans'],'font.size':8,'axes.labelsize':8,'axes.titlesize':9,'xtick.labelsize':8,'ytick.labelsize':8,'legend.fontsize':7.5,'pdf.fonttype':42,'svg.fonttype':'none','axes.spines.right':False,'axes.spines.top':False,'axes.linewidth':.7})
    methods=['RBF_return','RBF_joint','RBF_volume','RBF_shape_joint','Moment_volume']
    display={'RBF_return':'Return RBF','RBF_joint':'Joint RBF','RBF_volume':'Volume RBF','RBF_shape_joint':'Shape + volume RBF','Moment_volume':'Physics moments'}
    color=dict(zip(methods,['#929AA0','#287DA8','#4F927C','#B16A35','#7B6996']));marker=dict(zip(methods,['o','s','^','D','v']))
    def base(title,footer,left=.12,top=.78,wspace=.45,height=3.8):
        fig,axes=plt.subplots(1,2,figsize=(7.2047244094,height))
        fig.subplots_adjust(left=left,right=.975,top=top,bottom=.25,wspace=wspace)
        fig.suptitle(title,y=.99,fontsize=10)
        fig.text(left,.03,footer,fontsize=7.5,va='bottom')
        for ax,letter in zip(axes,'ab'):ax.annotate(letter,(0,1),xycoords='axes fraction',xytext=(-20,12),textcoords='offset points',fontsize=10,weight='bold')
        return fig,axes
    def save(fig,name):
        fig.canvas.draw()
        if require_matplotlib_panel_alignment:
            require_matplotlib_panel_alignment(fig,json_out=str(qa/f'{name}.alignment.json'),tolerance_pt=1.5,gutter_tolerance_pt=1.5,require_panel_labels=True,strict=True)
        else:
            (qa/f'{name}.alignment.json').write_text(json.dumps({'status':'not_run','reason':'Full alignment auditor not supplied; re-rendered figures need new alignment/text/collision/visual QA.','axes_bounds':[list(ax.get_window_extent().bounds) for ax in fig.axes]},indent=2)+'\n')
        fig.savefig(out/f'{name}.svg')
        fig.savefig(out/f'{name}.pdf')
        fig.savefig(out/f'{name}.png',dpi=600)
        plt.close(fig)
    runs=read(source/'run_metrics.csv');summary=read(analysis/'summary_metrics.csv');contrasts=read(source/'run_contrasts.csv')
    fig,axes=base('Simulation | Recovery gains depend on the baseline',
        'Points: 10 independent studies; thick bars: mean with 95% run-bootstrap CI.\nEach study: 252 train / 84 validation / 84 test windows; fixed price scale.',left=.235,wspace=.95)
    for i,method in enumerate(methods):
        vals=np.array([float(r['mae']) for r in runs if r['test_split']=='test' and float(r['lambda_multiplier'])==1 and r['method']==method]);row=next(r for r in summary if r['test_split']=='test' and float(r['lambda_multiplier'])==1 and r['method']==method)
        axes[0].scatter(vals,i+np.linspace(-.13,.13,len(vals)),s=12,color=color[method],alpha=.48,zorder=2)
        mean=float(row['mean_mae']);axes[0].errorbar(mean,i,xerr=[[mean-float(row['ci_low'])],[float(row['ci_high'])-mean]],fmt=marker[method],color=color[method],capsize=3,linewidth=1.5,markersize=5,zorder=3)
    axes[0].set_yticks(range(5),[display[m] for m in methods]);axes[0].invert_yaxis();axes[0].set_xlim(0,.062);axes[0].set_xlabel('Connectivity MAE');axes[0].set_title('Held-out parameter grid',pad=9)
    for j,(label,left,right) in enumerate([('Joint - return','RBF_joint','RBF_return'),('Joint - volume','RBF_joint','RBF_volume')]):
        a=np.array([float(r['mae']) for r in runs if r['test_split']=='test' and float(r['lambda_multiplier'])==1 and r['method']==left]);b=np.array([float(r['mae']) for r in runs if r['test_split']=='test' and float(r['lambda_multiplier'])==1 and r['method']==right]);d=a-b;row=contrasts[j]
        axes[1].scatter(d,j+np.linspace(-.10,.10,len(d)),s=12,color='#287DA8',alpha=.48)
        mean=float(row['mean_difference']);axes[1].errorbar(mean,j,xerr=[[mean-float(row['ci_low'])],[float(row['ci_high'])-mean]],fmt='s',color='#287DA8',capsize=3,linewidth=1.5,markersize=5)
    axes[1].axvline(0,color='#7B858C',linestyle='--',lw=.8);axes[1].set_yticks([0,1],['Joint - return','Joint - volume']);axes[1].set_ylim(1.6,-.6);axes[1].set_xlim(-.032,.011);axes[1].set_xlabel('Paired MAE difference');axes[1].set_title('Negative favors joint',pad=9)
    save(fig,'D01')
    fig,axes=base('Simulation | Scale invariance is a representation property',
        'Means and 95% run-bootstrap CI over 10 studies; same test windows across scales.\nShape and moment methods remove the fixed-window return scale by construction.',top=.69,wspace=.40,height=4.0)
    for ax,split,title in zip(axes,['test','unseen'],['Held-out grid','Unseen intermediate rho']):
        for j,method in enumerate(methods):
            rr=sorted([r for r in summary if r['test_split']==split and r['method']==method],key=lambda r:float(r['lambda_multiplier']));mean=np.array([float(r['mean_mae']) for r in rr]);lo=np.array([float(r['ci_low']) for r in rr]);hi=np.array([float(r['ci_high']) for r in rr]);x=np.arange(3)+(j-2)*.035
            assert np.all(mean>0) and np.all(lo>0), 'log-scale losses and interval endpoints must be positive'
            ax.errorbar(x,mean,yerr=[mean-lo,hi-mean],fmt=marker[method]+'-',color=color[method],linewidth=1.0,markersize=3.5,capsize=2,label=display[method])
        ax.set_yscale('log');ax.set_ylim(.017,.38);ax.set_yticks([.02,.05,.1,.2],['0.02','0.05','0.10','0.20']);ax.yaxis.set_minor_formatter(NullFormatter());ax.set_xticks([0,1,2],['0.5','1','2']);ax.set_xlim(-.2,2.2);ax.set_xlabel('Price-impact scale / training scale');ax.set_ylabel('Connectivity MAE');ax.set_title(title,pad=9)
    handles,labels=axes[0].get_legend_handles_labels();fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.53,.93),ncol=3,frameon=False,columnspacing=1.0,handlelength=1.8)
    save(fig,'D02')
    diagnostic=read(source/'mechanism_diagnostics.csv');null=read(source/'mechanism_null_distribution.csv')
    fig,axes=base('Simulation | Identical marginals do not fix the joint mechanism',
        '8192 iid periods/condition; 4999 volume permutations preserve both empirical marginals.\nBars: 95% period-bootstrap CI; null bars in a: central 99% permutation range.',top=.73,wspace=.42,height=4.)
    for i,row in enumerate(diagnostic):
        rho=float(row['rho']);vals=np.array([float(r['normalized_coupling']) for r in null if float(r['rho'])==rho]);lo,hi=np.quantile(vals,[.005,.995]);median=float(np.median(vals))
        axes[0].errorbar(i-.065,median,yerr=[[median-lo],[hi-median]],fmt='D',color='#929AA0',capsize=4,markersize=4,label='Permutation null' if i==0 else None)
        mean=float(row['coupling_original']);axes[0].errorbar(i+.065,mean,yerr=[[mean-float(row['coupling_ci_low'])],[float(row['coupling_ci_high'])-mean]],fmt='o',color='#287DA8',capsize=3,markersize=4,label='Original pairs' if i==0 else None)
        for shift,key,low,high,c,m,label in [(-.065,'constraint_original','constraint_ci_low','constraint_ci_high','#287DA8','o','Original pairs'),(.065,'constraint_surrogate','surrogate_constraint_ci_low','surrogate_constraint_ci_high','#B16A35','D','One matched surrogate')]:
            value=float(row[key]);axes[1].errorbar(i+shift,value,yerr=[[value-float(row[low])],[float(row[high])-value]],fmt=m,color=c,capsize=3,markersize=4,label=label if i==0 else None)
    for ax in axes:ax.axhline(0,color='#7B858C',linestyle='--',lw=.8);ax.set_xticks(range(3),['0.6','1.0','1.4']);ax.set_xlabel('Connectivity rho');ax.set_xlim(-.35,2.35)
    axes[0].set_ylabel('Normalized squared-return / volume coupling');axes[0].set_title('Joint information beyond marginals',pad=9);axes[0].legend(frameon=False,loc='upper left',fontsize=7)
    axes[1].set_ylabel('Joint-moment residual Z');axes[1].set_title('Action-interface constraint: Z = 0',pad=9);axes[1].legend(frameon=False,loc='upper left',fontsize=7)
    axes[0].set_ylim(-.025,.47);axes[1].set_ylim(-.012,.285)
    save(fig,'D03')
    (qa/'render_contract.json').write_text(json.dumps({'backend':'python','figure_ids':['D01','D02','D03'],'status':'rendered; external PDF text/collision and visual checks pending','raw_rows_excluded':0,'aggregation':'all replications and all specified conditions; source tables retained'},indent=2)+'\n')
    print(out)


if __name__=='__main__':main()
