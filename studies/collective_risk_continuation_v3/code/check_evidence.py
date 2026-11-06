"""Recalculate released evidence from case tables, without fitting a new model."""
from pathlib import Path
import csv, hashlib, json, math, statistics

ROOT=Path(__file__).resolve().parents[1]

def load(name):
    with (ROOT/'tables'/name).open(newline='') as f:return list(csv.DictReader(f))

def num(row,key):return float(row[key])

def close(a,b,tol=1e-11):
    assert math.isclose(a,b,rel_tol=tol,abs_tol=tol),(a,b)

def main():
    manifest=json.loads((ROOT/'source-manifest.json').read_text());checks=0
    for source in manifest['sources']:
        p=ROOT/source['path'];b=p.read_bytes()
        assert hashlib.sha256(b).hexdigest()==source['sha256'];assert len(b)==source['bytes'];checks+=1
    predictions=load('v3_predictions_scored.csv');scores=load('v3_risk_scores.csv')
    quantiles=load('v3_calibration_quantiles.csv');contrasts=load('v3_risk_contrasts.csv')
    groups={}
    for row in predictions:
        y,h=num(row,'actual_rv'),num(row,'forecast');assert y>0 and h>0
        loss=y/h-math.log(y/h)-1;close(loss,num(row,'qlike'));checks+=1
        groups.setdefault((row['split'],row['model'],row['horizon']),[]).append(row)
    for q in quantiles:
        rows=groups['cal',q['model'],q['horizon']];assert len(rows)==64
        rank=math.ceil(65*.9);assert rank==59==int(q['order'])
        calibrated=sorted(abs(math.log(num(r,'actual_rv')/num(r,'forecast'))) for r in rows)[rank-1]
        close(calibrated,num(q,'q'));checks+=1
    for s in scores:
        rows=groups['test',s['model'],s['horizon']];assert len(rows)==128
        close(statistics.mean(num(r,'qlike') for r in rows),num(s,'qlike_mean'))
        lo='raw_lower90' if s['interval']=='raw' else 'cp_lower90'
        hi='raw_upper90' if s['interval']=='raw' else 'cp_upper90'
        covered=sum(num(r,lo)<=num(r,'actual_rv')<=num(r,hi) for r in rows)
        close(covered/128,num(s,'coverage90'))
        close(statistics.mean(num(r,hi)-num(r,lo) for r in rows),num(s,'mean_width'));checks+=3
    for c in contrasts:
        a={r['unit']:r for r in groups['test',c['model'],c['horizon']]}
        b={r['unit']:r for r in groups['test',c['reference'],c['horizon']]};assert a.keys()==b.keys()
        diffs=[num(a[k],'qlike')-num(b[k],'qlike') for k in a]
        close(statistics.mean(diffs),num(c,'difference'));close(statistics.stdev(diffs),num(c,'paired_sd'));checks+=2
    truth={(r['unit'],r['state']):num(r,'truth') for r in load('v3_state_truth_validation_only.csv')}
    estimates=load('v3_state_estimates_before_truth.csv');state_scores=load('v3_state_scores.csv')
    for s in state_scores:
        if s['model']=='DirectPressureProxy':continue
        selected=[r for r in estimates if r['split']=='test' and r['model']==s['model'] and r['state']==s['state']]
        assert len(selected)==128
        errors=[num(r,'pred')-truth[r['unit'],r['state']] for r in selected]
        close(math.sqrt(statistics.mean(e*e for e in errors)),num(s,'rmse'))
        coverage=sum(num(r,'lower90')<=truth[r['unit'],r['state']]<=num(r,'upper90') for r in selected)/128
        close(coverage,num(s,'coverage90'));checks+=2
    prefix=load('v3_observable_prefixes.csv');assert len(prefix)==128*32
    assert {int(r['tick']) for r in prefix}==set(range(65,97))
    for row in prefix:close(num(row,'pressure'),num(row,'F')/num(row,'V'));checks+=1
    for s in state_scores:
        if s['model']!='DirectPressureProxy':continue
        end=[r for r in prefix if r['tick']=='96'];errors=[]
        for r in end:
            proxy=num(r,'pressure');proxy=abs(proxy) if s['state']=='coherence' else proxy
            errors.append(proxy-truth[r['unit'],s['state']])
        close(math.sqrt(statistics.mean(e*e for e in errors)),num(s,'rmse'));checks+=1
    seeds=load('v2_n01_seed_metrics.csv');summaries=load('v2_n01_summary.csv')
    for s in summaries:
        selected=[r for r in seeds if r['arm']==s['arm']];assert len(selected)==128
        close(statistics.mean(num(r,s['metric']) for r in selected),num(s,'mean'));checks+=1
    for c in load('v2_n01_contrasts.csv'):
        a={r['seed_index']:r for r in seeds if r['arm']==c['arm']}
        b={r['seed_index']:r for r in seeds if r['arm']==c['reference']};assert a.keys()==b.keys()
        diffs=[num(a[k],c['metric'])-num(b[k],c['metric']) for k in a]
        close(statistics.mean(diffs),num(c,'difference'));close(statistics.stdev(diffs),num(c,'paired_sd'));checks+=2
    for row in load('v3_effective_risk_state.csv'):
        m,v,s=num(row,'mean_flow1'),num(row,'variance_flow1'),num(row,'second_flow1')
        close(s,v+m*m);b=num(row,'model_execution_baseline');close(v/b,num(row,'G_centered'));close(s/b,num(row,'G_energy'));checks+=3
    evidence=json.loads((ROOT/'evidence.json').read_text());assert len(evidence['inference']['prefixes'])==128
    assert len(evidence['inference']['truthValidation'])==768
    result={'status':'pass','checks':checks,'source_tables':len(manifest['sources']),
        'independent_test_cases':128,'all_horizons':[1,8,48],'primary_horizon':8,
        'recalculated':['QLIKE from outcomes and forecasts','state RMSE and coverage','risk coverage and width',
            'finite-sample calibration ranks','paired mean and SD contrasts','shared-signal seed means','flow moment and G identities'],
        'scope':'Recalculation of saved evidence; not a fresh simulation or independent market validation.'}
    (ROOT/'checks/numeric-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

if __name__=='__main__':main()
