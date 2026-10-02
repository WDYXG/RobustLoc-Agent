"""Nested assumption updates. Provenance checks are conditional on honest issuers."""
from copy import deepcopy
from fractions import Fraction as F
from .certificates import validate

ISSUERS={'new-range':'simulated-range-service','anchor-recalibration':'simulated-independent-calibrator',
         'tighter-domain':'simulated-independent-prior','stronger-q-bound':'simulated-support-audit'}
FORBIDDEN={'truth','actual_anchors','bad_indices','actual_q','noise','private','scenario','contract_valid'}


def check_observation(obs):
    if FORBIDDEN.intersection(obs): raise ValueError('private fields in policy input')
    validate(obs)
    if len(obs['measurements'])!=len(obs['anchors']): raise ValueError('measurement count')
    if type(obs['q_max']) is not int or obs['q_max']<0: raise ValueError('q upper set missing')
    if F(obs['epsilon_max'])<=0 or F(obs['error_tolerance'])<=0: raise ValueError('positive budgets required')
    if F(obs['budget'])<0: raise ValueError('negative info budget')
    if len({o['id'] for o in obs['offers']})!=len(obs['offers']): raise ValueError('duplicate offer')
    for o in obs['offers']:
        if o['kind'] not in ISSUERS or F(o['cost'])<=0: raise ValueError('invalid offer')


def preview(obs,offer):
    s=deepcopy(obs); u=offer['update']; kind=offer['kind']
    if kind=='new-range':
        s['anchors'].append(u['anchor']); s['weights'].append(u['weight'])
        s['radii'].append(u['radius']); s['measurements'].append('0')
    elif kind=='anchor-recalibration':
        for i in u['indices']:
            if not 0<=i<len(s['radii']) or F(u['radius'])>F(s['radii'][i]): raise ValueError('non-nested anchor ball')
            s['radii'][i]=u['radius']
    elif kind=='tighter-domain':
        old=list(map(F,s['domain'])); new=list(map(F,u['domain']))
        if not(old[0]<=new[0]<new[1]<=old[1] and old[2]<=new[2]<new[3]<=old[3]): raise ValueError('non-nested domain')
        s['domain']=u['domain']
    elif kind=='stronger-q-bound':
        if type(u['q_max']) is not int or not 0<=u['q_max']<=s['q_max']: raise ValueError('non-nested q set')
        s['q_max']=u['q_max']
    s['offers']=[v for v in s['offers'] if v['id']!=offer['id']]
    s['budget']=str(F(s['budget'])-F(offer['cost']))
    if F(s['budget'])<0: raise ValueError('budget exhausted')
    check_observation(s)
    return s


def deliver(obs,offer,receipt):
    if (receipt.get('issuer')!=ISSUERS[offer['kind']] or receipt.get('offer_id')!=offer['id']
        or receipt.get('update')!=offer['update'] or receipt.get('episode_id')!=obs['episode_id']):
        raise ValueError('receipt source, binding or advertised contract mismatch')
    s=preview(obs,offer)
    if offer['kind']=='new-range':
        if not isinstance(receipt.get('measurement'),str): raise ValueError('missing measured range')
        F(receipt['measurement']); s['measurements'][-1]=receipt['measurement']
    s['receipts'].append(deepcopy(receipt)); return s


def volume_ratio(initial,current):
    # Common original dimensions; new measurements change constraints, not this measure.
    area=lambda d:(F(d[1])-F(d[0]))*(F(d[3])-F(d[2]))
    v=F(current['q_max']+1,initial['q_max']+1)*F(current['epsilon_max'])/F(initial['epsilon_max'])*area(current['domain'])/area(initial['domain'])
    for i,old in enumerate(initial['radii']):
        if not F(old): raise ValueError('volume convention requires positive original radii')
        v*=(F(current['radii'][i])/F(old))**2
    return v
