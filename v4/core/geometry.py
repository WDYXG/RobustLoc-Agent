"""Finite orbit covers; no problem-specific observation map in this module.

Euclidean circle support arithmetic is extracted from frozen v3d/finite.py.
The quotient reduction enumerates all consistent lifts, not just pair/triples.
"""
from itertools import combinations
from .arithmetic import F,distance2
from .symmetry import orientations,metric2


def euclidean_ball(points):
    p=[tuple(map(F,x)) for x in points]
    if not p or any(len(x)!=2 for x in p): raise ValueError('nonempty planar states required')
    candidates=[(x,F(0)) for x in p]
    for x,z in combinations(p,2):
        c=tuple((a+b)/2 for a,b in zip(x,z)); candidates.append((c,distance2(c,x)))
    for (x,y),(u,v),(s,t) in combinations(p,3):
        a,b,c,d=2*(u-x),2*(v-y),2*(s-x),2*(t-y); det=a*d-b*c
        if not det: continue
        e,f=u*u+v*v-x*x-y*y,s*s+t*t-x*x-y*y
        center=((e*d-b*f)/det,(a*f-e*c)/det)
        candidates.append((center,distance2(center,(x,y))))
    center,r=min(((c,r) for c,r in candidates if all(distance2(c,x)<=r for x in p)),key=lambda v:(v[1],v[0]))
    return dict(centre=list(map(str,center)),radius2=str(r))


def enclosing_ball(points,kind):
    results=[]
    for signs,lifted in orientations(points,kind):
        c=euclidean_ball(lifted); results.append(dict(c,signs=list(signs)))
    out=min(results,key=lambda c:(F(c['radius2']),c['centre'],c['signs']))
    out.update(orientations_checked=len(results),symmetry=kind)
    return out


def independent_radius2(points,kind):
    """Different computation: min over lifts, max Helly support radii per lift."""
    radii=[]
    for _,P in orientations(points,kind):
        maximum=F(0)
        for k in (2,3):
            for H in combinations(P,k):
                sides=[distance2(x,z) for x,z in combinations(H,2)]
                r=max(sides)/4
                if k==3 and 2*max(sides)<sum(sides):
                    a,b,c=H; cross=(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
                    r=sides[0]*sides[1]*sides[2]/(4*cross*cross)
                maximum=max(maximum,r)
        radii.append(maximum)
    return min(radii)


def verify_ball(points,kind,ball):
    r=independent_radius2(points,kind)
    if ball['symmetry']!=kind or F(ball['radius2'])!=r: raise ValueError('radius not exact for supplied quotient')
    if any(metric2(ball['centre'],x,kind)>r for x in points): raise ValueError('center fails quotient cover')
    expected=2**(len(points)-1) if kind=='sign' else 1
    if ball['orientations_checked']!=expected: raise ValueError('incomplete sign-lift search')
    return r
