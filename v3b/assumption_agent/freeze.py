"""Byte preservation for the complete pre-Phase3B checkout."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]


def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def check():
    data=json.loads((ROOT/'v3b/PREVIOUS_FREEZE.json').read_text(encoding='utf-8'))
    for name,h in data['files'].items():
        if not (ROOT/name).is_file() or digest(ROOT/name)!=h: raise RuntimeError('Prior phase freeze violated: '+name)
    return len(data['files'])


def source_hashes():
    return {str(p.relative_to(ROOT)).replace('\\','/'):digest(p) for p in sorted((ROOT/'v3b').rglob('*'))
            if p.is_file() and 'runs' not in p.parts and '__pycache__' not in p.parts and p.suffix in ('.py','.json','.md')}
