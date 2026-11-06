"""Normalize portable QA metadata and seal the completed workstream artifacts."""
from pathlib import Path
import hashlib,json

R=Path(__file__).resolve().parents[1]

def normalized(x):
    if isinstance(x,dict):return {k:normalized(v) for k,v in x.items()}
    if isinstance(x,list):return [normalized(v) for v in x]
    if isinstance(x,str):return x.replace(str(R)+'/', '').replace('outputs/Collective_Dynamics_Information_Study_v1/','')
    return x

def main():
    for p in (R/'checks').glob('*.json'):
        p.write_text(json.dumps(normalized(json.loads(p.read_text())),indent=2))
    causal=json.loads((R/'checks/causal_audit.json').read_text());repro=json.loads((R/'checks/reproduction.json').read_text());fig=json.loads((R/'checks/figure_export_audits.json').read_text())
    assert repro['status']=='pass' and repro['tables']==8 and all(x['maximum_absolute_difference']==0 for x in repro['checks'])
    assert causal['target_after_all_inputs'] and causal['date_budget_exact'] and causal['future_return_forecast_max_difference']==0 and causal['prefix_forecast_max_difference']==0 and causal['all_return_pressure_max_difference']==0
    assert all(x['exit_code']==0 for x in fig)
    acceptance=dict(status='ready_for_independent_review',scope='information-efficiency numerical workstream',protocol='PROTOCOL.md',uncertainty_audit='UNCERTAINTY_AUDIT_ADDENDUM.md',numerical_tables=8,fresh_reproduction='pass; zero differences',chronology='pass',information_budget='all fitting inside 30/60/120/240 days; zero microscopic prior',figures='2 actual figures; font, alignment and collision QA pass',scientific_result='no established information-efficiency or restriction-specific prediction advantage',full_game_network_empirically_validated=False,website_summary='website-summary.json',parent_final_release_review='required')
    (R/'checks/acceptance.json').write_text(json.dumps(acceptance,indent=2))
    paths=[p for p in R.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='MANIFEST.json'];manifest={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)};(R/'MANIFEST.json').write_text(json.dumps(dict(sha256=manifest),indent=2));print(json.dumps(acceptance,indent=2));print('Manifest entries',len(manifest))

if __name__=='__main__':main()
