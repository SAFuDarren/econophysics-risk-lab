#!/usr/bin/env python3
"""Conceptual bridge and source-bound skill comparison; no refit or new experiment.

10.5-inch research figure canvas; PDF/SVG editable, PNG is a preview.
"""

from pathlib import Path as _ProjectPath
import sys as _project_sys
_project_sys.path.insert(0, str(_ProjectPath(__file__).resolve().parents[1]))
from _bootstrap import ROOT as PROJECT_ROOT, script_path, resolve_recorded_path
from pathlib import Path
import csv
import json
import os
import sys

ROOT = PROJECT_ROOT
os.environ.setdefault("MPLCONFIGDIR",str(ROOT/".cache/matplotlib"))
sys.path.insert(0,str(ROOT/"scripts/figure_audit"))
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from audit_panel_alignment import require_matplotlib_panel_alignment

BLUE, TEAL, GOLD, GRAY, INK = "#24647D", "#3D8274", "#AF873F", "#89969F", "#263D49"


def main():
    out=ROOT/"figures/project_mainline_v2";qa=ROOT/"results/checks/project_mainline_v2/figure_qa"
    out.mkdir(parents=True,exist_ok=True);qa.mkdir(parents=True,exist_ok=True);registry=[]
    plt.rcParams.update({"font.family":"sans-serif","font.sans-serif":["DejaVu Sans"],"font.size":9.5,
                         "axes.labelsize":10,"axes.titlesize":11,"xtick.labelsize":9,"ytick.labelsize":9,
                         "legend.fontsize":9,"axes.spines.top":False,"axes.spines.right":False,
                         "pdf.fonttype":42,"svg.fonttype":"none"})
    def save(fig,name,kind,sources,interpretation,labels=False):
        fig.canvas.draw()
        require_matplotlib_panel_alignment(fig,json_out=str(qa/f"{name}.alignment.json"),
                                          strict=True,tolerance_pt=1.5,gutter_tolerance_pt=1.5,require_panel_labels=labels)
        fig.savefig(out/f"{name}.pdf");fig.savefig(out/f"{name}.svg");fig.savefig(out/f"{name}.png",dpi=300)
        plt.close(fig)
        registry.append({"id":name,"evidence_type":kind,"sources":sources,"interpretation":interpretation,
                         "outputs":[f"figures/project_mainline_v2/{name}.{ext}" for ext in ["png","pdf","svg"]],
                         "caption":"results/analysis/project_mainline_v2/figure-catalog.md","member_scientific_review":"not_run"})
    # A conceptual map: the rows deliberately have no causal arrow from ER to HAR coefficients.
    fig,ax=plt.subplots(figsize=(10.5,6.4));fig.subplots_adjust(left=.035,right=.965,bottom=.12,top=.86)
    fig.suptitle("How the physics study connects to forecasting",y=.98,fontsize=15,fontweight="bold",color=INK)
    ax.set(xlim=(0,1),ylim=(0,1));ax.set_axis_off()
    xs=[.025,.365,.705];width=.27;height=.235
    def box(x,y,title,body,color,fill):
        patch=FancyBboxPatch((x,y),width,height,boxstyle="round,pad=0.012,rounding_size=0.014",lw=.9,edgecolor=color,facecolor=fill)
        ax.add_patch(patch)
        ax.text(x+width/2,y+height-.045,title,ha="center",va="center",fontsize=10.5,fontweight="bold",color=color)
        ax.text(x+width/2,y+.085,body,ha="center",va="center",fontsize=9.0,color=INK,linespacing=1.65)
    ax.text(.025,.965,"PHYSICS / MECHANISM",fontsize=10.5,fontweight="bold",color=BLUE)
    ax.text(.025,.345,"OBSERVATIONS / APPLICATION",fontsize=10.5,fontweight="bold",color=TEAL)
    top=[("Coordination model","ER groups and shared actions\nFixed activity and response\nFinite-size percolation"),
         ("Observable hypotheses","Cluster moments S2 and S3\nVariance, activity and joint moments\nTail and scaling conditions"),
         ("Mechanism tests","Conditional parameter recovery\nObservational equivalence\nReal-data compatibility")]
    bottom=[("Past market observations","1 / 7 / 28-day volatility\nActivity and coupling\nTail concentration"),
            ("Classical forecasting","Ridge regression for next-day log RV\nFeatures available at the origin\nNo latent-network labels"),
            ("Historical evaluation","183 BTCUSDT target days\nConstant, persistence and EWMA\nStrong HAR comparison")]
    for x,(title,body) in zip(xs,top):box(x,.655,title,body,BLUE,"#EDF3F6")
    for x,(title,body) in zip(xs,bottom):box(x,.055,title,body,TEAL,"#EEF5F1")
    for y in [.7725,.1725]:
        for x in xs[:-1]:
            ax.annotate("",xy=(x+.34-.018,y),xytext=(x+width+.018,y),arrowprops={"arrowstyle":"->","lw":1.1,"color":INK})
    ax.text(.5,.51,"Link: observable statistics, empirical checks and temporal dependence",ha="center",va="center",fontsize=10.5,fontweight="bold",color=INK)
    ax.text(.5,.435,"Static independent ER draws do not provide a time-varying forecast.\nForecast skill does not establish a unique herding mechanism.",ha="center",va="center",fontsize=9.5,linespacing=1.6,color=INK)
    fig.text(.06,.035,"CONCEPTUAL MAP | Physics supplies testable relations and representation hypotheses.\nThe forecaster uses observed time series; no true market rho is inferred or supplied as a label.",fontsize=8.8,color=INK,linespacing=1.6)
    save(fig,"J01_link","CONCEPTUAL",["docs/PROJECT_MAINLINE_v2.md","docs/AB/METHODS_FORMULAE_v2.md","src/econophysics/forecasting.py"],"两部分通过可观测统计与检验逻辑相连，不能把预测技能解释成已识别羊群因果路径。")
    # Original point predictions and post-analysis intervals are reused without modifying their outcomes.
    def read(name):return list(csv.DictReader((ROOT/f"results/tables/predictive_utility_v1/{name}.csv").open()))
    scores,contrasts=read("scores"),read("contrasts")
    fig,axes=plt.subplots(1,2,figsize=(10.5,6.0));fig.subplots_adjust(left=.18,right=.965,bottom=.23,top=.78,wspace=.52)
    fig.suptitle("Historical forecast skill and added-feature evidence are different",y=.98,fontsize=14,fontweight="bold",color=INK)
    for ax,label in zip(axes,"ab"):
        ax.annotate(label,(0,1),xycoords="axes fraction",xytext=(-24,16),textcoords="offset points",fontsize=12,fontweight="bold")
        ax.set_axisbelow(True)
    methods=["FitMeanLogRV","Persistence","EWMA","HAR","HAR+All"]
    labels=["Fit-period mean","Persistence","EWMA","HAR","HAR + All"]
    for i,m in enumerate(methods):
        row=next(r for r in scores if r["model"]==m and r["metric"]=="log_mse");value=float(row["mean_loss"])
        color=BLUE if m=="HAR+All" else GRAY
        axes[0].plot(value,4-i,"o",color=color,ms=6)
        axes[0].text(value+.018,4-i,f"{value:.3f}",va="center",fontsize=9,color=INK)
    axes[0].set(yticks=range(5),yticklabels=labels[::-1],ylim=(-.5,4.5),xlim=(0,.94),
                xlabel="Mean squared error of log RV",title="Point losses · lower is better")
    # Numerical labels are directly readable without vertical rules crossing them.
    bases=methods[:4]
    for i,b in enumerate(bases):
        row=next(r for r in contrasts if r["baseline"]==b and r["metric"]=="log_mse" and r["block_days"]=="7")
        mid,lo,hi=[float(row[k]) for k in ["skill_pct","ci_low","ci_high"]]
        assert lo<=mid<=hi
        axes[1].errorbar(mid,3-i,xerr=[[mid-lo],[hi-mid]],fmt="o",color=GOLD if b=="HAR" else BLUE,capsize=3,lw=1.4,ms=5.5)
    axes[1].axvline(0,color=INK,lw=.8)
    axes[1].set(yticks=range(4),yticklabels=labels[:4][::-1],ylim=(-.5,3.5),xlim=(-5,55),
                xlabel="HAR + All loss reduction (%)",title="Skill depends on the named reference")
    axes[1].grid(axis="x",color="#E4EBEF",lw=.7)
    fig.text(.18,.035,"REAL DATA | 183 BTCUSDT days, Apr–Sep 2026. Original forecasts unchanged; constant uses the original fit mean.\nRight: 4,999 paired circular 7-day block, unadjusted 95% intervals from post-analysis reassessment.\nHAR already improves on persistence by 29.61%; total skill is not a herding or volume attribution.",fontsize=8.5,color=INK,linespacing=1.6)
    save(fig,"J02_forecast_skill","REAL_DATA",["results/tables/predictive_utility_v1/scores.csv","results/tables/predictive_utility_v1/contrasts.csv","results/tables/forecast_v1/regression_contrasts.csv"],"整体流程具有历史预测技能，但相对HAR的新增证据不足；强弱参照同页且不混淆归因。",labels=True)
    (out/"registry.json").write_text(json.dumps({"batch":"project_mainline_v2","backend":"Python/matplotlib","new_training":False,"figures":registry},ensure_ascii=False,indent=2)+'\n')
    print("Exported J01 conceptual bridge and J02 prediction comparison in PNG/PDF/SVG.")


if __name__=="__main__":main()
