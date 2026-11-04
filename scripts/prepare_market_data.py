#!/usr/bin/env python3
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from econophysics.market_data import prepare_dataset
if __name__=='__main__':
    result=prepare_dataset(ROOT,'binance_btcusdt_2025_5m_v1')
    print(json.dumps({k:v for k,v in result.items() if k!='source_files'},indent=2,ensure_ascii=False))
