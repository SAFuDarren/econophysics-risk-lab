"""Standard-library release checks; full numerical re-estimation is separately reproducible."""

from pathlib import Path as _ProjectPath
import sys as _project_sys
_project_sys.path.insert(0, str(_ProjectPath(__file__).resolve().parents[1]))
from _bootstrap import ROOT as PROJECT_ROOT, script_path, resolve_recorded_path
from pathlib import Path
import csv,hashlib,json,math,re

ROOT=PROJECT_ROOT;S=ROOT/'studies/collective_dynamics_v1'
def main():
    manifest=json.loads((S/'MANIFEST.json').read_text())['sha256']
    for rel,digest in manifest.items():assert hashlib.sha256((S/rel).read_bytes()).hexdigest()==digest,rel
    summary=json.loads((S/'website-summary.json').read_text());assert summary['status']=='no_incremental_advantage'
    page=(ROOT/'web/findings.html').read_text();block=page.split('id="information-efficiency"',1)[1].split('</section>',1)[0]
    for row in summary['primary_scores']:
        if row['metric']=='qlike' and row['model'] in ['ReturnHAR','MacroStat','PressureAR','MechanismSelected']:assert f"{row['mean']:.6f}" in block
    audit=json.loads((S/'checks/causal_audit.json').read_text());assert audit['microscopic_calibration_labels']==0 and audit['warmup_days_outside_budget']==0
    assert audit['future_return_forecast_max_difference']==0 and audit['prefix_forecast_max_difference']==0 and audit['all_return_pressure_max_difference']==0
    with (S/'tables/predictions.csv').open() as f:rows=list(csv.DictReader(f))
    assert len(rows)==10728
    for row in rows:assert math.isfinite(float(row['forecast_rv'])) and float(row['forecast_rv'])>0
    assert (ROOT/'web/assets/social-preview.jpg').exists() and 'web/assets/social-preview.jpg' in (ROOT/'README.md').read_text()
    print(json.dumps(dict(status='pass',study_files=len(manifest),prediction_rows=len(rows),display_values=16,source_hashes='pass',chronology_audits='pass',original_preview_retained=True),indent=2))
if __name__=='__main__':main()
