"""Verify the interactive payload, derived downloads and curated study packages."""
from pathlib import Path
import csv,json,math,re,zipfile
R=Path(__file__).resolve().parents[2]
W=R/'web';M=R/'studies/strategy_ecology_v10';E=R/'studies/real_factor_validation_v11'
comparisons=0
def rows(p):
    with p.open(newline='') as f:return list(csv.DictReader(f))
def match(browser,saved):
    global comparisons
    for k,v in browser.items():
        assert k in saved, k
        if isinstance(v,(int,float)):assert math.isclose(v,float(saved[k]),rel_tol=1e-12,abs_tol=1e-18),(k,v,saved[k])
        else:assert v==saved[k],(k,v,saved[k])
        comparisons+=1
def main():
    s=(W/'assets/data/strategy-ecology-evidence.js').read_text()
    data=json.loads(s[s.index('=')+1:].strip().rstrip(';'))
    cells=rows(M/'tables/model-cells.csv');lookup={(x['source_family'],int(x['scenario_id'])):x for x in cells}
    assert len(cells)==56 and len(data['cells'])==47
    for b in data['cells']:match(b,lookup[(b['source_family'],b['scenario_id'])])
    contrasts=rows(M/'tables/model-contrasts.csv')
    for family,key in [('factors','factorContrasts'),('scale','scaleContrasts')]:
        saved=[x for x in contrasts if x['source_family']==family]
        assert len(saved)==len(data[key])==8
        for b,r in zip(data[key],saved):match(b,r)
    for key,name in [('allocationPrimary','allocation-primary.csv'),('allocationSummary','allocation-summary.csv'),('allocationTrajectories','allocation-trajectories.csv')]:
        saved=rows(M/'tables'/name);assert len(saved)==len(data[key])
        for b,r in zip(data[key],saved):match(b,r)
    em=data['empirical'];assert em['summary']==json.loads((E/'results_summary.json').read_text())
    assert em['protocol']==json.loads((E/'PROTOCOL.json').read_text())
    saved=[x for x in rows(E/'tables/predictions_scored.csv') if x['role']=='evaluation']
    assert len(saved)==len(em['monthly'])==81
    for b,r in zip(em['monthly'],saved):match(b,r)
    months={x['future_month'] for x in saved}
    saved=[x for x in rows(E/'tables/computed_allocations.csv') if x['future_month'] in months]
    assert len(saved)==len(em['allocations'])==243
    for b,r in zip(em['allocations'],saved):match(b,r)
    for directory,study in [('strategy-ecology',M),('real-factors',E)]:
        dl=W/'downloads'/directory
        with zipfile.ZipFile(dl/'study-data.zip') as z:
            for p in study.rglob('*'):
                if p.is_file():assert z.read(study.name+'/'+str(p.relative_to(study)))==p.read_bytes(),p
        if study==M:
            for p in (M/'tables').glob('*.csv'):assert p.read_bytes()==(dl/p.name).read_bytes()
            assert (M/'checks/study-summary.json').read_bytes()==(dl/'study-summary.json').read_bytes()
        else:
            for a,b in {'monthly-results.csv':'tables/predictions_scored.csv','primary-contrasts.csv':'tables/primary_contrasts.csv','forecast-scores.csv':'tables/forecast_scores.csv','computed-allocations.csv':'tables/computed_allocations.csv','study-summary.json':'results_summary.json'}.items():assert (dl/a).read_bytes()==(E/b).read_bytes()
    html=(W/'strategy-ecology.html').read_text()
    assert not re.search(r'PC5253|Group 11|Lorem ipsum',html,re.I)
    assert 'strategy-ecology.html' in (W/'lab.html').read_text()
    for name in ['social-preview.jpg','trading-preview-en.webp']:assert 'web/assets/'+name in (R/'README.md').read_text()
    assert (W/'downloads/reports/research-report-en-v4.pdf').is_file()
    print(json.dumps({'status':'pass','browser_numeric_fields':comparisons,'model_cells':47,'observed_evaluation_months':81,'computed_allocations':243,'download_and_zip_parity':True},indent=2))
if __name__=='__main__':main()
