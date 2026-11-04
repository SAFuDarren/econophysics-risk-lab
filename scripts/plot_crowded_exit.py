#!/usr/bin/env python3
"""Three evidence figures for the fixed capacity feasibility experiment.

Slide/report canvas; conditional model results, not execution validation.
"""
from pathlib import Path
import csv
import datetime as dt
import json
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".cache/matplotlib"))
sys.path.insert(0, str(ROOT / "scripts/figure_audit"))
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from audit_panel_alignment import require_matplotlib_panel_alignment

BLUE, TEAL, GRAY, INK, GOLD = "#24647D", "#3D8274", "#89969F", "#263D49", "#AF873F"


def read(name):
    return list(csv.DictReader((ROOT / f"results/tables/crowded_exit_v1/{name}.csv").open()))


def main():
    out = ROOT / "figures/crowded_exit_v1"
    qa = ROOT / "results/checks/crowded_exit_v1/figure_qa"
    out.mkdir(parents=True, exist_ok=True); qa.mkdir(parents=True, exist_ok=True)
    registry = []
    plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["DejaVu Sans"],
                         "font.size": 9.5, "axes.labelsize": 10, "axes.titlesize": 11,
                         "xtick.labelsize": 9, "ytick.labelsize": 9, "legend.fontsize": 8.5,
                         "axes.spines.right": False, "axes.spines.top": False,
                         "axes.linewidth": .7, "pdf.fonttype": 42, "svg.fonttype": "none"})
    def panels(title, left=.12, wspace=.43):
        fig, axes = plt.subplots(1, 2, figsize=(10.5, 6.0))
        fig.subplots_adjust(left=left, right=.97, bottom=.23, top=.77, wspace=wspace)
        fig.suptitle(title, y=.98, fontsize=14, fontweight="bold", color=INK)
        for ax, label in zip(axes, "ab"):
            ax.annotate(label, (0, 1), xycoords="axes fraction", xytext=(-24, 16), textcoords="offset points", fontsize=12, fontweight="bold")
            ax.set_axisbelow(True)
        return fig, axes
    def foot(fig, text, left=.12):
        fig.text(left, .035, text, fontsize=8.7, color=INK, va="bottom", linespacing=1.6)
    def save(fig, identifier, sources, interpretation, notes, panels_required=True):
        fig.canvas.draw()
        require_matplotlib_panel_alignment(fig, json_out=str(qa/f"{identifier}.alignment.json"),
                                          strict=True, tolerance_pt=1.5, gutter_tolerance_pt=1.5,
                                          require_panel_labels=panels_required)
        fig.savefig(out/f"{identifier}.pdf")
        fig.savefig(out/f"{identifier}.svg")
        fig.savefig(out/f"{identifier}.png", dpi=300)
        plt.close(fig)
        registry.append({"id": identifier, "sources": [f"results/tables/crowded_exit_v1/{s}.csv" for s in sources],
                         "interpretation": interpretation, "notes": notes, "formats": ["pdf", "svg", "png"],
                         "member_scientific_review": "not_run", "evidence": "real-input-conditioned scenario or retrospective volume proxy"})
    pairs, summary, caps = read("paired_capacity"), read("summary_metrics"), read("capacities")
    primary = [r for r in pairs if r["allocation"] == "Equal" and r["depth_multiplier"] == "1.0"]
    dates = [dt.datetime.fromisoformat(r["date"]) for r in primary]
    fig, ax = panels("Fixed-scenario result: feedback adds no capacity constraint")
    for field, label, color, ls, lw in [("volume_cap_usd", "Volume only", GRAY, "-", 3.5),
                                       ("one_round_cap_usd", "One round", TEAL, "--", 2.3),
                                       ("feedback_cap_usd", "Feedback", BLUE, ":", 1.6)]:
        ax[0].plot(dates, [float(r[field])/1e9 for r in primary], color=color, ls=ls, lw=lw, label=label)
    ax[0].set(xlabel="Month-end state", ylabel="Reference capital ceiling (USD bn)", title="Equal allocation · primary market depth")
    ax[0].xaxis.set_major_locator(mdates.YearLocator(5)); ax[0].xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax[0].text(.03, .94, "All three curves coincide", transform=ax[0].transAxes, va="top", color=INK, fontsize=9)
    fig.legend(*ax[0].get_legend_handles_labels(), loc="upper center", bbox_to_anchor=(.33, .89), ncol=3, frameon=False)
    names = ["Equal", "InverseVol", "LW-MinVariance", "HRP"]
    for d, off, color, marker in [(.5, -.15, BLUE, "^"), (1., 0., GOLD, "o"), (2., .15, GRAY, "s")]:
        ys, vals = [], []
        for i, name in enumerate(names):
            row = next(r for r in summary if r["allocation"] == name and float(r["depth_multiplier"]) == d)
            ys.append(3-i+off); vals.append(float(row["max_haircut_pct"]))
        ax[1].scatter(vals, ys, color=color, marker=marker, s=32, label=f"Depth {d:g}", zorder=3)
    ax[1].axvline(10, ls="--", color=GRAY, lw=1)
    ax[1].set(yticks=range(4), yticklabels=names[::-1], ylim=(-.45, 3.45), xlim=(-.5, 11), xticks=[0,5,10],
              xlabel="Maximum feedback capacity haircut (%)", title="All allocations and fixed depth sensitivities")
    ax[1].grid(axis="x", color="#E4EBEF", lw=.7)
    fig.legend(*ax[1].get_legend_handles_labels(), loc="upper center", bbox_to_anchor=(.80,.89), ncol=3, frameon=False)
    foot(fig, "CONDITIONAL SCENARIOS: 190 states × 4 allocations × 3 depth levels; three methods per state.\nPaired reductions are exactly zero; dashed line: the fixed 10% materiality threshold. No statistical error bars.\n2011–2026, last available monthly close; October 2026 is partial. Historical inputs already inspected.")
    save(fig,"C01_capacity",["paired_capacity","summary_metrics"],"三种容量界重合，所有配置/深度的反馈增量为零。","均为条件模型资本界，不是实际资金部署建议；全部190状态保留。")
    # The mechanism panel shows all scenarios, not a selected stress illustration.
    rows = []
    labels = []
    all_dates = [r["date"] for r in primary]
    for name in names:
        for d in [.5,1.,2.]:
            lookup = {r["date"]:100*float(r["nav_loss_fraction"]) for r in caps
                      if r["method"]=="OneRound" and r["allocation"]==name and float(r["depth_multiplier"])==d}
            rows.append([lookup[t] for t in all_dates]); labels.append(f"{name} · {d:g}")
    matrix = np.array(rows)
    fig, axis = plt.subplots(figsize=(10.5,6.0)); fig.subplots_adjust(left=.22,right=.86,bottom=.23,top=.79)
    fig.suptitle("Why feedback stays inactive: losses remain below the trigger",y=.98,fontsize=14,fontweight="bold",color=INK)
    im = axis.imshow(matrix, aspect="auto", interpolation="nearest", cmap="Blues", vmin=0, vmax=2)
    axis.set(yticks=range(12), yticklabels=labels, ylabel="Allocation · market-depth multiplier")
    ticks = [i for i,d in enumerate(all_dates) if d[:4] in ["2011","2014","2017","2020","2023","2026"] and d[5:7]=="01"]
    axis.set_xticks(ticks); axis.set_xticklabels([all_dates[i][:4] for i in ticks]); axis.set_xlabel("Month-end state")
    for y in [2.5,5.5,8.5]: axis.axhline(y,color="white",lw=1.6)
    cb = fig.colorbar(im, ax=axis, fraction=.035, pad=.035, ticks=[0,.5,1,1.5,2])
    cb.set_label("One-round NAV loss at volume ceiling (%)",labelpad=8)
    axis.set_title(f"Maximum over all 2,280 scenarios: {matrix.max():.3f}%   |   Fixed trigger: 2.000%",fontsize=11,pad=13)
    foot(fig,"Model condition: loss is monotone in capital. Below-trigger loss at the volume ceiling implies no activation below it.\nFull 190 × 12 grid; depth levels are scenarios, not confidence bounds. No exogenous price shock or outside-fund flow.\nImpact and risk-control parameters are fixed assumptions; this is not an empirical market-safety certificate.",left=.12)
    save(fig,"C02_activation",["capacities"],"成交量上界内的自冲击损失不足触发2%反馈，解释零容量增量。","12×190完整状态矩阵；深度不是概率区间；色标上界为预设触发值，不截断数据。",panels_required=False)
    # Retrospective volume proxy: disclose the cost in capital, rather than claim a free improvement.
    replay_summary = read("volume_replay_summary")
    replay = [r for r in read("volume_replay") if r["allocation"]=="Equal" and r["future_available"]=="True"]
    base = next(r for r in replay_summary if r["allocation"]=="Equal" and r["method"]=="VolumeOnly")
    low = next(r for r in replay_summary if r["allocation"]=="Equal" and r["method"]=="ConservativeVolume")
    fig, ax = panels("In this replay, ordinary volume buffers change the trade-off",left=.19,wspace=.46)
    for y,row,color in [(1,base,GRAY),(0,low,TEAL)]:
        rate=100*float(row["volume_breach_fraction"])
        ax[0].hlines(y,0,rate,color=color,lw=2); ax[0].plot(rate,y,"o",color=color,ms=7)
        ax[0].text(3,y+.17,f"{rate:.1f}%  ({row['volume_breaches']}/{row['origins_with_future']})",color=INK,fontsize=10)
    ax[0].set(yticks=[0,1],yticklabels=["Past 20%\nvolume quantile","Mean ADV\n(all 3 models)"],ylim=(-.45,1.5),xlim=(0,100),
              xlabel="Origins exceeding the daily volume proxy (%)",title="Next 3 sessions · 189 retrospective origins")
    ax[0].grid(False)
    sub=[r for r in replay if r["method"]=="ConservativeVolume"]
    dts=[dt.datetime.fromisoformat(r["date"]) for r in sub]
    ax[1].plot(dts,np.ones(len(sub)),color=GRAY,lw=1.5,label="Mean ADV")
    ax[1].plot(dts,[float(r["relative_to_volume_cap"]) for r in sub],color=TEAL,lw=1.3,label="Past 20% quantile")
    ax[1].set(ylim=(0,1.07),ylabel="Capital / mean-ADV ceiling",xlabel="Month-end state",title=f"Conservative funding: mean {100*float(low['mean_relative_capital']):.1f}%")
    ax[1].xaxis.set_major_locator(mdates.YearLocator(5)); ax[1].xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    fig.legend(*ax[1].get_legend_handles_labels(),loc="upper center",bbox_to_anchor=(.80,.89),ncol=2,frameon=False)
    foot(fig,"RETROSPECTIVE VOLUME PROXY: equal-speed exits at each model's maximum indicated funding, with a 10% daily cap.\nA simple volume buffer lowers observed breaches but deploys less capital. It is not a tested optimal rule or physics gain.\n189 origins have 3 future sessions; one final origin is censored. No execution, slippage or impact validation.",left=.12)
    save(fig,"C03_volume_replay",["volume_replay_summary","volume_replay"],"简单成交量保守基线改变超限与资金利用的取舍，反馈未增加任何边界差异。","189截面为历史重放，非独立盲测；超限是成交额代理，不是真实订单失败。")
    (out/"registry.json").write_text(json.dumps({"batch":"crowded_exit_v1","backend":"Python/matplotlib","canvas_width_in":10.5,"figures":registry},ensure_ascii=False,indent=2)+'\n')
    print('Exported three figures in PNG, PDF and SVG; render-time alignment recorded.')


if __name__ == "__main__":
    main()
