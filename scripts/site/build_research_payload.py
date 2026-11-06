"""Build browser research replays from the project's immutable saved tables."""

from pathlib import Path as _ProjectPath
import sys as _project_sys
_project_sys.path.insert(0, str(_ProjectPath(__file__).resolve().parents[1]))
from _bootstrap import ROOT as PROJECT_ROOT, script_path, resolve_recorded_path
from pathlib import Path
import csv
import gzip
import hashlib
import json

ROOT = PROJECT_ROOT
WEB = ROOT / 'web/assets/data'


def main():
    sources = {}

    def table(relative):
        path = ROOT / relative
        sources[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
        with path.open() as stream:
            return list(csv.DictReader(stream))

    recovery = table('results/tables/depth_study_v1/run_metrics.csv')
    truth = table('results/tables/tail_increment_v1/synthetic_truth.csv')
    ccdf = table('results/tables/tail_increment_v1/synthetic_ccdf.csv')
    paths = table('results/tables/state_mechanism_v2/path_metrics.csv')
    summary = table('results/tables/state_mechanism_v2/summary.csv')
    market = table('results/tables/real_market_v1/market_metrics.csv')
    sensitivity = table('results/tables/real_market_v1/joint_constraint_sensitivity.csv')
    data = {'version': 2, 'sources': sources, 'recovery': recovery,
            'tails': {'truth': truth, 'ccdf': ccdf},
            'memory': {'paths': paths, 'summary': summary},
            'market': {'metrics': market, 'sensitivity': sensitivity}}
    (WEB / 'research-depth.json').write_text(json.dumps(data, separators=(',', ':')) + '\n')
    source = ROOT / 'data/snapshots/state-mechanism-series.csv.gz'
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    series = {i: {} for i in range(10)}
    with gzip.open(source, 'rt') as stream:
        for row in csv.DictReader(stream):
            series[int(row['replication'])].setdefault(row['arm'], []).append([float(row['r']), float(row['V'])])
    config = json.loads((ROOT / 'configs/state_forecast_v2.json').read_text())['mechanism']
    destination = WEB / 'memory'
    destination.mkdir(exist_ok=True)
    for replication, arms in series.items():
        assert len(arms) == 4 and all(len(pairs) == 8192 for pairs in arms.values())
        payload = {'replication': replication, 'length': 8192, 'config': config, 'arms': arms,
                   'source': 'data/snapshots/state-mechanism-series.csv.gz', 'source_sha256': digest,
                   'scope': 'Exact saved path replay; browser transformations are separately labelled. Summary research results average ten independent paths.'}
        # Preserve the already published replication-0 payload and its URL.
        if replication:
            (destination / f'path-{replication:02d}.json').write_text(json.dumps(payload, separators=(',', ':')) + '\n')
    print(json.dumps({'status': 'pass', 'recovery_rows': len(recovery), 'tail_curves': len(ccdf), 'saved_paths': 10, 'state_arms': 4}))


if __name__ == '__main__':
    main()
