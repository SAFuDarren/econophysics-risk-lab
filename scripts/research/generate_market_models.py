#!/usr/bin/env python3
"""Calibrate three declared ER comparators on H1; simulate independent H2-length paths."""

from pathlib import Path as _ProjectPath
import sys as _project_sys
_project_sys.path.insert(0, str(_ProjectPath(__file__).resolve().parents[1]))
from _bootstrap import ROOT as PROJECT_ROOT, script_path, resolve_recorded_path
from pathlib import Path
import argparse,csv,gzip,hashlib,io,json,math,sys,time
ROOT=PROJECT_ROOT;sys.path.insert(0,str(ROOT/'src'))
import numpy as np
from econophysics.model import Parameters,derived_seed,simulate_aggregates
from econophysics.physics_inference import finite_er_moments


def main():
    p=argparse.ArgumentParser();p.add_argument('--run-id',default='real_market_v1');args=p.parse_args()
    if not args.run_id.replace('_','').replace('-','').isalnum():p.error('invalid run-id')
    cfgpath=ROOT/'configs/real_market_v1.json';cfg=json.loads(cfgpath.read_text());source=ROOT/'data/processed'/cfg['dataset']/'bars.csv'
    data=list(csv.DictReader(source.open()));train=[r for r in data if r['split']=='calibration'];hold=[r for r in data if r['split']=='holdout']
    r=np.array([float(x['return_log']) for x in train]);v=np.array([float(x['volume']) for x in train]);mean=float(v.mean());var=float(v.var());sigma=float(r.std());cv2=var/mean**2
    tables=ROOT/'results/tables'/args.run_id;checks=ROOT/'results/checks'/args.run_id
    if tables.exists() or checks.exists():p.error('run already exists')
    tables.mkdir(parents=True);checks.mkdir(parents=True);(checks/'locked_config.json').write_text(json.dumps(cfg,indent=2)+'\n')
    n=cfg['model']['n'];parameters=[]
    for rho in cfg['model']['rho']:
        theoretical=finite_er_moments(n,rho);a2=theoretical['s2'];q=a2/(a2+n*n*cv2);u=mean/(q*n);lam=n*sigma/math.sqrt(q*a2)
        parameters.append({'rho':rho,'n':n,'q':q,'a':q/2,'unit_order':u,'lambda_impact':lam,'calibration_mean_volume':mean,'calibration_var_volume':var,'calibration_var_return':sigma*sigma,
                           'theory_s2':a2,'theory_s3':theoretical['s3'],'theory_delta':theoretical['s3']/(n*a2),'zero_volume_probability_lower_bound':(1-q)**n})
    with (tables/'calibration_parameters.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(parameters[0]));w.writeheader();w.writerows(parameters)
    source_paths=[cfgpath,Path(__file__).resolve(),ROOT/'src/econophysics/model.py',ROOT/'src/econophysics/physics_inference.py',source]
    record={'status':'running','command':f'python3 scripts/research/generate_market_models.py --run-id {args.run_id}','source_sha256':{str(x.relative_to(ROOT)):hashlib.sha256(x.read_bytes()).hexdigest() for x in source_paths},
            'calibration_rows':len(train),'holdout_rows':len(hold),'replications_per_rho':cfg['model']['replications'],'scope':'Conditional comparator calibration only; no rho selected or asserted as real-network truth','member_review':'not_run'}
    (checks/'model_run_record.json').write_text(json.dumps(record,indent=2)+'\n');started=time.perf_counter();seed_rows=[]
    with (tables/'model_series.csv.gz').open('wb') as binary:
        with gzip.GzipFile(fileobj=binary,mode='wb',mtime=0) as compressed:
            with io.TextIOWrapper(compressed,newline='') as text:
                writer=csv.DictWriter(text,fieldnames=['rho','replication','t','r','V']);writer.writeheader()
                for parameter in parameters:
                    for rep in range(cfg['model']['replications']):
                        seed=derived_seed(cfg['seed'],f'market-model:{parameter["rho"]}:{rep}')
                        params=Parameters(n=n,rho=parameter['rho'],a=parameter['a'],lambda_impact=parameter['lambda_impact'],unit_order=parameter['unit_order'])
                        obs=simulate_aggregates(params,len(hold),seed)
                        writer.writerows({'rho':parameter['rho'],'replication':rep,'t':i,**row} for i,row in enumerate(obs))
                        seed_rows.append({'rho':parameter['rho'],'replication':rep,'seed':seed,'periods':len(obs)})
                    print(f'Market comparator complete: rho={parameter["rho"]}; q={parameter["q"]:.6f}; seconds={time.perf_counter()-started:.1f}',flush=True)
    with (tables/'model_seeds_NOT_OBSERVATIONS.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(seed_rows[0]));w.writeheader();w.writerows(seed_rows)
    record.update(status='pass',paths=len(seed_rows),total_simulated_periods=sum(x['periods'] for x in seed_rows),seconds=time.perf_counter()-started,
                  outputs_sha256={x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in tables.iterdir() if x.is_file()})
    (checks/'model_run_record.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({'status':'pass','calibration':parameters,'periods':record['total_simulated_periods']},indent=2),flush=True)


if __name__=='__main__':main()
