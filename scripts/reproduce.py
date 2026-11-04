#!/usr/bin/env python3
"""Unified entry points for the public research snapshot."""
from pathlib import Path
import argparse,datetime,json,os,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--profile',choices=['quick','theory','site','notebooks','forecast'],default='quick')
 p.add_argument('--destination',type=Path)
 a=p.parse_args();stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
 out=(ROOT/'.runs'/f'{a.profile}-{stamp}');out.mkdir(parents=True,exist_ok=False)
 env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',MPLCONFIGDIR=str(ROOT/'.cache/matplotlib'),IPYTHONDIR=str(ROOT/'.cache/ipython'),JUPYTER_RUNTIME_DIR=str(out/'jupyter-runtime'))
 (ROOT/'.cache/ipython').mkdir(parents=True,exist_ok=True)
 (ROOT/'.cache/matplotlib').mkdir(parents=True,exist_ok=True)
 commands=[]
 def run(command):
  commands.append(command);subprocess.run(command,cwd=ROOT,env=env,check=True)
 if a.profile in ['quick','theory']:
  run([sys.executable,'scripts/check_theory_foundations.py','--output',str(out/'theory')])
 if a.profile=='quick':
  run([sys.executable,'-m','unittest','discover','-s','tests','-p','test_*.py','-v'])
  node=shutil.which('node')
  if node:run([node,'tests/test_web_math.cjs'])
  else:print('JavaScript checks require Node.js; the Python checks completed.')
 if a.profile=='site':
  run([sys.executable,'scripts/check_site.py'])
  node=shutil.which('node')
  if not node:raise RuntimeError('Node.js is required for the site profile')
  run([node,'--check','web/assets/site.js']);run([node,'tests/test_web_math.cjs'])
 if a.profile=='forecast':
  dest=a.destination or out/'reconstructed-study'
  run([sys.executable,'scripts/reproduce_forecast_study.py','--destination',str(dest.resolve())])
 if a.profile=='notebooks':
  import nbformat
  from nbclient import NotebookClient
  from jupyter_client import KernelManager
  notebooks=[]
  for path in sorted((ROOT/'notebooks').glob('*.ipynb')):
   nb=nbformat.read(path,as_version=4);nbformat.validate(nb)
   km=KernelManager(kernel_name='python3');km.kernel_spec.argv=[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}']
   client=NotebookClient(nb,km=km,timeout=300,resources={'metadata':{'path':str(ROOT/'notebooks')}})
   client.execute(env=env)
   nbformat.validate(nb);nbformat.write(nb,path)
   shutil.copyfile(path,ROOT/'web/downloads'/path.name)
   notebooks.append({'notebook':path.name,'executed_cells':sum(c.cell_type=='code' for c in nb.cells),'errors':sum(o.output_type=='error' for c in nb.cells if c.cell_type=='code' for o in c.outputs)})
  assert len(notebooks)==3
  (out/'notebooks.json').write_text(json.dumps(notebooks,indent=2))
  print(json.dumps(notebooks,indent=2))
 report={'status':'pass','profile':a.profile,'commands':commands,'output':str(out.relative_to(ROOT))}
 (out/'summary.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
