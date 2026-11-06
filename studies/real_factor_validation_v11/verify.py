#!/usr/bin/env python3
"""Standard-library saved-table audit; no download, fitting or daily-data access."""
from pathlib import Path
import csv,hashlib,json,math,datetime,statistics
R=Path(__file__).resolve().parent
checks=0
def check(ok,label):
    global checks
    if not ok:raise AssertionError(label)
    checks+=1
def close(a,b,label):check(math.isclose(float(a),float(b),rel_tol=2e-9,abs_tol=2e-14),label)
def table(name):
    with (R/'tables'/name).open(newline='') as f:return list(csv.DictReader(f))
def mean(a):return statistics.fmean(a)
def loss(x,model):
    ratio=float(x['realized_Fixed'])/float(x[model]);check(ratio>0,'positive risk')
    return ratio-1-math.log(ratio)
def main():
    for x in json.loads((R/'MANIFEST.json').read_text())['files']:
        p=R/x['path'];check(p.is_file(),'file '+x['path'])
        check(p.stat().st_size==x['bytes'],'size '+x['path'])
        check(hashlib.sha256(p.read_bytes()).hexdigest()==x['sha256'],'hash '+x['path'])
    allrows=table('predictions_scored.csv');ev=[x for x in allrows if x['role']=='evaluation']
    check(len(allrows)==429 and len(ev)==81,'429/81 monthly origins')
    for x in allrows:
        check(x['origin']<x['future_month']+'-01','past origin precedes future month')
        close(float(x['FullCov'])-float(x['Diagonal']),x['cross_term'],'signed covariance identity')
        close(float(x['FullCov'])/float(x['Diagonal']),x['full_over_diagonal'],'covariance ratio')
        check(1<=float(x['effective_corr_modes'])<=6,'effective modes bounded by six')
    allocations=table('computed_allocations.csv');lookup={(x['future_month'],x['mode']):x for x in allocations}
    names=['MktRF','SMB','HML','RMW','CMA','Mom']
    for x in allocations:
        weights=[float(x[n]) for n in names]
        check(all(w>=0 for w in weights),'nonnegative sleeve coefficients')
        close(sum(weights),1,'normalized coefficients')
        close(sum(w*w for w in weights),x['HHI'],'actual coefficient HHI')
        close(sum(float(x['budget_'+n]) for n in names),1,'normalized risk budgets')
    scores={x['model']:x for x in table('forecast_scores.csv')}
    for name,s in scores.items():
        close(mean(loss(x,name) for x in ev),s['QLIKE'],'QLIKE '+name)
        close(statistics.stdev(loss(x,name) for x in ev),s['QLIKE_SD'],'QLIKE sd '+name)
    contrasts=table('primary_contrasts.csv')
    for x in contrasts:
        m=x['model'];ref=x['reference']
        if x['metric']=='QLIKE':
            a=[loss(r,m) for r in ev];b=[loss(r,ref) for r in ev]
        elif x['metric']=='held_HHI':
            a=[float(lookup[(r['future_month'],m)]['HHI']) for r in ev];b=[float(lookup[(r['future_month'],ref)]['HHI']) for r in ev]
        else:
            a=[float(r['realized_'+m]) for r in ev];b=[float(r['realized_'+ref]) for r in ev]
        d=[aa-bb for aa,bb in zip(a,b)]
        close(mean(d),x['mean_difference'],'paired difference');close(mean(d)/mean(b),x['relative_difference'],'relative difference')
        close(statistics.stdev(d),x['paired_SD'],'paired sd')
    for block in ['3','6']:
        family=sorted([x for x in contrasts if x['block_months']==block],key=lambda x:float(x['p_raw']))
        check(len(family)==6,'six predeclared comparisons');last=0
        for i,x in enumerate(family):
            last=max(last,min(1,(6-i)*float(x['p_raw'])));close(last,x['p_holm'],'Holm adjustment')
    summary=json.loads((R/'results_summary.json').read_text());d=summary['descriptive']
    check(sum(float(x['cross_term'])<0 for x in ev)==d['negative_cross_term_months']==36,'hedging count')
    check(sum(float(x['cross_term'])>0 for x in ev)==d['positive_cross_term_months']==45,'amplifying count')
    close(statistics.median(float(x['effective_corr_modes']) for x in ev),d['median_effective_corr_modes'],'median effective modes')
    for mode in ['Fixed','Performance','Permuted']:
        close(mean(float(lookup[(r['future_month'],mode)]['HHI']) for r in ev),d['HHI_means'][mode],'mean HHI')
        close(mean(float(r['realized_'+mode]) for r in ev),d['RV_means'][mode],'mean risk')
    check(float(scores['HAR-Portfolio']['QLIKE'])<float(scores['FullCov']['QLIKE']),'simple HAR point score better')
    print(json.dumps({'status':'pass','checks':checks,'scope':'saved table, chronology, score, concentration and multiplicity reconstruction; not daily-source parsing, fit or bootstrap regeneration'},indent=2))
if __name__=='__main__':main()
