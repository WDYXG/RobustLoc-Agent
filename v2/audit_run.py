"""Read-only audit of saved v2 results and permanent v1 byte freeze."""
from pathlib import Path
from robustloc.storage import read,history
from .agent import freeze_check,code_hashes,ROOT
from .verify_task import verify

def audit(run):
    folder=Path(run); records=history(folder/'research_log.jsonl')
    assert len(records)==read(folder/'state.json')['iteration']
    assert read(folder/'manifest.json')['source_sha256']==code_hashes()
    for row in records:
        stage=row['iteration']; path=folder/'iterations'/f'{stage:03d}'
        assert verify(stage,read(path/'evidence.json'))==read(path/'verification.json')
    print(dict(v1_frozen_files_verified=freeze_check(),v2_iterations_verified=len(records),source_hashes='passed',historical_evidence='passed',status='numerically-supported'))

if __name__=='__main__': audit(ROOT/'v2/runs/theory-001')
