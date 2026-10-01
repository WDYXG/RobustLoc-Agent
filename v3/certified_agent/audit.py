"""Read-only independent verification of persisted Phase 3A evidence."""
import argparse
import hashlib
import json
from pathlib import Path
from robustloc.storage import read,history,save
from v3.freeze import ROOT,check
from .verifier import verify_record,verify_learning

def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def audit(folder,check_outputs=True):
    manifest=read(folder/'manifest.json'); cfg=manifest['config']
    for path,sha in manifest['source_sha256'].items():
        if digest(ROOT/path)!=sha: raise RuntimeError('Frozen Phase 3 source changed: '+path)
    pool={p.stem:read(p) for p in (folder/'certificates').glob('*.json')}
    for key,c in pool.items():
        if hashlib.sha256(json.dumps(c,sort_keys=True).encode()).hexdigest()!=key:
            raise RuntimeError('Certificate content ID mismatch')
    rows=[read(p) for p in sorted((folder/'episodes').glob('*.json'))]
    ids={(r['method'],r['case_id']) for r in rows}
    if len(ids)!=len(rows): raise RuntimeError('Duplicate episode result')
    counts={m:sum(r['method']==m for r in rows) for m in cfg['methods']}
    if any(c!=len(cfg['scenarios'])*cfg['heldout_cases_per_scenario'] for c in counts.values()):
        raise RuntimeError('Missing method–episode results')
    certified=valid=0
    for row in rows:
        result=verify_record(row,pool,cfg); certified+=result['certified_outputs']; valid+=result['in_contract']
    logs=history(folder/'action_log.jsonl')
    if len(logs)!=sum(len(r['trace']) for r in rows): raise RuntimeError('Missing action log rows')
    indexed={(r['method'],r['case_id'],i):turn for r in rows for i,turn in enumerate(r['trace'])}
    for event in logs:
        key=(event['method'],event['case_id'],event['step'])
        if event['turn']!=indexed.pop(key,None): raise RuntimeError('Action trace/log mismatch')
    if indexed: raise RuntimeError('Action log coverage gap')
    learning=verify_learning(read(folder/'learning.json'),cfg)
    if check_outputs:
        for path,sha in read(folder/'output_sha256.json').items():
            if digest(folder/path)!=sha: raise RuntimeError('Run output changed: '+path)
    return dict(verified=True,frozen_files=check(),episodes=len(rows),actions=len(logs),
        certificate_objects=len(pool),certified_outputs=certified,in_contract_results=valid,
        learning=learning,status='numerically-supported',
        scope='independent exact arithmetic/safety audit; shared v2 rational primitives, not formal proof')

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--run',default='v3/runs/certified-agent-001')
    parser.add_argument('--pre-report',action='store_true'); parser.add_argument('--output')
    args=parser.parse_args(); result=audit(ROOT/args.run,not args.pre_report)
    if args.output: save(args.output,result)
    print(result)
