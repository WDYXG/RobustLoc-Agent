"""Protected paired episode execution and outcome accounting."""
from copy import deepcopy
from fractions import Fraction as F
from time import perf_counter
import hashlib
import json
import numpy as np
from .policy import decide
from .decoder import solve
from .certificates import geometry,data_from
from .simulator import acquire,contract,private_snapshot

def compact(decision,certificate_pool):
    out=deepcopy(decision)
    if 'geometry' in out:
        g=out['geometry']; c=g.pop('certificate')
        key=hashlib.sha256(json.dumps(c,sort_keys=True).encode()).hexdigest()
        certificate_pool[key]=c; g['certificate_id']=key
    return out

def execute(episode,cfg,model,method,certificate_pool):
    obs=deepcopy(episode['observation']); private=deepcopy(episode['private'])
    initial=deepcopy(obs); initial_contract=contract(obs,private)
    q=obs.get('q_budget'); initial_g=geometry(data_from(obs),q) if q is not None else None
    trace=[]; started=perf_counter()
    if method=='always-cauchy':
        candidate=solve(obs,cfg,trim=False)
        decision=dict(action='recover',candidate=candidate,certified=False,error_bound=None,
            reason='always-output Cauchy comparator, no certificate claim')
        trace.append(dict(observation=deepcopy(obs),decision=decision))
    else:
        for step in range(initial['acquisitions_remaining']+1):
            decision=decide(obs,cfg,mode=method,model=model)
            trace.append(dict(observation=deepcopy(obs),decision=compact(decision,certificate_pool)))
            if decision['action']!='acquire-more-data': break
            obs=acquire(obs,private,decision['acquisition']['anchor'])
        else: raise RuntimeError('Episode terminated without terminal action')
    elapsed=perf_counter()-started
    terminal=trace[-1]['decision']; output=terminal['action']=='recover'
    truth=np.array([float(F(v)) for v in private['truth']])
    position=np.array([float(F(v)) for v in terminal['candidate']['position']]) if output else None
    error=float(np.linalg.norm(position-truth)) if output else None
    final_contract=contract(obs,private)
    final_g=geometry(data_from(obs),q) if q is not None else None
    lower_before=F(initial_g['lower']) if initial_g else None
    lower_after=F(final_g['lower']) if final_g else None
    acquisitions=len(obs['anchors'])-len(initial['anchors'])
    strict=bool(initial_g and final_g and lower_after>F(initial_g['upper']))
    bound=F(terminal['error_bound']) if output and terminal.get('certified') else None
    return dict(case_id=episode['id'],scenario=episode['scenario'],method=method,
        initial_observation=initial,trace=trace,final_observation=obs,
        private_final=private_snapshot(private),initial_contract=initial_contract,final_contract=final_contract,
        outcome=dict(action=terminal['action'],output=output,error=error,
            wrong_output=bool(output and error>float(F(obs['error_tolerance']))),
            certified=bool(output and terminal.get('certified')),
            error_bound=str(bound) if bound is not None else None,
            bound_violation=bool(bound is not None and error>float(bound)+1e-9),
            acquisitions=acquisitions,lower_before=str(lower_before) if lower_before is not None else None,
            lower_after=str(lower_after) if lower_after is not None else None,
            strict_mu_improvement=strict,runtime_seconds=elapsed))

def metrics(rows):
    n=len(rows); outputs=[r for r in rows if r['outcome']['output']]
    wrong=sum(r['outcome']['wrong_output'] for r in rows)
    return dict(cases=n,outputs=len(outputs),coverage=len(outputs)/n if n else None,
        wrong_outputs=wrong,wrong_output_rate=wrong/n if n else None,
        selective_risk=wrong/len(outputs) if outputs else None,
        abstentions=n-len(outputs),mean_acquisitions=sum(r['outcome']['acquisitions'] for r in rows)/n if n else None,
        accepted_mean_error=float(np.mean([r['outcome']['error'] for r in outputs])) if outputs else None,
        certified_outputs=sum(r['outcome']['certified'] for r in rows),
        certified_bound_violations=sum(r['outcome']['bound_violation'] for r in rows),
        strict_mu_improvement_cases=sum(r['outcome']['strict_mu_improvement'] for r in rows),
        runtime_seconds=sum(r['outcome']['runtime_seconds'] for r in rows))

def summarize(results,cfg):
    summary=dict(in_contract={},outside_contract={},all={},by_scenario={},
        status='numerically-supported',scope='paired fixed synthetic episodes, conditional assumptions separated')
    for method in cfg['methods']:
        rows=[r for r in results if r['method']==method]
        summary['all'][method]=metrics(rows)
        summary['in_contract'][method]=metrics([r for r in rows if r['final_contract']['valid']])
        summary['outside_contract'][method]=metrics([r for r in rows if not r['final_contract']['valid']])
        summary['by_scenario'][method]={s:metrics([r for r in rows if r['scenario']==s]) for s in cfg['scenarios']}
    # Passive risk/coverage curve uses recorded candidates; no held-out retuning.
    curve=[]
    passive=[r for r in results if r['method']=='passive-certified' and r['final_contract']['valid']]
    for tolerance in cfg['risk_coverage_tolerances']:
        outputs=[]
        for row in passive:
            dec=row['trace'][0]['decision']; candidate=dec.get('candidate')
            # Candidate absent at stricter geometry gate: curve coverage is a
            # conservative diagnostic over recorded searches, not complete decoding.
            if candidate and candidate['feasibility']['feasible'] and F(dec['geometry']['lower'])>0:
                bound=2*F(row['initial_observation']['epsilon'])/F(dec['geometry']['lower'])
                if float(bound)<=tolerance:
                    p=np.array([float(F(v)) for v in candidate['position']]); x=np.array([float(F(v)) for v in row['private_final']['truth']])
                    outputs.append(float(np.linalg.norm(p-x)))
        wrong=sum(e>tolerance for e in outputs)
        curve.append(dict(error_tolerance=tolerance,coverage=len(outputs)/len(passive) if passive else 0,
            selective_risk=wrong/len(outputs) if outputs else None,outputs=len(outputs),
            scope='recorded passive candidates; no claim of exhaustive risk-coverage frontier'))
    summary['risk_coverage']=curve
    return summary
