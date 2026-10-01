"""Bounded, resumable research workflow; Codex-authored proofs + actual searches.

The workflow is not an LLM theorem generator. Hypotheses/proofs are authored in
this development session; runtime outcomes and assumption repairs are gated by
independently checked evidence. Historical phase 1 sources remain unchanged.
"""
import argparse
import hashlib
from pathlib import Path
import subprocess
import sys
from datetime import datetime,timezone
from robustloc.storage import read,save,append,history
from v2.agent import freeze_check,code_hashes as phase1_hashes
from . import experiments

ROOT=Path(__file__).resolve().parents[2]
PACKAGE=Path(__file__).resolve().parent
TASKS=[
    ('T1','Fixed-pair separation equals the sorted surviving squared differences.','T1','known'),
    ('R-domain','Could the ambient local condition be necessary on every compact domain?','T3','conjectured'),
    ('T3','Repair T3 using allowed tangent directions and full-dimensional regular domains.','T3','conjectured'),
    ('C3','Could mu equal the infimum of local gamma on a compact full-dimensional domain?','C3 / R-branch','conjectured'),
    ('T5','Can bounded-domain scatter certify global stability even at anchor singularities?','T5','conjectured'),
    ('R-unbounded','Could global injectivity suffice for positive uniform stability on an unbounded domain?','C3 / R-branch','conjectured'),
    ('E-profile','Certify conditional q budgets and separate exact lower from witness upper.','T6','conjectured'),
    ('E-T2-stress','Stress the global two-feasible-explanation recovery bound without a smallball prior.','T2','conjectured')
]

def source_hashes():
    paths=sorted(p for p in PACKAGE.rglob('*') if p.is_file() and p.suffix in ('.py','.md','.json')
                 and '__pycache__' not in p.parts)
    return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}

