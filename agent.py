"""Persistent offline research controller. Commands: baseline, research, finalize.

The finite proposer is an adaptive rule agent; no external LLM is needed or claimed.
Independent verification is a separate process, not a second language model.
"""
import argparse
import hashlib
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone
try:
    import tomllib
except ImportError:
    import tomli as tomllib
from robustloc.storage import save, read, history, append
from robustloc.evaluator import evaluate
from robustloc.baseline import solve_unweighted, solve_weighted
from robustloc.candidate import solve, DEFAULT
from robustloc.proposer import propose

ROOT = Path(__file__).resolve().parent
PROTECTED = ['robustloc/simulator.py','robustloc/scenarios.py','robustloc/baseline.py','robustloc/optimizer.py','robustloc/metrics.py','robustloc/evaluator.py','robustloc/verifier.py','config.toml']

def hashes():
    return {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in PROTECTED}

def timestamp():
    return datetime.now(timezone.utc).isoformat()

def tests(path):
    result = subprocess.run([sys.executable,'-m','pytest','-q'],cwd=ROOT,capture_output=True,text=True)
    path.write_text(result.stdout+result.stderr,encoding='utf-8')
    if result.returncode: raise RuntimeError('Tests failed; see '+str(path))

def guard(run):
    manifest=read(run/'manifest.json')
    if manifest['protected_sha256'] != hashes():
        raise RuntimeError('EVALUATOR_ISSUE: protected environment changed; use a versioned new run')
    for relative, digest in manifest['baseline_sha256'].items():
        if hashlib.sha256((run/relative).read_bytes()).hexdigest() != digest:
            raise RuntimeError('Historical baseline changed')

def baseline(run, cfg):
    if (run/'manifest.json').exists():
        guard(run); print('Existing immutable baseline verified.'); return
    run.mkdir(parents=True,exist_ok=True)
    tests(run/'baseline_tests.txt')
    for split in ['development','validation']:
        for name,solver in [('unweighted',solve_unweighted),('weighted',solve_weighted)]:
            print('Baseline',split,name,flush=True)
            save(run/f'baseline_{split}_{name}.json',evaluate(solver,split,cfg['experiment'][split+'_cases']))
    save(run/'baseline_metrics.json',{s:{m:read(run/f'baseline_{s}_{m}.json')['by_scenario'] for m in ['unweighted','weighted']} for s in ['development','validation']})
    files=list(run.glob('baseline_*.json'))
    save(run/'manifest.json',dict(created=timestamp(),protected_sha256=hashes(),baseline_sha256={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in files},config=cfg,python=sys.version))
    initial=read(run/'baseline_validation_weighted.json')
    save(run/'state.json',dict(status='continue',iteration=0,current_hypothesis=None,current_method='weighted',best_method=dict(name='weighted',config=DEFAULT),best_validation_metrics={k:v for k,v in initial.items() if k!='rows'},best_validation_path=str((run/'baseline_validation_weighted.json').resolve()),last_result='inconclusive',summary='Baseline tested and frozen.',next_step='Investigate residual robustness.'))
    from robustloc.figures import baseline_figures
    baseline_figures(run)

