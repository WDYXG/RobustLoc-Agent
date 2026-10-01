"""Explicit recover/abstain/acquire policy with finite certificate lookahead."""
from copy import deepcopy
from fractions import Fraction as F
from itertools import combinations
from .certificates import data_from,geometry,profile,features,residual_certificate
from .decoder import solve,FORBIDDEN

def acquire_data(obs,p):
    data=deepcopy(data_from(obs)); data['anchors'].append(p); data['weights'].append('1')
    return data

def plan(obs,cfg,mode='active-certified'):
    q=obs['q_budget']; data=data_from(obs); current=F(geometry(data,q)['lower'])
    tau=2*F(obs['epsilon'])/F(obs['error_tolerance'])
    offers=[p for p in obs['available_anchors'] if p not in obs['anchors']]
    remaining=obs['acquisitions_remaining']
    if not offers or remaining<=0: return None
    if mode=='random-certified':
        return dict(anchor=offers[obs['random_choice_index']%len(offers)],projected_lower=None,
                    plan=[],criterion='seeded random, no truth or future range')
    if mode=='greedy-certified':
        scores=[(F(geometry(acquire_data(obs,p),q)['lower']),p) for p in offers]
        best,p=max(scores,key=lambda row:row[0])
        return dict(anchor=p,projected_lower=str(best),plan=[p],criterion='positive immediate gain') if best>current else None
    horizon=min(cfg['horizon'],remaining,len(offers)); plans=[]
    for k in range(1,horizon+1):
        for combo in combinations(offers,k):
            extended=deepcopy(data)
            extended['anchors']+=list(combo); extended['weights']+=['1']*k
            lower=F(geometry(extended,q)['lower'])
            plans.append((lower,k,list(combo)))
    feasible=[r for r in plans if r[0]>=tau]
    if feasible:
        lower,k,selected=min(feasible,key=lambda r:(r[1],-r[0]))
    else: lower,k,selected=max(plans,key=lambda r:(r[0],-r[1]))
    if lower<=current: return None
    # Execute one acquisition, then observe/replan. Future measurements stay hidden.
    first=max(selected,key=lambda p:F(geometry(acquire_data(obs,p),q)['lower']))
    return dict(anchor=first,projected_lower=str(lower),plan=selected,
        criterion='fewest additions crossing threshold, then terminal certified lower',
        horizon=horizon,immediate_lower=geometry(acquire_data(obs,first),q)['lower'])

def decide(obs,cfg,mode='active-certified',model=None,candidate=None):
    if FORBIDDEN.intersection(obs): raise ValueError('Private evaluator fields forbidden in agent')
    if F(obs['epsilon'])<=0 or F(obs['error_tolerance'])<=0: raise ValueError('Positive budgets required')
    q=obs.get('q_budget')
    if q is not None and (not isinstance(q,int) or q<0 or q>=len(obs['anchors'])):
        raise ValueError('Invalid conditional corruption budget')
    diagnostic=features(obs); conditional=profile(obs,cfg['q_profile_max'])
    probability=None
    if model is not None:
        from .learning import predict
        probability=predict(model,diagnostic['values'])
    common=dict(conditional_profile=conditional,geometry_features=diagnostic,
        learned_probability_advisory=probability,q_budget=q,
        guarantee='conditional on true-domain, q and clean-noise assumptions')
    if q is None:
        return dict(common,action='abstain',reason='missing-declared-q-budget; estimated q cannot authorize recovery')
    g=geometry(data_from(obs),q); common['geometry']=g
    b=F(g['lower']); tau=F(conditional['threshold'])
    if mode=='learned-gate':
        candidate=candidate or solve(obs,cfg)
        candidate=deepcopy(candidate)
        candidate['feasibility']=residual_certificate(obs,candidate['position'],q)
        if probability is not None and probability>=cfg['learning_threshold'] and candidate['feasibility']['feasible']:
            return dict(common,action='recover',reason='uncertified learned-gate ablation',
                candidate=candidate,certified=False,error_bound=None)
        return dict(common,action='abstain',reason='learned gate or feasibility rejected',candidate=candidate)
    if b>=tau:
        candidate=candidate or solve(obs,cfg)
        candidate=deepcopy(candidate)
        candidate['feasibility']=residual_certificate(obs,candidate['position'],q)
        if candidate['feasibility']['feasible']:
            bound=2*F(obs['epsilon'])/b
            return dict(common,action='recover',reason='geometry and exact residual feasibility passed',
                        candidate=candidate,certified=True,error_bound=str(bound))
        common['candidate']=candidate; reason='no-feasible-candidate-found; search incomplete'
    elif F(g['upper'])<tau:
        reason='witness rules out requested uniform margin; candidate-specific recovery may still exist'
    else: reason='insufficient lower certificate; instability not proved'
    proposal=plan(obs,cfg,mode) if mode not in ('passive-certified',) else None
    if proposal:
        return dict(common,action='acquire-more-data',reason=reason,acquisition=proposal)
    return dict(common,action='abstain',reason=reason+'; no improving permitted plan/budget')
