"""Freeze → train advisory model → paired active episodes → independent audit."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime,timezone
from robustloc.storage import read,save,canonical
from v3.freeze import ROOT,check
from . import learning,simulator,evaluation,reporting

PACKAGE=Path(__file__).resolve().parent

def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def sources():
    paths=[p for p in PACKAGE.rglob('*') if p.is_file() and p.suffix in ('.py','.md','.json') and '__pycache__' not in p.parts]
    paths += [ROOT/'v3/freeze.py',ROOT/'v3/V1_V2_FREEZE.json',ROOT/'v3/AGENTS.md',ROOT/'v3/README.md']
    return {p.relative_to(ROOT).as_posix():digest(p) for p in sorted(paths)}

def run(folder):
    folder=Path(folder).resolve()
    if not folder.is_relative_to(ROOT/'v3/runs'): raise ValueError('Output outside v3/runs')
    check(); cfg=read(PACKAGE/'config.json'); hashes=sources()
    if (folder/'manifest.json').exists():
        if read(folder/'manifest.json')['source_sha256']!=hashes: raise RuntimeError('Sources changed; preserve run, create another')
        if (folder/'output_sha256.json').exists():
            from .audit import audit
            print(audit(folder)); return
        raise RuntimeError('Incomplete run preserved; audit before explicit recovery')
    folder.mkdir(parents=True,exist_ok=True)
    import numpy,scipy
    save(folder/'manifest.json',dict(title=cfg['title'],created=datetime.now(timezone.utc).isoformat(),
        config=cfg,source_sha256=hashes,frozen_files=check(),numpy=numpy.__version__,scipy=scipy.__version__,
        engine='finite observation-only policy + local numerical decoder + horizon-3 certificate planner',
        novelty='not established',heldout_policy='fixed config before evaluation; no post-hoc threshold selection'))
    print('Train advisory geometry predictor on independent layouts',flush=True)
    learned=learning.train(cfg); save(folder/'learning.json',learned)
    model=learned['model']; pool={}; results=[]; previous='GENESIS'; actions=0
    for scenario in cfg['scenarios']:
        print('Evaluate paired scenario: '+scenario,flush=True)
        for index in range(cfg['heldout_cases_per_scenario']):
            episode=simulator.make_episode(scenario,index,cfg)
            save(folder/'observations'/f'{episode["id"]}.json',episode['observation'])
            save(folder/'private'/f'{episode["id"]}.json',simulator.private_snapshot(episode['private']))
            for method in cfg['methods']:
                row=evaluation.execute(episode,cfg,model,method,pool); results.append(row)
                save(folder/'episodes'/f'{method}__{episode["id"]}.json',row)
                for step,turn in enumerate(row['trace']):
                    event=dict(timestamp=datetime.now(timezone.utc).isoformat(),case_id=row['case_id'],method=method,step=step,
                        turn=turn,previous_hash=previous)
                    event['record_hash']=hashlib.sha256(canonical(event).encode()).hexdigest()
                    with (folder/'action_log.jsonl').open('a',encoding='utf-8') as stream:
                        stream.write(canonical(event)+'\n'); stream.flush()
                    previous=event['record_hash']; actions+=1
            check()
        save(folder/'state.json',dict(status='continue',completed_scenario=scenario,
            method_episode_results=len(results),actions=actions,next_step='independent verification before report'))
    for key,c in pool.items(): save(folder/'certificates'/f'{key}.json',c)
    cmd=[sys.executable,'-m','v3.certified_agent.audit','--run',str(folder.relative_to(ROOT)),
         '--pre-report','--output',str(folder/'verification.json')]
    completed=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)
    (folder/'verifier_stdout.txt').write_text(completed.stdout+completed.stderr,encoding='utf-8')
    if completed.returncode: raise RuntimeError('Independent verifier rejected run; evidence preserved')
    verified=read(folder/'verification.json'); summary=evaluation.summarize(results,cfg)
    reporting.report(folder,summary,learned,results,verified,cfg)
    active=summary['in_contract']['active-certified']; always=summary['in_contract']['always-cauchy']
    passive=summary['in_contract']['passive-certified']
    claims=[dict(id='C-decision',status='numerically-supported' if active['wrong_outputs']<always['wrong_outputs'] else 'conjectured',
        claim='Fewer wrong outputs with useful conditional coverage',evidence='summary.json',novelty='not established'),
        dict(id='C-one-anchor',status='refuted',claim='One new reporter always restores q-corruption stability',
             evidence='episodes/active-certified__new-report-corrupted-000.json and unit exact upper witnesses',novelty='not established'),
        dict(id='C-lookahead',status='numerically-supported' if active['outputs']>passive['outputs'] else 'conjectured',
             claim='Finite lookahead restores some cases unavailable to passive certification',evidence='summary.json',novelty='not established'),
        dict(id='C-learning-cert',status='refuted' if learned['summary']['false_positive'] else 'conjectured',
             claim='High surrogate probability alone supplies a safety certificate',evidence='learning.json',
             scope='empirical false positive only if witnessed; absence of errors is not proof',novelty='not established')]
    save(folder/'claims.json',claims)
    save(folder/'state.json',dict(status='complete',completion_scope='fixed Phase 3A simulation and independent audit',
        method_episode_results=len(results),actions=actions,
        unresolved=['real-world assumptions','uncertain anchors','decoder completeness','generality and novelty','full capacity beyond computed q']))
    check()
    save(folder/'output_sha256.json',{p.relative_to(folder).as_posix():digest(p) for p in sorted(folder.rglob('*'))
        if p.is_file() and p.name!='output_sha256.json'})
    print(json.dumps(dict(in_contract=summary['in_contract'],verification=verified),indent=2),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--run',default='v3/runs/certified-agent-001')
    args=parser.parse_args(); run(ROOT/args.run)
