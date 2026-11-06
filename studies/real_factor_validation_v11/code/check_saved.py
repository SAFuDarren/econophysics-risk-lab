"""Independent recomputation from official archives. Does not import study.py."""
from pathlib import Path
import calendar, hashlib, io, json, zipfile
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
checks = []

def close(label, got, expected, rtol=2e-10, atol=2e-14):
    np.testing.assert_allclose(got, expected, rtol=rtol, atol=atol, err_msg=label)
    checks.append(label)

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def frozen(path):
    x = json.loads(path.read_text())
    for filename, expected in x['files'].items():
        assert digest(ROOT / filename) == expected, filename
        checks.append('unchanged ' + filename)
    return x

pre = frozen(ROOT / 'checks/pre_download_freeze.json')
pf = frozen(ROOT / 'checks/prediction_freeze.json')
assert pre['before_download'] and pf['evaluation_truth_joined'] is False
manifest = json.loads((ROOT / 'checks/download_manifest.json').read_text())
panels = []
for record in manifest['records']:
    archive = ROOT / 'inputs' / record['url'].rsplit('/', 1)[-1]
    assert digest(archive) == record['sha256']
    assert record['retrieved_utc'] > pre['created_utc']
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        text = z.read(z.namelist()[0]).decode('utf-8-sig')
    cols = ['MktRF', 'SMB', 'HML', 'RMW', 'CMA', 'RF'] if '5_Factors' in archive.name else ['Mom']
    rows = []
    for line in text.splitlines():
        fields = [s.strip() for s in line.split(',')]
        if fields[0].isdigit() and len(fields[0]) == 8:
            vals = [float(s) for s in fields[1:len(cols)+1]]
            assert all(v not in (-99.99, -999) for v in vals)
            rows.append([pd.Timestamp(fields[0]), *np.divide(vals, 100)])
    panels.append(pd.DataFrame(rows, columns=['date', *cols]).set_index('date'))
    checks.append('archive integrity/source provenance ' + archive.name)

names = ['MktRF', 'SMB', 'HML', 'RMW', 'CMA', 'Mom']
d = pd.concat(panels, axis=1, join='inner')[names].loc['1990-01-01':'2026-10-31']
last = d.index[-1]
lastweekday = pd.Timestamp(last.year, last.month, calendar.monthrange(last.year,last.month)[1])
while lastweekday.dayofweek > 4:
    lastweekday -= pd.Timedelta(days=1)
if last < lastweekday:
    d = d[d.index.to_period('M') < last.to_period('M')]
assert len(d) == 9254 and d.index[-1] == pd.Timestamp('2026-09-30')
assert d.index.is_unique and d.index.is_monotonic_increasing
assert not d.isna().any().any()
saved_daily = pd.read_csv(ROOT/'tables/observed_factor_returns.csv', index_col=0, parse_dates=True)
close('official percent returns divided by100, fixed six-series source panel', d, saved_daily)

