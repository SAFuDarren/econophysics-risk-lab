#!/usr/bin/env python3
"""Verify the saved evidence release without fitting models or importing research helpers."""
import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
count = 0

def check(condition, name):
    global count
    if not condition:
        raise AssertionError(name)
    count += 1

def close(a, b, name):
    check(math.isclose(float(a), float(b), rel_tol=2e-9, abs_tol=1e-12), name)

def table(name):
    with (ROOT/'tables'/name).open(newline='') as f:
        return list(csv.DictReader(f))

def mean(values):
    values=list(values)
    return math.fsum(values)/len(values)

def qlike(y, prediction):
    ratio=float(y)/float(prediction)
    check(ratio>0 and math.isfinite(ratio), 'positive finite QLIKE ratio')
    return ratio-math.log(ratio)-1

def main():
    manifest=json.loads((ROOT/'MANIFEST.json').read_text())
    for row in manifest['files']:
        p=ROOT/row['path']
        check(p.is_file(), 'manifest path '+row['path'])
        check(p.stat().st_size==row['bytes'], 'size '+row['path'])
        check(hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'], 'hash '+row['path'])
    cells=table('response_surface_cells.csv')
    check(len(cells)==29, '27 grid plus two recovery cells')
    def cell(rho,kappa,capacity,chi=.5):
        matches=[x for x in cells if all(math.isclose(float(x[k]),v) for k,v in [('rho',rho),('feedback',kappa),('liquidity',capacity),('recovery',chi)])]
        check(len(matches)==1,'unique fixed response cell')
        return matches[0]
    for row in table('covariance_effects_by_environment.csv'):
        hi=cell(.65,float(row['feedback']),float(row['liquidity']))
        lo=cell(0,float(row['feedback']),float(row['liquidity']))
        difference=float(hi['risk_mean'])-float(lo['risk_mean'])
        close(difference,row['mean'],'paired response mean')
        # The retained release normalizes each effect by the common-signal arm.
        close(difference/float(hi['risk_mean']),row['relative_mean_difference'],'relative response effect')
        check(float(row['ci_low'])<float(row['mean'])<float(row['ci_high']),'effect inside saved interval')
    for row in cells:
        close(float(row['signal_RV_mean'])+float(row['noise_RV_mean']),row['risk_mean'],'signal/noise accounting')
    precision=json.loads((ROOT/'checks/precision_outcome.json').read_text())
    for target,name in [('DeltaC','coordination'),('DeltaF','feedback')]:
        origins=table('precision_'+name+'_origins.csv')
        check(len(origins)==256,'precision origin count')
        close(mean(float(x['effect_integrated512']) for x in origins),precision['effects'][target]['mean'],'precision paired mean')
        close(mean(float(x['full_integrated_mean']) for x in origins),precision['full_risk_RB'],'full expected risk')
    source_predictions=[x for x in table('information_predictions.csv') if x['split']=='test']
    check(len(source_predictions)==64,'source test origins')
    for row in table('information_summary.csv'):
        score=mean(qlike(x['risk_target_independent_RB256'],x[row['model']]) for x in source_predictions)
        close(score,row['test_QLIKE'],'independent-replicate source QLIKE '+row['model'])
    market=table('market_predictions.csv')
    controls=table('market_controls_predictions.csv')
    # First 273 queries are development/calibration; all 674 dates have been seen.
    market=market[-401:]
    controls=controls[-401:]
    check(len({x['date'] for x in market})==401,'distinct internal evaluation dates')
    check([x['date'] for x in market]==[x['date'] for x in controls],'control date alignment')
    scores={}
    for source,predictions in [('market_score_summary.csv',market),('market_controls_summary.csv',controls)]:
        for row in table(source):
            check(int(row['n'])==401,'score denominator')
            value=mean(qlike(x['actual_RV'],x[row['model']]) for x in predictions)
            close(value,row['QLIKE'],'market QLIKE '+row['model'])
            scores[row['model']]=value
    for row in table('market_primary_contrasts.csv'):
        close(scores[row['model']]-scores[row['reference']],row['mean_difference'],'paired score contrast')
        close(1-scores[row['model']]/scores[row['reference']],row['relative_improvement'],'relative score contrast')
    selected=[x for x in table('market_primary_contrasts.csv') if x['model']=='HAR+Components' and x['reference']=='HAR-All' and x['block_days']=='7'][0]
    check(float(selected['CI_low'])<0<float(selected['CI_high']),'primary difference interval crosses zero')
    check(float(selected['p_holm'])>.05,'no accepted primary superiority')
    for row in table('market_controls_summary.csv'):
        check(row['post_run_descriptive']=='True','post-run control label')
    print(json.dumps({'status':'pass','checks':count,'scope':'saved-table reconstruction and file integrity; not simulation/calibration/fit reproduction','internal_market_dates':401,'source_test_origins':64},indent=2))

if __name__=='__main__':main()
