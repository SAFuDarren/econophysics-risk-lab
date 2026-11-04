"""Fixed, centrally netted liquidation scenario; no empirical impact calibration."""
from pathlib import Path
import csv
import numpy as np


def inputs(root, cfg):
    root = Path(root)
    data = []
    for part in ["historical", "confirmation"]:
        data.extend(csv.DictReader((root / f"data/processed/us_equity_v1/{part}.csv").open()))
    lookup = {(r["date"], r["symbol"]): r for r in data}
    if len(lookup) != len(data):
        raise ValueError("Duplicate market cells")
    book = np.load(root / "results/tables/us_equity_v1/positions.npz")
    dates, symbols = book["dates"].astype(str), book["symbols"].astype(str)
    adj = np.array([[float(lookup[d, s]["adjusted_close"]) for s in symbols] for d in dates])
    # The original research unit is a normalized total-return-index unit.
    index = adj / adj[0]
    dv = np.array([[float(lookup[d, s]["close"]) * float(lookup[d, s]["volume"])
                    for s in symbols] for d in dates])
    returns = adj[1:] / adj[:-1] - 1
    returns = np.vstack([np.full((1, 9), np.nan), returns])
    exposures = {name: book[f"units_{name}"] * index for name in cfg["allocations"]}
    sleeves = book["strategy_units"] * index[:, None, :]
    for name in cfg["allocations"]:
        reconstructed = np.einsum("ts,tsi->ti", book[f"weights_{name}"], sleeves)
        if not np.allclose(reconstructed, exposures[name], atol=2e-12):
            raise ValueError("Saved strategy aggregation mismatch: " + name)
    if not (np.isfinite(dv).all() and (dv > 0).all()):
        raise ValueError("Invalid dollar-volume inputs")
    return dates, symbols, exposures, sleeves, dv, returns


def monthly_origins(dates, cfg):
    return [i for i, d in enumerate(dates)
            if d >= cfg["history_start"] and
            (i + 1 == len(dates) or dates[i + 1][:7] != d[:7])]


def observations(i, dv, returns, cfg):
    adv = dv[i - cfg["adv_lookback"]:i].mean(axis=0)
    vol = np.std(returns[i - cfg["volatility_lookback"]:i], axis=0, ddof=1)
    if not ((adv > 0).all() and (vol > 0).all() and np.isfinite(vol).all()):
        raise ValueError("Invalid strictly preceding information window")
    depth = cfg["market_depth_c"] * adv / vol * np.sqrt(cfg["horizon_sessions"])
    return adv, vol, depth


def state(capital, weights, depth, q, cfg, impact=True):
    """Continuous-fill cash ledger along the fixed cumulative impact curve."""
    z = np.asarray(weights, dtype=float)
    x = capital * z
    a = x / np.asarray(depth) if impact else np.zeros_like(x)
    exponent = -a * q
    if np.max(exponent) > 650:
        return {"loss": float("inf"), "q": q, "cash": -float("inf"),
                "equity": -float("inf"), "fees": float("inf"), "gain_slope": float("inf")}
    price = np.exp(exponent)
    small = np.abs(a) < 1e-6
    integral = np.empty_like(a)
    integral[~small] = -np.expm1(exponent[~small]) / a[~small]
    aa = a[small]
    integral[small] = q - aa * q**2 / 2 + aa**2 * q**3 / 6 - aa**3 * q**4 / 24
    per_unit_loss = 1 - integral - (1 - q) * price
    per_unit_loss[small] = (aa * (q - q**2 / 2) - aa**2 * (q**2 / 2 - q**3 / 3)
                            + aa**3 * (q**3 / 6 - q**4 / 8))
    fee = cfg["fee_bps"] / 1e4
    fees = fee * float(np.dot(np.abs(x), integral))
    loss = float(np.dot(z, per_unit_loss) + fees / capital)
    cash = capital - float(x.sum()) + float(x @ integral) - fees
    equity = cash + float((1 - q) * (x @ price))
    derivative = float(np.sum(z * a * (1 - q) * price) + fee * np.dot(abs(z), price))
    return {"loss": loss, "q": q, "cash": cash, "equity": equity, "fees": fees,
            "gain_slope": derivative, "prices": price, "integral": integral}


def simulate(capital, weights, depth, cfg, method="Feedback", trace=False):
    f = cfg["initial_liquidation_fraction"]
    q, path = f, []
    for k in range(cfg["max_feedback_iterations"]):
        result = state(capital, weights, depth, q, cfg, impact=method != "VolumeOnly")
        target = f if method != "Feedback" else min(1., f + cfg["feedback_slope"] * max(0., result["loss"] - cfg["loss_buffer"]))
        next_q = max(q, target)
        if trace:
            path.append({"iteration": k, "q": q, "loss": result["loss"], "target_q": target})
        if next_q - q <= cfg["feedback_tolerance"]:
            result.update({"iterations": k + 1, "converged": True, "trace": path,
                           "active": q > f + 1e-9,
                           "local_gain": cfg["feedback_slope"] * result["gain_slope"]
                           if method == "Feedback" and f + 1e-9 < q < 1 - 1e-9 else 0.})
            return result
        q = next_q
    result.update({"iterations": cfg["max_feedback_iterations"], "converged": False,
                   "trace": path, "active": True, "local_gain": float("nan")})
    return result


def volume_capacity(weights, adv, cfg):
    active = np.abs(weights) > 1e-12
    if not active.any():
        raise ValueError("Zero net exposure has no finite volume capacity")
    bounds = cfg["horizon_sessions"] * cfg["daily_participation_cap"] * adv[active] / (
        cfg["initial_liquidation_fraction"] * np.abs(weights[active]))
    return float(bounds.min())


def evaluate(capital, weights, adv, depth, cfg, method):
    result = simulate(capital, weights, depth, cfg, method)
    loads = result["q"] * capital * np.abs(weights) / (
        cfg["horizon_sessions"] * cfg["daily_participation_cap"] * adv)
    result["volume_load"] = float(loads.max())
    result["bottleneck_index"] = int(np.argmax(loads))
    result["feasible"] = bool(result["converged"] and result["volume_load"] <= 1 + 1e-10
                              and result["loss"] <= cfg["max_nav_loss"] + 1e-12)
    return result


def capacity(weights, adv, depth, cfg, method):
    upper = volume_capacity(weights, adv, cfg)
    result = evaluate(upper, weights, adv, depth, cfg, method)
    if result["feasible"]:
        return upper, result
    lo, hi = upper * 1e-12, upper
    if not evaluate(lo, weights, adv, depth, cfg, method)["feasible"]:
        raise ValueError("No feasible small-capital state")
    for _ in range(cfg["capacity_bisection_iterations"]):
        mid = (lo + hi) / 2
        if evaluate(mid, weights, adv, depth, cfg, method)["feasible"]:
            lo = mid
        else:
            hi = mid
    return lo, evaluate(lo, weights, adv, depth, cfg, method)
