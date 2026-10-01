"""Permanent byte checks for the user's complete v1/v2 freeze."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=Path(__file__).with_name('V1_V2_FREEZE.json')

def check():
    manifest=json.loads(MANIFEST.read_text(encoding='utf-8'))
    for name,digest in manifest['files'].items():
        p=ROOT/name
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:
            raise RuntimeError('Permanent v1/v2 freeze violated: '+name)
    return len(manifest['files'])
