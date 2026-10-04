"""Shared support-union arithmetic for ANY scalar observation map."""
from .arithmetic import F


def budget(q,n):
    if type(q) is not int or q<0 or q>n: raise ValueError('invalid corruption budget')


def interval_distance2(a,b):
    l,u=map(F,a); v,w=map(F,b)
    if l>u or v>w: raise ValueError('invalid observation interval')
    return max(F(0),l-w,v-u)**2,max(abs(l-w),abs(u-v))**2


def residual_interval2(predicted,observed,q):
    n=len(predicted); budget(q,n)
    if len(observed)!=n: raise ValueError('measurement length')
    squares=[interval_distance2(p,(F(y),F(y))) for p,y in zip(predicted,observed)]
    k=n-q
    return sum(sorted(a for a,b in squares)[:k]),sum(sorted(b for a,b in squares)[:k])


def trimmed_difference2(left,right,q):
    n=len(left); budget(q,n)
    if len(right)!=n: raise ValueError('measurement length')
    k=max(0,n-2*q); squares=[interval_distance2(a,b) for a,b in zip(left,right)]
    return sum(sorted(a for a,b in squares)[:k]),sum(sorted(b for a,b in squares)[:k])


def common_corrupted_transcript(left,right,q):
    """Construct a common zero-noise transcript when supports can be split."""
    budget(q,len(left))
    if len(left)!=len(right): raise ValueError('measurement length')
    if any(F(a)!=F(b) for a,b in left+right): raise ValueError('exact predictions required for support witness')
    x=[F(a) for a,b in left]; z=[F(a) for a,b in right]
    different=[i for i in range(len(x)) if x[i]!=z[i]]
    if len(different)>2*q: return None
    y=x[:]
    for i in different[:q]: y[i]=z[i]
    sx=[i for i in range(len(x)) if y[i]!=x[i]]; sz=[i for i in range(len(x)) if y[i]!=z[i]]
    assert len(sx)<=q and len(sz)<=q
    return dict(values=list(map(str,y)),left_support=sx,right_support=sz,differing_coordinates=different,q=q)
