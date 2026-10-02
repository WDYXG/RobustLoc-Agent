"""Observation-only deterministic finite planning; no simulator imports."""
from copy import deepcopy
from fractions import Fraction as F
from itertools import permutations
from functools import lru_cache
import json
import random
from v3.certified_agent.decoder import solve
from .certificates import frontier,zeta
from .contracts import check_observation,preview
from .verifier import residual,verify_recovery


def quality(f,r):
    return F(0) if f['worst_error_bound'] is None else F(r)/(F(r)+F(f['worst_error_bound']))


@lru_cache(maxsize=20000)
def _profile(serialized):
    return frontier(json.loads(serialized),include_grid=False,complete=False)


def profile(obs):
    return deepcopy(_profile(json.dumps({k:obs[k] for k in ('anchors','weights','domain','radii','q_max','epsilon_max','error_tolerance')},sort_keys=True)))


def choose(obs,method,cfg,seed):
    check_observation(obs); f=profile(obs)
    if f['all_contracts_certified']:
        candidate_obs={k:deepcopy(obs[k]) for k in ('anchors','weights','domain','measurements')}
        candidate_obs.update(q_budget=obs['q_max'],epsilon=str(F(obs['epsilon_max'])+zeta(obs,obs['q_max'])),error_tolerance=obs['error_tolerance'])
        candidate=solve(candidate_obs,cfg)
        # A Q-sparse explanation works uniformly for every actual q<=Q.
        rows=[f['rows'][obs['q_max']]]; bounds=[]
        for row in rows:
            rr=residual(obs,candidate['position'],row['q']); z=F(row['zeta_upper'])
            if rr is None or rr>F(obs['epsilon_max'])+z: break
            bounds.append((F(obs['epsilon_max'])+rr+z)/F(row['lower']))
        if len(bounds)==len(rows):
            d=dict(action='recover',position=candidate['position'],error_bound=str(max(bounds)),frontier=f,
                   search_complete=False,optimizer_failures=candidate['optimizer_failures'])
            verify_recovery(obs,d); return d
        residual_failure='candidate-not-feasible-for-entire-assumption-set'
    else: residual_failure=None
    base=quality(f,obs['error_tolerance']); choices=[]; plans=[]
    offers=[o for o in obs['offers'] if F(o['cost'])<=F(obs['budget'])]
    for o in offers:
        ff=profile(preview(obs,o)); gain=quality(ff,obs['error_tolerance'])-base
        choices.append(dict(offer=o,gain=str(gain),gain_per_cost=str(gain/F(o['cost'])),
                            all_contracts_certified=ff['all_contracts_certified'],after_bound=ff['worst_error_bound']))
    if not offers: return dict(action='abstain',reason=residual_failure or 'no-affordable-credible-information',frontier=f,choices=choices)
    if method=='measurement-only':
        available=[c for c in choices if c['offer']['kind']=='new-range']
        if not available: return dict(action='abstain',reason='measurement-only-has-no-range-offer',frontier=f,choices=choices)
        selected=max(available,key=lambda c:F(c['gain_per_cost']))['offer']
    elif method=='random-information': selected=random.Random(seed).choice(offers)
    elif method=='one-step-gain': selected=max(choices,key=lambda c:F(c['gain_per_cost']))['offer']
    elif method=='multi-step':
        # All offers have deterministic public effects; enumerate ordered feasible plans.
        for length in range(1,min(cfg['horizon'],len(offers))+1):
            for plan in permutations(offers,length):
                state=obs
                try:
                    for o in plan: state=preview(state,o)
                except ValueError: continue
                ff=profile(state); cost=sum(F(o['cost']) for o in plan)
                gain=quality(ff,obs['error_tolerance'])-base
                plans.append(dict(ids=[o['id'] for o in plan],cost=str(cost),gain_per_cost=str(gain/cost),
                                  certified=ff['all_contracts_certified']))
        successful=[p for p in plans if p['certified']]
        if successful: best=min(successful,key=lambda p:(F(p['cost']),len(p['ids']),tuple(p['ids'])))
        else: best=max(plans,key=lambda p:(F(p['gain_per_cost']),-F(p['cost'])))
        selected=next(o for o in offers if o['id']==best['ids'][0])
    else: raise ValueError('unknown baseline')
    max_gain=max((F(c['gain_per_cost']) for c in choices),default=F(0))
    limiter=[c['offer']['kind'] for c in choices if F(c['gain_per_cost'])==max_gain and max_gain>0]
    return dict(action='acquire-more-data',offer_id=selected['id'],kind=selected['kind'],cost=selected['cost'],
                frontier=f,choices=choices,plan=best if method=='multi-step' else None,
                candidate_failure=residual_failure,limiting_premise_diagnostics=limiter,
                diagnostic_scope='finite offered marginal effects, not causal attribution')
