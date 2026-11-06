"""Validate source bytes while preserving historical experimental digests."""

from pathlib import Path as _ProjectPath
import sys as _project_sys
_project_sys.path.insert(0, str(_ProjectPath(__file__).resolve().parents[1]))
from _bootstrap import ROOT as PROJECT_ROOT, script_path, resolve_recorded_path
from pathlib import Path
import hashlib
import json


def matches_recorded_digest(path, expected, root):
    path, root = Path(path), Path(root)
    supplied_path = path
    path = resolve_recorded_path(path, root)
    if not path.is_file():
        return False
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual == expected:
        return True
    relocation = root / 'scripts/relocations.json'
    if relocation.exists():
        relative = path.resolve().relative_to(root.resolve()).as_posix()
        for record in json.loads(relocation.read_text())['files']:
            if relative == record['new_path']:
                return (expected in record['accepted_historical_sha256']
                        and actual == record['relocated_sha256'])
    manifest = root / 'data/publication_adaptations.json'
    if not manifest.exists():
        return False
    relative = path.resolve().relative_to(root.resolve()).as_posix()
    for record in json.loads(manifest.read_text())['files']:
        if record['path'] != relative:
            continue
        historical = {record.get('original_sha256'), record.get('prior_publication_sha256'), *record.get('publication_history_sha256', [])}
        return expected in historical and actual == record.get('published_sha256')
    return False
