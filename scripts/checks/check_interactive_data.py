"""Compare browser replay with saved source pairs and independent path statistics."""

from pathlib import Path as _ProjectPath
import sys as _project_sys
_project_sys.path.insert(0, str(_ProjectPath(__file__).resolve().parents[1]))
from _bootstrap import ROOT as PROJECT_ROOT, script_path, resolve_recorded_path
from pathlib import Path
import csv
import gzip
import hashlib
import json
import math

ROOT = PROJECT_ROOT


def main():
    payload = json.loads((ROOT / 'web/assets/data/memory-path.json').read_text())
    source = ROOT / payload['source']
    assert hashlib.sha256(source.read_bytes()).hexdigest() == payload['source_sha256']
    config = json.loads((ROOT / 'configs/state_forecast_v2.json').read_text())['mechanism']
    assert payload['config'] == config
    arms = {key: [] for key in config['arms']}
    with gzip.open(source, 'rt') as stream:
        for row in csv.DictReader(stream):
            if int(row['replication']) == payload['replication']:
                arms[row['arm']].append([float(row['r']), float(row['V'])])
    assert arms == payload['arms']
    assert all(len(values) == 8192 for values in arms.values())
    assert sorted(arms['PersistentActivity']) == sorted(arms['ShuffledActivity'])
    metrics = list(csv.DictReader((ROOT / 'results/tables/state_mechanism_v2/path_metrics.csv').open()))
    fixture = {row['arm']: row for row in metrics if int(row['replication']) == payload['replication']}
    checks = 0
    for arm, pairs in arms.items():
        r = [pair[0] for pair in pairs]
        v = [pair[1] for pair in pairs]
        mean_v = math.fsum(v) / len(v)
        mean_r = math.fsum(r) / len(r)
        variance_r = math.fsum((x - mean_r) ** 2 for x in r) / len(r)
        for observed, key in [(mean_v, 'mean_volume'), (variance_r, 'return_variance')]:
            assert math.isclose(observed, float(fixture[arm][key]), rel_tol=1e-12, abs_tol=1e-18)
            checks += 1
    source_map = json.loads((ROOT / 'web/assets/data/source-map.json').read_text())
    for figure in source_map['figures']:
        assert (ROOT / figure['source']).read_bytes() == (ROOT / 'web/assets/figures' / (figure['id'] + '.svg')).read_bytes()
        checks += 1
    print(json.dumps({'status': 'pass', 'checks': checks, 'source_pairs': sum(map(len, arms.values())), 'scope': 'Exact saved-path parity, pair preservation, independent frozen moments and source figure bytes'}))


if __name__ == '__main__':
    main()
