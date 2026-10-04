"""Exact finite-world producer: enclosing disks, witness covers, adaptive trees."""
from fractions import Fraction as F
from functools import lru_cache
from itertools import combinations
import json


def key(response):
    return json.dumps(response,sort_keys=True,separators=(',',':'))


def distance2(a,b):
    return sum((F(x)-F(y))**2 for x,y in zip(a,b))


def minimum_enclosing_circle(points):
    p=[tuple(map(F,x)) for x in points]
    if not p: raise ValueError('empty world set is inconsistent, not a free recovery')
    candidates=[(x,F(0),(i,)) for i,x in enumerate(p)]
    for i,j in combinations(range(len(p)),2):
        c=tuple((a+b)/2 for a,b in zip(p[i],p[j]))
        candidates.append((c,distance2(c,p[i]),(i,j)))
    for i,j,k in combinations(range(len(p)),3):
        x,y=p[i]; u,v=p[j]; s,t=p[k]
        a,b=2*(u-x),2*(v-y); c,d=2*(s-x),2*(t-y)
        det=a*d-b*c
        if not det: continue
        e=u*u+v*v-x*x-y*y; f=s*s+t*t-x*x-y*y
        centre=((e*d-b*f)/det,(a*f-e*c)/det)
        candidates.append((centre,distance2(centre,p[i]),(i,j,k)))
    c,r,s=min((z for z in candidates if all(distance2(z[0],x)<=z[1] for x in p)),
              key=lambda z:(z[1],z[0],z[2]))
    return dict(centre=list(map(str,c)),radius2=str(r),support=list(s))


def validate(model):
    W=model['worlds']; A=model['actions']; ids=[w['id'] for w in W]
    if not W or len(set(ids))!=len(ids): raise ValueError('nonempty unique world ids required')
    if len({a['id'] for a in A})!=len(A): raise ValueError('duplicate action ids')
    if F(model['tolerance'])<0: raise ValueError('negative tolerance')
    for w in W:
        if len(w['target'])!=2: raise ValueError('planar targets required')
        tuple(map(F,w['target']))
    for a in A:
        if F(a['cost'])<=0 or set(a['responses'])!=set(ids): raise ValueError('invalid action or incomplete replies')


def analyze(model):
    validate(model); W=model['worlds']; A=model['actions']; tol2=F(model['tolerance'])**2
    indices=tuple(range(len(W))); remaining=tuple(range(len(A)))
    replies=[[key(a['responses'][w['id']]) for w in W] for a in A]
    edges=[]
    for size in (2,3):
        for H in combinations(indices,size):
            circle=minimum_enclosing_circle([W[i]['target'] for i in H])
            if F(circle['radius2'])>tol2:
                edges.append(dict(worlds=list(H),radius2=circle['radius2'],breakers=[a for a in remaining if len({replies[a][i] for i in H})>1]))
    cover_nodes=0
    def cover(E):
        nonlocal cover_nodes
        best=None; chosen=None
        for size in range(len(A)+1):
            for S in combinations(remaining,size):
                cover_nodes+=1; cost=sum((F(A[a]['cost']) for a in S),F(0))
                if best is not None and cost>=best: continue
                if all(set(S).intersection(e['breakers']) for e in E): best,chosen=cost,S
        return dict(cost=str(best) if best is not None else None,actions=[A[a]['id'] for a in chosen] if chosen is not None else None,
                    status='finite' if best is not None else 'infinite')
    pair=cover([e for e in edges if len(e['worlds'])==2]); batch=cover(edges)
    incident=[cover([e for e in edges if w in e['worlds']]) for w in indices]
    incident_lb=max(F(v['cost']) for v in incident) if all(v['cost'] is not None for v in incident) else None
    nodes=0
    @lru_cache(None)
    def dp(S,U):
        nonlocal nodes
        nodes+=1
        disk=minimum_enclosing_circle([W[i]['target'] for i in S])
        if F(disk['radius2'])<=tol2:
            return F(0),dict(terminal=True,worlds=list(S),circle=disk)
        best=None; tree=None
        for a in U:
            parts={}
            for i in S: parts.setdefault(replies[a][i],[]).append(i)
            if len(parts)==1: continue
            child={r:dp(tuple(V),tuple(b for b in U if b!=a)) for r,V in sorted(parts.items())}
            if any(v[0] is None for v in child.values()): continue
            cost=F(A[a]['cost'])+max(v[0] for v in child.values())
            if best is None or cost<best:
                best=cost; tree=dict(terminal=False,worlds=list(S),action=A[a]['id'],children={r:v[1] for r,v in child.items()})
        return best,tree
    cost,tree=dp(indices,remaining)
    return dict(schema='finite-minimal-trust-v1',adaptive_cost=str(cost) if cost is not None else None,
       adaptive_status='finite' if cost is not None else 'infinite',optimal_tree=tree,
       pair_batch=pair,hypergraph_batch=batch,incident_lower=str(incident_lb) if incident_lb is not None else None,
       incident_status='finite' if incident_lb is not None else 'infinite',incident_covers=incident,
       witnesses=edges,pair_count=sum(len(e['worlds'])==2 for e in edges),triple_count=sum(len(e['worlds'])==3 for e in edges),
       search=dict(adaptive_states=nodes,cover_nodes=cover_nodes,complete=True),
       scope='exact optimum only for the declared complete finite deterministic-response model; restriction supplies a lower bound only')
