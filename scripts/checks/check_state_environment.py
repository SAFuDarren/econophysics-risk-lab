"""Check the website evidence against the separately packaged numerical tables."""
from pathlib import Path
import csv
import json
import math
import re
import zipfile

ROOT = Path(__file__).resolve().parents[2]
STUDY = ROOT/'studies/state_environment_v9'
WEB = ROOT/'web'

def main():
    source=(WEB/'assets/data/state-environment-evidence.js').read_text()
    data=json.loads(source.split('window.StateEnvironmentEvidence=',1)[1].strip().rstrip(';'))
    with (STUDY/'tables/response_surface_cells.csv').open() as f:
        cells=list(csv.DictReader(f))
    assert len(data['surface']['cells'])==len(cells)==29
    comparisons=0
    for browser,record in zip(data['surface']['cells'],cells):
        for key,value in record.items():
            if key=='kind':assert browser[key]==value
            else:assert math.isclose(float(browser[key]),float(value),rel_tol=1e-12,abs_tol=1e-18),(key,browser[key],value)
            comparisons+=1
    downloads=WEB/'downloads/state-environment'
    for name in ['response_surface_cells.csv','covariance_effects_by_environment.csv','paired_interactions.csv','precision_budget.csv','information_summary.csv','market_score_summary.csv','market_primary_contrasts.csv','market_controls_summary.csv']:
        assert (STUDY/'tables'/name).read_bytes()==(downloads/name).read_bytes(),name
    with zipfile.ZipFile(downloads/'study-data.zip') as z:
        for p in STUDY.rglob('*'):
            if p.is_file():assert z.read('state_environment_v9/'+str(p.relative_to(STUDY)))==p.read_bytes(),str(p)
    page=(WEB/'risk-environment.html').read_text()
    assert 'data-en' in page and 'data-zh' in page
    assert 'lab.html#research-bench' in page
    assert 'risk-environment.html' in (WEB/'lab.html').read_text()
    for name in ['social-preview.jpg','trading-preview-en.webp']:
        assert 'web/assets/'+name in (ROOT/'README.md').read_text()
    assert not re.search(r'PC5253|Group 11',page,re.I)
    assert (WEB/'downloads/reports/research-report-en-v3.pdf').is_file()
    print(json.dumps({'status':'pass','browser_numeric_values_matched':comparisons,'fixed_cells':len(cells),'download_and_zip_parity':True,'preview_links_retained':True},indent=2))

if __name__=='__main__':main()
