"""Exact rational inputs and directed square-root enclosures."""
from fractions import Fraction as F
from math import isqrt


def sqrt_interval(value):
    v=F(value)
    if v<0: raise ValueError('negative squared quantity')
    scale=10**18; n=isqrt(v.numerator*scale*scale//v.denominator)
    lo=F(n,scale)
    return lo,lo if lo*lo==v else F(n+1,scale)


def distance2(x,z):
    if len(x)!=len(z): raise ValueError('dimension mismatch')
    return sum((F(a)-F(b))**2 for a,b in zip(x,z))


def dot(x,z): return sum(F(a)*F(b) for a,b in zip(x,z))


def det3(M):
    a,b,c=M[0]; d,e,f=M[1]; g,h,i=M[2]
    return a*(e*i-f*h)-b*(d*i-f*g)+c*(d*h-e*g)
