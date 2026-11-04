"""Validate source bytes while preserving historical experimental digests."""
from pathlib import Path
import hashlib
import json


def matches_recorded_digest(path, expected, root):
    path, root = Path(path), Path(root)
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual == expected:
        return True
    manifest = root / 'data/publication_adaptations.json'
    if not manifest.exists():
        return False
    relative = path.resolve().relative_to(root.resolve()).as_posix()
    for record in json.loads(manifest.read_text())['files']:
        if record['path'] != relative:
            continue
        historical = {record.get('original_sha256'), record.get('prior_publication_sha256')}
        return expected in historical and actual == record.get('published_sha256')
    return False
