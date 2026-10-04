"""Subset certificates and response-uniform purchase upper bounds."""
from copy import deepcopy
from fractions import Fraction as F
from itertools import combinations
from v3b.assumption_agent.certificates import build,zeta
from v3b.assumption_agent.verifier import verify_margin,residual,root
from v3.certified_agent.decoder import solve
from v3c.trust_agent.core import validate,groups,branch


def model_for(obs,selected,indices):
    mm=[obs['measurements'][i] for i in indices]
    return dict(anchors=[selected[m['anchor']]['centre'] for m in mm],
        radii=[selected[m['anchor']]['radius'] for m in mm],weights=[m['weight'] for m in mm],
        measurements=[m['value'] for m in mm],domain=obs['domain'],q_max=obs['q'],
        epsilon_max=obs['epsilon'],error_tolerance=obs['tolerance'])


def subsets(indices,q):
    for size in range(2*q+3,len(indices)+1): yield from combinations(indices,size)


def recover_subsets(obs,cfg,node_limit=None):
    validate(obs)
    if node_limit is not None and node_limit<0: raise ValueError('negative search limit')
    G=groups(obs); h=min(obs['r'],len(G)); rows=[]; nodes=0; complete=True; candidate_failures=0
    for H in combinations(G,h):
        initial=branch(obs,list(H))
        if initial['status']=='proved-empty': rows.append(initial); continue
        selected=initial['selected']; best=None
        for S in subsets(initial['measurement_indices'],obs['q']):
            if node_limit is not None and nodes>=node_limit: complete=False; break
            nodes+=1
            subset_refs={obs['measurements'][i]['anchor']:selected[obs['measurements'][i]['anchor']] for i in S}
            m=model_for(obs,subset_refs,S); data={k:m[k] for k in ('anchors','radii','weights','domain')}
            cert=build(data,obs['q']); b=verify_margin(cert)
            if not b: continue
            zz=zeta(m,obs['q']); solobs={k:m[k] for k in ('anchors','weights','measurements','domain')}
            solobs.update(q_budget=obs['q'],epsilon=str(F(obs['epsilon'])+zz),error_tolerance=obs['tolerance'])
            candidate=solve(solobs,cfg); u=residual(m,candidate['position'],obs['q'])
            if u is None or u>F(obs['epsilon'])+zz: candidate_failures+=1; continue
            radius=(F(obs['epsilon'])+u+zz)/b
            if best is None or radius<F(best['radius']):
                best=dict(removed=list(H),status='covered',selected=subset_refs,measurement_indices=list(S),
                    model=m,certificate=cert,lower=str(b),zeta=str(zz),centre=candidate['position'],
                    residual_upper=str(u),radius=str(radius))
        rows.append(best or dict(removed=list(H),status='unresolved',reason='subset-or-candidate-search-gap'))
    result=dict(certified=False,branches=rows,search=dict(subset_nodes=nodes,subset_enumeration_complete=complete,
        nonlinear_search_complete=False,candidate_failures=candidate_failures,node_limit=node_limit),
        scope='continuous conditional cover; numerical candidate search is incomplete; failure is not impossibility')
    alive=[r for r in rows if r['status']!='proved-empty']
    if not alive: return dict(result,reason='inconsistent-declared-premises')
    if any(r['status']!='covered' for r in alive): return result
    gap=lambda a,b:root(sum((F(x)-F(y))**2 for x,y in zip(a,b)))[1]
    # Best among branch centers; not the exact enclosing ball of the ball union.
    choices=[(max(gap(a['centre'],b['centre'])+F(b['radius']) for b in alive),a['centre']) for a in alive]
    U,c=min(choices,key=lambda p:(p[0],p[1]))
    diameter=max(gap(a['centre'],b['centre'])+F(a['radius'])+F(b['radius']) for a in alive for b in alive)
    result.update(position=c,radius_upper=str(U),diameter_upper=str(diameter),certified=U<=F(obs['tolerance']))
    return result


def uniform_upper(obs,node_limit=None):
    """Buy exact references; certify every reply allowed by the initial hard balls.

    All other actions remain in the physical menu but need not be used by this
    feasible policy. None means no proved UB found, never physical infinity.
    """
    validate(obs)
    if any(F(o['cost'])<=0 for o in obs['offers']): raise ValueError('positive query costs required')
    if node_limit is not None and node_limit<0: raise ValueError('negative search limit')
    if obs['reports']: return dict(cost_upper=None,reason='uniform-family-does-not-handle-soft-source-replies',search=dict(nodes=0,complete=False))
    selected={}
    for a in obs['hard_refs']:
        if a['anchor'] not in selected or F(a['radius'])<F(selected[a['anchor']]['radius']): selected[a['anchor']]=a
    usable=[i for i,m in enumerate(obs['measurements']) if m['anchor'] in selected]
    offers=[o for o in obs['offers'] if o['kind']=='absolute-reference' and F(o['radius'])==0 and o['root'] in obs['external_roots']]
    bundles=[(sum((F(o['cost']) for o in O),F(0)),tuple(o['id'] for o in O),O)
             for size in range(len(offers)+1) for O in combinations(offers,size)]
    bundles.sort(key=lambda z:(z[0],len(z[1]),z[1])); nodes=0; bundle_nodes=0
    for cost,ids,O in bundles:
        bundle_nodes+=1; purchased={i for o in O for i in o['anchors']}
        for S in subsets(usable,obs['q']):
            if node_limit is not None and nodes>=node_limit:
                return dict(cost_upper=None,reason='uniform-search-limit',search=dict(nodes=nodes,bundles=bundle_nodes,complete=False))
            nodes+=1; refs={obs['measurements'][i]['anchor']:selected[obs['measurements'][i]['anchor']] for i in S}
            m=model_for(obs,refs,S); data={k:m[k] for k in ('anchors','radii','weights','domain')}
            c=build(data,obs['q']); b=verify_margin(c)
            if not b: continue
            after=[('0' if obs['measurements'][i]['anchor'] in purchased else m['radii'][j]) for j,i in enumerate(S)]
            zz=zeta(dict(m,radii=after),obs['q']); B=2*(F(obs['epsilon'])+zz)/b
            if B<=F(obs['tolerance']):
                return dict(cost_upper=str(cost),offers=list(ids),measurement_indices=list(S),initial_refs=deepcopy(refs),
                    initial_geometry_certificate=c,remaining_radii=after,zeta_upper=str(zz),radius_upper=str(B),
                    search=dict(nodes=nodes,bundles=bundle_nodes,complete=True,
                        meaning='all cheaper offered exact-reference bundles exhausted for this sufficient family; equal-cost ties need not be exhausted'),
                    scope='continuous response-uniform nonadaptive policy UB; not a finite forecast or a lower bound on physical cost')
    return dict(cost_upper=None,reason='no-uniform-certificate-in-family',search=dict(nodes=nodes,bundles=bundle_nodes,complete=True))
