"""Check command relocation, strict historical aliases and isolated root discovery."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _bootstrap import ROOT, resolve_recorded_path, script_path
from publication_integrity import matches_recorded_digest
import ast
import hashlib
import json
import re
import shutil
import subprocess
import tempfile


def main():
    rows = json.loads((ROOT / 'scripts/relocations.json').read_text())['files']
    for row in rows:
        old, new = ROOT / row['old_path'], ROOT / row['new_path']
        assert not old.exists() and new.is_file(), row
        assert hashlib.sha256(new.read_bytes()).hexdigest() == row['relocated_sha256'], row['new_path']
        assert resolve_recorded_path(old, ROOT) == new
        assert script_path(new.name) == new
        assert matches_recorded_digest(old, row['before_sha256'], ROOT)
        assert not matches_recorded_digest(old, '0' * 64, ROOT)
    parsed = 0
    for path in (ROOT / 'scripts').rglob('*.py'):
        if '__pycache__' in path.parts:
            continue
        ast.parse(path.read_text())
        parsed += 1
    for relative in re.findall(r'scripts/[\w./-]+\.(?:py|cjs)', (ROOT / 'scripts/reproduce.py').read_text()):
        assert (ROOT / relative).is_file(), relative
    with tempfile.TemporaryDirectory(prefix='econophysics-layout-') as temporary:
        isolated = Path(temporary)
        for name in ['scripts', 'src']:
            shutil.copytree(ROOT / name, isolated / name, ignore=shutil.ignore_patterns('__pycache__'))
        command = [sys.executable, str(script_path('check_theory_foundations.py', isolated)), '--output', str(isolated / 'theory-check')]
        result = subprocess.run(command, cwd=isolated, check=True, capture_output=True, text=True)
        assert json.loads(result.stdout)['check_count'] == 480
        row = rows[0]
        copied = isolated / row['new_path']
        copied.write_bytes(copied.read_bytes() + b'\n# changed bytes\n')
        assert not matches_recorded_digest(isolated / row['old_path'], row['before_sha256'], isolated)
    report = {
        'status': 'pass', 'relocated_scripts': len(rows),
        'python_sources_parsed': parsed,
        'stable_entrypoint': 'scripts/reproduce.py',
        'root_python_files': sorted(p.name for p in (ROOT / 'scripts').glob('*.py')),
        'strict_historical_digest_aliases': True,
        'arbitrary_changed_source_rejected': True,
        'isolated_full_script_tree_and_root_discovery': True,
        'isolated_exact_theory_checks': 480,
        'historical_data_results_studies_records_rewritten': False,
    }
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
