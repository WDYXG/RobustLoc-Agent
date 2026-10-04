"""World-set provenance is part of the mathematical contract."""
from .arithmetic import F


def validate_model(model):
    W=model['worlds']; A=model['actions']; ids={w['id'] for w in W}
    if not W or len(ids)!=len(W) or any(len(w['target'])!=2 for w in W): raise ValueError('nonempty unique planar worlds required')
    if model['semantics'] not in ('complete-finite-prior','verified-restriction'): raise ValueError('world completeness must be explicit')
    if len({a['id'] for a in A})!=len(A) or F(model['tolerance'])<0: raise ValueError('menu/tolerance')
    for a in A:
        if F(a['cost'])<=0 or set(a['responses'])!=ids: raise ValueError('full positive-cost reply table required')
    return True
