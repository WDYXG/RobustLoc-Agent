"""Search an explicitly supplied finite transformation family, then verify it."""
from itertools import product
from .arithmetic import F,distance2

IDENTITY=((1,0),(0,1))
NEGATION=((-1,0),(0,-1))
CANDIDATES=[((a,0),(0,b)) for a,b in product((1,-1),repeat=2)]+[((0,a),(b,0)) for a,b in product((1,-1),repeat=2)]


def apply(T,x): return tuple(sum(F(a)*F(b) for a,b in zip(row,x)) for row in T)


def discover(problem):
    accepted=[T for T in CANDIDATES if problem.verify_universal_symmetry(T)]
    identified='sign' if set(accepted)=={IDENTITY,NEGATION} else ('identity' if set(accepted)=={IDENTITY} else None)
    if identified is None or problem.symmetry!=identified: raise ValueError('adapter quotient differs from verified transformation family')
    return dict(candidate_count=len(CANDIDATES),accepted=accepted,identified_quotient=identified,
        scope='exact adapter algebra over a human-supplied finite transformation family; no unconstrained symmetry discovery')


def metric2(x,z,kind):
    if kind=='identity': return distance2(x,z)
    if kind=='sign': return min(distance2(x,z),distance2(x,[-F(a) for a in z]))
    raise ValueError('unsupported quotient group')


def orientations(points,kind):
    if not points: raise ValueError('empty feasible set is inconsistent')
    if kind not in ('identity','sign'): raise ValueError('unsupported quotient')
    # Global sign flips preserve an enclosing radius; fix the first lift.
    choices=product((1,-1),repeat=len(points)-1) if kind=='sign' else [(1,)*(len(points)-1)]
    for tail in choices:
        signs=(1,)+tuple(tail)
        yield signs,[tuple(s*F(a) for a in x) for s,x in zip(signs,points)]
