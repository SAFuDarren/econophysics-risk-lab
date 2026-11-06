#!/usr/bin/env python3
"""Rebuild selection from the complete derived pool, and compare exact artifacts."""
from pathlib import Path
import json,subprocess,sys,tempfile,hashlib
R=Path(__file__).resolve().parent
out=Path(tempfile.mkdtemp(prefix='historical_replay_reproduction_'))
subprocess.run([sys.executable,str(R/'code/curate.py'),'--input',str(R/'inputs/minute-observables.csv.gz'),'--output',str(out)],check=True)
checks=[]
for name,expected in [('all-alerts.csv',R/'tables/all-alerts.csv'),('eligible-candidates.csv',R/'tables/eligible-candidates.csv'),('selected-cases.csv',R/'tables/selected-cases.csv'),('historical-replays-v1.json',R.parent.parent/'web/assets/data/historical-replays-v1.json')]:
 actual=out/name;assert actual.read_bytes()==expected.read_bytes(),name;checks.append(dict(file=name,sha256=hashlib.sha256(actual.read_bytes()).hexdigest(),byte_identical=True))
print(json.dumps(dict(status='pass',scope='All selection artifacts rebuilt from the complete 26-day derived pool; raw acquisition is a separate command',checks=checks),indent=2))
