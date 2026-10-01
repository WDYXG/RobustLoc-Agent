"""Shared audited primitives: rational inputs and integer outward sqrt only."""
from fractions import Fraction as F
from math import isqrt
from itertools import combinations

PRECISION = 15

def rational(value):
    if isinstance(value, float):
        raise TypeError('Certificate inputs must be declared rational strings, not floats')
    return F(value)

def sqrt_interval(value):
    value = rational(value)
    if value < 0:
        raise ValueError('Negative square root')
    scale = 10 ** PRECISION
    k = isqrt((value.numerator * scale * scale) // value.denominator)
    lo = F(k, scale)
    return lo, lo if lo * lo == value else F(k + 1, scale)

def point(values):
    return tuple(rational(v) for v in values)

def box(values):
    b = tuple(rational(v) for v in values)
    if len(b) != 4 or b[0] >= b[1] or b[2] >= b[3]:
        raise ValueError('Expected nondegenerate [xmin,xmax,ymin,ymax]')
    return b

def dataset(data):
    anchors = [point(p) for p in data['anchors']]
    weights = [rational(w) for w in data['weights']]
    if not anchors or len(weights) != len(anchors) or any(w <= 0 for w in weights):
        raise ValueError('Weights must be fixed and positive')
    if any(len(p) != 2 for p in anchors):
        raise ValueError('Only planar anchors supported')
    return anchors, weights, box(data['domain'])

def survivors(n, q):
    if not isinstance(q, int) or q < 0:
        raise ValueError('q must be nonnegative integer')
    return max(0, n - 2 * q)

def distance2(x, z):
    return sum((a-b)**2 for a,b in zip(x,z))

def centre(b):
    return ((b[0]+b[1])/2, (b[2]+b[3])/2)

def squared_range_box(p, b):
    lower = upper = F(0)
    for k,(lo,hi) in enumerate(((b[0],b[1]),(b[2],b[3]))):
        lower += max(lo-p[k], p[k]-hi, F(0))**2
        upper += max(abs(lo-p[k]),abs(hi-p[k]))**2
    return lower, upper

def range_box(p, b):
    lo,hi = squared_range_box(p,b)
    return sqrt_interval(lo)[0], sqrt_interval(hi)[1]

def pair_max2(bx,bz):
    return sum(max(abs(bx[k]-bz[k+1]),abs(bx[k+1]-bz[k]))**2 for k in (0,2))

def split_pair(bx,bz):
    dims = [(bx[1]-bx[0],0),(bx[3]-bx[2],1),
            (bz[1]-bz[0],2),(bz[3]-bz[2],3)]
    dim = max(dims, key=lambda item:item[0])[1]  # deterministic first tie
    children = []
    for side in (0,1):
        x,z = list(bx),list(bz)
        target = x if dim < 2 else z
        k = 2*(dim%2); mid = (target[k]+target[k+1])/2
        target[k+1 if side == 0 else k] = mid
        children.append((tuple(x),tuple(z)))
    return children

def grid(b, divisions):
    if not isinstance(divisions,int) or divisions < 1:
        raise ValueError('Invalid grid')
    dx=(b[1]-b[0])/divisions; dy=(b[3]-b[2])/divisions
    return [(b[0]+i*dx,b[0]+(i+1)*dx,b[2]+j*dy,b[2]+(j+1)*dy)
            for i in range(divisions) for j in range(divisions)]

def det_trace_lower(g):
    a,b,c=g; trace=a+c; det=a*c-b*b
    if det < 0:
        raise ArithmeticError('Exact PSD check failed')
    return det/trace if trace else F(0)

def gram_at(anchors,weights,x,indices):
    a=b=c=F(0)
    for i in indices:
        dx,dy=x[0]-anchors[i][0],x[1]-anchors[i][1]
        r2=dx*dx+dy*dy
        if not r2:
            raise ValueError('Differential margin undefined at anchor')
        a+=weights[i]*dx*dx/r2; b+=weights[i]*dx*dy/r2; c+=weights[i]*dy*dy/r2
    return a,b,c

def point_upper(anchors,weights,x,z,q):
    """Exact feasible pair upper bound on μ; no sampled lower estimate."""
    t2=distance2(x,z)
    if not t2:
        raise ValueError('Distinct points required')
    m=survivors(len(anchors),q)
    values=[]; exact_equal=0
    for p,w in zip(anchors,weights):
        r2x,r2z=distance2(x,p),distance2(z,p)
        if r2x == r2z:
            values.append(F(0)); exact_equal+=1; continue
        lx,ux=sqrt_interval(r2x); lz,uz=sqrt_interval(r2z)
        values.append(w*max(abs(lx-uz),abs(ux-lz))**2)
    ub=sqrt_interval(sum(sorted(values)[:m])/t2)[1]
    return ub,exact_equal

def encode(value):
    if isinstance(value,F): return str(value)
    if isinstance(value,dict): return {k:encode(v) for k,v in value.items()}
    if isinstance(value,(tuple,list)): return [encode(v) for v in value]
    return value
