"""Resumable theory-task loop: authored conjectures, proof artifacts, adversarial
witness search and fixed experiments. Not an automatic formal theorem prover.
"""
import argparse
import hashlib
from pathlib import Path
import subprocess
import sys
from datetime import datetime,timezone
from robustloc.storage import save,read,append,history
from .claims import CLAIMS
from . import experiments

ROOT=Path(__file__).resolve().parents[1]; V2=ROOT/'v2'
TASKS=[
    ('R1','Could q-erasure margin suffice for q unknown corruptions?','THEORY.md R1','Use exact support-splitting counterexample; choose 2q after rejection.'),
    ('K2-K4','Use alpha_2q and explicit 2D spectra to quantify linearized recovery.','THEORY.md K2-K4','Distinguish known linear theory from nonlinear branch behavior.'),
    ('R2-R4','Could positive differential margin imply global uniqueness or success of L1?','THEORY.md R2-R4','Reject overclaims; derive a local ball with curvature and anchor separation.'),
    ('P1-P2','A curvature-limited prior ball should yield a conditional local recovery bound.','THEORY.md P1-P2','Test geometry/residual joint selection for reliability inversions.'),
    ('C2','Does unguarded residual/geometry ratio always improve finite-pool selection?','THEORY.md C2','If refuted, add residual feasibility gate before geometry.'),
    ('C1','Feasibility-first geometry selection may improve trustworthy stability, with abstention.','THEORY.md P2 and C1','Retain unresolved performance conjecture; audit novelty and prior assumptions.')
]

def freeze_check():
    manifest=read(V2/'V1_FREEZE.json')
    for path,digest in manifest['files'].items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=digest:
            raise RuntimeError('Permanent v1 freeze violated: '+path)
    return len(manifest['files'])

def code_hashes():
    files=list(V2.glob('*.py'))+list((V2/'tests').glob('*.py'))+[V2/name for name in ['config.json','references.json','THEORY.md','LITERATURE_AUDIT.md','PROBLEM_SPEC.md','AGENTS.md']]
    return {f.relative_to(V2).as_posix():hashlib.sha256(f.read_bytes()).hexdigest() for f in files}

def execute(stage,cfg):
    if stage==1: return experiments.erasure_witness()
    if stage==2: return experiments.algebra_checks(cfg['algebra_seed'],cfg['algebra_trials'])
    if stage==3: return experiments.nonlinear_witnesses()
    if stage==4: return experiments.local_bound_checks(cfg['local_seed'],cfg['local_trials'])
    if stage==5: return experiments.ratio_counterexample(cfg['counterexample_seed'],cfg['counterexample_trials'])
    return experiments.estimator_experiment(cfg['estimator_seed'],cfg['estimator_cases_per_scenario'])

def run(folder,steps):
    freeze_check(); cfg=read(V2/'config.json'); folder=Path(folder).resolve(); folder.mkdir(parents=True,exist_ok=True)
    manifest=folder/'manifest.json'; hashes=code_hashes()
    if not manifest.exists(): save(manifest,dict(config=cfg,source_sha256=hashes,v1_frozen_files=freeze_check(),engine='bounded Python task agent; Codex-authored written proofs; independent numeric verifier subprocess'))
    elif read(manifest)['source_sha256']!=hashes: raise RuntimeError('v2 source changed; preserve this run and start a new theory run')
    state_path=folder/'state.json'
    state=read(state_path) if state_path.exists() else dict(status='continue',iteration=0,next_step=TASKS[0][1],unresolved=['C1 performance and novelty','solver search completeness','untrusted prior / unknown q','uncertain anchors'])
    records=history(folder/'research_log.jsonl')
    if len(records)!=state['iteration']: raise RuntimeError('Log/state mismatch; manual recovery required')
    for stage in range(state['iteration']+1,min(len(TASKS),state['iteration']+steps)+1):
        freeze_check(); key,hypothesis,proof,next_step=TASKS[stage-1]
        prior=records[-1]['verdict'] if records else None
        if stage in [2,4] and prior!='refuted': raise RuntimeError('Required refutation missing before assumption repair')
        if stage==6 and prior!='refuted':
            next_step='Unguarded conjecture unresolved; retain feasibility gate as conservative design.'
        out=folder/'iterations'/f'{stage:03d}'; out.mkdir(parents=True,exist_ok=True)
        proposal=dict(claim_id=key,hypothesis=hypothesis,status_before='known' if stage==2 else 'conjectured',parent_iteration=stage-1,previous_verdict=prior,proof_artifact=proof,scope='one conjecture or one explicit assumption repair, no v1 parameter optimization')
        save(out/'proposal.json',proposal)
        test=subprocess.run([sys.executable,'-m','pytest','v2/tests','-q'],cwd=ROOT,text=True,capture_output=True)
        (out/'tests.txt').write_text(test.stdout+test.stderr,encoding='utf-8')
        if test.returncode: raise RuntimeError('v2 tests failed')
        print(f'Theory iteration {stage}: {key}',flush=True)
        evidence=execute(stage,cfg); save(out/'evidence.json',evidence)
        subprocess.run([sys.executable,'-m','v2.verify_task',str(stage),str(out/'evidence.json'),str(out/'verification.json')],cwd=ROOT,check=True)
        verification=read(out/'verification.json'); freeze_check()
        row=dict(iteration=stage,timestamp=datetime.now(timezone.utc).isoformat(),proposal=proposal,proof_artifact=proof,proof_sha256=hashes['THEORY.md'],evidence_artifact=f'iterations/{stage:03d}/evidence.json',verifier_artifact=f'iterations/{stage:03d}/verification.json',verdict=verification['status'],evidence_scope=verification['scope'],next_step=next_step,source_snapshot=hashes,novelty='not established; known foundations retained as known')
        records.append(append(folder/'research_log.jsonl',row))
        state.update(iteration=stage,current_hypothesis=hypothesis,last_result=verification['status'],next_step=next_step,summary=verification['scope'])
        # Budget completed is distinct from settling unresolved research questions.
        if stage==len(TASKS): state['status']='complete'; state['completion_scope']='six configured theory tasks executed; unresolved list retained'
        save(state_path,state)
        print('  '+verification['status'],flush=True)
    registry=[dict(r) for r in CLAIMS]
    if len(records)>=5 and records[4]['verdict']=='refuted':
        for claim in registry:
            if claim['id']=='C2': claim.update(status='refuted',witness='runs/theory-001/iterations/005/evidence.json',scope='finite-pool universal selector claim, not all continuous optimizers')
    save(folder/'claims.json',registry)
    if state['iteration']==len(TASKS):
        from .reporting import report
        report(folder)
    freeze_check()

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--run',default='v2/runs/theory-001'); parser.add_argument('--steps',type=int,default=6); args=parser.parse_args()
    run(ROOT/args.run,args.steps)
