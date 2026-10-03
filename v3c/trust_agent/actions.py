"""Information type and externally asserted trust-root semantics."""
from copy import deepcopy
from fractions import Fraction as F
from .witnesses import transform


def payload(obs,offer,frame):
    coords={i:transform(p,frame['R'],frame['t']) for i,p in obs['nominal'].items()}
    if offer['kind']=='absolute-reference':
        return dict(points=[dict(anchor=i,centre=coords[i],radius=offer['radius'],root=offer['root']) for i in offer['anchors']])
    if offer['kind']=='independent-source':
        return dict(report=dict(issuer=offer['issuer'],points=[dict(anchor=i,centre=coords[i],radius='0') for i in offer['anchors']]))
    if offer['kind']=='baseline':
        a,b=offer['anchors']; d2=sum((F(x)-F(y))**2 for x,y in zip(coords[a],coords[b]))
        return dict(baseline=dict(a=a,b=b,distance2=str(d2),root=offer['root']))
    return dict(measurements=[dict(anchor=i,value='0',weight='1') for i in offer['anchors']])


def apply(obs,offer,result):
    s=deepcopy(obs)
    if F(offer['cost'])>F(s['budget']): raise ValueError('information budget exhausted')
    if offer['kind']=='absolute-reference':
        if offer['root'] not in s['external_roots']: raise ValueError('missing external absolute trust root')
        for a in result['points']:
            if a['anchor'] not in offer['anchors'] or a['root']!=offer['root'] or a['radius']!=offer['radius']: raise ValueError('reference response binding')
        if {a['anchor'] for a in result['points']}!=set(offer['anchors']): raise ValueError('incomplete reference reply')
        s['hard_refs']+=result['points']
    elif offer['kind']=='independent-source':
        rr=result['report']
        if rr['issuer']!=offer['issuer'] or rr['issuer'] not in s['failure_groups']: raise ValueError('source binding')
        if {a['anchor'] for a in rr['points']}!=set(offer['anchors']): raise ValueError('source coverage')
        s['reports'].append(rr)
    elif offer['kind']=='baseline':
        bb=result['baseline']
        if offer['root'] not in s['external_roots']: raise ValueError('missing baseline trust root')
        if bb['root']!=offer['root'] or [bb['a'],bb['b']]!=offer['anchors']: raise ValueError('baseline binding')
        s['baselines'].append(bb)
    elif offer['kind']=='ordinary-range':
        if [m['anchor'] for m in result['measurements']]!=offer['anchors']: raise ValueError('range binding')
        if any(m['weight']!='1' for m in result['measurements']): raise ValueError('fixed range weights changed')
        s['measurements']+=result['measurements']
    else: raise ValueError('unknown information type')
    s['budget']=str(F(s['budget'])-F(offer['cost'])); s['offers']=[o for o in s['offers'] if o['id']!=offer['id']]
    s['receipts'].append(dict(offer_id=offer['id'],kind=offer['kind'],payload=deepcopy(result),
        scope='conditional on externally assumed roots and registered source budget, not a signature protocol'))
    return s