prediction = pd.read_csv(ROOT/'tables/predictions_scored.csv')
allocation = pd.read_csv(ROOT/'tables/computed_allocations.csv')
feature_saved = np.load(ROOT/'tables/past_features.npz')
models = json.loads((ROOT/'checks/fitted_models.json').read_text())
periods = d.index.to_period('M')
values = d.to_numpy()
budgets = {x:np.repeat(1/6,6) for x in ['Fixed','Performance','Permuted']}
previous = {x:None for x in budgets}
recomputed = []
features = {'HAR-Portfolio':[], 'HAR-All':[]}
truth = {x:[] for x in budgets}
all_hhi = {x:[] for x in budgets}
count = 0
for period in periods.unique()[:-1]:
    current = np.where(periods==period)[0]
    t = current[-1]
    if t < 251:
        continue
    row = prediction.iloc[count]
    assert row['origin'] == str(d.index[t].date()) and row['future_month'] == str(period+1)
    history = values[t-251:t+1]
    assert history.shape == (252,6)
    scale = np.sqrt(np.var(history,axis=0,ddof=1))
    scores = np.sum(values[current],axis=0)/(scale*np.sqrt(len(current)))
    permutation_seed = int(hashlib.sha256(str(period).encode()).hexdigest()[:16],16)
    perm = np.random.default_rng(permutation_seed).permutation(6)
    for mode in budgets:
        if mode != 'Fixed':
            score = scores if mode == 'Performance' else scores[perm]
            tilts = budgets[mode] * np.exp(.1*np.clip(score,-2,2))
            budgets[mode] = .98 * tilts / tilts.sum() + .02/6
        coeff = budgets[mode]/scale
        coeff /= coeff.sum()
        close(mode+' held coefficients month'+str(count), coeff,feature_saved['weights_'+mode][count])
        saved = allocation[(allocation['future_month']==str(period+1))&(allocation['mode']==mode)].iloc[0]
        close(mode+' explicit coefficient table month'+str(count), coeff,saved[names].to_numpy(dtype=float))
        close(mode+' budget month'+str(count), budgets[mode],saved[['budget_'+x for x in names]].to_numpy(dtype=float))
        hhi = float(np.square(coeff).sum())
        close(mode+' HHI month'+str(count),hhi,saved.HHI)
        close(mode+' risk-budget HHI month'+str(count),float(np.square(budgets[mode]).sum()),saved.risk_budget_HHI)
        turn = 0 if previous[mode] is None else .5*np.abs(coeff-previous[mode]).sum()
        close(mode+' turnover month'+str(count),turn,saved.turnover)
        close(mode+' illustrative cost month'+str(count),turn*.0001,saved.assumed_1bp_turnover_charge)
        previous[mode] = coeff
        # Next calendar month only. Weights and scales already fixed from history.
        future = values[periods==period+1]
        target = float(np.mean(np.square(np.matmul(future,coeff))))
        close(mode+' next-month alignment month'+str(count),target,row['realized_'+mode])
        truth[mode].append(target)
        all_hhi[mode].append(hhi)
    w = previous['Fixed']
    h63 = history[-63:]
    mean = h63.mean(axis=0)
    centered = h63-mean
    cov = centered.T@centered / len(centered)
    diag = float(np.dot(w*w,np.diag(cov))+np.square(np.dot(w,mean)))
    full = float(np.mean(np.square(h63@w)))
    cor = np.corrcoef(h63,rowvar=False)
    modes = float(np.trace(cor)**2 / np.sum(cor*cor))
    close('full second moment month'+str(count),full,row.FullCov)
    close('diagonal counterfactual month'+str(count),diag,row.Diagonal)
    close('signed covariance month'+str(count),full-diag,row.cross_term)
    close('effective modes month'+str(count),modes,row.effective_corr_modes)
    har = np.log([np.mean(np.square((history@w)[-k:])) for k in [22,66,252]])
    allx = np.r_[har,np.log(np.array([np.mean(history[-k:]**2,axis=0) for k in [22,66,252]])).reshape(-1),mean,cor[np.triu_indices(6,1)]]
    features['HAR-Portfolio'].append(har)
    features['HAR-All'].append(allx)
    year = (period+1).year
    assert row.role == ('fit' if year<=2009 else 'development' if year<=2019 else 'evaluation')
    assert row.future_days == len(future)
    count += 1
