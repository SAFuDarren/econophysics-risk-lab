"""Rebuild the retained four-module laboratory from its shared source files."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
a=ROOT/'apps/risk_lab_v1';s=a/'src'
payload=(a/'data.json').read_text();json.loads(payload)
html=(s/'template.html').read_text().replace('__STYLE__',(s/'style.css').read_text()).replace('__DATA__',payload.replace('</','<\\/')).replace('__SCRIPT__',(s/'app.js').read_text())
(ROOT/'web/advanced/index.html').write_text(html)
print('Rebuilt web/advanced/index.html from retained source and derived data.')
