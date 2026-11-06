
from pathlib import Path as _ProjectPath
import sys as _project_sys
_project_sys.path.insert(0, str(_ProjectPath(__file__).resolve().parents[1]))
from _bootstrap import ROOT as PROJECT_ROOT, script_path, resolve_recorded_path
#!/usr/bin/env python3
from pathlib import Path
import json,sys
ROOT=PROJECT_ROOT;sys.path.insert(0,str(ROOT/'src'))
from econophysics.market_data import prepare_dataset
if __name__=='__main__':
    result=prepare_dataset(ROOT,'binance_btcusdt_2025_5m_v1')
    print(json.dumps({k:v for k,v in result.items() if k!='source_files'},indent=2,ensure_ascii=False))
