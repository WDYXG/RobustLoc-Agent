"""Canonical artifacts, deduplicated certificates and hash-linked action history."""
import hashlib
import json
from pathlib import Path


def canonical(v): return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def hash_value(v): return hashlib.sha256(canonical(v).encode()).hexdigest()
def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def save(p,v):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')


class Writer:
    def __init__(self,path): self.path=Path(path); self.prev='0'*64; self.events=0
    def compact(self,v):
        if isinstance(v,dict):
            if v.get('schema')=='robust-anchor-margin-v1':
                h=hash_value(v); p=self.path/'certificates'/f'{h}.json'
                if not p.exists(): save(p,v)
                return {'certificate_id':h}
            return {k:self.compact(a) for k,a in v.items()}
        if isinstance(v,list): return [self.compact(a) for a in v]
        return v
    def event(self,value):
        value=self.compact(value); row=dict(index=self.events,previous_hash=self.prev,payload=value)
        row['hash']=hash_value(row)
        with (self.path/'history.jsonl').open('a',encoding='utf-8') as stream: stream.write(canonical(row)+'\n')
        self.prev=row['hash']; self.events+=1
    def artifact(self,name,v): save(self.path/name,self.compact(v))


def hydrate(path,value):
    if isinstance(value,dict):
        if set(value)=={'certificate_id'}:
            c=read(Path(path)/'certificates'/f"{value['certificate_id']}.json")
            if hash_value(c)!=value['certificate_id']: raise ValueError('certificate hash')
            return c
        return {k:hydrate(path,v) for k,v in value.items()}
    if isinstance(value,list): return [hydrate(path,v) for v in value]
    return value
