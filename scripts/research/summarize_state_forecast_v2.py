#!/usr/bin/env python3
"""Transparent control re-expression and predeclared practical-gate evaluation."""

from pathlib import Path as _ProjectPath
import sys as _project_sys
_project_sys.path.insert(0, str(_ProjectPath(__file__).resolve().parents[1]))
from _bootstrap import ROOT as PROJECT_ROOT, script_path, resolve_recorded_path
from pathlib import Path
import argparse,csv,hashlib,json
ROOT=PROJECT_ROOT


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run-id',default='state_forecast_v2');args=parser.parse_args();p=ROOT/'results/tables'/args.run_id;checks=ROOT/'results/checks'/args.run_id;metrics=list(csv.DictReader((p/'metrics.csv').open()));primary=list(csv.DictReader((p/'primary_contrasts.csv').open()));out=[]
    for asset,tag in [('ETHUSDT','external_asset'),('BTCUSDT','new_time'),('ETHUSDT','new_time')]:
        for metric in ['qlike','log_mse']:
            values={r['model']:float(r['estimate']) for r in metrics if r['asset']==asset and r['evaluation']==tag and r['metric']==metric and r['day_block_length']=='7'}
            for name,v in values.items():out.append({'asset':asset,'evaluation':tag,'metric':metric,'model':name,'loss':v,'improvement_vs_legacy_HAR_pct':100*(1-v/values['LegacyHAR-Static']),'scope':'Descriptive full-model table; not a replacement for primary matched Gamma comparison'})
    with (p/'legacy_control_summary.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
    ext=next(r for r in primary if r['asset']=='ETHUSDT' and r['evaluation']=='external_asset' and r['metric']=='qlike' and r['day_block_length']=='7');log=next(r for r in primary if r['asset']=='ETHUSDT' and r['evaluation']=='external_asset' and r['metric']=='log_mse' and r['day_block_length']=='7');forward=[r for r in primary if r['evaluation']=='new_time' and r['metric']=='qlike' and r['day_block_length']=='7'];gate=float(ext['improvement_pct'])>=5 and float(ext['ci_low'])>0 and float(log['improvement_pct'])>=0 and all(float(r['improvement_pct'])>=0 for r in forward)
    summary={'status':'pass','practical_numeric_gate_met':gate,'stable_volume_increment_established':False,'deployment_or_trading_utility_validated':False,'external_asset_primary':ext,'new_time_primary':forward,'distinct_new_time_dates':25,'off_interpretation':'Exact algorithmic fallback to return-only, not statistical proof that volume has no information','gate_scope':'Frozen project research gate; new-time length too short for stable deployment conclusions even if numeric gate passed'}
    outdir=ROOT/'results/analysis'/args.run_id;outdir.mkdir(parents=True,exist_ok=True);(outdir/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');(checks/'reporting_note.json').write_text(json.dumps({'status':'pass','script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'legacy_control_summary':'Arithmetic re-expression of all predeclared model metrics, no new fit','compensation_theory':'Post-analysis explanatory construction only; no new forecast model'},indent=2)+'\n');print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
