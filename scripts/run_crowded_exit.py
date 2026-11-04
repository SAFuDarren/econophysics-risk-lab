#!/usr/bin/env python3
"""Run the fixed six-strategy/nine-ETF capacity feasibility scenario."""
from pathlib import Path
import argparse
import csv
import datetime as dt
import hashlib
import json
import sys
import time
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from econophysics.crowded_exit import inputs, monthly_origins, observations, capacity, evaluate, simulate


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, rows):
    if not rows:
        raise ValueError("Empty required table " + str(path))
    with Path(path).open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=ROOT)
    args = parser.parse_args()
    destination = args.output_root.resolve()
    cfg = json.loads((ROOT / "configs/crowded_exit_v1.json").read_text())
    freeze = json.loads((ROOT / "results/checks/crowded_exit_v1/before_run.json").read_text())
    for path, digest in freeze["sha256"].items():
        if sha(ROOT / path) != digest:
            raise ValueError("Frozen input or source changed: " + path)
    out = destination / "results/tables/crowded_exit_v1"
    check = destination / "results/checks/crowded_exit_v1"
    if (out / "capacities.csv").exists():
        raise SystemExit("Existing output preserved; use --output-root with a new directory.")
    out.mkdir(parents=True, exist_ok=True); check.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    dates, symbols, books, sleeves, dv, returns = inputs(ROOT, cfg)
    origins = monthly_origins(dates, cfg)
    caps, paired, source, replay, summaries = [], [], [], [], []
    h, alpha, f = cfg["horizon_sessions"], cfg["daily_participation_cap"], cfg["initial_liquidation_fraction"]
    path_rows, grid_rows = [], []
    rawbook = np.load(ROOT / "results/tables/us_equity_v1/positions.npz")
    for count, i in enumerate(origins):
        adv, vol, base_depth = observations(i, dv, returns, cfg)
        day = str(dates[i])
        for name in cfg["allocations"]:
            z = books[name][i]
            gross = float(abs(z).sum())
            unnetted = float(np.dot(rawbook[f"weights_{name}"][i], abs(sleeves[i]).sum(axis=1)))
            for j, symbol in enumerate(symbols):
                source.append({"date": day, "allocation": name, "symbol": str(symbol),
                               "net_exposure": float(z[j]), "past_adv_usd": float(adv[j]),
                               "past_daily_sigma": float(vol[j]), "base_depth_usd": float(base_depth[j]),
                               "net_gross": gross, "gross_before_netting": unnetted,
                               "netting_fraction": 1 - gross / unnetted})
            for d in cfg["depth_multipliers"]:
                depth, results = base_depth * d, {}
                for method in cfg["methods"]:
                    limit, result = capacity(z, adv, depth, cfg, method)
                    results[method] = (limit, result)
                    row = {"date": day, "year": int(day[:4]), "allocation": name, "depth_multiplier": d,
                           "method": method, "capacity_usd": limit, "final_fraction": result["q"],
                           "nav_loss_fraction": result["loss"], "fees_fraction": result["fees"] / limit,
                           "volume_load": result["volume_load"], "net_gross": gross,
                           "bottleneck": str(symbols[result["bottleneck_index"]]),
                           "feedback_active": result["active"], "iterations": result["iterations"],
                           "local_feedback_gain": result["local_gain"], "converged": result["converged"]}
                    caps.append(row)
                    if d == cfg["primary_depth_multiplier"]:
                        available = i + h < len(dates)
                        load = (result["q"] * limit * abs(z)[None, :] / h / (alpha * dv[i+1:i+h+1])).max() if available else None
                        replay.append({"date": day, "allocation": name, "method": method,
                                       "capital_usd": limit, "relative_to_volume_cap": limit / results["VolumeOnly"][0],
                                       "q": result["q"], "future_available": available,
                                       "future_max_daily_load": float(load) if available else "",
                                       "future_volume_breach": bool(load > 1 + 1e-10) if available else ""})
                av, a1, af = [results[m][0] for m in cfg["methods"]]
                paired.append({"date": day, "year": int(day[:4]), "allocation": name, "depth_multiplier": d,
                               "volume_cap_usd": av, "one_round_cap_usd": a1, "feedback_cap_usd": af,
                               "one_round_vs_volume_haircut_pct": 100 * (1 - a1 / av),
                               "feedback_vs_one_round_haircut_pct": 100 * (1 - af / a1),
                               "feedback_vs_volume_haircut_pct": 100 * (1 - af / av),
                               "feedback_active_at_capacity": results["Feedback"][1]["active"]})
            # An ordinary, conservative liquidity reference in the retrospective volume replay.
            adv_low = np.quantile(dv[i-cfg["adv_lookback"]:i], .2, axis=0)
            active = abs(z) > 1e-12
            acon = float((h * alpha * adv_low[active] / (f * abs(z[active]))).min())
            av = next(r["volume_cap_usd"] for r in paired[-3:] if r["depth_multiplier"] == 1.)
            available = i + h < len(dates)
            load = (f * acon * abs(z)[None, :] / h / (alpha * dv[i+1:i+h+1])).max() if available else None
            replay.append({"date": day, "allocation": name, "method": "ConservativeVolume",
                           "capital_usd": acon, "relative_to_volume_cap": acon / av, "q": f,
                           "future_available": available, "future_max_daily_load": float(load) if available else "",
                           "future_volume_breach": bool(load > 1 + 1e-10) if available else ""})
        if count % 40 == 0:
            print(f"Completed {count+1}/{len(origins)} month-end states.", flush=True)
    for name in cfg["allocations"]:
        for d in cfg["depth_multipliers"]:
            sub = [r for r in paired if r["allocation"] == name and r["depth_multiplier"] == d]
            effect = np.array([r["feedback_vs_one_round_haircut_pct"] for r in sub])
            summaries.append({"allocation": name, "depth_multiplier": d, "snapshots": len(sub),
                              "mean_haircut_pct": float(effect.mean()), "sd_across_states_pct": float(effect.std(ddof=1)),
                              "median_haircut_pct": float(np.median(effect)), "p95_haircut_pct": float(np.quantile(effect, .95)),
                              "max_haircut_pct": float(effect.max()), "material_snapshots": int((effect >= 10 - 1e-8).sum()),
                              "material_years": len({r["year"] for r in sub if r["feedback_vs_one_round_haircut_pct"] >= 10 - 1e-8}),
                              "active_at_capacity": sum(r["feedback_active_at_capacity"] for r in sub)})
    # A fixed, familiar stress date; never selected by observed new effect size.
    case = "2020-03-31"
    i = int(np.flatnonzero(dates == case)[0])
    adv, vol, depth = observations(i, dv, returns, cfg)
    z = books[cfg["primary_allocation"]][i]
    fixed_capital, _ = capacity(z, adv, depth, cfg, "OneRound")
    display = cfg["display_capital_grid"]
    capitals = np.geomspace(display["min_usd"], display["max_usd"], display["points"])
    for d in cfg["depth_multipliers"]:
        for method in cfg["methods"]:
            for a in capitals:
                r = evaluate(float(a), z, adv, depth*d, cfg, method)
                grid_rows.append({"date": case, "allocation": cfg["primary_allocation"], "depth_multiplier": d,
                                  "method": method, "capital_usd": float(a), "final_fraction": r["q"],
                                  "nav_loss_fraction": r["loss"], "volume_load": r["volume_load"],
                                  "volume_ok": r["volume_load"] <= 1 + 1e-10,
                                  "loss_ok": r["loss"] <= cfg["max_nav_loss"], "feasible": r["feasible"],
                                  "converged": r["converged"]})
        result = simulate(fixed_capital, z, depth*d, cfg, "Feedback", trace=True)
        for row in result["trace"]:
            path_rows.append({"date": case, "allocation": cfg["primary_allocation"], "depth_multiplier": d,
                              "capital_usd": fixed_capital, **row})
    replay_summary = []
    for name in cfg["allocations"]:
        for method in cfg["methods"] + ["ConservativeVolume"]:
            sub = [r for r in replay if r["allocation"] == name and r["method"] == method and r["future_available"]]
            replay_summary.append({"allocation": name, "method": method, "origins_with_future": len(sub),
                                   "volume_breaches": sum(r["future_volume_breach"] for r in sub),
                                   "volume_breach_fraction": float(np.mean([r["future_volume_breach"] for r in sub])),
                                   "mean_relative_capital": float(np.mean([r["relative_to_volume_cap"] for r in sub]))})
    primary = next(r for r in summaries if r["allocation"] == cfg["primary_allocation"] and r["depth_multiplier"] == 1)
    gate = {"primary_materiality_passed": primary["material_years"] >= 2,
            "primary_summary": primary, "rule": cfg["primary_materiality_gate"],
            "decision": "review_only_no_real_world_advantage_claim" if primary["material_years"] >= 2 else "stop_application_expansion_keep_course_mainline",
            "real_world_utility_validated": False, "member_scientific_review": "not_run"}
    tables = {"snapshot_inputs": source, "capacities": caps, "paired_capacity": paired, "summary_metrics": summaries,
              "case_metrics": [r for r in caps if r["date"] in cfg["case_dates"]], "volume_replay": replay,
              "volume_replay_summary": replay_summary, "capital_grid": grid_rows, "feedback_paths": path_rows}
    for name, rows in tables.items():
        write(out / f"{name}.csv", rows)
    (check / "gate.json").write_text(json.dumps(gate, ensure_ascii=False, indent=2) + "\n")
    after = {path: sha(ROOT / path) for path in freeze["sha256"]}
    if after != freeze["sha256"]:
        raise ValueError("Inputs/source mutated during run")
    record = {"batch": cfg["batch"], "status": "computed_not_member_accepted", "snapshot_count": len(origins),
              "first_snapshot": str(dates[origins[0]]), "last_snapshot": str(dates[origins[-1]]),
              "fixed_case_date": case, "runtime_seconds": time.perf_counter() - start,
              "frozen_manifest_sha256": sha(ROOT / "results/checks/crowded_exit_v1/before_run.json"),
              "randomness": "none; deterministic conditional scenarios", "gate": gate,
              "tables": {name: {"rows": len(rows), "sha256": sha(out/f"{name}.csv")} for name, rows in tables.items()}}
    (check / "run.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"states": len(origins), "tables": len(tables), "gate": gate, "seconds": record["runtime_seconds"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
