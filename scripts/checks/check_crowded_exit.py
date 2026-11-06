#!/usr/bin/env python3
"""Independent ledger quadrature and scenario/capacity checks, not market validation."""

from pathlib import Path as _ProjectPath
import sys as _project_sys
_project_sys.path.insert(0, str(_ProjectPath(__file__).resolve().parents[1]))
from _bootstrap import ROOT as PROJECT_ROOT, script_path, resolve_recorded_path
from publication_integrity import matches_recorded_digest
from pathlib import Path
import copy
import csv
import hashlib
import json
import sys
import numpy as np
from scipy.integrate import quad

ROOT = PROJECT_ROOT
sys.path.insert(0, str(ROOT / "src"))
from econophysics.crowded_exit import state, simulate, capacity, volume_capacity, inputs, observations


def main():
    cfg = json.loads((ROOT / "configs/crowded_exit_v1.json").read_text())
    out = ROOT / "results/checks/crowded_exit_v1"
    checks = []
    def test(name, condition):
        checks.append({"check": name, "status": "pass" if bool(condition) else "fail"})
    manifest = json.loads((out / "before_run.json").read_text())
    for path, digest in manifest["sha256"].items():
        test("Frozen input/source " + path, matches_recorded_digest(ROOT / path, digest, ROOT))
    rng = np.random.default_rng(2026102721)
    for n in range(32):
        z = rng.normal(size=9); z *= rng.uniform(.3, 1.2) / abs(z).sum()
        capital = float(10**rng.uniform(3, 8)); depth = 10**rng.uniform(7, 10, size=9); q = rng.uniform(0, 1)
        actual = state(capital, z, depth, q, cfg)
        x = capital*z
        cash = capital - x.sum()
        for xi, di in zip(x, depth):
            received = quad(lambda v: xi*np.exp(-xi*v/di), 0, q, epsabs=1e-8)[0]
            fee = quad(lambda v: cfg["fee_bps"]/1e4*abs(xi)*np.exp(-xi*v/di), 0, q, epsabs=1e-8)[0]
            cash += received - fee
        terminal = cash + sum((1-q)*xi*np.exp(-xi*q/di) for xi, di in zip(x, depth))
        test(f"Independent signed cash quadrature {n}", abs(actual["equity"]-terminal) < capital*2e-12)
        test(f"Independent NAV loss {n}", abs(actual["loss"]-(1-terminal/capital)) < 3e-12)
        zero = state(capital, z, depth, 0., cfg)
        test(f"No trade preserves NAV {n}", zero["loss"] == 0 and abs(zero["equity"]-capital) < capital*1e-12)
        noimpact = state(capital, z, depth, q, cfg, impact=False)
        test(f"No impact only exact fees {n}", abs(noimpact["loss"]-cfg["fee_bps"]/1e4*q*abs(z).sum()) < 1e-14)
        eps = 1e-6
        numerical = (state(capital,z,depth,q+eps,cfg)["loss"]-state(capital,z,depth,q-eps,cfg)["loss"])/(2*eps)
        test(f"Local derivative agrees with finite difference {n}", abs(numerical-actual["gain_slope"]) < 1e-8)
        test(f"Fixed-fraction loss monotone in capital {n}", state(capital*1.01,z,depth,q,cfg)["loss"] >= state(capital*.99,z,depth,q,cfg)["loss"]-1e-13)
        disabled = copy.deepcopy(cfg); disabled["feedback_slope"] = 0
        a = simulate(capital,z,depth,disabled,"Feedback")
        b = simulate(capital,z,depth,disabled,"OneRound")
        test(f"Disabled feedback exactly equals one round {n}", a["q"] == b["q"] and a["loss"] == b["loss"])
    z = np.array([1., -1.]) / 2
    a = state(1e6,z,np.array([1e7,1e7]),.25,cfg)
    test("Long sale down, short covering up", a["prices"][0] < 1 < a["prices"][1] and a["loss"] > 0)
    a = state(1e6,np.array([0.]),np.array([1e7]),.5,cfg)
    test("Opposite sleeve positions net to no impact or cost", a["loss"] == 0)
    # Synthetic canary only: proves the feedback code is live; not market evidence.
    z, adv, depth = np.array([1.]), np.array([1e6]), np.array([5e6])
    av = volume_capacity(z,adv,cfg)
    a1,r1 = capacity(z,adv,depth,cfg,"OneRound")
    af,rf = capacity(z,adv,depth,cfg,"Feedback")
    test("Synthetic feedback canary activates and tightens capacity", af < a1 < av and rf["q"] > cfg["initial_liquidation_fraction"])
    test("Canary feedback does not reset total volume budget", rf["q"]*af/(cfg["horizon_sessions"]*cfg["daily_participation_cap"]*adv[0]) == rf["volume_load"])
    test("Canary capacity reaches a volume or common loss boundary", abs(rf["volume_load"]-1) < 1e-8 or abs(rf["loss"]-cfg["max_nav_loss"]) < 1e-8)
    for method, capital in [("OneRound",a1),("Feedback",af)]:
        from econophysics.crowded_exit import evaluate
        test("Canary capacity bracket "+method, evaluate(capital*(1-1e-6),z,adv,depth,cfg,method)["feasible"]
             and not evaluate(capital*(1+1e-6),z,adv,depth,cfg,method)["feasible"])
    p = ROOT / "results/tables/crowded_exit_v1"
    rows = list(csv.DictReader((p/"capacities.csv").open()))
    pairs = list(csv.DictReader((p/"paired_capacity.csv").open()))
    test("Complete three methods x four books x three depths x 190 states", len(rows)==6840 and len(pairs)==2280)
    test("All saved capacity states converge and satisfy volume/loss constraints", all(r["converged"]=="True" and float(r["volume_load"])<=1+2e-10 and float(r["nav_loss_fraction"])<=cfg["max_nav_loss"]+2e-12 for r in rows))
    test("Nested capacity sets", all(float(r["feedback_cap_usd"])<=float(r["one_round_cap_usd"])*(1+1e-10)<=float(r["volume_cap_usd"])*(1+2e-10) for r in pairs))
    # Independent sufficient condition: the initial trade cannot activate feedback anywhere below volume capacity.
    ones = [r for r in rows if r["method"]=="OneRound"]
    test("All initial losses below fixed response buffer", max(float(r["nav_loss_fraction"]) for r in ones) < cfg["loss_buffer"])
    dates,symbols,books,sleeves,dv,returns = inputs(ROOT,cfg)
    for day in cfg["case_dates"]:
        i=int(np.flatnonzero(dates==day)[0]);adv,vol,depth=observations(i,dv,returns,cfg)
        expected=dv[i-20:i].sum(axis=0)/20
        test("Strictly preceding ADV "+day,np.allclose(adv,expected,atol=1e-7))
        for name in cfg["allocations"]:
            z=books[name][i];a=volume_capacity(z,adv,cfg)
            test("Analytic volume ceiling "+day+name,abs(max(cfg["initial_liquidation_fraction"]*a*abs(z)/(cfg["horizon_sessions"]*cfg["daily_participation_cap"]*adv))-1)<1e-12)
    replay=list(csv.DictReader((p/"volume_replay.csv").open()))
    test("Missing final future volume retained as censored", sum(r["future_available"]=="False" for r in replay)==16 and all(r["future_max_daily_load"]==r["future_volume_breach"]=="" for r in replay if r["future_available"]=="False"))
    test("Replay future windows have 189 dates per book/method", len([r for r in replay if r["future_available"]=="True"])==189*4*4)
    gate=json.loads((out/"gate.json").read_text())
    test("Failed gate records stop without market-advantage claim", gate["decision"]=="stop_application_expansion_keep_research_mainline" and gate["real_world_utility_validated"] is False)
    result={"status":"pass" if all(c["status"]=="pass" for c in checks) else "fail",
            "scope":"Implementation, frozen design, signed ledger and arithmetic. Synthetic canary is not an application result; no market impact validation.",
            "checks":checks,"synthetic_canary":{"volume_cap":av,"one_round_cap":a1,"feedback_cap":af,"feedback_q":rf["q"]}}
    (out/"method_checks.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(f"Crowded-exit method checks: {result['status']}; {len(checks)} checks.")
    for row in checks:
        if row["status"]=="fail": print(row)
    raise SystemExit(0 if result["status"]=="pass" else 1)


if __name__ == "__main__":
    main()
