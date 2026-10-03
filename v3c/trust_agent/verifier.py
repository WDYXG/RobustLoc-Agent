"""Independent conditional cover and continuous-world witness consumer."""
from fractions import Fraction as F
from itertools import combinations
from v3b.assumption_agent.verifier import root,verify_margin,residual


def _inside(a,p): return sum((F(x)-F(y))**2 for x,y in zip(a['centre'],p))<=F(a['radius'])**2


def feasible_world(obs,w):
    x=list(map(F,w['target'])); d=list(map(F,obs['domain'])); p=w['positions']
    if not(d[0]<=x[0]<=d[1] and d[2]<=x[1]<=d[3]): return False
    if any(not _inside(a,p[a['anchor']]) for a in obs['hard_refs']): return False
    failed=set()
    for report in obs['reports']:
        if any(not _inside(a,p[a['anchor']]) for a in report['points']): failed.add(obs['failure_groups'][report['issuer']])
    if len(failed)>obs['r']: return False
    for bb in obs['baselines']:
        if sum((F(a)-F(b))**2 for a,b in zip(p[bb['a']],p[bb['b']]))!=F(bb['distance2']): return False
    values=[]
    for m in obs['measurements']:
        lo,hi=root(sum((F(v)-u)**2 for v,u in zip(p[m['anchor']],x))); y=F(m['value'])
        values.append(F(m['weight'])*max(abs(lo-y),abs(hi-y))**2)
    return sum(sorted(values)[:max(0,len(values)-obs['q'])])<=F(obs['epsilon'])**2


def verify_witness(obs,witness):
    A,B=witness['worlds']
    if not feasible_world(obs,A) or not feasible_world(obs,B): raise ValueError('inadmissible world witness')
    d2=sum((F(x)-F(y))**2 for x,y in zip(A['target'],B['target']))
    if not d2: raise ValueError('targets identical')
    # Structural sparse equality is about noiseless maps after support union, not estimator residuals.
    differences=0
    for m in obs['measurements']:
        r2=lambda W:sum((F(a)-F(b))**2 for a,b in zip(W['target'],W['positions'][m['anchor']]))
        differences+=int(r2(A)!=r2(B))
    if differences>2*obs['q']: raise ValueError('not a sparse zero-noise indistinguishability witness')
    lo,hi=root(d2)
    if F(witness['diameter_lower'])!=lo or F(witness['minimax_radius_lower'])!=lo/2: raise ValueError('diameter arithmetic')
    return lo/2


def verify_cover(obs,cert):
    if any(a['root'] not in obs['external_roots'] for a in obs['hard_refs']): raise ValueError('unknown external root')
    G=sorted({obs['failure_groups'][r['issuer']] for r in obs['reports']}); h=min(obs['r'],len(G))
    expected=[list(H) for H in combinations(G,h)]
    if [r['removed'] for r in cert['branches']]!=expected: raise ValueError('incomplete source deletion union')
    alive=[]
    for row in cert['branches']:
        assertions=list(obs['hard_refs'])
        for rr in obs['reports']:
            if obs['failure_groups'][rr['issuer']] not in row['removed']: assertions+=rr['points']
        if row['status']=='proved-empty':
            a,b=row['disjoint']
            if a not in assertions or b not in assertions or a['anchor']!=b['anchor']: raise ValueError('empty-branch claim binding')
            if sum((F(x)-F(y))**2 for x,y in zip(a['centre'],b['centre']))<=(F(a['radius'])+F(b['radius']))**2:
                raise ValueError('branch not proved empty')
            continue
        if row['status']!='covered': raise ValueError('unresolved branch cannot authorize recovery')
        selected=row['selected']
        if any(a not in assertions or a['anchor']!=i for i,a in selected.items()): raise ValueError('untrusted selected assertion')
        usable=[(i,m) for i,m in enumerate(obs['measurements']) if m['anchor'] in selected]
        if row['measurement_indices']!=[i for i,m in usable]: raise ValueError('measurement selection')
        expected_model=dict(anchors=[selected[m['anchor']]['centre'] for i,m in usable],
            radii=[selected[m['anchor']]['radius'] for i,m in usable],weights=[m['weight'] for i,m in usable],
            measurements=[m['value'] for i,m in usable],domain=obs['domain'],q_max=obs['q'],
            epsilon_max=obs['epsilon'],error_tolerance=obs['tolerance'])
        if expected_model!=row['model']: raise ValueError('branch model not bound to observation')
        c=row['certificate']; data={k:expected_model[k] for k in ('anchors','weights','domain','radii')}
        if c['data']!=data or c['q']!=obs['q']: raise ValueError('geometry binding')
        b=verify_margin(c); n=len(usable)
        zz=root(sum(sorted((F(w)*F(d)**2 for w,d in zip(data['weights'],data['radii'])),reverse=True)[:max(0,n-obs['q'])]))[1]
        u=residual(expected_model,row['centre'],obs['q'])
        if not b or u is None or u>F(obs['epsilon'])+zz: raise ValueError('candidate feasibility')
        B=(F(obs['epsilon'])+u+zz)/b
        if F(row['radius'])!=B or F(row['residual_upper'])!=u or F(row['zeta'])!=zz: raise ValueError('branch radius arithmetic')
        alive.append(row)
    if not alive: raise ValueError('empty union is not a physical recovery output')
    gap=lambda a,b:root(sum((F(x)-F(y))**2 for x,y in zip(a,b)))[1]
    U=max(gap(cert['position'],a['centre'])+F(a['radius']) for a in alive)
    diam=max(gap(a['centre'],b['centre'])+F(a['radius'])+F(b['radius']) for a in alive for b in alive)
    if F(cert['radius_upper'])!=U or F(cert['diameter_upper'])!=diam or U>F(obs['tolerance']): raise ValueError('union cover arithmetic/gate')
    return U
