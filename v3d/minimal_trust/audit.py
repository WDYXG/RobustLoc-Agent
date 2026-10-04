"""Separate mathematical consumers, physical replies and immutable histories."""
from pathlib import Path
from fractions import Fraction as F
import json
from v3b.assumption_agent.storage import read,hydrate,hash_value
from v3b.assumption_agent.verifier import verify_margin
from v3c.trust_agent.actions import apply
from v3c.trust_agent.verifier import feasible_world
from .freeze import ROOT,sources,check,digest
from .finite_verify import verify,response_key
from .worlds import validate_restriction,response
from .subset_verify import verify_uniform_upper,verify_subset_cover
from .analytic import verify_completeness


def check_interval(v,L,U,B):
    if L is None:
        if U is not None or v['cost_upper'] is not None or not v['lower_infinite'] or v['state']!='provably-insufficient-information-budget': raise ValueError('infinite lower diagnosis')
        return
    lo=F(L); hi=F(U) if U is not None else None; budget=F(B)
    if hi is not None and hi<lo: raise ValueError('reversed bounds')
    expected='provably-insufficient-information-budget' if lo>budget else ('certifiably-recoverable' if hi is not None and hi<=budget else 'unresolved-certificate-or-search-gap')
    if v['cost_lower']!=str(lo) or v['cost_upper']!=(str(hi) if hi is not None else None) or v['state']!=expected or v['lower_infinite']:
        raise ValueError('interval/epistemic state')
    gap=str(hi-lo) if hi is not None else None
    relative=str((hi-lo)/hi) if hi else ('0' if hi==0 else None)
    if v['gap']!=gap or v['relative_gap']!=relative: raise ValueError('optimality gap arithmetic')


