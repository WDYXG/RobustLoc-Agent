"""Atomic state files and hash-linked append-only research records."""
import hashlib
import json
from pathlib import Path

def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=True)

def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding='utf-8')
    temp.replace(path)

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def history(path):
    path = Path(path)
    records = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()] if path.exists() else []
    previous = 'GENESIS'
    for row in records:
        payload = {k:v for k,v in row.items() if k != 'record_hash'}
        if row['previous_hash'] != previous or row['record_hash'] != hashlib.sha256(canonical(payload).encode()).hexdigest():
            raise RuntimeError('Research log integrity failure')
        previous = row['record_hash']
    return records

def append(path, record):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    records = history(path)
    row = dict(record, previous_hash=records[-1]['record_hash'] if records else 'GENESIS')
    row['record_hash'] = hashlib.sha256(canonical(row).encode()).hexdigest()
    with path.open('a', encoding='utf-8') as stream:
        stream.write(canonical(row) + '\n')
        stream.flush()
    return row
