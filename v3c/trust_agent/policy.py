"""Finite cheapest sufficient trust bundles; no physical truth access."""
from fractions import Fraction as F
from itertools import combinations
from copy import deepcopy
from functools import lru_cache
import json
import random
from .core import basis,recover,validate
from .actions import payload,apply
from .witnesses import find
from .verifier import verify_cover,verify_witness


def sufficient_forecast(s):
    geometry=deepcopy(s)
    for m in geometry['measurements']: m['value']='0'
    b=basis(geometry); alive=[r for r in b['branches'] if r['status']!='proved-empty']
    # Equal branch outer models yield one common candidate target and bound.
    same=bool(alive and all(r['model']==alive[0]['model'] for r in alive))
    return dict(safe=bool(b['pre_certified'] and same),empty=b['all_branches_empty'],
                bound=b['pre_bound'],branches=len(b['branches']),alive=len(alive),common_outer_model=same)


@lru_cache(maxsize=3000)
def _frontier(serialized):
    obs=json.loads(serialized); affordable=[o for o in obs['offers'] if F(o['cost'])<=F(obs['budget'])]; rows=[]
    for n in range(len(affordable)+1):
        for bundle in combinations(affordable,n):
            cost=sum(F(o['cost']) for o in bundle)
            if cost>F(obs['budget']): continue
            responses=[]
            for frame in obs['forecast_frames']:
                s=obs
                try:
                    for o in bundle: s=apply(s,o,payload(s,o,frame))
                    result=sufficient_forecast(s)
                except ValueError: result=dict(safe=False,empty=False,bound=None,reason='invalid-forecast-reply')
                responses.append(result)
            admissible=[r for r in responses if not r['empty']]
            certified=bool(admissible and all(r['safe'] for r in admissible))
            rows.append(dict(ids=[o['id'] for o in bundle],cost=str(cost),certified=certified,
                forecast_results=responses,excluded_proved_empty_forecasts=len(responses)-len(admissible)))
    successes=[r for r in rows if r['certified']]
    best=min(successes,key=lambda r:(F(r['cost']),len(r['ids']),tuple(r['ids']))) if successes else None
    return dict(rows=rows,minimum_sufficient_bundle=best,
        scope='exact finite bundle cost minimum for this sufficient common-model pre-gate and declared finite forecasts; not a continuous optimal trust theorem')


def trust_frontier(obs):
    return deepcopy(_frontier(json.dumps(obs,sort_keys=True)))


def choose(obs,method,cfg,seed):
    validate(obs); c=recover(obs,cfg)
    if c.get('certified'):
        verify_cover(obs,c)
        return dict(action='recover',diagnosis='certified-at-required-resolution',certificate=c,
                    position=c['position'],radius_upper=c['radius_upper'])
    witness=find(obs,cfg)
    b=basis(obs)
    if b['all_branches_empty']:
        return dict(action='abstain',diagnosis='inconsistent-declared-premises',reason='all-source-branches-proved-empty',
                    current_basis=b,scope='contradiction of declared assumptions, not identification of the liar')
    if witness:
        verify_witness(obs,witness); diagnosis='structural-ambiguity-at-required-resolution'
    else:
        alive=[r for r in b['branches'] if r['status']!='proved-empty']
        common=bool(alive and all(r['model']==alive[0]['model'] for r in alive))
        if common and all(r.get('lower') and F(r['lower'])>0 and all(F(v)==0 for v in r['model']['radii']) for r in alive):
            diagnosis='precision-or-certificate-gap'
        else: diagnosis='unresolved-trust-or-geometry-gap'
    offers=[o for o in obs['offers'] if F(o['cost'])<=F(obs['budget'])]
    output=dict(diagnosis=diagnosis,witness=witness,current_basis=b,
                scope='diagnosis requires positive certificate or exact witness; no zero-lower impossibility claim')
    if not offers: return dict(output,action='abstain',reason='no-affordable-certificate-capable-information')
    if method=='range-only':
        ordinary=[o for o in offers if o['kind']=='ordinary-range']
        if not ordinary: return dict(output,action='abstain',reason='ordinary-only-menu-exhausted')
        offer=ordinary[0]; frontier=None
    elif method=='random-information': offer=random.Random(seed).choice(offers); frontier=None
    elif method=='trust-directed':
        frontier=trust_frontier(obs); best=frontier['minimum_sufficient_bundle']
        if best is None or not best['ids']:
            return dict(output,action='abstain',reason='no-sufficient-bundle-in-finite-forecast-menu',frontier=frontier)
        # Min-cost whole bundle; execute once and recompute after physical response.
        ids=best['ids']
        if witness:
            trust=[i for i in ids if next(o for o in offers if o['id']==i)['kind'] in ('absolute-reference','independent-source')]
            if trust: ids=trust+ids
        offer=next(o for o in offers if o['id']==ids[0])
    else: raise ValueError('unknown method')
    return dict(output,action='acquire-information',offer_id=offer['id'],kind=offer['kind'],cost=offer['cost'],
                frontier=frontier)
