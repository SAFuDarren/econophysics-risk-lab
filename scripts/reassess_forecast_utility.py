#!/usr/bin/env python3
"""Post-analysis assessment of predictive skill; no model refit or new test data."""
from pathlib import Path
import csv
import datetime as dt
import hashlib
import json
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from econophysics.real_market_statistics import circular_day_weights
from econophysics.model import derived_seed


def main():
    old = ROOT / "results/tables/forecast_v1"
    cfg = json.loads((ROOT / "configs/forecast_v1.json").read_text())
    def read(path): return list(csv.DictReader(path.open()))
    samples = read(old/"forecast_samples.csv")
    original = read(old/"test_predictions.csv")
    fit = [r for r in samples if r["target_date"] < cfg["test_target_start"]]
    mean_log = float(np.mean([np.log(float(r["target_rv"])) for r in fit]))
    coefficients = read(old/"linear_coefficients.csv")
    assert abs(mean_log-float(coefficients[0]["target_mean"])) < 1e-12
    models = cfg["regression_models"]
    ordered = {m: sorted([r for r in original if r["model"]==m],key=lambda r:r["target_date"]) for m in models}
    days = [r["target_date"] for r in ordered[models[0]]]
    actual = np.array([float(r["actual_rv"]) for r in ordered[models[0]]])
    assert len(fit)==427 and len(days)==183
    assert max(r["target_date"] for r in fit) < min(days)
    losses = {}; scores = []
    for m in models+["FitMeanLogRV"]:
        if m == "FitMeanLogRV":
            forecast = np.full(len(days),mean_log)
        else:
            rows=ordered[m]
            assert [r["target_date"] for r in rows]==days
            assert all((dt.date.fromisoformat(r["target_date"])-dt.date.fromisoformat(r["origin_date"])).days==1 for r in rows)
            assert np.array_equal(actual,np.array([float(r["actual_rv"]) for r in rows]))
            forecast=np.array([float(r["log_prediction"]) for r in rows])
        ratio=actual/np.exp(forecast)
        losses[m]={"log_mse":(np.log(actual)-forecast)**2,
                   "qlike":ratio-np.log(ratio)-1,
                   "volatility_mae":100*np.abs(np.sqrt(actual)-np.sqrt(np.exp(forecast)))}
        for metric, values in losses[m].items():
            if m != "FitMeanLogRV":
                assert np.allclose(values,[float(r[metric]) for r in ordered[m]],rtol=1e-12,atol=1e-12)
            scores.append({"model":m,"metric":metric,"mean_loss":float(values.mean()),"days":len(days)})
    comparisons=[]
    for block in cfg["bootstrap_day_block_lengths"]:
        weights=circular_day_weights(len(days),block,cfg["bootstrap_replicates"],np.random.default_rng(derived_seed(cfg["seed"],f"forecast-block:{block}")))
        for baseline in ["FitMeanLogRV","Persistence","EWMA","HAR"]:
            for metric in ["log_mse","qlike","volatility_mae"]:
                x,y=losses["HAR+All"][metric],losses[baseline][metric]
                values=100*(1-(weights@x)/(weights@y));lo,hi=np.quantile(values,[.025,.975])
                comparisons.append({"model":"HAR+All","baseline":baseline,"metric":metric,"days":len(days),
                                    "block_days":block,"skill_pct":float(100*(1-x.mean()/y.mean())),
                                    "ci_low":float(lo),"ci_high":float(hi),
                                    "status":"Post-analysis goal reassessment; unadjusted paired block intervals, not a new confirmatory study"})
    tables=ROOT/"results/tables/predictive_utility_v1";tables.mkdir(parents=True,exist_ok=True)
    for name, rows in [("scores",scores),("contrasts",comparisons)]:
        with (tables/f"{name}.csv").open("w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    check=ROOT/"results/checks/predictive_utility_v1";check.mkdir(parents=True,exist_ok=True)
    sources=[old/"forecast_samples.csv",old/"test_predictions.csv",old/"linear_coefficients.csv",ROOT/"configs/forecast_v1.json",Path(__file__)]
    result={"status":"existing_predictive_skill_reassessed_not_new_validation","fit_days":len(fit),"test_days":len(days),
            "first_test":min(days),"last_test":max(days),"constant_log_forecast":mean_log,
            "constant_forecast_definition":"Mean log RV over the same 427 original fit targets through 2026-03-31; no final outcomes used",
            "no_model_refit":True,"no_new_market_data":True,"no_formal_equivalence_test":True,
            "skill_unit":"Loss reduction versus the named baseline, not return-direction accuracy or trading profit",
            "old_primary_incremental_test":"unchanged; no stable unique volume/physics advantage confirmed",
            "source_sha256":{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
            "primary_block_descriptive_contrasts":[r for r in comparisons if r["block_days"]==7],
            "member_scientific_review":"not_run"}
    (check/"assessment.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps([r for r in comparisons if r["block_days"]==7 and r["metric"]=="log_mse"],indent=2))


if __name__=="__main__":main()
