#!/usr/bin/env python3
"""Rebuild all numerical tables in a new directory and compare every value."""
from pathlib import Path
import json,os,shutil,subprocess,sys,tempfile,hashlib
import numpy as np
import pandas as pd

R=Path(__file__).resolve().parent

def main():
    out=Path(tempfile.mkdtemp(prefix='collective_information_reproduction_'))
    for name in ['code','inputs','tables','fits','checks','analysis','figures']:(out/name).mkdir()
    for p in (R/'code').glob('*.py'):shutil.copy2(p,out/'code'/p.name)
    shutil.copy2(R/'inputs/macro_observables.npz',out/'inputs/macro_observables.npz');shutil.copy2(R/'PROTOCOL.md',out/'PROTOCOL.md')
    env=os.environ.copy();env.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MPLCONFIGDIR=str(out/'private_mpl'))
    with (out/'run.log').open('w') as log:
        for script in ['run.py','evaluate.py','accounting.py']:
            subprocess.run([sys.executable,str(out/'code'/script)],env=env,stdout=log,stderr=subprocess.STDOUT,check=True);print('Rebuilt',script,flush=True)
    checks=[]
    for p in sorted((R/'tables').glob('*.csv')):
        q=out/'tables'/p.name;assert q.exists(),p.name;old=pd.read_csv(p);new=pd.read_csv(q);assert old.shape==new.shape and list(old.columns)==list(new.columns),p.name;maxerr=0.
        for key in old:
            if pd.api.types.is_numeric_dtype(old[key]) and pd.api.types.is_numeric_dtype(new[key]):
                np.testing.assert_allclose(old[key],new[key],rtol=1e-10,atol=1e-12,equal_nan=True,err_msg=p.name+':'+key)
                if old[key].notna().any():maxerr=max(maxerr,float(np.nanmax(abs(old[key]-new[key]))))
            else:assert list(old[key].fillna('').astype(str))==list(new[key].fillna('').astype(str)),(p.name,key)
        checks.append(dict(table=p.name,rows=len(old),maximum_absolute_difference=maxerr))
    assert json.loads((R/'fits/selection.json').read_text())==json.loads((out/'fits/selection.json').read_text())
    report=dict(status='pass',input_sha256=hashlib.sha256((R/'inputs/macro_observables.npz').read_bytes()).hexdigest(),protocol_sha256=hashlib.sha256((R/'PROTOCOL.md').read_bytes()).hexdigest(),tables=len(checks),checks=checks,isolated_directory='fresh temporary directory outside the study',raw_input_reaggregation=False,scope='fresh numerical model reproduction from inherited derived five-minute input')
    (R/'checks/reproduction.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));print('Isolated run:',out)

if __name__=='__main__':main()
