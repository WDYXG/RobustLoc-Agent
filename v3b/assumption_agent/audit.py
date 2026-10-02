"""Read-only consumer replay: bounds, receipts, budgets, private metrics and hashes."""
import argparse
from copy import deepcopy
from fractions import Fraction as F
from pathlib import Path
from .storage import read,hash_value,hydrate
from .freeze import ROOT,check,source_hashes,digest
from .verifier import verify_margin,verify_recovery,verify_frontier
from .contracts import deliver,volume_ratio
from .simulator import evaluate


def audit(path):
    path=Path(path); manifest=read(path/'manifest.json')
    if manifest['sources']!=source_hashes(): raise ValueError('run/source mismatch; do not repair frozen files')
    frozen=check(); certs=0
    if (path/'output_hashes.json').exists():
        for name,h in read(path/'output_hashes.json')['files'].items():
            if not (path/name).is_file() or digest(path/name)!=h: raise ValueError('output byte mismatch: '+name)
    for p in sorted((path/'certificates').glob('*.json')):
        c=read(p)
        if hash_value(c)!=p.stem: raise ValueError('certificate identity mismatch')
        verify_margin(c); certs+=1
    previous='0'*64; events=0; states={}; costs={}; outputs=0; verified=0
    for line in (path/'history.jsonl').read_text(encoding='utf-8').splitlines():
        import json
        row=json.loads(line); claimed=row.pop('hash')
        if row['index']!=events or row['previous_hash']!=previous or hash_value(row)!=claimed: raise ValueError('history chain')
        previous=claimed; events+=1; event=hydrate(path,row['payload'])
        key=(event['episode_id'],event['method']); obs=event['observation']; d=event['decision']
        initial=read(path/'episodes'/event['episode_id']/'observation.json')
        if key not in states: states[key]=initial; costs[key]=F(0)
        if states[key]!=obs: raise ValueError('action observation replay mismatch')
        verify_frontier(obs,d['frontier'])
        for fr in d['frontier']['rows']:
            expected={k:obs[k] for k in ('anchors','weights','domain','radii')}
            if fr['certificate']['data']!=expected or fr['certificate']['q']!=fr['q']: raise ValueError('frontier contract mismatch')
            b=verify_margin(fr['certificate'])
            if F(fr['lower'])!=b: raise ValueError('frontier lower mismatch')
        if d['action']=='recover': verify_recovery(obs,d); verified+=1
        if d['action']=='acquire-more-data':
            offer=next(o for o in obs['offers'] if o['id']==d['offer_id']); costs[key]+=F(offer['cost'])
            try:
                new=deliver(obs,offer,event['receipt'])
                if not event['receipt_accepted']: raise ValueError('valid receipt rejected in stored replay')
            except ValueError:
                if event['receipt_accepted']: raise ValueError('invalid receipt authorized')
                new=deepcopy(obs); new['offers']=[o for o in obs['offers'] if o['id']!=offer['id']]
                new['budget']=str(F(obs['budget'])-F(offer['cost']))
            states[key]=new
        else:
            private=read(path/'episodes'/event['episode_id']/'private.json')
            ev=evaluate(obs,private,d)
            if ev!=event['evaluation']: raise ValueError('private evaluation replay mismatch')
            outputs+=int(ev['output'])
    completion=read(path/'completion.json')
    if events!=completion['events'] or previous!=completion['last_hash']: raise ValueError('completion mismatch')
    results=read(path/'results.json'); valid_violations=0; invalid_violations=0; new_certified=0
    for row in results:
        key=(row['episode_id'],row['method']); initial=read(path/'episodes'/row['episode_id']/'observation.json')
        outcome=hydrate(path,read(path/'outcomes'/row['episode_id']/(row['method']+'.json')))
        if states[key]!=outcome['final_observation']: raise ValueError('final state mismatch')
        if row!=outcome['summary']: raise ValueError('result/outcome mismatch')
        verify_frontier(states[key],outcome['complete_frontier'])
        verify_frontier(initial,hydrate(path,read(path/'episodes'/row['episode_id']/'initial_frontier.json')))
        if F(row['information_cost'])!=costs[key] or F(row['information_cost'])>F(initial['budget']): raise ValueError('cost mismatch')
        if F(row['volume_ratio'])!=volume_ratio(initial,states[key]): raise ValueError('uncertainty volume mismatch')
        if F(row['volume_reduction'])!=1-F(row['volume_ratio']): raise ValueError('volume reduction mismatch')
        ev=evaluate(states[key],read(path/'episodes'/row['episode_id']/'private.json'),outcome['decision'])
        if ev!=row['evaluation']: raise ValueError('result evaluator mismatch')
        if row['service_model_valid'] and not ev['contract_valid']: raise ValueError('honest fixture violates contract')
        if ev['contract_valid']: valid_violations+=int(ev['bound_violation'])
        else: invalid_violations+=int(ev['bound_violation'])
        new_certified+=int(row['new_certified'])
    tasks=hydrate(path,read(path/'research_tasks.json')); c1,c2=tasks['counterexamples']
    A=[tuple(map(F,a)) for a in c1['p']]; B=[tuple(map(F,a)) for a in c1['p_prime']]
    x,z=tuple(map(F,c1['x'])),tuple(map(F,c1['z']))
    for i,(a,b) in enumerate(zip(A,B)):
        if sum((v-u)**2 for v,u in zip(a,b))>F(c1['radii'][i])**2: raise ValueError('translation outside uncertainty set')
        if sum((v-u)**2 for v,u in zip(a,x))!=sum((v-u)**2 for v,u in zip(b,z)): raise ValueError('translation range mismatch')
    if x==z or verify_margin(c1['certificate'])<=0: raise ValueError('translation counterexample prerequisite')
    for actual,nominal,radius in zip(c2['actual_anchors'],c2['nominal']['anchors'],c2['nominal']['radii']):
        if sum((F(a)-F(b))**2 for a,b in zip(actual,nominal))>F(radius)**2: raise ValueError('collapsed anchor outside ball')
        if sum((F(a)-F(b))**2 for a,b in zip(actual,c2['x']))!=sum((F(a)-F(b))**2 for a,b in zip(actual,c2['z'])): raise ValueError('reflection range mismatch')
    if valid_violations: raise ValueError('in-contract bound violation')
    return dict(passed=True,previous_files_unchanged=frozen,certificates_verified=certs,
        history_events=events,method_episodes=len(results),outputs=outputs,recovery_certificates_verified=verified,
        newly_certified_outputs=new_certified,in_contract_bound_violations=valid_violations,
        out_of_contract_bound_violations=invalid_violations,counterexamples_verified=2,
        scope='exact mathematical consumer plus frozen simulator replay; physical issuer honesty remains conditional')


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--run',default='v3b/runs/assumption-frontier-001'); args=p.parse_args()
    print(audit(ROOT/args.run))
