"""Worst surviving lower frame bound; known object with explicit 2D algebra."""
from itertools import combinations
import numpy as np

def directions(position, anchors):
    delta=np.asarray(position,float)-np.asarray(anchors,float)
    radius=np.linalg.norm(delta,axis=1)
    if np.any(radius<=1e-12):
        raise ValueError('Range Jacobian undefined at an anchor')
    return delta/radius[:,None]

def eigenvalue_2d(unit,weights):
    """Stable smaller eigenvalue using the determinant pairwise expansion."""
    unit=np.asarray(unit,float); weights=np.asarray(weights,float)
    t=float(weights.sum())
    if t<=0: return 0.
    cross=unit[:,0,None]*unit[None,:,1]-unit[:,1,None]*unit[None,:,0]
    determinant=float(np.sum(np.triu(weights[:,None]*weights[None,:]*cross**2,1)))
    discriminant=max(0.,t*t-4*determinant)
    return 2*determinant/(t+np.sqrt(discriminant))

def margin(unit,weights,k):
    unit=np.asarray(unit,float); weights=np.asarray(weights,float)
    if unit.ndim!=2 or unit.shape[1]!=2 or len(unit)!=len(weights):
        raise ValueError('Expected n by 2 unit directions and n weights')
    if not np.isfinite(unit).all() or not np.isfinite(weights).all() or np.any(weights<=0):
        raise ValueError('Finite directions and positive fixed weights required')
    if not np.allclose(np.linalg.norm(unit,axis=1),1,atol=1e-9):
        raise ValueError('Directions must have unit norm')
    if not isinstance(k,(int,np.integer)) or not 0<=k<=len(unit):
        raise ValueError('Invalid erasure budget')
    if len(unit)-k<2: return dict(alpha=0.,subset=list(range(len(unit)-k)),erased=k)
    best=float('inf'); witness=None
    for ids in combinations(range(len(unit)),len(unit)-k):
        ids=list(ids); value=eigenvalue_2d(unit[ids],weights[ids])
        if value<best: best,witness=value,ids
    return dict(alpha=best,subset=witness,erased=k)

def point_margin(position,anchors,weights,k):
    return margin(directions(position,anchors),weights,k)

def curvature_bound(center,radius,anchors,weights):
    separation=np.linalg.norm(np.asarray(center)-anchors,axis=1)-radius
    if radius<=0 or np.any(separation<=0):
        raise ValueError('Positive prior radius must exclude all anchors')
    return float(np.linalg.norm(np.sqrt(weights)/separation))

def beta(position,center,radius,anchors,weights,q):
    L=curvature_bound(center,radius,anchors,weights)
    gamma=np.sqrt(point_margin(position,anchors,weights,2*q)['alpha'])
    return float(gamma-L*(radius+np.linalg.norm(np.asarray(position)-center)))
