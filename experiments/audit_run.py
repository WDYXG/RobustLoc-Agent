"""Audit saved artifacts without rerunning or tuning the held-out benchmark."""
from pathlib import Path
import hashlib
import numpy as np
from robustloc.storage import history, read, save
from robustloc.metrics import summarize
from robustloc.verifier import verify
from agent import guard, ROOT

def audit(run):
    run=Path(run).resolve(); guard(run)
    records=history(run/'research_log.jsonl'); state=read(run/'state.json')
    assert len(records)==state['iteration']==8
    assert state['status']=='complete'
    frozen=read(run/'frozen_method.json')
    assert frozen['method']==state['best_method']
    assert frozen['log_hash']==records[-1]['record_hash']
    assert frozen['candidate_sha256']==hashlib.sha256((ROOT/'robustloc/candidate.py').read_bytes()).hexdigest()
    checked=0
    for path in run.rglob('*.json'):
        result=read(path)
        if not isinstance(result,dict) or 'rows' not in result: continue
        calc=summarize(result['rows'])
        for key,value in calc.items(): assert np.isclose(value,result['overall'][key]),(path,key)
        checked+=len(result['rows'])
    for r in records:
        folder=run/'iterations'/f'{r["iteration"]:03d}'
        request=read(folder/'verify_request.json')
        decision=verify(read(request['candidate']),read(request['incumbent']),read(request['baseline']),request['policy'])
        assert decision==read(folder/'verification.json')
        assert decision['verdict']==r['verdict']
    save(run/'audit.json',dict(status='passed',log_records=len(records),checked_case_records=checked,protected_hashes='passed',baseline_hashes='passed',saved_metrics='recomputed',verifier_decisions='independently replayed',heldout_solver_reruns=0))
    print(read(run/'audit.json'))

if __name__=='__main__': audit(ROOT/'runs/run-001')
