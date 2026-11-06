#!/usr/bin/env python3
"""Read-only reconstruction of the saved model release; standard library only."""
from pathlib import Path
import csv, hashlib, json, math
R=Path(__file__).resolve().parent
checks=0
def check(ok,name):
    global checks
    if not ok: raise AssertionError(name)
    checks+=1
def close(a,b,name):check(math.isclose(float(a),float(b),rel_tol=3e-9,abs_tol=1e-13),name)
def rows(n):
    with (R/'tables'/n).open(newline='') as f:return list(csv.DictReader(f))
def mean(a):
    a=list(a);return math.fsum(a)/len(a)
def main():
    for x in json.loads((R/'MANIFEST.json').read_text())['files']:
        p=R/x['path'];check(p.is_file(),'file '+x['path'])
        check(p.stat().st_size==x['bytes'],'size '+x['path'])
        check(hashlib.sha256(p.read_bytes()).hexdigest()==x['sha256'],'hash '+x['path'])
    cells=rows('model-cells.csv');orig=rows('model-origin-means.csv')
    check(len(cells)==56 and len(orig)==1792,'56 cells x32 origins')
    for c in cells:
        o=[x for x in orig if (x['source_family'],x['scenario_id'])==(c['source_family'],c['scenario_id'])]
        check(len(o)==32 and len({x['origin'] for x in o})==32,'unique origins')
        for metric,column in [('integrated_RV','risk_mean'),('actual_RV','actual_RV_mean'),('signal_RV','signal_RV_mean'),('noise_RV','noise_RV_mean')]:
            close(mean(float(x[metric]) for x in o),c[column],column)
        close(float(c['signal_RV_mean'])+float(c['noise_RV_mean']),c['risk_mean'],'signal noise accounting')
    alloc=rows('allocation-origin-metrics.csv')
    summaries=rows('allocation-summary.csv')
    for s in summaries:
        o=[float(x['value']) for x in alloc if x['case']==s['case'] and x['metric']==s['metric']]
        check(len(o)==32,'allocation origins');close(mean(o),s['mean'],'allocation mean')
    def get(m,mode,metric):return next(x for x in summaries if x['M']==m and x['mode']==mode and x['metric']==metric)
    for x in rows('allocation-primary.csv'):
        hi=get(x['M'],x['model'],x['metric']);lo=get(x['M'],x['reference'],x['metric'])
        close(float(hi['mean'])-float(lo['mean']),x['mean'],'allocation contrast')
        close(float(x['mean'])/float(lo['mean']),x['relative_difference'],'allocation relative difference')
        if x['metric']=='integrated_RV':check(float(x['ci_low'])<0<float(x['ci_high']),'unestablished 16h risk increment')
    for x in rows('model-contrasts.csv'):
        check(float(x['ci_low'])<float(x['mean_difference'])<float(x['ci_high']),'contrast inside interval')
        check(float(x['p_holm'])>=float(x['p_raw']),'Holm no smaller than raw')
    for n in ['allocation-trajectories.csv','allocation-all-paths.csv']:
        for x in rows(n):check(float(x['ci_low_pp'])<=float(x['mean_HHI_pp'])<=float(x['ci_high_pp']),'trajectory interval')
    print(json.dumps({'status':'pass','checks':checks,'scope':'hashes and saved origin/summary reconstruction; no stochastic regeneration or interval recalculation'},indent=2))
if __name__=='__main__':main()
