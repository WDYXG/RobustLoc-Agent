"""Canonical records and immutable writes. No model-generated code execution."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = Path(__file__).resolve().parent


def canonical(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def digest(obj):
    return hashlib.sha256(canonical(obj).encode('utf-8')).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write_new(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + '\n')


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_hashes(mapping):
    bad = [p for p, h in mapping.items() if not (ROOT/p).is_file() or file_hash(ROOT/p) != h]
    if bad:
        raise RuntimeError('Frozen bytes changed: ' + ', '.join(bad[:8]))
    return len(mapping)


def sources():
    paths = list(PACKAGE.rglob('*')) + list((ROOT/'v5/tests').rglob('*'))
    paths += [ROOT/'v5/PREVIOUS_FREEZE.json', ROOT/'v5/PROTOCOL.md', ROOT/'v5/AGENTS.md', ROOT/'v5/__init__.py']
    return {p.relative_to(ROOT).as_posix(): file_hash(p) for p in sorted(paths)
            if p.is_file() and '__pycache__' not in p.parts and p.suffix in ('.py', '.json', '.md')}
