"""Paired forecast contrasts at the fixed primary horizon, from released tables."""
from pathlib import Path
import argparse, csv, json, sys
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parents[1]

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--qa-tools',type=Path)
    args=parser.parse_args()
    with (ROOT/'tables/v3_risk_contrasts.csv').open() as f:
        rows={r['reference']:r for r in csv.DictReader(f) if r['horizon']=='8'}
    order=['MacroGamma','PriorEnsemble','ReturnHAR','TrailingRV']
    labels={'MacroGamma':'Same-feature MacroGamma','PriorEnsemble':'Unconditional network prior',
            'ReturnHAR':'Return HAR comparator','TrailingRV':'Trailing realized variance'}
    mpl.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','Helvetica','DejaVu Sans'],
        'font.size':9,'axes.titlesize':10,'axes.labelsize':9,'xtick.labelsize':8,
        'ytick.labelsize':9,'pdf.fonttype':42,'svg.fonttype':'none',
        'axes.spines.right':False,'axes.spines.top':False,'axes.linewidth':.7})
    fig,ax=plt.subplots(figsize=(7.2,3.35))
    fig.subplots_adjust(left=.34,right=.96,bottom=.34,top=.80)
    for i,name in enumerate(order):
        r=rows[name];mean,lo,hi=[float(r[k]) for k in ['difference','ci_low','ci_high']]
        y=len(order)-1-i
        ax.errorbar(mean,y,xerr=[[mean-lo],[hi-mean]],fmt='o',markersize=5.5,
            color='#416b73' if i<3 else '#8a9299',elinewidth=1.4,capsize=3)
    ax.axvline(0,color='#687887',linewidth=.9,linestyle=(0,(3,3)),zorder=0)
    ax.set_yticks(range(4),[labels[n] for n in order[::-1]])
    ax.tick_params(axis='y',length=0,pad=10)
    ax.set_ylim(-.5,3.5);ax.set_xlim(-.105,.025)
    ax.set_xlabel('QLIKE difference: conditional ensemble minus comparator',labelpad=10)
    ax.spines['left'].set_visible(False);ax.spines['bottom'].set_color('#99a8b3')
    ax.grid(axis='x',color='#e7ecef',linewidth=.5);ax.set_axisbelow(True)
    fig.text(.035,.93,'Observable conditioning and the matched risk controls',fontsize=11,color='#173e60',weight='bold')
    fig.text(.035,.85,'Primary horizon: 8 synthetic steps; 128 independent paired test cases',fontsize=9,color='#4b5b68')
    fig.text(.035,.12,'Negative differences favour the conditional ensemble. Bars: 95% paired basic-bootstrap intervals.',fontsize=8,color='#4b5b68')
    fig.text(.035,.055,'Bank: 2,048; tuning: 32; calibration: 64. Strong-control intervals span zero.',fontsize=8,color='#4b5b68')
    out=REPO/'web/assets/figures/continuation/R_conditional_risk'
    fig.canvas.draw()
    if args.qa_tools:
        sys.path.insert(0,str(args.qa_tools))
        from audit_panel_alignment import require_matplotlib_panel_alignment
        require_matplotlib_panel_alignment(fig,json_out=str(ROOT/'checks/R_conditional_risk.alignment.json'),
            tolerance_pt=1.5,gutter_tolerance_pt=1.5,strict=True)
    else:
        (ROOT/'checks/R_conditional_risk.alignment.json').write_text(json.dumps({'status':'not applicable','reason':'Single quantitative panel.'})+'\n')
    fig.savefig(str(out)+'.svg',facecolor='white')
    fig.savefig(str(out)+'.pdf',facecolor='white')
    fig.savefig(str(out)+'.png',dpi=600,facecolor='white')
    plt.close(fig)
    print(str(out))

if __name__=='__main__':main()
