"""Frozen, paired, held-out evaluation; proposer never receives target coordinates."""
import argparse
import csv
import gzip
import hashlib
import io
import json
import platform
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np
import scipy
from scipy.stats import binom
from robustloc.baseline import solve_unweighted, solve_weighted
from robustloc.proposer import propose
from .service import INCUMBENT, localize, observations
from .simulation import specifications, generate, COUNTS, NOISE, GEOMETRIES, CONTAMINATION, SPLITS

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = Path(__file__).resolve().parent
POLICY = dict(minimum_relative_cep90_gain=.01, maximum_failure_rate_increase=.01,
              maximum_scenario_cep90_ratio=1.25)
EVALUATOR_VERSION = 2


def save(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def hashes():
    paths = list(PACKAGE.glob('*.py'))+list((PACKAGE/'tests').glob('*.py'))+[PACKAGE/'PROTOCOL.md']
    paths += [ROOT/'robustloc'/f for f in ('candidate.py','proposer.py','verifier.py','optimizer.py','baseline.py','simulator.py')]
    paths += [ROOT/'v3b/assumption_agent'/f for f in ('certificates.py','verifier.py')]
    paths += [ROOT/'v2/global_stability/exact.py']
    paths += [ROOT/'v3/certified_agent'/f for f in ('decoder.py','certificates.py')]
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}


def frozen_history():
    f = json.loads((PACKAGE/'PREVIOUS_FREEZE.json').read_text())
    changed = [p for p, h in f['sha256'].items() if not (ROOT/p).is_file() or hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h]
    if changed: raise AssertionError(changed)
    return f['count']


def one(job):
    spec, method, config = job
    payload, private = generate(spec)
    start = time.perf_counter()
    if method in ('unweighted-ls', 'weighted-ls'):
        obs, _ = observations(payload)
        sol = (solve_unweighted if method=='unweighted-ls' else solve_weighted)(obs)
        pos, success = sol.position, sol.success
        decision = 'unverified-baseline'
    else:
        answer = localize(payload, config)
        pos, success, decision = np.array(answer['estimate']), answer['optimizer_success'], answer['decision']
    elapsed = time.perf_counter()-start
    error = float(np.linalg.norm(pos-np.array(private['truth'])))
    if not np.isfinite(error): raise RuntimeError('Nonfinite output: do not silently drop a case')
    return dict(**spec, method=method, estimate=list(map(float, pos)), error=error,
                optimizer_success=bool(success), decision=decision, seconds=elapsed)


def metrics(rows):
    e = np.sort([r['error'] for r in rows]); n = len(e)
    fail = int(sum(v>30 for v in e)); p = fail/n; z = 1.959963984540054
    den = 1+z*z/n; centre=(p+z*z/(2*n))/den
    half=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    lo=int(binom.ppf(.025, n, .9)); hi=int(binom.ppf(.975, n, .9))+1
    return dict(cases=n, mean_error=float(np.mean(e)), cep50=float(np.quantile(e,.5)),
                cep90=float(np.quantile(e,.9)), max_error=float(e[-1]),
                cep90_order_statistic_95_interval=[0. if lo==0 else float(e[lo-1]),
                                                  None if hi>n else float(e[hi-1])],
                failure_rate=p, failure_count=fail, failure_rate_wilson95=[max(0.,centre-half),min(1.,centre+half)],
                nonfinite_cases=0, optimization_failures=sum(not r['optimizer_success'] for r in rows),
                total_solver_seconds=sum(r['seconds'] for r in rows),
                meets_30m_point_estimate=bool(np.quantile(e,.9)<=30))


def summarize(rows):
    return dict(overall=metrics(rows), by_scenario={s:metrics([r for r in rows if r['scenario']==s])
                for s in sorted({r['scenario'] for r in rows})}, rows=rows)


def evaluate(pool, specs, name, config, path):
    rows=list(pool.map(one, ((s,name,config) for s in specs), chunksize=16))
    result=summarize(rows); save(path,result)
    print(f'{name}: {len(rows)} cases; CEP90={result["overall"]["cep90"]:.3f} m', flush=True)
    return result


def public_state(best, validation, last):
    # No truth coordinates, individual error labels or private simulator state.
    return dict(best_method=best, best_validation_metrics={k:v for k,v in validation.items() if k!='rows'}, last_result=last)


def dump_inputs(path, specs):
    for kind in ('observations', 'evaluation-private'):
        with open(path/f'{kind}.jsonl.gz','xb') as raw:
            with gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) as zipped:
                for s in specs:
                    obs, private=generate(s)
                    zipped.write((json.dumps(dict(specification=s, data=obs if kind=='observations' else private))+'\n').encode())


