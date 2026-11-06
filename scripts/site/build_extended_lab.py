"""Rebuild the retained four-module laboratory from its shared source files."""

from pathlib import Path as _ProjectPath
import sys as _project_sys
_project_sys.path.insert(0, str(_ProjectPath(__file__).resolve().parents[1]))
from _bootstrap import ROOT as PROJECT_ROOT, script_path, resolve_recorded_path
from pathlib import Path
import json
ROOT=PROJECT_ROOT
a=ROOT/'apps/risk_lab_v1';s=a/'src'
payload=(a/'data.json').read_text();json.loads(payload)
html=(s/'template.html').read_text().replace('__STYLE__',(s/'style.css').read_text()).replace('__DATA__',payload.replace('</','<\\/')).replace('__SCRIPT__',(s/'app.js').read_text())
(ROOT/'web/advanced/index.html').write_text(html)
print('Rebuilt web/advanced/index.html from retained source and derived data.')