def artifact_hash(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def proof_excerpt(name):
    text=(PACKAGE/'THEORY.md').read_text(encoding='utf-8')
    section=next(s for s in text.split('\n## ') if s.startswith(name))
    return '## '+section+'\n\nWritten deduction authored in the Codex development session; not a runtime formal proof.\n'

def run(folder,steps):
    folder=Path(folder).resolve()
    require_run=folder.is_relative_to(ROOT/'v2/runs')
    if not require_run: raise ValueError('Phase 2 outputs must be under v2/runs')
    freeze_check(); hashes=source_hashes(); cfg=read(PACKAGE/'config.json')
    folder.mkdir(parents=True,exist_ok=True)
    manifest=folder/'manifest.json'
    if not manifest.exists():
        save(manifest,dict(title=cfg['title'],config=cfg,source_sha256=hashes,
            phase1_sha256=phase1_hashes(),v1_frozen_files=freeze_check(),
            created=datetime.now(timezone.utc).isoformat(),
            engine='Codex-authored mathematics + finite Python task controller + exact rational consumer',
            novelty='not established'))
    else:
        saved=read(manifest)
        if saved['source_sha256']!=hashes or saved['phase1_sha256']!=phase1_hashes():
            raise RuntimeError('Sources changed; historical run cannot be resumed')
    records=history(folder/'research_log.jsonl')
    state_path=folder/'state.json'
    state=read(state_path) if state_path.exists() else dict(iteration=0,status='continue',
        unresolved=['novelty/full Calafiore theorem-level comparison',
            'tight mu values and scalable subset certificates',
            'C3 under an additional connected/convex domain restriction',
            'unknown actual q and true-domain/noise-budget validity',
            'uncertain anchors and existence/completeness of a decoder'])
    if len(records)!=state['iteration']: raise RuntimeError('Log/state mismatch; audit before recovery')
    for stage in range(state['iteration']+1,min(len(TASKS),state['iteration']+steps)+1):
        freeze_check()
        if stage in (3,5,7) and records[-1]['verdict']!='refuted':
            state.update(status='needs-attention',next_step='Required counterexample not verified; preserve unresolved conjecture')
            save(state_path,state); return
        key,hypothesis,proof,status_before=TASKS[stage-1]
        out=folder/'iterations'/f'{stage:03d}'
        if out.exists(): raise RuntimeError('Existing incomplete iteration preserved; manual audit required')
        out.mkdir(parents=True)
        proposal=dict(claim_id=key,hypothesis=hypothesis,status_before=status_before,
            parent_iteration=stage-1,previous_verdict=records[-1]['verdict'] if records else None,
            proof_artifact='v2/global_stability/THEORY.md '+proof,
            assumptions_and_scope='exact fixed anchors and weights; individual claim assumptions in THEORY.md')
        save(out/'proposal.json',proposal)
        (out/'proof_attempt.md').write_text(proof_excerpt(proof),encoding='utf-8')
        print(f'Phase 2 iteration {stage}: {key}',flush=True)
        if stage==1: evidence=experiments.algebra(cfg)
        elif stage==2: evidence=experiments.domain_witness()
        elif stage==3: evidence=experiments.local_limits(cfg)
        elif stage==4: evidence=experiments.branch_search()
        elif stage==5: evidence=experiments.bounded_extension(cfg)
        elif stage==6: evidence=experiments.unbounded_witness(cfg)
        elif stage==7: evidence=experiments.profile(cfg)
        else: evidence=experiments.recovery(cfg,read(folder/'iterations/007/evidence.json'))
        save(out/'evidence.json',evidence)
        cmd=[sys.executable,'-m','v2.global_stability.verify_task',str(stage),str(out/'evidence.json'),str(out/'verification.json')]
        if stage==8: cmd+=['--profile',str(folder/'iterations/007/evidence.json')]
        result=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)
        (out/'verifier_stdout.txt').write_text(result.stdout+result.stderr,encoding='utf-8')
        if result.returncode: raise RuntimeError('Independent verifier failed; artifacts preserved')
        verification=read(out/'verification.json'); freeze_check()
        next_step=TASKS[stage][1] if stage<len(TASKS) else 'Eight configured tasks complete; retain unresolved mathematics and provenance limits'
        row=dict(iteration=stage,timestamp=datetime.now(timezone.utc).isoformat(),proposal=proposal,
            verdict=verification['status'],verification=verification,next_step=next_step,
            artifact_sha256={name:artifact_hash(out/name) for name in ['proposal.json','proof_attempt.md','evidence.json','verification.json','verifier_stdout.txt']})
        records.append(append(folder/'research_log.jsonl',row))
        state.update(iteration=stage,status='continue',last_result=verification['status'],next_step=next_step)
        if stage==len(TASKS): state.update(status='complete',completion_scope='Configured eight-task workflow only; unresolved research retained')
        save(state_path,state); print('  '+verification['status'],flush=True)
    claims=read(PACKAGE/'claims.json')
    for claim in claims:
        matching=[r for r in records if r['proposal']['claim_id']==claim['id']]
        if matching:
            last=matching[-1]
            # Numeric evidence does not demote the separately authored T3 proof.
            if claim['id'] not in ('T1','T3'): claim['status']=last['verdict']
            claim['runtime_evidence']=f"iterations/{last['iteration']:03d}/evidence.json"
    save(folder/'claims.json',claims)
    if state['iteration']==len(TASKS) and not (folder/'output_sha256.json').exists():
        from .reporting import report
        report(folder)
        save(folder/'output_sha256.json',{p.relative_to(folder).as_posix():artifact_hash(p)
            for p in sorted(folder.rglob('*')) if p.is_file() and p.name!='output_sha256.json'})
    freeze_check()

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--run',default='v2/runs/global-stability-001')
    parser.add_argument('--steps',type=int,default=8); args=parser.parse_args()
    if args.steps<1: parser.error('steps must be positive')
    run(ROOT/args.run,args.steps)