def audit(path):
    path=Path(path); manifest=read(path/'manifest.json')
    if manifest['sources']!=sources(): raise ValueError('source freeze mismatch')
    previous=check()
    if (path/'output_hashes.json').exists():
        for name,h in read(path/'output_hashes.json')['files'].items():
            if digest(path/name)!=h: raise ValueError('output hash '+name)
    certificates=0
    for p in (path/'certificates').glob('*.json'):
        c=read(p)
        if hash_value(c)!=p.stem: raise ValueError('certificate id')
        verify_margin(c); certificates+=1
    finite_count=finite_closed=infinite_lower=continuous_count=outputs=repairs=analytic_count=0
    finite_artifacts={}; continuous_artifacts={}
    for p in sorted((path/'finite').glob('*.json')):
        a=hydrate(path,read(p)); finite_artifacts[p.stem]=a
        validate_restriction(a['observation'],a['model']); f=a['decision']['finite']; verify(a['model'],f)
        check_interval(a['decision']['interval'],f['adaptive_cost'],f['adaptive_cost'],a['budget'])
        finite_count+=1; finite_closed+=f['adaptive_cost'] is not None; infinite_lower+=f['adaptive_cost'] is None
        if f['adaptive_cost'] is not None:
            if {o['world'] for o in a['outcomes']}!={w['id'] for w in a['model']['worlds']}: raise ValueError('tree worlds not executed')
            if max(F(o['cost']) for o in a['outcomes'])!=F(f['adaptive_cost']): raise ValueError('executed worst cost')
    for p in sorted((path/'continuous').glob('*.json')):
        a=hydrate(path,read(p)); continuous_artifacts[p.stem]=a; obs=a['observation']; d=a['decision']
        validate_restriction(obs,d['finite_witness_model']); verify(d['finite_witness_model'],d['finite_restriction'])
        if d['upper']['cost_upper'] is not None: verify_uniform_upper(obs,d['upper'])
        check_interval(d['interval'],d['finite_restriction']['adaptive_cost'],d['upper']['cost_upper'],a['budget'])
        if F(a['spent'])>F(a['budget']): raise ValueError('spent budget')
        private=a['private']; world=dict(target=private['target'],positions=private['positions'])
        if not feasible_world(a['final_observation'],world): raise ValueError('actual world outside contract')
        if a['actual'] and a['actual']['certificate']['certified']:
            c=a['actual']['certificate']; radius=verify_subset_cover(a['final_observation'],c)
            error2=sum((F(x)-F(y))**2 for x,y in zip(c['position'],private['target']))
            if error2>radius**2 or a['actual']['error2']!=str(error2): raise ValueError('actual recovery error')
            outputs+=1; repairs+=a['actual']['automatic_old_miss_repaired']
        continuous_count+=1
    for p in sorted((path/'analytic').glob('*.json')):
        a=hydrate(path,read(p)); finite_artifacts[p.stem]=a
        verify_completeness(a['observation'],a['model'],a['completeness_certificate'])
        f=a['decision']['finite']; verify(a['model'],f)
        check_interval(a['decision']['interval'],f['adaptive_cost'],f['adaptive_cost'],a['budget'])
        if {o['world'] for o in a['outcomes']}!={w['id'] for w in a['model']['worlds']}: raise ValueError('analytic worlds not executed')
        analytic_count+=1
    states={}; costs={}; paths={}; last='0'*64; events=0
    for line in (path/'history.jsonl').read_text(encoding='utf-8').splitlines():
        row=json.loads(line); h=row.pop('hash')
        if row['index']!=events or row['previous_hash']!=last or hash_value(row)!=h: raise ValueError('history chain')
        events+=1; last=h; ev=hydrate(path,row['payload'])
        case=ev['case']; mode=ev['mode']; wid=ev.get('world'); key=(mode,case,wid)
        a=finite_artifacts[case] if mode=='finite' else continuous_artifacts[case]
        states.setdefault(key,a['observation'])
        costs.setdefault(key,F(0)); paths.setdefault(key,[])
        if states[key]!=ev['before'] or ev['offer'] not in states[key]['offers']: raise ValueError('history state')
        if mode=='finite':
            world=next(w for w in a['model']['worlds'] if w['id']==wid)
            if ev['reply']!=response(ev['before'],ev['offer'],world): raise ValueError('finite actual reply')
        after=apply(ev['before'],ev['offer'],ev['reply'])
        if after!=ev['after']: raise ValueError('service replay')
        states[key]=after
        costs[key]+=F(ev['offer']['cost']); paths[key].append(ev['offer']['id'])
    completion=read(path/'completion.json')
    if completion!={'events':events,'last_hash':last}: raise ValueError('completion binding')
    for name,a in continuous_artifacts.items():
        if states.get(('continuous',name,None),a['observation'])!=a['final_observation']: raise ValueError('continuous final replay')
        if costs.get(('continuous',name,None),F(0))!=F(a['spent']): raise ValueError('continuous paid cost')
    for name,a in finite_artifacts.items():
        for outcome in a['outcomes']:
            wid=outcome['world']; k=('finite',name,wid); world=next(w for w in a['model']['worlds'] if w['id']==wid)
            if paths.get(k,[])!=outcome['actions'] or costs.get(k,F(0))!=F(outcome['cost']): raise ValueError('finite execution cost/path')
            node=a['decision']['finite']['optimal_tree']; state=a['observation']
            for oid in outcome['actions']:
                if node['terminal'] or node['action']!=oid: raise ValueError('executed policy differs from verified tree')
                o=next(o for o in state['offers'] if o['id']==oid); reply=response(state,o,world)
                node=node['children'][response_key(reply)]; state=apply(state,o,reply)
            if not node['terminal'] or node['circle']!=outcome['circle'] or node['worlds']!=outcome['terminal_worlds']: raise ValueError('terminal finite state')
            err=sum((F(x)-F(y))**2 for x,y in zip(outcome['circle']['centre'],world['target']))
            if str(err)!=outcome['error2'] or err>F(a['observation']['tolerance'])**2: raise ValueError('finite output error')
    return dict(passed=True,previous_files_unchanged=previous,finite_cases=finite_count,finite_optima_closed=finite_closed,
        finite_impossibility_cases=infinite_lower,continuous_cases_including_development=continuous_count,
        continuous_nonzero_exact_optima=analytic_count,
        continuous_outputs=outputs,automatic_old_miss_repairs_including_development=repairs,
        geometric_certificates=certificates,history_events=events,
        scope='independent Helly/Bellman/tree and continuous-bound consumers; analytic tangency completeness checked separately; physical responses and histories checked; generic finite-prior completeness and root truth remain external')


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(); p.add_argument('--run',default='v3d/runs/minimal-trust-001'); a=p.parse_args(); print(audit(ROOT/a.run))
