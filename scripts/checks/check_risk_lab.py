#!/usr/bin/env python3
"""Audit the diagnostic against archived positions and full daily observations."""

from pathlib import Path as _ProjectPath
import sys as _project_sys
_project_sys.path.insert(0, str(_ProjectPath(__file__).resolve().parents[1]))
from _bootstrap import ROOT as PROJECT_ROOT, script_path, resolve_recorded_path
from publication_integrity import matches_recorded_digest
from pathlib import Path
import csv, hashlib, json, sys
ROOT = PROJECT_ROOT
sys.path.insert(0, str(ROOT / 'src'))
import numpy as np
from econophysics.us_equity import load_panel
from econophysics.risk_lab import portfolio_risk, screen_candidates, reconstruction


def main():
    checks = []
    def check(name, condition, **details):
        checks.append({'name': name, 'pass': bool(condition), **details})
    def close(a, b):
        return np.allclose(a, b, rtol=2e-10, atol=2e-10)
    def rows(path):
        return list(csv.DictReader(path.open()))
    data = json.loads((ROOT / 'apps/risk_lab_v1/data.json').read_text())
    cfg = json.loads((ROOT / 'configs/risk_lab_v1.json').read_text())
    oldcfg = json.loads((ROOT / 'configs/us_equity_v1.json').read_text())
    frozen = json.loads((ROOT / 'results/checks/risk_lab_v1/input_snapshot.json').read_text())
    check('Frozen input hashes unchanged', all(matches_recorded_digest(ROOT/p, sha, ROOT) for p,sha in frozen['sha256'].items()))
    old = json.loads((ROOT / 'results/checks/us_equity_v1/delivery_verification.json').read_text())
    check('Prior delivered US package unchanged', hashlib.sha256((ROOT/'handoff/AB_to_CD/Econophysics_US_Equity_PnL_v1.zip').read_bytes()).hexdigest() == old['zip_sha256'])
    check('Original 19 numeric tables unchanged', all(hashlib.sha256((ROOT/'results/tables/us_equity_v1'/r['table']).read_bytes()).hexdigest() == r['sha256'] for r in old['extracted_package_fixed_snapshot_reproduction']['tables']))
    dates, returns, price, names = load_panel(ROOT, oldcfg)
    price = price[:,:9] / price[0,:9]
    position = np.load(ROOT/'results/tables/us_equity_v1/positions.npz')
    check('Archived position dates align with full source', np.array_equal(position['dates'], dates))
    for snapshot in data['risk']:
        i = int(np.flatnonzero(dates == snapshot['date'])[0])
        for length in (63,126):
            s = np.array(snapshot['cov'][str(length)]).reshape(9,9)
            exact = np.cov(returns[i-length+1:i+1,:9], rowvar=False, ddof=1)
            check(f'Window covariance {snapshot["date"]}/{length}', close(s, exact) and np.linalg.eigvalsh(s).min() >= -1e-13)
            check(f'Counterfactual PSD and marginal variance {snapshot["date"]}/{length}', all(np.linalg.eigvalsh((1-eta)*np.diag(np.diag(s))+eta*s).min() >= -1e-13 for eta in (0,.25,.5,.75,1)))
    for f in json.loads((ROOT/'results/checks/risk_lab_v1/browser_fixtures.json').read_text())['risk_cases']:
        s = np.array(next(x for x in data['risk'] if x['date']==f['date'])['cov'][str(f['lookback'])]).reshape(9,9)
        got = portfolio_risk(s, f['weights'], f['eta'])
        check('Risk fixture '+f['date'], all(close(v, f['expected'][k]) for k,v in got.items()))
    source = rows(ROOT/'results/tables/us_equity_v1/strategy_daily.csv')
    lookup = {(r['date'], r['strategy']):r for r in source}
    recipes = position['strategy_names'].tolist()
    pnl = np.array([[float(lookup[str(d),s]['net_5bp']) if (str(d),s) in lookup else 0 for s in recipes] for d in dates])
    turnover = np.array([[float(lookup[str(d),s]['turnover']) if (str(d),s) in lookup else 0 for s in recipes] for d in dates])
    train = (dates >= cfg['train'][0]) & (dates < cfg['train'][1])
    corr = np.corrcoef(pnl[train],rowvar=False)
    check('Screen correlations and ranking use training rows only', close(corr.ravel(),data['screen']['training_corr']) and close(turnover[train].mean(0),data['screen']['training_turnover']))
    mask,_ = screen_candidates(corr,turnover[train].mean(0),recipes,.8)
    check('Training screen marks LowVol-21 and keeps five representatives', mask == data['screen']['default_mask'] == 47)
    active = position['weights_Equal'].sum(1)>0
    oldrows = rows(ROOT/'results/tables/us_equity_v1/allocation_daily.csv')
    oldequal = {r['date']:r for r in oldrows if r['method']=='Equal'}
    periods = {'validation':cfg['validation'], **cfg['evaluations']}
    masks = {key:(dates>=lo)&(dates<hi) for key,(lo,hi) in periods.items()}
    # Independent full-day accounting from units; no sleeve cost averaging.
    q_all = position['strategy_units'].mean(1) * active[:,None]
    previous_all = np.vstack([np.zeros(9),q_all[:-1]])
    delta = np.vstack([np.zeros(9),np.diff(price,axis=0)])
    net_by_mask = {}
    for mask in range(1,64):
        ids = [j for j in range(6) if mask & (1<<j)]
        q = position['strategy_units'][:,ids].mean(1)*active[:,None]
        previous = np.vstack([np.zeros(9),q[:-1]])
        gross = (previous*delta).sum(1)
        turns = (abs(q-previous)*price).sum(1)
        shorts = np.r_[0,np.maximum(-previous[1:]*price[:-1],0).sum(1)]
        exposure = (abs(q)*price).sum(1)
        prior_net = None
        for cost in cfg['cost_bps']:
            net = gross-cost/10000*turns-.01/252*shorts
            if cost==5: net_by_mask[mask]=net
            check(f'Nonincreasing net P&L with cost / subset {mask}/{cost}', prior_net is None or np.all(net<=prior_net+1e-15))
            prior_net = net
            for period,ix in masks.items():
                m = data['subsets'][str(mask)]['metrics'][str(cost)][period]
                values = [100*net[ix].sum(), 100*np.sqrt(252)*net[ix].std(ddof=1), turns[ix].mean(), exposure[ix].mean()]
                check(f'Full-day subset metrics {mask}/{cost}/{period}', close(values,[m['cumulative_pnl_pct'],m['annual_sigma_pnl_pct'],m['mean_daily_turnover'],m['mean_underlying_gross_exposure']]) and np.isfinite(list(m.values())).all())
                if period in cfg['evaluations']:
                    indices = data['period_axes'][period]['indices']
                    check(f'Curve endpoints and sampled path {mask}/{cost}/{period}', close((100*np.cumsum(net[ix]))[indices],data['subsets'][str(mask)]['curves'][str(cost)][period]))
            if mask==63:
                archived = np.array([float(oldequal[str(d)][f'net_{cost}bp']) if str(d) in oldequal else 0. for d in dates])
                check(f'All-six exact legacy Equal accounting / {cost}bp', close(net,archived), maximum_absolute_difference=float(abs(net-archived).max()))
    base_sigma = net_by_mask[63][masks['validation']].std(ddof=1)
    for mask,net in net_by_mask.items():
        scale = data['subsets'][str(mask)]['scale']
        check(f'Validation-only risk normalization {mask}', close(scale*net[masks['validation']].std(ddof=1),base_sigma))
    for period in cfg['evaluations']:
        ix = masks[period]
        rec = reconstruction(pnl[train],pnl[ix],[0,1,2,3,5],4)
        saved = data['subsets']['47']['reconstruction']['4'][period]
        check(f'Training-only OLS and evaluation R2 {period}', all(close(v,saved[k]) for k,v in rec.items()))
        a,b = net_by_mask[47][ix], net_by_mask[63][ix]
        comparisons = [r for r in data['default_comparison'] if r['period']==period]
        check(f'Default paired contrast point estimates {period}', all(close(r['sigma_reduction_pct'],100*(1-a.std(ddof=1)/b.std(ddof=1))) and close(r['annual_mean_pnl_difference_pp'],100*252*(a-b).mean()) for r in comparisons))
        check(f'Primary intervals report lack of stable improvement {period}', all(r['sigma_ci_low']<0<r['sigma_ci_high'] and r['mean_ci_low']<0<r['mean_ci_high'] for r in comparisons if r['block_sessions']==20))
    report = {'status':'pass' if all(r['pass'] for r in checks) else 'fail','checks':len(checks),'failures':[r for r in checks if not r['pass']],'classification':'Numerical implementation audit; not scientific signoff or fresh holdout validation','details':checks,'member_scientific_review':'not_run'}
    path = ROOT/'results/checks/risk_lab_v1/method_audit.json'
    path.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='details'},indent=2))
    if report['status']!='pass': raise SystemExit(1)

if __name__=='__main__': main()
