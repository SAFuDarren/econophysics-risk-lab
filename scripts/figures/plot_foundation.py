"""Render source-backed simulation figures; optional installed figure QA tools."""

from pathlib import Path as _ProjectPath
import sys as _project_sys
_project_sys.path.insert(0, str(_ProjectPath(__file__).resolve().parents[1]))
from _bootstrap import ROOT as PROJECT_ROOT, script_path, resolve_recorded_path

from pathlib import Path
import argparse
import csv
import hashlib
import json
import os
import sys

ROOT = PROJECT_ROOT
os.environ.setdefault('MPLCONFIGDIR', str(ROOT / '.cache/matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import networkx as nx


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-run', default='foundation_v1')
    parser.add_argument('--figure-set', default='foundation_v1')
    parser.add_argument('--qa-tools', type=Path, help='Optional installed nature-figure scripts directory.')
    args = parser.parse_args()
    for name in [args.source_run, args.figure_set]:
        if not name.replace('_', '').replace('-', '').isalnum():
            parser.error('invalid run/set ID')
    source = ROOT / 'results/tables' / args.source_run
    destination = ROOT / 'figures' / args.figure_set
    if destination.exists():
        parser.error('figure set already exists; use a fresh set ID')
    destination.mkdir(parents=True)
    qa_dir = ROOT / 'results/checks' / args.source_run / 'figure_qa' / args.figure_set
    qa_dir.mkdir(parents=True, exist_ok=True)
    if args.qa_tools:
        sys.path.insert(0, str(args.qa_tools.resolve()))
        from audit_panel_alignment import require_matplotlib_panel_alignment
    else:
        require_matplotlib_panel_alignment = None
    plt.rcParams.update({'font.family': 'sans-serif', 'font.sans-serif': ['DejaVu Sans'],
                         'font.size': 8, 'axes.titlesize': 9, 'axes.labelsize': 8,
                         'xtick.labelsize': 8, 'ytick.labelsize': 8, 'legend.fontsize': 8,
                         'pdf.fonttype': 42, 'svg.fonttype': 'none',
                         'axes.spines.top': False, 'axes.spines.right': False,
                         'axes.linewidth': .7, 'savefig.dpi': 300})

    def save(fig, name):
        fig.canvas.draw()
        geometry = {str(i): [float(x) for x in ax.get_window_extent().bounds] for i, ax in enumerate(fig.axes)}
        (qa_dir / f'{name}.geometry.json').write_text(json.dumps(geometry, indent=2))
        if require_matplotlib_panel_alignment:
            require_matplotlib_panel_alignment(fig, json_out=str(qa_dir / f'{name}.alignment.json'),
                                               tolerance_pt=1.5, gutter_tolerance_pt=1.5,
                                               require_panel_labels=True, strict=True)
        fig.savefig(destination / f'{name}.svg')
        fig.savefig(destination / f'{name}.pdf')
        fig.savefig(destination / f'{name}.png', dpi=300)
        plt.close(fig)

    snapshots = json.loads((source / 'network_snapshots.json').read_text())
    fig, axes = plt.subplots(1, 3, figsize=(7.2047244094, 2.6771653543), layout=None)
    fig.subplots_adjust(left=.04, right=.98, top=.76, bottom=.19, wspace=.18)
    for index, (ax, snapshot) in enumerate(zip(axes, snapshots)):
        graph = nx.Graph()
        graph.add_nodes_from(range(snapshot['n']))
        graph.add_edges_from(snapshot['edges'])
        positions = nx.circular_layout(graph)
        largest = max(snapshot['groups'], key=len)
        nx.draw_networkx_edges(graph, positions, ax=ax, width=.6,
                               edge_color=['#28739A' if v in largest and w in largest else '#AEB9C2' for v, w in graph.edges])
        nx.draw_networkx_nodes(graph, positions, ax=ax, node_size=12,
                               node_color=['#28739A' if i in largest else '#C5CDD3' for i in graph], linewidths=0)
        ax.set_xlim(-1.15, 1.15)
        ax.set_ylim(-1.15, 1.15)
        ax.set_aspect('equal')
        ax.set_axis_off()
        ax.set_title(f"rho = {snapshot['rho']:.1f}", pad=8)
        ax.text(0, -.16, f"Largest group: {len(largest)} / {snapshot['n']}", transform=ax.transAxes, fontsize=8)
        ax.text(-.04, 1.13, 'abc'[index], transform=ax.transAxes, weight='bold', fontsize=10)
    fig.suptitle('Simulation | One ER network per condition; N = 48', fontsize=10, y=.97)
    fig.text(.04, .04, 'Blue: largest group. Fixed circular node layout; one independent draw per condition.', fontsize=8)
    save(fig, 'F01')

    with (source / 'market_observations.csv').open() as stream:
        rows = [{key: float(value) for key, value in row.items()} for row in csv.DictReader(stream)]
    t = [row['t'] for row in rows]
    fig, axes = plt.subplots(3, 1, sharex=True, figsize=(7.2047244094, 5.1968503937), layout=None)
    fig.subplots_adjust(left=.14, right=.97, top=.87, bottom=.14, hspace=.24)
    axes[0].plot(t, [row['C'] for row in rows], color='#28739A', linewidth=1.1)
    axes[1].plot(t, [100 * row['r'] for row in rows], color='#965D36', linewidth=.8)
    axes[1].axhline(0, color='#AEB9C2', linewidth=.5, zorder=0)
    axes[2].bar(t, [row['V'] for row in rows], color='#7A8A96', width=.8, linewidth=0)
    for ax, letter, ylabel in zip(axes, 'abc', ['Price (model units)', 'Log return (%)', 'Volume (units)']):
        ax.set_ylabel(ylabel)
        ax.text(-.13, 1.02, letter, transform=ax.transAxes, weight='bold', fontsize=10)
        ax.margins(x=.01)
    axes[2].set_xlabel('Simulated interval')
    fig.suptitle('Simulation | One execution, consistent price and volume', fontsize=10, y=.98)
    fig.text(.14, .91, 'N = 128; rho = 1.0; a = 0.10; lambda = 0.02; u = 1; T = 128', fontsize=8)
    fig.text(.14, .025, 'Single unselected trajectory; no real-market or learning-performance claim.', fontsize=8)
    save(fig, 'F07')
    record = {'source_run': args.source_run, 'figure_set': args.figure_set,
              'evidence_type': 'SIMULATION', 'data_exclusions': [], 'uncertainty': 'raw single draws/trajectory; no aggregate interval claimed',
              'matplotlib': matplotlib.__version__, 'networkx': nx.__version__,
              'panel_alignment': 'checked using installed helper' if args.qa_tools else 'geometry recorded; external alignment audit not run',
              'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (qa_dir / 'render_record.json').write_text(json.dumps(record, indent=2) + '\n')
    print(str(destination.relative_to(ROOT)))


if __name__ == '__main__':
    main()
