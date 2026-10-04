"""Consumer binds arbitrary coordinate subsets to the original transcript."""
from fractions import Fraction as F
from itertools import combinations
from v3b.assumption_agent.verifier import root,verify_margin,residual


def check_obs(obs):
    if type(obs['q']) is not int or obs['q']<0 or type(obs['r']) is not int or obs['r']<0: raise ValueError('budgets')
    if F(obs['epsilon'])<0 or F(obs['tolerance'])<=0: raise ValueError('noise/tolerance')
    if any(a['root'] not in obs['external_roots'] or F(a['radius'])<0 for a in obs['hard_refs']): raise ValueError('external root/radius')
    if any(F(m['weight'])<=0 for m in obs['measurements']): raise ValueError('weights')


def subset_model(obs,refs,indices,assertions):
    if not indices or len(set(indices))!=len(indices) or sorted(indices)!=indices: raise ValueError('duplicate/unordered range coordinates')
    if any(type(i) is not int or i<0 or i>=len(obs['measurements']) for i in indices): raise ValueError('coordinate binding')
    if any(a not in assertions or a['anchor']!=i or F(a['radius'])<0 for i,a in refs.items()): raise ValueError('untrusted reference')
    mm=[obs['measurements'][i] for i in indices]
    if any(m['anchor'] not in refs for m in mm): raise ValueError('unsupported measured anchor')
    return dict(anchors=[refs[m['anchor']]['centre'] for m in mm],radii=[refs[m['anchor']]['radius'] for m in mm],
        weights=[m['weight'] for m in mm],measurements=[m['value'] for m in mm],domain=obs['domain'],
        q_max=obs['q'],epsilon_max=obs['epsilon'],error_tolerance=obs['tolerance'])


def inflation(weights,radii,q):
    return root(sum(sorted([F(w)*F(r)**2 for w,r in zip(weights,radii)],reverse=True)[:max(0,len(weights)-q)]))[1]


def verify_subset_cover(obs,cert):
    check_obs(obs)
    G=sorted({obs['failure_groups'][r['issuer']] for r in obs['reports']}); h=min(obs['r'],len(G))
    if [r['removed'] for r in cert['branches']]!=[list(H) for H in combinations(G,h)]: raise ValueError('incomplete source union')
    alive=[]
    for r in cert['branches']:
        assertions=list(obs['hard_refs'])
        for report in obs['reports']:
            if obs['failure_groups'][report['issuer']] not in r['removed']: assertions+=report['points']
        if r['status']=='proved-empty':
            a,b=r['disjoint']
            if a not in assertions or b not in assertions or a['anchor']!=b['anchor']: raise ValueError('empty proof binding')
            if sum((F(x)-F(y))**2 for x,y in zip(a['centre'],b['centre']))<=(F(a['radius'])+F(b['radius']))**2: raise ValueError('false empty branch')
            continue
        if r['status']!='covered': raise ValueError('unresolved source branch')
        model=subset_model(obs,r['selected'],r['measurement_indices'],assertions)
        if model!=r['model']: raise ValueError('model binding')
        data={k:model[k] for k in ('anchors','radii','weights','domain')}; c=r['certificate']
        if c['data']!=data or c['q']!=obs['q']: raise ValueError('geometry binding')
        b=verify_margin(c); zz=inflation(model['weights'],model['radii'],obs['q']); u=residual(model,r['centre'],obs['q'])
        if not b or u is None or u>F(obs['epsilon'])+zz: raise ValueError('candidate feasibility')
        radius=(F(obs['epsilon'])+u+zz)/b
        if F(r['radius'])!=radius or F(r['zeta'])!=zz or F(r['residual_upper'])!=u: raise ValueError('radius arithmetic')
        alive.append(r)
    if not alive: raise ValueError('empty model does not authorize recovery')
    gap=lambda a,b:root(sum((F(x)-F(y))**2 for x,y in zip(a,b)))[1]
    U=max(gap(cert['position'],r['centre'])+F(r['radius']) for r in alive)
    D=max(gap(a['centre'],b['centre'])+F(a['radius'])+F(b['radius']) for a in alive for b in alive)
    if U!=F(cert['radius_upper']) or D!=F(cert['diameter_upper']) or U>F(obs['tolerance']): raise ValueError('unsafe union cover')
    return U


def verify_uniform_upper(obs,c):
    check_obs(obs)
    if obs['reports'] or c['cost_upper'] is None: raise ValueError('unsupported uniform upper')
    ids=c['offers']
    if len(ids)!=len(set(ids)): raise ValueError('duplicate purchase')
    offered={o['id']:o for o in obs['offers']}
    O=[offered[i] for i in ids]
    if any(o['kind']!='absolute-reference' or F(o['radius'])!=0 or o['root'] not in obs['external_roots'] or F(o['cost'])<=0 for o in O): raise ValueError('action contract')
    cost=sum((F(o['cost']) for o in O),F(0))
    if cost!=F(c['cost_upper']): raise ValueError('purchase cost')
    m=subset_model(obs,c['initial_refs'],c['measurement_indices'],obs['hard_refs'])
    data={k:m[k] for k in ('anchors','radii','weights','domain')}; geometry=c['initial_geometry_certificate']
    if geometry['data']!=data or geometry['q']!=obs['q']: raise ValueError('initial uncertainty geometry binding')
    b=verify_margin(geometry); purchased={i for o in O for i in o['anchors']}
    remaining=['0' if obs['measurements'][i]['anchor'] in purchased else m['radii'][j] for j,i in enumerate(c['measurement_indices'])]
    zz=inflation(m['weights'],remaining,obs['q'])
    if not b: raise ValueError('zero uniform margin')
    bound=2*(F(obs['epsilon'])+zz)/b
    if remaining!=c['remaining_radii'] or F(c['zeta_upper'])!=zz or F(c['radius_upper'])!=bound or bound>F(obs['tolerance']): raise ValueError('uniform bound arithmetic')
    return cost
