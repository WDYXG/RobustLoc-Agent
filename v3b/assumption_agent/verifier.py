"""Consumer recomputes bounds by pairwise variance, no producer import."""
from fractions import Fraction as F
from math import isqrt
from itertools import combinations
from functools import lru_cache
import json


def root(v):
    v=F(v)
    if v<0: raise ValueError('negative sqrt')
    t=10**15; a=isqrt(v.numerator*t*t//v.denominator)
    lo=F(a,t); return lo,lo if lo*lo==v else F(a+1,t)


def _range2(p,d):
    lo=hi=F(0)
    for k in range(2):
        a,b=d[2*k:2*k+2]; v=p[k]
        lo+=max(a-v,v-b,F(0))**2; hi+=max(abs(a-v),abs(b-v))**2
    return lo,hi


def _pair_scatter(p,nu,S):
    t=sum(nu[i] for i in S)
    if not t: return F(0)
    a=b=c=F(0)
    for i,j in combinations(S,2):
        x,y=p[i][0]-p[j][0],p[i][1]-p[j][1]; u=nu[i]*nu[j]/t
        a+=u*x*x; b+=u*x*y; c+=u*y*y
    det=a*c-b*b
    if det<0: raise ValueError('PSD violation')
    return det/(a+c) if a+c else F(0)


@lru_cache(maxsize=20000)
def _verify_margin(serialized):
    cert=json.loads(serialized)
    if cert['schema']!='robust-anchor-margin-v1': raise ValueError('schema')
    data=cert['data']; p=[tuple(F(v) for v in x) for x in data['anchors']]
    w=[F(v) for v in data['weights']]; d=tuple(F(v) for v in data['domain']); delta=[F(v) for v in data['radii']]
    n=len(p); q=cert['q']
    if (not n or len(w)!=n or len(delta)!=n or any(len(x)!=2 for x in p)
        or any(v<=0 for v in w) or any(v<0 for v in delta)
        or len(d)!=4 or d[0]>=d[1] or d[2]>=d[3] or type(q) is not int or q<0):
        raise ValueError('invalid rational contract')
    m=max(0,n-2*q); sets=list(combinations(range(n),m))
    R2=[_range2(x,d)[1] for x in p]
    nu=[w[i]/((root(R2[i])[1]+delta[i])**2 if delta[i] else R2[i]) for i in range(n)]
    if [tuple(row['indices']) for row in cert['subsets']]!=sets: raise ValueError('incomplete survivor coverage')
    bounds=[]
    for S,row in zip(sets,cert['subsets']):
        e=_pair_scatter(p,nu,S); c=sum(nu[i]*delta[i]**2 for i in S)
        b=max(F(0),root(e)[0]-root(c)[1]); bounds.append(b)
        if F(row['eigen_lower2'])!=e or F(row['perturbation2'])!=c or F(row['lower'])!=b:
            raise ValueError('scatter arithmetic')
    scatter=min(bounds); nn=[w[i]/R2[i] for i in range(n)]
    nominal=root(min(_pair_scatter(p,nn,S) for S in sets))[0]
    separation=[root(_range2(x,d)[0])[0] for x in p]
    available=all(separation[i]>delta[i] for i in range(n)); der=cert['derivative']; bound=F(0)
    if der['available']!=available: raise ValueError('separation prerequisite')
    if available:
        c2=sum(sorted((w[i]*(delta[i]/(separation[i]-delta[i]))**2 for i in range(n)),reverse=True)[:m])
        c=root(c2)[1]; bound=max(F(0),nominal-c)
        if (list(map(F,der['separation_lower']))!=separation or F(der['constant2_upper'])!=c2
            or F(der['constant_upper'])!=c or F(der['lower'])!=bound): raise ValueError('derivative arithmetic')
    elif F(der['lower'])!=0: raise ValueError('unavailable bound positive')
    lower=max(scatter,bound)
    if (F(cert['nominal_scatter_lower'])!=nominal or F(cert['scatter_lower'])!=scatter
        or F(cert['lower'])!=lower): raise ValueError('claimed lower mismatch')
    return lower


def verify_margin(cert):
    return _verify_margin(json.dumps(cert,sort_keys=True))


def residual(obs,x,q):
    p=[tuple(F(v) for v in a) for a in obs['anchors']]; z=tuple(F(v) for v in x)
    d=list(map(F,obs['domain']))
    if not(d[0]<=z[0]<=d[1] and d[2]<=z[1]<=d[3]): return None
    squares=[]
    for a,w,y in zip(p,obs['weights'],obs['measurements']):
        lo,hi=root(sum((v-u)**2 for v,u in zip(a,z))); y=F(y)
        squares.append(F(w)*max(abs(lo-y),abs(hi-y))**2)
    return root(sum(sorted(squares)[:max(0,len(p)-q)]))[1]


def verify_frontier(obs,f):
    rows=f['rows']; expected={k:obs[k] for k in ('anchors','weights','domain','radii')}
    E=F(obs['epsilon_max']); r=F(obs['error_tolerance']); n=len(obs['anchors'])
    if len(rows)<=obs['q_max'] or [row['q'] for row in rows]!=list(range(len(rows))):
        raise ValueError('incomplete q frontier')
    for row in rows:
        q=row['q']; c=row['certificate']
        if c['data']!=expected or c['q']!=q: raise ValueError('frontier bound to wrong contract')
        b=verify_margin(c)
        zz=root(sum(sorted((F(w)*F(d)**2 for w,d in zip(obs['weights'],obs['radii'])),reverse=True)[:max(0,n-q)]))[1]
        ceiling=r*b/2-zz if b else None; bound=2*(E+zz)/b if b else None
        if (F(row['lower'])!=b or F(row['zeta_upper'])!=zz
            or row['epsilon_ceiling']!=(str(ceiling) if ceiling is not None else None)
            or row['error_bound']!=(str(bound) if bound is not None else None)
            or row['certified']!=bool(b and 2*(E+zz)<=r*b)):
            raise ValueError('frontier scalar arithmetic')
    rel=rows[:obs['q_max']+1]
    worst=max(F(row['error_bound']) for row in rel) if all(row['error_bound'] is not None for row in rel) else None
    if (f['all_contracts_certified']!=all(row['certified'] for row in rel)
        or f['worst_error_bound']!=(str(worst) if worst is not None else None)
        or f['q_cert']!=max((row['q'] for row in rows if row['certified']),default=None)):
        raise ValueError('frontier aggregation')
    return True


def verify_recovery(obs,decision):
    if decision['action']!='recover': raise ValueError('not recovery')
    verify_frontier(obs,decision['frontier'])
    r=F(obs['error_tolerance']); E=F(obs['epsilon_max']); bounds=[]
    if not all(row['certified'] for row in decision['frontier']['rows'][:obs['q_max']+1]):
        raise ValueError('entire frontier pre-gate failed')
    for row in [decision['frontier']['rows'][obs['q_max']]]:
        q=row['q']; expected={k:obs[k] for k in ('anchors','weights','domain','radii')}
        if row['certificate']['data']!=expected or row['certificate']['q']!=q:
            raise ValueError('certificate not bound to observation')
        b=verify_margin(row['certificate'])
        z=root(sum(sorted((F(w)*F(v)**2 for w,v in zip(obs['weights'],obs['radii'])),reverse=True)[:max(0,len(obs['anchors'])-q)]))[1]
        rr=residual(obs,decision['position'],q)
        if not b or 2*(E+z)>r*b or rr is None or rr>E+z: raise ValueError('conditional recovery gate')
        bounds.append((E+rr+z)/b)
    exact=max(bounds)
    if F(decision['error_bound'])!=exact: raise ValueError('recovery bound mismatch')
    return exact
