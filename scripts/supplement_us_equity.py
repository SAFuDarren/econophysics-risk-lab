#!/usr/bin/env python3
"""Labelled post-analysis interpretation: exact projection theory and P&L redundancy."""
from pathlib import Path
from fractions import Fraction as F
from itertools import product
import csv,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import numpy as np
from econophysics.us_equity import write_csv,block_weights

def main():
    table=ROOT/'results/tables/us_equity_v1';check=ROOT/'results/checks/us_equity_v1';cfg=json.loads((ROOT/'configs/us_equity_v1.json').read_text());rows=list(csv.DictReader((table/'strategy_daily.csv').open()));names=list(cfg['strategy_library']['families']);strategy_names=[f'{f}-{l}' for f,ls in cfg['strategy_library']['families'].items() for l in ls];dates=sorted(set(r['date'] for r in rows));lookup={(r['date'],r['strategy']):float(r['net_5bp']) for r in rows};pnl=np.array([[lookup[d,s] for s in strategy_names] for d in dates]);train=(np.array(dates)>='2011-01-01')&(np.array(dates)<'2018-01-01');c=np.corrcoef(pnl[train],rowvar=False);a,b=max(((a,b) for a in range(6) for b in range(a+1,6)),key=lambda pair:c[pair]);rng=np.random.default_rng(cfg['seed']+999);summary=[]
    for split in ['historical_test','confirmation']:
        lo,hi=cfg['splits'][split];mask=(np.array(dates)>=lo)&(np.array(dates)<hi);x=pnl[mask,a];y=pnl[mask,b];w=block_weights(len(x),20,cfg['bootstrap']['replicates'],rng);mx=w@x/len(x);my=w@y/len(x);cross=w@(x*y)/len(x)-mx*my;vx=w@(x*x)/len(x)-mx*mx;vy=w@(y*y)/len(x)-my*my;bs=cross/np.sqrt(vx*vy);rho=float(np.corrcoef(x,y)[0,1]);neff=2/(1+rho);nbs=2/(1+bs)
        summary.append({'split':split,'strategy_a':strategy_names[a],'strategy_b':strategy_names[b],'training_selection_correlation':float(c[a,b]),'daily_net_correlation':rho,'corr_ci_low':float(np.quantile(bs,.025)),'corr_ci_high':float(np.quantile(bs,.975)),'equal_risk_two_sleeve_effective_count':neff,'neff_ci_low':float(np.quantile(nbs,.025)),'neff_ci_high':float(np.quantile(nbs,.975)),'days':len(x),'scope':'Post-analysis descriptive diagnostic; pair rule uses 2011-2017 only, specified after viewing primary results. Equal-risk count is not actual portfolio exposure or independent alpha.'})
    write_csv(table/'redundancy_diagnostic.csv',summary)
    # Four latent cluster actions, three observable coordinates, two P&L projections.
    q=F(1,5);B=[[F(2),F(1),F(0)],[F(1),F(0),F(1)],[F(0),F(1),F(2)],[F(1),F(-1),F(0)]];W=[[F(1,2),F(1,2),F(0)],[F(1,2),F(-1,2),F(1)]];expected=[[F(0) for _ in range(2)] for _ in range(2)];mass=F(0)
    for actions in product([-1,0,1],repeat=4):
        probability=F(1)
        for action in actions:probability*=q/2 if action else 1-q
        z=[sum(B[k][j]*actions[k] for k in range(4)) for j in range(3)];p=[sum(W[i][j]*z[j] for j in range(3)) for i in range(2)];mass+=probability
        for a in range(2):
            for b in range(2):expected[a][b]+=probability*p[a]*p[b]
    analytical=[[q*sum(sum(W[a][j]*B[k][j] for j in range(3))*sum(W[b][j]*B[k][j] for j in range(3)) for k in range(4)) for b in range(2)] for a in range(2)];assert mass==1 and expected==analytical
    theory={'status':'pass','scope':'Post-analysis conditional observation extension; no market calibration or new predictive model','enumerated_states':81,'q':str(q),'covariance_by_enumeration':[[str(v) for v in row] for row in expected],'covariance_by_projection_formula':[[str(v) for v in row] for row in analytical],'original_research_spine':'Finite-cluster second moment S2 under the stated herding assumptions; real correlations do not identify criticality','source_sha256':hashlib.sha256((ROOT/'docs/theory/COLLECTIVE_PNL_v1.md').read_bytes()).hexdigest()};(check/'collective_pnl_theory.json').write_text(json.dumps(theory,indent=2)+'\n')
    (check/'reporting_notes.json').write_text(json.dumps({'post_analysis_extensions':['Conditional projection theory with exact finite enumeration','Redundancy diagnostic with paired 20-session blocks; exploratory, not a newly untouched test'],'bootstrap_zero_tail_mass':'Raw p_bootstrap_approx=0 means no crossing among 4999 resamples, not exact probability zero. Report at two-sided finite-resample resolution below about 0.0004; these are approximate resampling-tail measures, not exact null tests. Primary Holm family retained.','no_new_alpha_claim':True,'no_profitable_allocation_claim':True},indent=2)+'\n');print(json.dumps({'status':'pass','redundancy_pair':[summary[0]['strategy_a'],summary[0]['strategy_b']],'theory_exact_states':81,'summary':summary},indent=2))

if __name__=='__main__':main()
