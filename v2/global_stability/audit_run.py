"""Read-only audit: historical integrity + independent arithmetic recomputation."""
import argparse
from robustloc.storage import read,history
from v2.agent import freeze_check,code_hashes as phase1_hashes
from .agent import ROOT,source_hashes,artifact_hash
from .verify_task import verify

def audit(folder):
    manifest=read(folder/'manifest.json'); records=history(folder/'research_log.jsonl')
    if manifest['source_sha256']!=source_hashes(): raise RuntimeError('Phase 2 source mismatch')
    if manifest['phase1_sha256']!=phase1_hashes(): raise RuntimeError('Phase 1 source mismatch')
    if len(records)!=read(folder/'state.json')['iteration']: raise RuntimeError('State mismatch')
    cfg=manifest['config']
    for row in records:
        stage=row['iteration']; out=folder/'iterations'/f'{stage:03d}'
        for name,digest in row['artifact_sha256'].items():
            if artifact_hash(out/name)!=digest: raise RuntimeError('Iteration artifact changed: '+name)
        profile=read(folder/'iterations/007/evidence.json') if stage==8 else None
        if verify(stage,read(out/'evidence.json'),cfg,profile)!=read(out/'verification.json'):
            raise RuntimeError('Independent recomputation failed')
    for name,digest in read(folder/'output_sha256.json').items():
        if artifact_hash(folder/name)!=digest: raise RuntimeError('Final artifact changed: '+name)
    return dict(verified=True,iterations=len(records),v1_frozen_files=freeze_check(),
        phase1_sources_unchanged=True,phase2_source_and_output_hashes='passed',
        independent_exact_recomputation='passed',status='proved-in-project',novelty='not established')

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--run',default='v2/runs/global-stability-001')
    args=parser.parse_args(); print(audit(ROOT/args.run))
