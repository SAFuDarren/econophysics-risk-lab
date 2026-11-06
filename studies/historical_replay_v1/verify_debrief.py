#!/usr/bin/env python3
"""Independent NumPy/pandas recalculation of the browser's conditional map."""
from pathlib import Path
import json
import numpy as np,pandas as pd
R=Path(__file__).resolve().parent;data=json.loads((R.parent.parent/'web/assets/data/historical-replays-v1.json').read_text());traces=pd.read_csv(R/'tables/debrief-traces.csv');maxerr={};checks=0
for c in data['cases']:
 bars=pd.DataFrame(c['bars']).set_index('tick');bars['r']=np.log(bars.close/bars.close.shift());z=bars.loc[-29:0];f=z.flowBase.to_numpy();r=z.r.to_numpy();beta=max(0.,np.mean((f-f.mean())*(r-r.mean()))/np.var(f));alpha=r.mean()-beta*f.mean();eta=np.mean((r-alpha-beta*f)**2)
 for row in traces[traces.caseId==c['id']].to_dict('records'):
  t=int(row['tick']);slow=bars.loc[t-14:t];fast=bars.loc[t-2:t];bslow=slow.squaredSizeBase.mean();bfast=fast.squaredSizeBase.mean();vf=np.var(slow.flowBase);g=vf/bslow;me=(alpha+beta*slow.flowBase.mean())**2;h=me+beta**2*bfast*g+eta;h1=me+beta**2*bfast+eta
  actual=dict(g=g,modelSecondMoment=h,independentSecondMoment=h1,observedTrailingRmsPct=100*np.sqrt(np.mean(slow.r**2)),beta=beta,bFast=bfast,bSlow=bslow,varFlow=vf,meanEnergy=me,flowEnergy=beta**2*bfast*g,residualEnergy=eta)
  for key,value in actual.items():
   assert np.isclose(value,row[key],rtol=1e-9,atol=1e-13),(c['id'],t,key,value,row[key]);maxerr[key]=max(maxerr.get(key,0),abs(value-row[key]));checks+=1
report=dict(status='pass',origins=len(traces),scalar_comparisons=checks,maximum_absolute_errors=maxerr,scope='Independent numerical recalculation of execution baseline, centred amplification and local conditional response map; no predictive-performance claim')
(R/'checks/debrief-independent.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
