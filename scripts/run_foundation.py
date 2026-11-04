"""Reproducible foundation checks and source tables, using only Python's stdlib."""

from pathlib import Path
import argparse
import csv
from dataclasses import asdict
import hashlib
import json
import math
import platform
import random
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from econophysics.model import Parameters, aggregate_orders, components, conditional_moments, derived_seed, draw_actions, er_edges, execute_bar, simulate_window
from econophysics.features import window_features


def dump_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def dump_csv(path, rows):
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', default='configs/foundation_v1.json')
    parser.add_argument('--run-id', default='foundation_v1')
    args = parser.parse_args()
    if not args.run_id.replace('_', '').replace('-', '').isalnum():
        parser.error('run-id must contain only letters, digits, underscore or hyphen')
    config_path = ROOT / args.config
    config = json.loads(config_path.read_text())
    checks_dir, tables_dir = [ROOT / folder / args.run_id for folder in ['results/checks', 'results/tables']]
    if checks_dir.exists() or tables_dir.exists():
        parser.error('run-id already exists; use a fresh run-id to preserve old evidence')
    checks_dir.mkdir(parents=True)
    tables_dir.mkdir(parents=True)
    started = time.perf_counter()
    params = Parameters(**config['parameters'])
    checks = []
    def check(name, ok, **details):
        checks.append({'check': name, 'status': 'pass' if ok else 'fail', **details})
    check('empty ER graph', er_edges(10, 0, random.Random(1)) == [] and len(components(10, [])) == 10)
    check('complete ER graph', len(er_edges(10, 1, random.Random(1))) == 45)
    check('known components include isolated nodes', components(6, [(0, 1), (1, 2), (3, 4)]) == [[0, 1, 2], [3, 4], [5]])
    groups = [[i] for i in range(params.n)]
    zero, zero_book = execute_bar(groups, [0] * params.n, params, 100., random.Random(1))
    check('zero-trade OHLC and amount', zero == {'r': 0., 'V': 0., 'D': 0., 'O': 100., 'H': 100., 'L': 100., 'C': 100.})
    bought, _ = execute_bar(groups, [1] * params.n, params, 100., random.Random(1))
    check('all buy agrees with normalization', bought['r'] == params.lambda_impact and bought['V'] == params.n * params.unit_order and math.isclose(bought['C'], 100 * math.exp(params.lambda_impact), rel_tol=1e-12))
    balanced, _ = execute_bar(groups, [1] * (params.n // 2) + [-1] * (params.n // 2) + [0] * (params.n % 2), params, 100., random.Random(2))
    check('balanced orders have zero return and positive volume', balanced['r'] == 0 and balanced['V'] > 0)
    invalid = 0
    for kwargs in [{'n': 1}, {'n': 4, 'rho': 4}, {'a': .5}, {'lambda_impact': 0}]:
        try:
            Parameters(**kwargs)
        except ValueError:
            invalid += 1
    check('invalid physical parameters rejected', invalid == 4)
    # Known population-centered moments, each estimated as a mean of iid draws.
    fixed = Parameters(n=10, rho=1, a=.17, lambda_impact=.02)
    sizes = [1, 2, 3, 4]
    expected = conditional_moments(sizes, fixed)
    rng = random.Random(derived_seed(config['seed'], 'moment_check'))
    sample = [aggregate_orders(sizes, draw_actions(4, fixed.a, rng), fixed) for _ in range(config['fixed_graph_draws'])]
    series = {'mean_r': [r for r, v in sample], 'mean_V': [v for r, v in sample],
              'var_r': [r * r for r, v in sample],
              'var_V': [(v - expected['mean_V']) ** 2 for r, v in sample],
              'cov_r_V': [r * (v - expected['mean_V']) for r, v in sample]}
    moment_rows = []
    for name, values in series.items():
        observed, se = statistics.fmean(values), statistics.stdev(values) / math.sqrt(len(values))
        error = observed - expected[name]
        row = {'quantity': name, 'theory': expected[name], 'estimate': observed, 'standard_error': se,
               'z_score': error / se if se else None, 'draws': len(values)}
        moment_rows.append(row)
        check('fixed graph moment: ' + name, abs(error) <= 6 * se + 1e-14, **row,
              rule='absolute error <= 6 estimated SE; diagnostic, not a formal test of all model claims')
    dump_csv(tables_dir / 'moment_checks.csv', moment_rows)
    # Independent analytic N=3 identity: P(1 connected to 2)=p+(1-p)*p^2.
    p = .3
    graph_rng = random.Random(derived_seed(config['seed'], 'small_graph_check'))
    s2 = [sum(len(group) ** 2 for group in components(3, er_edges(3, p, graph_rng))) for _ in range(config['small_er_graph_draws'])]
    theoretical = 3 + 6 * (p + p*p - p*p*p)
    se = statistics.stdev(s2) / math.sqrt(len(s2))
    observed = statistics.fmean(s2)
    check('ER generator analytic three-node susceptibility', abs(observed - theoretical) <= 6 * se,
          theory=theoretical, estimate=observed, standard_error=se, independent_graphs=len(s2))
    chain = components(4, [(0, 1), (1, 2), (2, 3)])
    star = components(4, [(0, 1), (0, 2), (0, 3)])
    small = Parameters(n=4)
    equal = all(execute_bar(chain, [x], small, 100., random.Random(7)) == execute_bar(star, [x], small, 100., random.Random(7)) for x in [-1, 0, 1])
    check('chain-star fixed-component boundary', equal, scope='specified coordinated component interface; mathematical explanation in model_spec.md')
    observations, latent, books, first_graph = simulate_window(params, config['window_length'], config['seed'])
    check('counterparty inventory and cash conserved', all(b['trader_inventory_change'] + b['counterparty_inventory_change'] == 0 and b['trader_cash_change'] + b['counterparty_cash_change'] == 0 for b in books))
    max_error = max(abs(math.log(row['C'] / row['O']) - row['r']) for row in observations)
    check('execution path matches aggregate log return', max_error < 1e-12, max_absolute_error=max_error)
    check('OHLC bounds and exact counted volume', all(row['L'] <= min(row['O'], row['C']) <= max(row['O'], row['C']) <= row['H'] and row['V'] == b['unit_trades'] * params.unit_order for row, b in zip(observations, books)))
    repeated, _, _, _ = simulate_window(params, config['window_length'], config['seed'])
    check('same configuration and seed reproduces observations', observations == repeated)
    features = window_features(observations)
    check('features contain only declared observations', set(features) == {'return_std', 'mean_abs_return', 'abs_return_q95', 'abs_return_q99', 'zero_return_fraction', 'volume_mean', 'volume_std', 'volume_q95', 'corr_volume_abs_return'})
    flat = window_features([zero, zero])
    check('constant-window correlation is missing, not invented', flat['corr_volume_abs_return'] is None)
    dump_csv(tables_dir / 'market_observations.csv', observations)
    dump_csv(tables_dir / 'latent_graphs_NOT_FEATURES.csv', latent)
    dump_json(tables_dir / 'window_features.json', features)
    dump_json(tables_dir / 'labels_and_seeds_NOT_FEATURES.json', {'parameters': asdict(params), 'seed': config['seed'], 'length': config['window_length']})
    snapshots = []
    for rho in config['snapshot_rho']:
        n = config['snapshot_n']
        edges = er_edges(n, rho / (n - 1), random.Random(derived_seed(config['seed'], f'snapshot_{rho}')))
        groups = components(n, edges)
        snapshots.append({'n': n, 'rho': rho, 'edges': edges, 'groups': groups})
    dump_json(tables_dir / 'network_snapshots.json', snapshots)
    dump_json(checks_dir / 'checks.json', {'evidence_type': 'MODEL_CHECK', 'status': 'pass' if all(c['status'] == 'pass' for c in checks) else 'fail', 'checks': checks})
    source_files = sorted((ROOT / 'src/econophysics').glob('*.py')) + [Path(__file__).resolve(), config_path]
    snapshot = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files}
    output_files = list(tables_dir.iterdir()) + [checks_dir / 'checks.json']
    dump_json(checks_dir / 'run_record.json', {'protocol_id': config['protocol_id'], 'run_id': args.run_id,
              'scope': 'foundation only; not a phase scan, inverse benchmark or real-market analysis',
              'command': f'python3 scripts/run_foundation.py --config {args.config} --run-id {args.run_id}',
              'config': str(config_path.relative_to(ROOT)), 'source_sha256': snapshot,
              'python': platform.python_version(), 'elapsed_seconds': time.perf_counter() - started,
              'outputs': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in output_files},
              'member_review': 'not_run'})
    print(json.dumps({'status': 'pass' if all(c['status'] == 'pass' for c in checks) else 'fail', 'checks': len(checks), 'observations': len(observations), 'checks_dir': str(checks_dir.relative_to(ROOT)), 'tables_dir': str(tables_dir.relative_to(ROOT))}, indent=2))
    return 0 if all(c['status'] == 'pass' for c in checks) else 1


if __name__ == '__main__':
    raise SystemExit(main())
