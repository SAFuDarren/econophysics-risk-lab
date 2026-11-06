"""Export frozen study evidence; this does not rerun or fit the research models."""
from pathlib import Path
import argparse, csv, hashlib, json, math, shutil
import numpy as np

REPO = Path(__file__).resolve().parents[3]
STUDY = REPO / 'studies/collective_risk_continuation_v3'
WEB = REPO / 'web'

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def scalar(s):
    if s == '': return None
    if s in ('True', 'False'): return s == 'True'
    try:
        n = float(s)
        if not math.isfinite(n): return None
        return int(n) if n.is_integer() else n
    except (TypeError, ValueError): return s

def rows(p):
    with p.open(newline='') as f:
        return [{k: scalar(v) for k,v in r.items()} for r in csv.DictReader(f)]

def write_rows(p, data):
    with p.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(data[0])); w.writeheader(); w.writerows(data)

def main():
    a=argparse.ArgumentParser();a.add_argument('--source-root',type=Path,default=REPO.parent)
    source=a.parse_args().source_root
    roots={1:source/'Collective_Risk_Continuation_v1',2:source/'Collective_Risk_Continuation_v2',3:source/'Collective_Risk_State_Remedy_v3'}
    sources=[];tables={}
    def record(p,name,original,rows_count=None,derivation=None):
        destination=WEB/'downloads/continuation/tables'/p.name
        shutil.copy2(p,destination)
        entry={'id':name,'url':'downloads/continuation/tables/'+p.name,'path':'tables/'+p.name,
               'sha256':digest(p),'bytes':p.stat().st_size,'rows':rows_count,
               'sourceStudy':original[0],'sourcePath':original[1]}
        if derivation:entry['derivation']=derivation
        sources.append(entry)
    def take(v,name):
        original=roots[v]/'tables'/(name+'.csv');p=STUDY/'tables'/f'v{v}_{name}.csv'
        shutil.copy2(original,p);data=rows(p);tables[f'v{v}_{name}']=data
        record(p,f'v{v}_{name}',(roots[v].name,'tables/'+name+'.csv'),len(data))
        return data
    channels={key:take(2,name) for key,name in {
        'summary':'n01_summary','contrasts':'n01_contrasts','seedMetrics':'n01_seed_metrics','curves':'n01_curves'}.items()}
    moments=take(2,'d01_ensemble_moments')
    propagation={'moments':[r for r in moments if r['metric'] in ('F','RV')],
        'meanClosure':take(2,'d01_mean_closure'),
        'summary':take(2,'d01_ensemble_summary'),
        'oneStepMoments':take(1,'w2_conditional_flow_moments'),
        'pulseCurves':take(1,'w2_response_curves'),
        'pulseContrasts':take(1,'w2_primary_contrasts')}
    propagation['summary']=[r for r in propagation['summary'] if r['metric'] in ('F','RV')]
    propagation['pulseCurves']=[r for r in propagation['pulseCurves'] if r['horizon'] in (1,48)]
    source_states=roots[2]/'tables/d01_reference_states.json'
    raw_states=json.loads(source_states.read_text());state_rows=[]
    for i,s in enumerate(raw_states):
        nodes=s['nodes'];w=np.array([n['weight'] for n in nodes])
        state_rows.append({'state':i,'tick':s['tick'],
            'fast':float(sum(n['weight']*n['fast'] for n in nodes)),
            'slow':float(sum(n['weight']*n['slow'] for n in nodes)),
            'coherence':abs(float(sum(n['weight']*n['fast'] for n in nodes))),
            'trace':float(sum(n['weight']*n['trace'] for n in nodes)),
            'liquidity':s['liquidity'],'weight_concentration':float(sum(w*w))})
    p=STUDY/'tables/v2_reference_state_summaries.csv';write_rows(p,state_rows)
    record(p,'v2_reference_state_summaries',(roots[2].name,'tables/d01_reference_states.json'),len(state_rows),
           {'source_sha256':digest(source_states),'rule':'All eight states; weighted fast/slow/trace, absolute fast coherence, sum of squared normalized weights.'})
    propagation['states']=state_rows
    estimates=take(3,'state_estimates_before_truth');diagnostics=take(3,'conditioning_diagnostics')
    inference={'stateScores':take(3,'state_scores'),
        'estimates':[r for r in estimates if r['split']=='test'],
        'diagnostics':[r for r in diagnostics if r['split']=='test'],
        'effectiveRiskState':take(3,'effective_risk_state'),
        'simpleControls':take(2,'i01_simple_state_controls')}
    hidden_path=roots[3]/'tables/test_hidden_validation_only.npz'
    hidden=np.load(hidden_path);state_names=hidden['state_names'].tolist();truth=[]
    for i,values in enumerate(hidden['state']):
        truth.extend({'unit':i,'state':name,'truth':float(v)} for name,v in zip(state_names,values))
    p=STUDY/'tables/v3_state_truth_validation_only.csv';write_rows(p,truth)
    record(p,'v3_state_truth_validation_only',(roots[3].name,'tables/test_hidden_validation_only.npz'),len(truth),
           {'source_sha256':digest(hidden_path),'rule':'All 128 independent test cases and all six latent projections; evaluation-only, not estimator inputs.'})
    inference['truthValidation']=truth
    observable_path=roots[3]/'tables/test_observable_only.npz';obs=np.load(observable_path)['observables'][:,64:96,:]
    prefixes=[];prefix_rows=[]
    for i,values in enumerate(obs):
        f,v,k,r=values.T;pressure=f/v
        prefixes.append({'unit':i,'ticks':list(range(65,97)),'F':f.tolist(),'V':v.tolist(),
            'K':k.tolist(),'r':r.tolist(),'pressure':pressure.tolist()})
        for j,(ff,vv,kk,rr) in enumerate(values):
            prefix_rows.append({'unit':i,'tick':65+j,'relative_tick':j-31,'F':float(ff),'V':float(vv),
                'K':int(kk),'r':float(rr),'pressure':float(ff/vv)})
    p=STUDY/'tables/v3_observable_prefixes.csv';write_rows(p,prefix_rows)
    record(p,'v3_observable_prefixes',(roots[3].name,'tables/test_observable_only.npz'),len(prefix_rows),
           {'source_sha256':digest(observable_path),'rule':'All 128 cases, only the 32 observed ticks 65–96. Future ticks are excluded.'})
    inference['prefixes']=prefixes
    predictions=take(3,'predictions_scored')
    risk={'scores':take(3,'risk_scores'),'contrasts':take(3,'risk_contrasts'),
          'predictions':[r for r in predictions if r['split']=='test'],
          'calibrationQuantiles':take(3,'calibration_quantiles')}
    transport={'features':take(2,'v01_feature_mismatch')}
    # These full source tables support independent recalculation beyond the browser subset.
    take(1,'w2_seed_effects');take(2,'n01_common_input_covariance_identity')
    take(2,'d01_mean_closure_summary');take(3,'tune_grid')
    provenance={'version':'2026-11-06 controlled-network continuation snapshot',
        'date':'2026-11-06','model':'48 effective units, weighted fast/slow interacting decision layers; original source law retained',
        'evidenceTypes':['conditional mathematics','controlled stochastic simulation','descriptive Bitcoin observation check'],
        'caseSelection':'All cases of each published table are retained. Browser D01 display uses F and RV metrics, and the earlier pulse summary uses horizons 1 and 48; complete source tables are downloadable.',
        'primaryRiskHorizon':8,'secondaryRiskHorizons':[1,48],
        'conditioning':{'bank':2048,'tune':32,'calibration':64,'test':128,'prefix':32,'origin':96,'neighbors':128,
            'features':13,'method':'Equal-weight nearest-neighbor conditional simulation mixture; approximate, not exact posterior.',
            'offlineCosts':'Complete supplied network law and prior, 2048 full labelled simulation histories, 32 tuning and 64 calibration histories.'},
        'channels':{'pairedSeeds':128,'steps':240,'independentAnchorTrainingSeeds':64,'primaryComparisons':10,
            'bootstrapDraws':19999,'multiplicity':'Holm across five arms × two primary metrics'},
        'propagation':{'states':8,'doses':[-24,0,24],'horizons':48,'ensemblePathsPerCell':512,'referencePathsPerCell':4096,
            'intervalMeaning':'Monte Carlo error in a mean; not a future-outcome prediction interval.'},
        'market':{'days':663,'blocks':1989,'barsPerBlock':96,'barMinutes':5,
            'status':'Existing Bitcoin history, descriptive transport check. Blocks are not independent dates. No new independent market forecast test.'}}
    units={'F':'synthetic quantity units','V':'synthetic quantity units','K':'active effective units, not raw exchange executions',
        'r':'log return','RV':'sum of squared log returns over declared horizon',
        'fast':'weighted mean binary direction, dimensionless','slow':'weighted mean binary direction, dimensionless',
        'trace':'weighted adaptation trace, dimensionless','coherence':'absolute weighted fast direction, dimensionless',
        'liquidity':'synthetic positive accommodation state, not observed order-book depth',
        'weight_concentration':'sum of squared normalized positive effective weights, dimensionless',
        'qlike':'dimensionless y/h − log(y/h) − 1; lower is better'}
    scopes={'channels':'Fixed hypothetical economic inputs in the retained simulator; not measured causal effects of actual quant institutions.',
        'inference':'Hidden truth is revealed for validation only. No latent test states or future observations enter estimation.',
        'risk':'Independent simulated cases. Same bank and future labels supplied to all fitted comparisons; MacroGamma has identical 13 macro features.',
        'calibration':'90% split-conformal construction, independent exchangeable simulated units, 64 calibration cases, 59th score. Not state-conditional market coverage.',
        'transport':'Descriptive activity, persistence and support mismatch; model ticks are not calibrated to five-minute market bars.',
        'G':'Centered amplification Var(F)/mean(B) and energy E[F²]/mean(B) are distinct; a shared observed numerator cancels in relative errors.'}
    data={'schemaVersion':1,'provenance':provenance,'units':units,'scopes':scopes,'sources':sources,
          'channels':channels,'propagation':propagation,'inference':inference,'risk':risk,'transport':transport}
    encoded=json.dumps(data,ensure_ascii=False,separators=(',',':'),allow_nan=False)
    (STUDY/'evidence.json').write_text(encoded+'\n')
    (WEB/'assets/data/continuation-evidence.js').write_text('window.ContinuationEvidence='+encoded+';\n')
    (STUDY/'source-manifest.json').write_text(json.dumps({'date':'2026-11-06','sources':sources},indent=2)+'\n')
    shutil.copy2(STUDY/'source-manifest.json',WEB/'downloads/continuation/source-manifest.json')
    print(json.dumps({'sources':len(sources),'browser_bytes':len(encoded.encode()),'test_cases':len(prefixes),
        'd01_display_rows':len(propagation['moments']),'state_validation_rows':len(truth)}))

if __name__=='__main__': main()
