"""Exact mathematical consumer, complete branch/frontier coverage and frozen replay."""
import argparse
from pathlib import Path
from fractions import Fraction as F
from itertools import combinations
import json
from v3b.assumption_agent.storage import read,hydrate,hash_value
from .freeze import ROOT,check,sources,digest
from .verifier import verify_cover,verify_witness,feasible_world
from .actions import apply


def verify_minimum(obs,f):
    affordable=[o for o in obs['offers'] if F(o['cost'])<=F(obs['budget'])]
    expected=[]
    for n in range(len(affordable)+1):
        for bundle in combinations(affordable,n):
            cost=sum(F(o['cost']) for o in bundle)
            if cost<=F(obs['budget']): expected.append(([o['id'] for o in bundle],str(cost)))
    if [(r['ids'],r['cost']) for r in f['rows']]!=expected: raise ValueError('incomplete bundle/cost frontier')
    for r in f['rows']:
        alive=[x for x in r['forecast_results'] if not x['empty']]
        if r['certified']!=bool(alive and all(x['safe'] for x in alive)): raise ValueError('forecast aggregation')
    successes=[r for r in f['rows'] if r['certified']]
    best=min(successes,key=lambda r:(F(r['cost']),len(r['ids']),tuple(r['ids']))) if successes else None
    if f['minimum_sufficient_bundle']!=best: raise ValueError('not the cheapest sufficient bundle')


def audit(path):
    path=Path(path); m=read(path/'manifest.json')
    if m['sources']!=sources(): raise ValueError('historical sources changed')
    frozen=check()
    if (path/'output_hashes.json').exists():
        for n,h in read(path/'output_hashes.json')['files'].items():
            if not (path/n).is_file() or digest(path/n)!=h: raise ValueError('output hash mismatch '+n)
    from v3b.assumption_agent.verifier import verify_margin
    certs=0
    for p in (path/'certificates').glob('*.json'):
        c=read(p)
        if hash_value(c)!=p.stem: raise ValueError('certificate identity')
        verify_margin(c); certs+=1
    states={}; costs={}; last='0'*64; events=0; outputs=0; witnesses=0; frontiers=0
    for line in (path/'history.jsonl').read_text(encoding='utf-8').splitlines():
        row=json.loads(line); h=row.pop('hash')
        if row['index']!=events or row['previous_hash']!=last or hash_value(row)!=h: raise ValueError('history integrity')
        last=h; events+=1; ev=hydrate(path,row['payload']); key=(ev['episode_id'],ev['method'])
        initial=read(path/'episodes'/ev['episode_id']/'observation.json')
        states.setdefault(key,initial); costs.setdefault(key,F(0))
        if states[key]!=ev['observation']: raise ValueError('observation replay mismatch')
        obs=ev['observation']; d=ev['decision']
        if d.get('witness'): verify_witness(obs,d['witness']); witnesses+=1
        if d.get('frontier'): verify_minimum(obs,d['frontier']); frontiers+=1
        if d['action']=='recover': verify_cover(obs,d['certificate']); outputs+=1
        if d['action']=='acquire-information':
            o=next(o for o in obs['offers'] if o['id']==d['offer_id']); costs[key]+=F(o['cost']); states[key]=apply(obs,o,ev['reply'])
    completed=read(path/'completion.json')
    if completed['history_events']!=events or completed['last_hash']!=last: raise ValueError('completion mismatch')
    results=read(path/'results.json'); good_violations=bad_violations=0
    for r in results:
        key=(r['episode_id'],r['method']); outcome=hydrate(path,read(path/'outcomes'/r['episode_id']/(r['method']+'.json')))
        if r!=outcome['result'] or states[key]!=outcome['observation']: raise ValueError('result replay')
        initial=read(path/'episodes'/r['episode_id']/'observation.json'); private=read(path/'episodes'/r['episode_id']/'private.json')
        if costs[key]!=F(r['information_cost']) or costs[key]>F(initial['budget']): raise ValueError('cost/budget')
        valid=feasible_world(states[key],dict(target=private['target'],positions=private['positions']))
        if valid!=r['contract_valid']: raise ValueError('physical feasibility evaluation mismatch')
        if r['intended_in_contract'] and not valid: raise ValueError('honest fixture assumption failure')
        if r['output']:
            d=outcome['decision']; verify_cover(states[key],d['certificate'])
            error=sum(float(F(a)-F(b))**2 for a,b in zip(d['position'],private['target']))**.5
            if error!=r['error']: raise ValueError('error metric replay')
            violation=error>float(F(d['radius_upper']))+1e-10
            if violation!=r['bound_violation']: raise ValueError('bound metric mismatch')
            if valid: good_violations+=int(violation)
            else: bad_violations+=int(violation)
    tasks=hydrate(path,read(path/'research_tasks.json'))
    for c in tasks['counterexamples']: verify_witness(c['observation'],c['witness'])
    pos=tasks['five_reference_q1']; verify_cover(pos['observation'],pos['certificate'])
    if good_violations: raise ValueError('valid-world bound violated')
    return dict(passed=True,previous_files_unchanged=frozen,method_episodes=len(results),history_events=events,
       mathematical_certificates=certs,positive_continuous_covers=outputs,structural_witnesses_verified=witnesses,
       finite_minimum_frontiers_verified=frontiers,exact_counterexamples=len(tasks['counterexamples']),
       in_contract_bound_violations=good_violations,out_of_contract_bound_violations=bad_violations,
       scope='independent math consumers and complete-cost enumeration; frozen simulation replay; no physical root verification')


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--run',default='v3c/runs/trust-identifiability-001'); a=p.parse_args(); print(audit(ROOT/a.run))
