"""Explicit transport overlay, with independent source manifest and replay."""
import argparse
import json
from pathlib import Path
from v5.researcher import runner, codex_client
from v5.researcher.io import ROOT, read, write_new, file_hash, check_hashes, sources

HERE=Path(__file__).resolve().parent
REQUESTED_MODEL='gpt-6.1-sol'
BASE_COMMAND=codex_client.command
BASE_PROPOSE=codex_client.propose
BASE_WRITE=codex_client.write_new
BASE_CHECK=runner.frozen_check


def own_sources():
    return {p.relative_to(ROOT).as_posix():file_hash(p) for p in sorted(HERE.rglob('*'))
            if p.is_file() and '__pycache__' not in p.parts and p.suffix in ('.py','.json','.md')}


def v2_command(workspace,schema,output):
    argv=BASE_COMMAND(workspace,schema,output)
    return argv[:-1]+['-c','suppress_unstable_features_warning=true','--model',REQUESTED_MODEL,argv[-1]]


def v2_write(path,obj):
    if Path(path).name=='invocation.json':
        obj=dict(obj,model_selection='Pinned to the available default returned by the CLI model catalog',
                 requested_model=REQUESTED_MODEL,transport_version=2)
    return BASE_WRITE(path,obj)


def v2_propose(*args,**kwargs):
    proposal,meta=BASE_PROPOSE(*args,**kwargs)
    return proposal,dict(meta,requested_model=REQUESTED_MODEL,transport_version=2)


def activate(expected=None):
    codex_client.command=v2_command
    codex_client.write_new=v2_write
    runner.codex_propose=v2_propose
    def frozen(manifest):
        BASE_CHECK(manifest)
        if expected is not None:
            check_hashes(expected)
            if own_sources()!=expected:raise RuntimeError('version-2 source set changed')
    runner.frozen_check=frozen


def audit(envelope):
    envelope=Path(envelope);m=read(envelope/'transport_manifest.json')
    check_hashes(m['transport_sources']);check_hashes(m['scientific_sources'])
    if own_sources()!=m['transport_sources']:raise RuntimeError('v2 source-set mismatch')
    activate(m['transport_sources'])
    result=runner.replay(envelope/'scientific')
    if m['policy']=='codex':
        for p in sorted((envelope/'scientific/iterations').glob('r*/invocation.json')):
            r=read(p);a=r['argv']
            if a[a.index('--model')+1]!=REQUESTED_MODEL or 'suppress_unstable_features_warning=true' not in a:
                raise ValueError('transport request differs from declared v2')
            if r['requested_model']!=REQUESTED_MODEL or r['transport_version']!=2:
                raise ValueError('transport invocation metadata mismatch')
    return dict(result,transport_version=2,requested_model=REQUESTED_MODEL,
                actual_model_id='only reported IDs in per-round runtime are authoritative')


def run(envelope,policy):
    envelope=Path(envelope).resolve()
    if envelope.exists() or not envelope.is_relative_to(ROOT/'v5/runs'):
        raise ValueError('fresh v5/runs envelope required')
    envelope.mkdir(parents=True)
    own=own_sources()
    write_new(envelope/'transport_manifest.json',{'version':2,'policy':policy,'requested_model':REQUESTED_MODEL,
              'transport_sources':own,'scientific_sources':sources(),
              'changes':['suppress experimental-feature CLI warning','pin catalog-default available model'],
              'mathematical_changes':None})
    activate(own)
    runner.run(envelope/'scientific',policy)
    if not (envelope/'scientific/blocked.json').exists():
        result=audit(envelope);write_new(envelope/'audit.json',result);print(json.dumps(result),flush=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['scripted','codex','replay','compare'])
    p.add_argument('path');p.add_argument('--other');p.add_argument('--output')
    a=p.parse_args()
    if a.mode=='replay':
        result=audit(a.path)
        if a.output:write_new(a.output,result)
        print(json.dumps(result,indent=2))
    elif a.mode=='compare':
        ma,mb=read(Path(a.path)/'transport_manifest.json'),read(Path(a.other)/'transport_manifest.json')
        for k in ('transport_sources','scientific_sources','requested_model'):
            if ma[k]!=mb[k]:raise ValueError('unmatched transport experiment')
        audit(a.path);audit(a.other)
        result=runner.compare(Path(a.path)/'scientific',Path(a.other)/'scientific')
        result['transport_version']=2
        write_new(a.output,result);print(json.dumps(result,indent=2))
    else:run(a.path,a.mode)


if __name__=='__main__':main()
