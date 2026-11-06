"""Check browser depth payloads against saved evidence and distribution identities."""

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
from fractions import Fraction

ROOT = PROJECT_ROOT


def exact_root_probabilities(n, probability):
    """Independent breadth-first enumeration with rational probability weights."""
    possible = [(a, b) for a in range(n) for b in range(a + 1, n)]
    probabilities = [Fraction(0)] * n
    expected_s2 = Fraction(0)
    for mask in range(1 << len(possible)):
        neighbors = [set() for _ in range(n)]
        edge_count = 0
        for index, (a, b) in enumerate(possible):
            if mask >> index & 1:
                neighbors[a].add(b)
                neighbors[b].add(a)
                edge_count += 1
        remaining = set(range(n))
        groups = []
        while remaining:
            start = min(remaining)
            seen, pending = {start}, [start]
            while pending:
                for node in neighbors[pending.pop()] - seen:
                    seen.add(node)
                    pending.append(node)
            remaining -= seen
            groups.append(seen)
        weight = probability ** edge_count * (1 - probability) ** (len(possible) - edge_count)
        size = len(next(group for group in groups if 0 in group))
        probabilities[size - 1] += weight
        expected_s2 += weight * sum(len(group) ** 2 for group in groups)
    return probabilities, expected_s2


def main():
    payload = json.loads((ROOT / 'web/assets/data/research-depth.json').read_text())
    checks = 0
    fixtures = json.loads((ROOT / 'tests/fixtures/finite_graph_recurrence.json').read_text())
    for case in fixtures['cases']:
        probabilities, expected_s2 = exact_root_probabilities(case['n'], Fraction(str(case['p'])))
        assert sum(probabilities) == 1
        assert list(map(float, probabilities)) == case['root_probabilities']
        assert float(expected_s2) == case['expected_s2']
        checks += 1
    for name, digest in payload['sources'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest
        checks += 1
    pairs = [
        (payload['recovery'], 'results/tables/depth_study_v1/run_metrics.csv'),
        (payload['tails']['truth'], 'results/tables/tail_increment_v1/synthetic_truth.csv'),
        (payload['tails']['ccdf'], 'results/tables/tail_increment_v1/synthetic_ccdf.csv'),
        (payload['memory']['paths'], 'results/tables/state_mechanism_v2/path_metrics.csv'),
        (payload['memory']['summary'], 'results/tables/state_mechanism_v2/summary.csv'),
        (payload['market']['metrics'], 'results/tables/real_market_v1/market_metrics.csv'),
        (payload['market']['sensitivity'], 'results/tables/real_market_v1/joint_constraint_sensitivity.csv'),
    ]
    for rows, name in pairs:
        with (ROOT / name).open() as stream:
            assert rows == list(csv.DictReader(stream))
        checks += 1
    source = ROOT / 'data/snapshots/state-mechanism-series.csv.gz'
    series = {rep: {} for rep in range(10)}
    with gzip.open(source, 'rt') as stream:
        for row in csv.DictReader(stream):
            series[int(row['replication'])].setdefault(row['arm'], []).append([float(row['r']), float(row['V'])])
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    for rep, arms in series.items():
        filename = 'memory-path.json' if rep == 0 else f'memory/path-{rep:02d}.json'
        path = json.loads((ROOT / 'web/assets/data' / filename).read_text())
        assert path['replication'] == rep and path['arms'] == arms
        assert path['source_sha256'] == digest
        assert all(len(rows) == 8192 for rows in arms.values())
        assert sorted(arms['PersistentActivity']) == sorted(arms['ShuffledActivity'])
        checks += 4
    for truth in payload['tails']['truth']:
        assert float(truth['covariance_relative_error']) < 1e-10
        assert math.isclose(float(truth['portfolio_sigma']), float(payload['tails']['truth'][0]['portfolio_sigma']), rel_tol=1e-12)
        assert -float(truth['es01']) >= -float(truth['q01'])
        assert -float(truth['es05']) >= -float(truth['q05'])
        curve = [row for row in payload['tails']['ccdf'] if row['truth'] == truth['truth']]
        assert len(curve) == 81
        assert all(0 <= float(row['exceedance_probability']) <= 1 for row in curve)
        assert all(float(a['exceedance_probability']) >= float(b['exceedance_probability']) for a, b in zip(curve, curve[1:]))
        checks += 7
    print(json.dumps({'status': 'pass', 'checks': checks, 'saved_state_pairs': 327680,
                      'scope': 'Full table parity, ten-path replay, covariance matching and saved tail-curve consistency'}))


if __name__ == '__main__':
    main()
