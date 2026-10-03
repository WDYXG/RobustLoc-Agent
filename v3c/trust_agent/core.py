"""Continuous source-deletion outer covers; only actual trust constraints count."""
from copy import deepcopy
from fractions import Fraction as F
from itertools import combinations
from functools import lru_cache
import json
from v3b.assumption_agent.certificates import build,zeta
from v3b.assumption_agent.verifier import verify_margin,residual,root
from v3.certified_agent.decoder import solve

PRIVATE={'truth','actual_anchors','private','actual_world','scenario','bad_indices','bad_groups'}


def validate(obs):
    if PRIVATE.intersection(obs): raise ValueError('private evaluator fields forbidden')
    for name in ('q','r'):
        if type(obs[name]) is not int or obs[name]<0: raise ValueError('external corruption budgets required')
    if F(obs['epsilon'])<0 or F(obs['tolerance'])<=0 or F(obs['budget'])<0: raise ValueError('invalid budget')
    d=list(map(F,obs['domain']))
    if len(d)!=4 or d[0]>=d[1] or d[2]>=d[3]: raise ValueError('domain')
    for m in obs['measurements']:
        if m['anchor'] not in obs['nominal'] or F(m['weight'])<=0: raise ValueError('measurement binding')
        F(m['value'])
    for report in obs['reports']:
        if report['issuer'] not in obs['failure_groups']: raise ValueError('unregistered premise source')
    for a in obs['hard_refs']:
        if a['root'] not in obs['external_roots']: raise ValueError('unknown trust root')


def groups(obs):
    return sorted({obs['failure_groups'][r['issuer']] for r in obs['reports']})


def retained(obs,removed):
    assertions=deepcopy(obs['hard_refs'])
    for report in obs['reports']:
        if obs['failure_groups'][report['issuer']] not in removed:
            assertions+=deepcopy(report['points'])
    return assertions


def branch(obs,removed):
    assertions=retained(obs,removed); by={}
    for a in assertions:
        if a['anchor'] not in obs['nominal'] or F(a['radius'])<0: raise ValueError('anchor assertion')
        by.setdefault(a['anchor'],[]).append(a)
    for values in by.values():
        for a,b in combinations(values,2):
            d2=sum((F(x)-F(y))**2 for x,y in zip(a['centre'],b['centre']))
            if d2>(F(a['radius'])+F(b['radius']))**2:
                return dict(removed=removed,status='proved-empty',disjoint=[a,b])
    selected={i:min(a,key=lambda row:F(row['radius'])) for i,a in by.items()}
    usable=[(i,m) for i,m in enumerate(obs['measurements']) if m['anchor'] in selected]
    model=dict(anchors=[selected[m['anchor']]['centre'] for i,m in usable],
        radii=[selected[m['anchor']]['radius'] for i,m in usable],weights=[m['weight'] for i,m in usable],
        measurements=[m['value'] for i,m in usable],domain=obs['domain'],q_max=obs['q'],
        epsilon_max=obs['epsilon'],error_tolerance=obs['tolerance'])
    result=dict(removed=removed,status='unresolved',selected=selected,measurement_indices=[i for i,m in usable],model=model)
    if not usable: return dict(result,reason='no-measured-trusted-reference')
    c=build({k:model[k] for k in ('anchors','weights','domain','radii')},obs['q']); b=verify_margin(c)
    zz=zeta(model,obs['q'])
    return dict(result,certificate=c,lower=str(b),zeta=str(zz),
        pre_bound=str(2*(F(obs['epsilon'])+zz)/b) if b else None,
        reason='zero-sufficient-margin' if not b else 'candidate-not-yet-checked')


@lru_cache(maxsize=12000)
def _basis(serialized):
    obs=json.loads(serialized); G=groups(obs); h=min(obs['r'],len(G))
    rows=[branch(obs,list(H)) for H in combinations(G,h)]
    alive=[a for a in rows if a['status']!='proved-empty']
    worst=max(F(a['pre_bound']) for a in alive) if alive and all(a.get('pre_bound') is not None for a in alive) else None
    return dict(branches=rows,group_ids=G,discarded_count=h,
        pre_bound=str(worst) if worst is not None else None,
        pre_certified=bool(worst is not None and worst<=F(obs['tolerance'])),
        all_branches_empty=not alive,scope='continuous feasible-world outer cover; explicit external trust roots and q/r assumptions')


def basis(obs):
    validate(obs)
    keys=('nominal','measurements','hard_refs','reports','failure_groups','external_roots','q','r','epsilon','tolerance','domain')
    return deepcopy(_basis(json.dumps({k:obs[k] for k in keys},sort_keys=True)))


def recover(obs,cfg):
    result=basis(obs); alive=[]
    if not result['pre_certified']: return result
    for row in result['branches']:
        if row['status']=='proved-empty': continue
        m=row['model']; zz=F(row['zeta']); b=F(row['lower'])
        solobs={k:m[k] for k in ('anchors','weights','measurements','domain')}
        solobs.update(q_budget=obs['q'],epsilon=str(F(obs['epsilon'])+zz),error_tolerance=obs['tolerance'])
        candidate=solve(solobs,cfg); u=residual(m,candidate['position'],obs['q'])
        if u is None or u>F(obs['epsilon'])+zz:
            row.update(status='unresolved',reason='incomplete-candidate-search',optimizer_failures=candidate['optimizer_failures']); continue
        B=(F(obs['epsilon'])+u+zz)/b
        row.update(status='covered',centre=candidate['position'],residual_upper=str(u),radius=str(B))
        alive.append(row)
    if any(row['status']=='unresolved' for row in result['branches']): return result
    if not alive: return result
    # Any chosen point is valid if every branch cover is enclosed. No minimax optimizer claim.
    a=alive[0]['centre']; gap=lambda c,d:root(sum((F(x)-F(y))**2 for x,y in zip(c,d)))[1]
    U=max(gap(a,row['centre'])+F(row['radius']) for row in alive)
    diameter=max(gap(x['centre'],y['centre'])+F(x['radius'])+F(y['radius']) for x in alive for y in alive)
    result.update(position=a,radius_upper=str(U),diameter_upper=str(diameter),
                  certified=U<=F(obs['tolerance']))
    return result
