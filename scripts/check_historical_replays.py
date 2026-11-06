"""Standard-library release gate for historical replay source/selection integrity."""
from pathlib import Path
import json,hashlib,csv,gzip,math
R=Path(__file__).resolve().parents[1];S=R/'studies/historical_replay_v1';D=json.loads((R/'web/assets/data/historical-replays-v1.json').read_text());report=json.loads((S/'checks/data-verification.json').read_text());sources=json.loads((S/'inputs/source-manifest.json').read_text());assert report['status']=='pass' and len(sources['sources'])==52 and all(x['official_checksum_match'] for x in sources['sources']);assert hashlib.sha256((S/'inputs/minute-observables.csv.gz').read_bytes()).hexdigest()==D['input_sha256']==report['input_sha256']
with gzip.open(S/'inputs/minute-observables.csv.gz','rt') as f:rows=list(csv.DictReader(f))
assert len(rows)==37440;days={}
for r in rows:days.setdefault(r['date'],[]).append(r)
manifest=json.loads((S/'MANIFEST.json').read_text())
for item in manifest['files']:assert hashlib.sha256((S/item['path']).read_bytes()).hexdigest()==item['sha256'],item['path']
assert hashlib.sha256((R/'web/assets/data/historical-replays-v1.json').read_bytes()).hexdigest()==manifest['web_payload_sha256']
checks=0
for c in D['cases']:
 g=days[c['review']['date']];start=c['review']['minute']-20;prices={b['tick']:b['close'] for b in c['bars']};d=c['review']['direction'];future=[d*(prices[t]/prices[20]-1) for t in range(21,111)];assert max(future)>=.02 and math.isclose(max(future),c['review']['favorableMove'],rel_tol=1e-12)
 for b in c['bars']:
  raw=g[start+b['tick']]
  assert all(b[k]==float(raw[k]) for k in ['open','high','low','close','volume']);checks+=1
 for a in c['alerts']:
  i=start+a['tick'];name='largeBuyQuote' if a['direction']==1 else 'largeSellQuote';values=[float(r[name]) for r in g[i-122:i+1]];past=sorted(sum(values[j:j+3]) for j in range(120));rank=119*.9;threshold=max(1000000,past[int(rank)]+(rank-int(rank))*(past[math.ceil(rank)]-past[int(rank)]));assert math.isclose(threshold,a['pastThreshold'],rel_tol=1e-10,abs_tol=1e-5);assert math.isclose(sum(values[-3:]),a['sideQuote'],rel_tol=1e-10,abs_tol=1e-5);checks+=1
assert len(D['cases'])==9 and len(days)==26
print(json.dumps({'status':'pass','cases':9,'source_dates':26,'official_archives':52,'minute_rows':len(rows),'independent_candle_and_past_threshold_checks':checks}))
