import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]


def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def check():
    m=json.loads((ROOT/'v3c/PREVIOUS_FREEZE.json').read_text(encoding='utf-8'))
    for name,h in m['files'].items():
        if not (ROOT/name).is_file() or digest(ROOT/name)!=h: raise RuntimeError('prior freeze violated: '+name)
    return len(m['files'])


def sources():
    return {str(p.relative_to(ROOT)).replace('\\','/'):digest(p) for p in sorted((ROOT/'v3c').rglob('*'))
       if p.is_file() and 'runs' not in p.parts and '__pycache__' not in p.parts and p.suffix in ('.py','.md','.json')}