def run(output, workers=4):
    out=Path(output); out.mkdir(parents=True, exist_ok=False)
    started=time.time(); before=hashes()
    save(out/'manifest.json', dict(source_sha256=before, frozen_historical_files=frozen_history(),
         python=sys.version, numpy=np.__version__, scipy=scipy.__version__, platform=platform.platform(),
         counts=COUNTS, geometries=GEOMETRIES, noise=NOISE, contamination=CONTAMINATION,
         splits=SPLITS, policy=POLICY, workers=workers, timestamp=time.strftime('%Y-%m-%dT%H:%M:%S%z'),
         metric='Euclidean metres; CEP90 linear quantile over ALL estimates; failure >30m',
         synthetic_only=True, evaluator_version=EVALUATOR_VERSION))
    dev=list(specifications('development')); val=list(specifications('validation'))
    best=dict(name='frozen-cauchy', config=INCUMBENT)
    # Reuse the existing policy, skipping mechanisms already established in v1.
    skip=['robust_loss','cauchy','adaptive_scale','soft_l1','confidence']
    history=[dict(proposal=dict(mechanism=k), historical_skip=True) for k in skip]
    save(out/'reuse.json',dict(source='runs/run-001/frozen_method.json',
         skipped_mechanisms=skip, reason='Bounded transfer check only: threshold, weighting, multistart'))
    with ProcessPoolExecutor(max_workers=workers) as pool:
        baseline=evaluate(pool,val,'weighted-ls',None,out/'validation-baseline.json')
        incumbent=evaluate(pool,val,best['name'],best['config'],out/'validation-incumbent.json')
        current_path=out/'validation-incumbent.json'
        for step in range(1,4):
            state=public_state(best,incumbent,'initial' if step==1 else result['verdict'])
            proposal=propose(state,history)
            if proposal is None: break
            iteration=out/f'iteration-{step:02d}'; iteration.mkdir()
            save(iteration/'state.json',state); save(iteration/'proposal.json',proposal)
            evaluate(pool,dev,f'proposal-{step}',proposal['config'],iteration/'development.json')
            candidate=evaluate(pool,val,f'proposal-{step}',proposal['config'],iteration/'validation.json')
            request=dict(candidate=str((iteration/'validation.json').resolve()), incumbent=str(current_path.resolve()),
                         baseline=str((out/'validation-baseline.json').resolve()), policy=POLICY)
            save(iteration/'verifier-request.json',request)
            subprocess.run([sys.executable,'-m','robustloc.verifier',str(iteration/'verifier-request.json'),
                            str(iteration/'verdict.json')],cwd=ROOT,check=True)
            result=json.loads((iteration/'verdict.json').read_text())
            history.append(dict(proposal=proposal,result=result))
            if result['verdict']=='supported':
                best=dict(name=f'proposal-{step}',config=proposal['config']); incumbent=candidate
                current_path=iteration/'validation.json'
            print(f'Agent step {step} {proposal["mechanism"]}: {result["verdict"]}',flush=True)
        save(out/'research-trace.json', history)
        # This artifact precedes ANY construction/evaluation of final cases.
        save(out/'selected-method.json', dict(**best, source_sha256=before,
             selected_using='development and validation only', evidence='numerically-supported'))
        if hashes()!=before: raise AssertionError('Sources changed during selection')
        final=list(specifications('test')); dump_inputs(out,final)
        all_results={}
        for name,cfg in [('unweighted-ls',None),('weighted-ls',None),('frozen-cauchy',INCUMBENT),('final',best['config'])]:
            all_results[name]=evaluate(pool,final,name,cfg,out/f'test-{name}.json')
        strata=[]
        for name,res in all_results.items():
            groups={}
            for r in res['rows']:
                groups.setdefault((r['model'],r['n'],r['geometry'],r['noise'],r['contamination'],r['mismatch']),[]).append(r)
            for key,rs in groups.items():
                strata.append(dict(method=name,model=key[0],n=key[1],geometry=key[2],noise=key[3],
                                    contamination=key[4],mismatch=key[5],**metrics(rs)))
        save(out/'strata.json',strata)
        with (out/'strata.csv').open('w',newline='',encoding='utf-8-sig') as f:
            w=csv.DictWriter(f,fieldnames=list(strata[0])); w.writeheader(); w.writerows(strata)
    save(out/'completion.json',dict(elapsed_seconds=time.time()-started, sources_unchanged=hashes()==before,
          historical_files_unchanged=frozen_history(), final_cases=len(final),
          selected_method=best, final_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
          for p in out.glob('test-*.json')}))


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('output'); p.add_argument('--workers',type=int,default=4)
    a=p.parse_args(); run(a.output,a.workers)
