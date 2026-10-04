"""Immutable LF JSON records, source hashes, prior-byte freeze and history chain."""
from pathlib import Path
import hashlib,json

ROOT=Path(__file__).resolve().parents[1]


def canonical(v): return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def hash_value(v): return hashlib.sha256(canonical(v).encode()).hexdigest()
def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def save(p,v):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
def sources():
    return {p.relative_to(ROOT).as_posix():digest(p) for p in sorted((ROOT/'v4').rglob('*')) if p.is_file() and 'runs' not in p.parts and '__pycache__' not in p.parts and p.suffix in ('.py','.md','.json')}
def check_previous():
    old=read(ROOT/'v4/PREVIOUS_FREEZE.json')['files']
    for name,h in old.items():
        if digest(ROOT/name)!=h: raise ValueError('frozen prior file changed: '+name)
    return len(old)


class History:
    def __init__(self,path): self.path=Path(path); self.last='0'*64; self.count=0
    def append(self,payload):
        row=dict(index=self.count,previous=self.last,payload=payload); row['hash']=hash_value(row)
        with self.path.open('a',encoding='utf-8',newline='\n') as stream: stream.write(canonical(row)+'\n')
        self.last=row['hash']; self.count+=1
