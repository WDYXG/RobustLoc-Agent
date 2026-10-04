from pathlib import Path
import hashlib
import json

ROOT=Path(__file__).resolve().parents[2]


def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def check():
    files=json.loads((ROOT/'v3d/PREVIOUS_FREEZE.json').read_text(encoding='utf-8'))['files']
    for name,h in files.items():
        if not (ROOT/name).is_file() or digest(ROOT/name)!=h: raise RuntimeError('previous bytes changed: '+name)
    return len(files)


def sources():
    return {str(p.relative_to(ROOT)).replace('\\','/'):digest(p) for p in sorted((ROOT/'v3d').rglob('*'))
       if p.is_file() and 'runs' not in p.parts and '__pycache__' not in p.parts and p.suffix in ('.py','.md','.json')}