def research(run,cfg,limit):
    guard(run)
    state=read(run/'state.json')
    if (run/'frozen_method.json').exists(): raise RuntimeError('Method frozen; research prohibited in this run')
    records=history(run/'research_log.jsonl')
    if len(records)!=state['iteration']: raise RuntimeError('State/log mismatch; inspect interrupted transaction')
    for _ in range(min(limit,cfg['experiment']['iterations']-state['iteration'])):
        guard(run)
        proposal=propose(state,records)
        if proposal is None: break
        i=state['iteration']+1
        folder=run/'iterations'/f'{i:03d}'
        folder.mkdir(parents=True,exist_ok=True)
        save(folder/'proposal.json',proposal)
        active=ROOT/'robustloc'/'candidate_config.json'
        previous=active.read_text(encoding='utf-8') if active.exists() else '{}'
        save(active,proposal['config'])
        (folder/'candidate_config.json').write_bytes(active.read_bytes())
        (folder/'candidate.py').write_bytes((ROOT/'robustloc/candidate.py').read_bytes())
        tests(folder/'tests.txt')
        print(f'Iteration {i}: {proposal["mechanism"]}, parent={proposal["parent"]}',flush=True)
        for split in ['development','validation']:
            result=evaluate(lambda obs:solve(obs,proposal['config']),split,cfg['experiment'][split+'_cases'])
            save(folder/f'{split}.json',result)
        request=dict(candidate=str((folder/'validation.json').resolve()),incumbent=state['best_validation_path'],baseline=str((run/'baseline_validation_weighted.json').resolve()),policy=cfg['verification'])
        save(folder/'verify_request.json',request)
        subprocess.run([sys.executable,'-m','robustloc.verifier',str(folder/'verify_request.json'),str(folder/'verification.json')],cwd=ROOT,check=True)
        check=read(folder/'verification.json')
        result=read(folder/'validation.json')
        if check['verdict']=='supported':
            state['best_method']=dict(name=f'iteration-{i}',config=proposal['config'])
            state['best_validation_metrics']={k:v for k,v in result.items() if k!='rows'}
            state['best_validation_path']=str((folder/'validation.json').resolve())
        state.update(iteration=i,current_hypothesis=proposal['hypothesis'],current_method=f'iteration-{i}',last_result=check['verdict'],summary=f'{proposal["mechanism"]}: {check["decision"]}',next_step='Re-read worst scenario and rejected failure cases; propose one untested mechanism.')
        row=dict(iteration=i,timestamp=timestamp(),proposal=proposal,hypothesis=proposal['hypothesis'],mathematical_reasoning_summary=proposal['mathematical_reasoning_summary'],code_changes=dict(file='robustloc/candidate_config.json',before=previous,after=proposal['config'],candidate_source_sha256=hashlib.sha256((folder/'candidate.py').read_bytes()).hexdigest()),experiment_config=cfg['experiment'],metrics={s:{k:v for k,v in read(folder/f'{s}.json').items() if k!='rows'} for s in ['development','validation']},comparison_to_baseline=check['comparison_to_baseline'],comparison_to_best=dict(relative_cep90_gain=check['relative_cep90_gain'],failure_rate_difference=check['failure_rate_difference']),failure_cases=check['failure_cases'],verdict=check['verdict'],decision=check['decision'],next_step=state['next_step'],best_method=state['best_method'])
        records.append(append(run/'research_log.jsonl',row))
        save(run/'state.json',state)
        print(f'  {check["verdict"]}: CEP90={result["overall"]["cep90"]:.3f}; best={state["best_method"]["name"]}',flush=True)
    from robustloc.figures import iteration_figures
    iteration_figures(run)

def finalize(run,cfg):
    guard(run)
    state=read(run/'state.json')
    if state['iteration']<cfg['experiment']['iterations']: raise RuntimeError('Research budget incomplete')
    frozen=run/'frozen_method.json'
    if not frozen.exists():
        save(frozen,dict(method=state['best_method'],timestamp=timestamp(),candidate_sha256=hashlib.sha256((ROOT/'robustloc/candidate.py').read_bytes()).hexdigest(),protected_sha256=hashes(),log_hash=history(run/'research_log.jsonl')[-1]['record_hash']))
    spec=read(frozen)
    if spec['candidate_sha256'] != hashlib.sha256((ROOT/'robustloc/candidate.py').read_bytes()).hexdigest(): raise RuntimeError('Frozen candidate source changed')
    for name,solver in [('unweighted',solve_unweighted),('weighted',solve_weighted),('final',lambda obs:solve(obs,spec['method']['config']))]:
        path=run/f'heldout_{name}.json'
        if not path.exists():
            print('Final held-out',name,flush=True)
            save(path,evaluate(solver,'heldout',cfg['experiment']['heldout_cases']))
    save(run/'final_metrics.json',{m:{k:v for k,v in read(run/f'heldout_{m}.json').items() if k!='rows'} for m in ['unweighted','weighted','final']})
    state.update(status='complete',summary='Frozen method evaluated once on final held-out; no post-test tuning.',next_step='Report evidence and limitations. Use a new benchmark for future research.')
    save(run/'state.json',state)
    from robustloc.reporting import report
    report(run,cfg)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('command',choices=['baseline','research','finalize'])
    parser.add_argument('--run',default='runs/run-001')
    parser.add_argument('--iterations',type=int,default=8)
    args=parser.parse_args()
    os.chdir(ROOT)
    run=Path(args.run).resolve()
    cfg=tomllib.loads((ROOT/'config.toml').read_text())
    if args.command=='baseline': baseline(run,cfg)
    elif args.command=='research': research(run,cfg,args.iterations)
    else: finalize(run,cfg)

if __name__=='__main__': main()
