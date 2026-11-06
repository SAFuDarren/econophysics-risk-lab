"""Plot the finite simulation study and source-backed diagnostic followup."""

from pathlib import Path as _ProjectPath
import sys as _project_sys
_project_sys.path.insert(0, str(_ProjectPath(__file__).resolve().parents[1]))
from _bootstrap import ROOT as PROJECT_ROOT, script_path, resolve_recorded_path

from pathlib import Path
from collections import Counter
import argparse,csv,hashlib,json,os,sys
ROOT=PROJECT_ROOT
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.cache/matplotlib'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def read(path):
    with path.open() as f:return list(csv.DictReader(f))


def write(path,rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def empirical_ccdf(values):
    values=np.asarray(values,dtype=float)
    unique,counts=np.unique(values,return_counts=True)
    probabilities=np.cumsum(counts[::-1])[::-1]/len(values)
    mask=unique>0
    return unique[mask],probabilities[mask],int(np.sum(values==0))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id',default='simulation_study_v1')
    parser.add_argument('--followup-id',default='simulation_followup_v1')
    parser.add_argument('--figure-set',default='simulation_study_v1')
    parser.add_argument('--qa-tools',type=Path)
    args=parser.parse_args()
    for value in [args.run_id,args.followup_id,args.figure_set]:
        if not value.replace('_','').replace('-','').isalnum():parser.error('invalid ID')
    source=ROOT/'results/tables'/args.run_id;extra=ROOT/'results/tables'/args.followup_id
    out=ROOT/'figures'/args.figure_set;qa=ROOT/'results/checks'/args.run_id/'figure_qa'/args.figure_set
    if out.exists():parser.error('figure set exists; choose a new set ID')
    out.mkdir(parents=True);qa.mkdir(parents=True,exist_ok=True)
    align=None
    if args.qa_tools:
        sys.path.insert(0,str(args.qa_tools.resolve()))
        from audit_panel_alignment import require_matplotlib_panel_alignment
        align=require_matplotlib_panel_alignment
    plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['DejaVu Sans'],
                         'font.size':8,'axes.titlesize':9,'axes.labelsize':8,
                         'xtick.labelsize':8,'ytick.labelsize':8,'legend.fontsize':8,
                         'pdf.fonttype':42,'svg.fonttype':'none','axes.spines.right':False,
                         'axes.spines.top':False,'axes.linewidth':.7})
    colors=['#287DA8','#B16A35','#4F927C'];view_colors={'Return only':'#B16A35','Return + volume':'#287DA8','Volume-only control':'#4F927C'}
    exclusions=[];catalog=[]
    def base(title,footer,two=False):
        fig,axes=plt.subplots(1,2 if two else 1,figsize=(7.2047244094,3.70),layout=None)
        fig.subplots_adjust(left=.12,right=.96,top=.79,bottom=.24,wspace=.40)
        fig.suptitle(title,fontsize=10,y=.99)
        fig.text(.12,.035,footer,fontsize=8,va='bottom')
        axes=np.atleast_1d(axes)
        if two:
            for ax,letter in zip(axes,'ab'):
                ax.annotate(letter,xy=(0,1),xycoords='axes fraction',xytext=(-24,11),textcoords='offset points',fontsize=10,weight='bold')
        return fig,axes
    def save(fig,name,sources,exclude_axes=()):
        fig.canvas.draw()
        if align:
            align(fig,json_out=str(qa/f'{name}.alignment.json'),tolerance_pt=1.5,gutter_tolerance_pt=1.5,require_panel_labels=len(fig.axes)>1,strict=True,exclude_axes=exclude_axes)
        geometry={str(i):list(ax.get_window_extent().bounds) for i,ax in enumerate(fig.axes)}
        (qa/f'{name}.geometry.json').write_text(json.dumps(geometry,indent=2))
        fig.savefig(out/f'{name}.svg')
        fig.savefig(out/f'{name}.pdf')
        fig.savefig(out/f'{name}.png',dpi=300)
        plt.close(fig)
        catalog.append({'figure_id':name,'source_paths':[str(p.relative_to(ROOT)) for p in sources]})

    phase=read(source/'phase_summary.csv')
    fig,axes=base('Simulation | Collective structure changes with connectivity',
                  '40 independent graphs/cell; pointwise 95% graph-bootstrap bands.\nDashed line: ER infinite-size threshold, not a finite-sample estimate.',True)
    for n,color in zip([128,256,512],colors):
        rows=[r for r in phase if int(r['n'])==n];rho=np.array([float(r['rho']) for r in rows])
        for ax,key in zip(axes,['largest_fraction','finite_chi']):
            mean=np.array([float(r[key+'_mean']) for r in rows]);lo=np.array([float(r[key+'_ci_low']) for r in rows]);hi=np.array([float(r[key+'_ci_high']) for r in rows])
            ax.plot(rho,mean,'o-',color=color,label=f'N = {n}',markersize=3,linewidth=1)
            ax.fill_between(rho,lo,hi,color=color,alpha=.14,linewidth=0)
            ax.axvline(1,color='#7B858C',linestyle='--',linewidth=.7,zorder=0)
            ax.set_xlabel('Connectivity rho')
    axes[0].set_ylabel('Largest group / N');axes[0].set_ylim(0,1)
    axes[1].set_ylabel('Finite-cluster statistic')
    fig.legend(*axes[0].get_legend_handles_labels(),loc='upper center',bbox_to_anchor=(.55,.94),ncol=3,frameon=False)
    save(fig,'F03',[source/'phase_summary.csv'])

    clusters=read(source/'cluster_sizes.csv');density_rows=[]
    fig,axes=base('Simulation | Finite-cluster size distributions',
                  'N = 512; exclude one largest group/graph; 40 independent graphs/condition.\nDensity = clusters per node. Bands: pointwise 95% graph-bootstrap CI.')
    ax=axes[0];generator=np.random.default_rng(52532001)
    for rho,color in zip([.6,1.,1.4],colors):
        matrix=np.zeros((40,512))
        for row in clusters:
            if int(row['n'])==512 and float(row['rho'])==rho and int(row['excluded_largest'])==0:
                matrix[int(row['graph_id']),int(row['size'])-1]+=1
        density=matrix.mean(axis=0)/512
        weights=generator.multinomial(40,np.ones(40)/40,size=999)
        bootstrap=weights@matrix/(40*512);lo,hi=np.quantile(bootstrap,[.025,.975],axis=0)
        sizes=np.arange(1,513);mask=density>0;band=mask&(lo>0)
        ax.loglog(sizes[mask],density[mask],'o-',markersize=2.5,linewidth=.85,color=color,label=f'rho = {rho:.1f}')
        ax.fill_between(sizes,lo,hi,where=band,color=color,alpha=.12,linewidth=0)
        exclusions.append({'figure':'F04','rho':rho,'zero_density_sizes_not_drawn':int(np.sum(~mask)),'zero_lower_CI_not_drawn':int(np.sum(mask&~band)),'reason':'log coordinate only; complete values retained in source'})
        density_rows.extend({'n':512,'rho':rho,'size':int(s),'density':float(d),'ci_low':float(l),'ci_high':float(h),'drawn_on_log':bool(m)} for s,d,l,h,m in zip(sizes,density,lo,hi,mask))
    ax.set_xlabel('Finite cluster size');ax.set_ylabel('Cluster density');ax.legend(frameon=False,loc='upper right')
    write(source/'cluster_density_plot.csv',density_rows)
    save(fig,'F04',[source/'cluster_sizes.csv',source/'cluster_density_plot.csv'])

    series=read(source/'return_volume_series.csv');lookup={}
    for row in series:lookup.setdefault((int(row['n']),float(row['rho'])),[]).append(float(row['r']))
    probabilities=read(source/'tail_probabilities.csv');tail=read(source/'tail_diagnostics.csv')
    fig,axes=base('Simulation | Finite-support return-tail diagnostics',
                  'N = 128; T = 8192/condition; tail fit on integer net units 4...128.\nDotted: conditional finite power-law fits; GOF rejects all three specified fits.')
    ax=axes[0]
    for rho,color in zip([.6,1.,1.4],colors):
        values=np.rint(np.abs(np.array(lookup[(128,rho)]))*128/.02)
        x,ccdf,zeros=empirical_ccdf(values)
        ax.loglog(x,ccdf,color=color,linewidth=1.1,label=f'rho = {rho:.1f}')
        rows=[r for r in probabilities if float(r['rho'])==rho];mass=next(int(r['tail_count'])/int(r['total_count']) for r in tail if float(r['rho'])==rho)
        model=np.cumsum([float(r['power_probability']) for r in rows][::-1])[::-1]*mass
        ax.loglog([int(r['m']) for r in rows],model,':',color=color,linewidth=1)
        exclusions.append({'figure':'F05','rho':rho,'zeros_not_drawn':zeros,'reason':'zero retained in CCDF denominator; log x excludes zero'})
    ax.set_xlabel('Absolute net order count m');ax.set_ylabel('P(absolute net count >= m)');ax.legend(frameon=False,loc='lower left')
    save(fig,'F05',[source/'return_volume_series.csv',source/'tail_probabilities.csv',source/'tail_diagnostics.csv'])

    fig,axes=base('Simulation | Population size and sampling scale are distinct',
                  'Each base series: 8192 independent periods at rho = 1, a = 0.1.\nShape comparison only; zeros kept in denominators, omitted on log x.',True)
    scale_rows=[];variance_rows=[]
    for n,color in zip([128,256,512],colors):
        values=np.asarray(lookup[(n,1.)]);normalizer=np.std(values,ddof=1)
        x,ccdf,zeros=empirical_ccdf(np.abs(values)/normalizer)
        axes[0].loglog(x,ccdf,color=color,linewidth=1,label=f'N = {n}')
        scale_rows.extend({'family':'population','condition':n,'threshold':float(xx),'ccdf':float(yy)} for xx,yy in zip(x,ccdf))
        exclusions.append({'figure':'F06','family':'population','condition':n,'zeros_not_drawn':zeros,'reason':'zero retained in denominator; log x excludes zero'})
    values=np.asarray(lookup[(128,1.)]);sd=np.std(values,ddof=1)
    lattice=values*128/.02
    assert np.max(np.abs(lattice-np.rint(lattice)))<1e-9
    integer_orders=np.rint(lattice).astype(np.int64)
    for k,color,style in zip([1,4,16,64],colors+['#745A90'],['-','--','-.',':']):
        # Preserve exact zero cancellation; floating sums can create false 1e-18 returns.
        aggregated=integer_orders.reshape(-1,k).sum(axis=1)*(.02/128)
        x,ccdf,zeros=empirical_ccdf(np.abs(aggregated)/(np.sqrt(k)*sd))
        axes[1].loglog(x,ccdf,linestyle=style,color=color,linewidth=1,label=f'k = {k}')
        scale_rows.extend({'family':'aggregation','condition':k,'threshold':float(xx),'ccdf':float(yy)} for xx,yy in zip(x,ccdf))
        variance_rows.append({'aggregation':k,'nonoverlapping_blocks':len(aggregated),'variance_ratio_to_iid':float(np.var(aggregated,ddof=1)/(k*sd*sd))})
        exclusions.append({'figure':'F06','family':'aggregation','condition':k,'zeros_not_drawn':zeros,'reason':'exact integer net-order aggregation; zero retained in denominator, not drawn on log x'})
    for ax in axes:
        ax.set_xlabel('Absolute return / reference scale');ax.set_ylabel('CCDF');ax.legend(frameon=False,loc='lower left')
    write(source/'scale_ccdf_plot.csv',scale_rows);write(source/'aggregation_variance.csv',variance_rows)
    save(fig,'F06',[source/'return_volume_series.csv',source/'scale_ccdf_plot.csv',source/'aggregation_variance.csv'])

    metrics=read(source/'learning_metrics.csv')
    fig,axes=base('Simulation | Added volume improves the specified recovery task',
                  '84 held-out windows; bands/bars: stratified 95% bootstrap CI, one training split.\nMAE is in rho units. Learning budgets and tuning rules fixed before test evaluation.',True)
    methods=['Dummy','Ridge','RBF'];positions=np.arange(3)
    for view,offset in [('Return only',-.18),('Return + volume',.18)]:
        rows=[next(r for r in metrics if float(r['training_fraction'])==1 and r['method']==method and r['view']==view) for method in methods]
        mean=np.array([float(r['mae']) for r in rows]);lo=np.array([float(r['ci_low']) for r in rows]);hi=np.array([float(r['ci_high']) for r in rows])
        axes[0].bar(positions+offset,mean,width=.33,color=view_colors[view],label=view)
        axes[0].errorbar(positions+offset,mean,yerr=[np.maximum(0,mean-lo),np.maximum(0,hi-mean)],fmt='none',color='#343B40',capsize=2,linewidth=.7)
        for xp,m,h in zip(positions+offset,mean,hi):axes[0].text(xp,max(m,h)+.008,f'{m:.2f}',ha='center',fontsize=8)
        curve=sorted([r for r in metrics if r['method']=='RBF' and r['view']==view],key=lambda r:float(r['training_fraction']))
        tx=[int(r['training_windows']) for r in curve];my=[float(r['mae']) for r in curve]
        axes[1].plot(tx,my,'o-',color=view_colors[view],markersize=3,linewidth=1)
        axes[1].fill_between(tx,[float(r['ci_low']) for r in curve],[float(r['ci_high']) for r in curve],color=view_colors[view],alpha=.15,linewidth=0)
    axes[0].set_xticks(positions,methods);axes[0].set_ylabel('Test MAE');axes[0].set_ylim(0,.40)
    axes[1].set_xlabel('Independent training windows');axes[1].set_ylabel('RBF test MAE');axes[1].set_ylim(bottom=0)
    fig.legend(*axes[0].get_legend_handles_labels(),loc='upper center',bbox_to_anchor=(.55,.94),ncol=2,frameon=False)
    save(fig,'F10',[source/'learning_metrics.csv',source/'view_contrasts.csv'])

    stress=read(extra/'stress_control_metrics.csv');groups=read(source/'rbf_group_errors.csv')
    fig,axes=base('Simulation | Scale sensitivity is a fitted-model boundary',
                  'Stress: same 84 base test windows; volume-only control added after primary study.\nMap: joint RBF mean error, 4 windows/cell; descriptive, cell SD retained in source.',True)
    fig.subplots_adjust(right=.86,wspace=.48)
    for view,marker in [('Return only','o'),('Return + volume','s'),('Volume-only control','D')]:
        rows=[r for r in stress if r['view']==view];xx=[float(r['lambda_multiplier']) for r in rows]
        axes[0].plot(xx,[float(r['mae']) for r in rows],marker=marker,color=view_colors[view],label=view,markersize=3,linewidth=1)
        axes[0].fill_between(xx,[float(r['ci_low']) for r in rows],[float(r['ci_high']) for r in rows],color=view_colors[view],alpha=.12,linewidth=0)
    axes[0].set_xlabel('Test lambda / training lambda');axes[0].set_ylabel('Frozen RBF test MAE');axes[0].set_ylim(bottom=0)
    rhos=[.4,.6,.8,1.,1.2,1.4,1.6];activities=[.05,.1,.2]
    matrix=np.array([[1000*float(next(r['mae'] for r in groups if r['view']=='Return + volume' and float(r['rho'])==rho and float(r['a'])==a)) for rho in rhos] for a in activities])
    image=axes[1].imshow(matrix,aspect='auto',origin='lower',cmap='Blues',vmin=0,vmax=float(matrix.max()))
    axes[1].set_xticks(range(7),[f'{r:.1f}' for r in rhos]);axes[1].set_yticks(range(3),[f'{a:.2f}' for a in activities])
    axes[1].set_xlabel('Connectivity rho');axes[1].set_ylabel('Activity a')
    for i in range(3):
        for j in range(7):axes[1].text(j,i,f'{matrix[i,j]:.0f}',ha='center',va='center',color='white' if matrix[i,j]>.6*matrix.max() else '#182B37',fontsize=8)
    cax=fig.add_axes([.89,.24,.022,.55]);bar=fig.colorbar(image,cax=cax);bar.set_label('MAE x 1000',fontsize=8)
    fig.legend(*axes[0].get_legend_handles_labels(),loc='upper center',bbox_to_anchor=(.54,.94),ncol=3,frameon=False,columnspacing=1)
    save(fig,'F11',[extra/'stress_control_metrics.csv',source/'rbf_group_errors.csv'],exclude_axes=[cax])

    record={'scope':'simulation study only','figures':catalog,'log_coordinate_omissions':exclusions,
            'data_rows_removed':0,'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'matplotlib':matplotlib.__version__,'member_review':'not_run'}
    (qa/'render_record.json').write_text(json.dumps(record,indent=2)+'\n')
    print(str(out.relative_to(ROOT)))


if __name__=='__main__':main()
