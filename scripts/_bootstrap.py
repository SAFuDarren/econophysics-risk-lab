"""Shared project root and historical script relocation resolver."""
from pathlib import Path
import json
import sys
ROOT = Path(__file__).resolve().parents[1]
for _directory in ['src', 'scripts', *['scripts/' + p for p in ('data','research','figures','site','checks')]]:
    _path = str(ROOT / _directory)
    if _path not in sys.path:
        sys.path.insert(0, _path)

def _relocations(root):
    path = Path(root) / 'scripts/relocations.json'
    return json.loads(path.read_text())['files'] if path.exists() else []

def resolve_recorded_path(path, root=ROOT):
    root, path = Path(root).resolve(), Path(path)
    path = path if path.is_absolute() else root / path
    if path.exists():
        return path
    try:
        relative = path.resolve().relative_to(root).as_posix()
    except ValueError:
        return path
    for row in _relocations(root):
        if row['old_path'] == relative:
            return root / row['new_path']
    return path

def script_path(name, root=ROOT):
    root = Path(root)
    candidate = resolve_recorded_path(root / 'scripts' / name, root)
    if candidate.is_file():
        return candidate
    matches = [p for p in (root / 'scripts').rglob(name) if '__pycache__' not in p.parts]
    if len(matches) != 1:
        raise FileNotFoundError(f'Expected one script named {name}, found {len(matches)}')
    return matches[0]
