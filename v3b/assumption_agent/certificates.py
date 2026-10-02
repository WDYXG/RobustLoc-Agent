"""Exact rational producer. Samples never authorize a lower bound."""
from copy import deepcopy
from fractions import Fraction as F
from functools import lru_cache
from itertools import combinations
import json
from v2.global_stability.exact import dataset, sqrt_interval, squared_range_box, encode


def validate(data):
    p,w,d=dataset(data)
    radii=[F(v) for v in data['radii']]
    if len(radii)!=len(p) or any(v<0 for v in radii):
        raise ValueError('One nonnegative rational anchor radius per range required')
    if any(isinstance(v,float) for v in data['radii']):
        raise TypeError('Rational radii required')
    return p,w,d,radii


def _scatter(p,nu,indices):
    t=sum(nu[i] for i in indices)
    if not t: return F(0)
    c=[sum(nu[i]*p[i][k] for i in indices)/t for k in (0,1)]
    a=sum(nu[i]*(p[i][0]-c[0])**2 for i in indices)
    b=sum(nu[i]*(p[i][0]-c[0])*(p[i][1]-c[1]) for i in indices)
    e=sum(nu[i]*(p[i][1]-c[1])**2 for i in indices)
    return (a*e-b*b)/(a+e) if a+e else F(0)


@lru_cache(maxsize=20000)
def _build(serialized,q):
    data=json.loads(serialized); p,w,d,delta=validate(data)
    if type(q) is not int or q<0: raise ValueError('Invalid corruption budget')
    m=max(0,len(p)-2*q); sets=list(combinations(range(len(p)),m))
    max2=[squared_range_box(v,d)[1] for v in p]
    # delta=0 uses exact squared range, avoiding needless sqrt relaxation.
    R2=[(sqrt_interval(r)[1]+e)**2 if e else r for r,e in zip(max2,delta)]
    nu=[v/r for v,r in zip(w,R2)]; nominal_nu=[v/r for v,r in zip(w,max2)]
    rows=[]
    for S in sets:
        e=_scatter(p,nu,S); err=sum(nu[i]*delta[i]**2 for i in S)
        rows.append(dict(indices=list(S),eigen_lower2=e,perturbation2=err,
                         lower=max(F(0),sqrt_interval(e)[0]-sqrt_interval(err)[1])))
    scatter=min(r['lower'] for r in rows)
    nominal=sqrt_interval(min(_scatter(p,nominal_nu,S) for S in sets))[0]
    sep=[sqrt_interval(squared_range_box(v,d)[0])[0] for v in p]
    if all(r>e for r,e in zip(sep,delta)):
        values=sorted((v*(e/(r-e))**2 for v,r,e in zip(w,sep,delta)),reverse=True)
        c2=sum(values[:m]); c=sqrt_interval(c2)[1]
        derivative=dict(available=True,separation_lower=sep,constant2_upper=c2,
                        constant_upper=c,lower=max(F(0),nominal-c))
    else: derivative=dict(available=False,reason='nominal-anchor-ball-not-separated-from-domain',lower=F(0))
    return encode(dict(schema='robust-anchor-margin-v1',data=data,q=q,
        subsets=rows,scatter_lower=scatter,nominal_scatter_lower=nominal,
        derivative=derivative,lower=max(scatter,derivative['lower']),
        scope='uniform shared-map lower bound, not joint nuisance injectivity'))


def build(data,q): return deepcopy(_build(json.dumps(data,sort_keys=True),q))


def geometry_data(obs):
    return {k:obs[k] for k in ('anchors','weights','domain','radii')}


def zeta(obs,q):
    n=len(obs['anchors']); terms=sorted((F(w)*F(e)**2 for w,e in zip(obs['weights'],obs['radii'])),reverse=True)
    return sqrt_interval(sum(terms[:max(0,n-q)]))[1]


def frontier(obs,include_grid=True,complete=True):
    from .verifier import verify_margin
    n=len(obs['anchors']); top=max((n+1)//2,obs['q_max']) if complete else obs['q_max']; rows=[]
    E=F(obs['epsilon_max']); r=F(obs['error_tolerance'])
    for q in range(top+1):
        cert=build(geometry_data(obs),q); b=verify_margin(cert); z=zeta(obs,q)
        ceiling=r*b/2-z if b else None
        rows.append(dict(q=q,lower=str(b),zeta_upper=str(z),
            epsilon_ceiling=str(ceiling) if ceiling is not None else None,
            error_bound=str(2*(E+z)/b) if b else None,
            certified=bool(b and 2*(E+z)<=r*b),certificate=cert))
    relevant=rows[:obs['q_max']+1]
    worst=max((F(row['error_bound']) for row in relevant),default=F(0)) if all(row['error_bound'] is not None for row in relevant) else None
    result=dict(rows=rows,all_contracts_certified=all(row['certified'] for row in relevant),
        worst_error_bound=str(worst) if worst is not None else None,
        q_cert=max((row['q'] for row in rows if row['certified']),default=None),
        assumption_set=dict(q=list(range(obs['q_max']+1)),epsilon=['0',obs['epsilon_max']],
                            domain=obs['domain'],radii=obs['radii']),
        scope='sufficient conditional frontier; actual q is not inferred')
    if include_grid:
        cells=[]
        for scale in ('0','1/2','1'):
            data=geometry_data(obs); data=dict(data,radii=[str(F(v)*F(scale)) for v in obs['radii']])
            for q in range(top+1):
                b=verify_margin(build(data,q)); z=zeta(dict(obs,radii=data['radii']),q)
                for eps in (F(0),E/2,E):
                    cells.append(dict(q=q,epsilon=str(eps),radius_scale=scale,lower=str(b),
                         certified=bool(b and 2*(eps+z)<=r*b),
                         conditional_reduction=scale!='1'))
        result['grid']=cells
    return result