assert count == 429
checks.append('all monthly origins and horizons disjoint; no future data used for scales, scores or coefficients')
fit = prediction.role.eq('fit').to_numpy()
dev = prediction.role.eq('development').to_numpy()
ev = prediction.role.eq('evaluation').to_numpy()
assert (fit.sum(),dev.sum(),ev.sum()) == (228,120,81)
y = np.asarray(truth['Fixed'])
for label,xlist in features.items():
    x = np.array(xlist)
    close(label+' all past features',x,feature_saved[label.replace('-','_')])
    m = models[label]['parameters']
    close(label+' fit-only feature means',x[fit].mean(axis=0),m['mean'])
    close(label+' fit-only feature scales',x[fit].std(axis=0),m['sd'])
    close(label+' fit-only target scale',y[fit].mean(),m['scale'])
    design = np.column_stack([np.ones(len(x)),(x-np.array(m['mean']))/m['sd']])
    coeff = np.array(m['b'])
    forecast = m['scale'] * np.exp(design@coeff)
    close(label+' parameter predictions',forecast,prediction[label].to_numpy())
    penalty = np.r_[0,np.repeat(m['penalty'],x.shape[1])]
    gradient = design[fit].T@(1-y[fit]/forecast[fit])+penalty*coeff
    assert np.max(np.abs(gradient))/fit.sum()<1e-5
    grid = pd.read_csv(ROOT/'tables/development_grid.csv')
    best = grid[grid.model==label].sort_values(['development_QLIKE','penalty']).iloc[0]
    assert best.penalty == m['penalty']
    loss = (y[dev]/forecast[dev]-np.log(y[dev]/forecast[dev])-1).mean()
    close(label+' dev-only ridge selection',loss,best.development_QLIKE)
    checks.append(label+' fit-only penalized Gamma gradient converged')

summary = json.loads((ROOT/'results_summary.json').read_text())
scores = {}
for label in ['FullCov','Diagonal','HAR-Portfolio','HAR-All']:
    ratio = y[ev]/prediction.loc[ev,label].to_numpy()
    loss = ratio - 1 - np.log(ratio)
    scores[label] = loss
    stored = next(x for x in summary['forecast_scores'] if x['model']==label)
    close(label+' evaluation QLIKE',loss.mean(),stored['QLIKE'])
    close(label+' evaluation QLIKE SD',loss.std(ddof=1),stored['QLIKE_SD'])

contrasts = [(scores['FullCov']-scores['Diagonal'],scores['Diagonal'].mean()),
             (scores['FullCov']-scores['HAR-All'],scores['HAR-All'].mean())]
for ref in ['Fixed','Permuted']:
    risk_m = np.asarray(truth['Performance'])[ev]
    risk_r = np.asarray(truth[ref])[ev]
    hm = np.asarray(all_hhi['Performance'])[ev]
    hr = np.asarray(all_hhi[ref])[ev]
    contrasts.extend([(risk_m-risk_r,risk_r.mean()),(hm-hr,hr.mean())])

for block,field in [(3,'primary'),(6,'sensitivity')]:
    n = ev.sum()
    rng = np.random.default_rng(11062026)
    start = rng.integers(0,n,size=(4999,int(np.ceil(n/block))))
    # Construct blocks by explicit per-replicate expansion, independent of study.boot.
    indices = np.array([[int((s+k)%n) for s in row for k in range(block)][:n] for row in start])
    pvals = []
    for i,(diff,refmean) in enumerate(contrasts):
        mu = np.mean(diff)
        sampled = diff[indices].mean(axis=1)
        low,high = 2*mu-np.quantile(sampled,[.975,.025])
        null = (diff-mu)[indices].mean(axis=1)
        p = (np.count_nonzero(np.abs(null)>=abs(mu))+1)/5000
        rec = summary[field][i]
        close(field+' mean contrast'+str(i),mu,rec['mean_difference'])
        close(field+' relative contrast'+str(i),mu/refmean,rec['relative_difference'])
        close(field+' bootstrap contrast'+str(i),[low,high,p],[rec['CI_low'],rec['CI_high'],rec['p_raw']])
        pvals.append(p)
    order = np.argsort(pvals)
    adjusted = np.empty(6)
    adjusted[order] = np.minimum(1,np.maximum.accumulate(np.array(pvals)[order]*np.arange(6,0,-1)))
    close(field+' Holm six comparisons',adjusted,[r['p_holm'] for r in summary[field]])

out = {'status':'PASS','recomputation_checks':len(checks),'checks':checks,
       'scope':'Independent implementation, same observed inputs; this is not independent data or independent error evidence.',
       'hashes_unchanged':True,'all_429_months_reconstructed':True,'evaluation_months':int(ev.sum())}
(ROOT/'checks/independent_recomputation.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='checks'},indent=2))
