"""Small exact polynomial kernel; strings are data, never eval/sympify/code.

An accepted certificate is p = sum_j w_j s_j^2 g_j, where w_j >= 0 and
g_j is 1 or one of the declared nonnegative constraints. This is sufficient,
not complete. Coefficients, identities and counterexample values are rational.
"""
from fractions import Fraction as F
from itertools import product
import re


class BudgetExceeded(ValueError):
    pass


class Meter:
    def __init__(self, limit=50000):
        self.limit, self.used = limit, 0

    def tick(self, n=1):
        self.used += n
        if self.used > self.limit:
            raise BudgetExceeded('deterministic operation budget exhausted')


def rational(value):
    if isinstance(value, bool) or not isinstance(value, (int, str)) or len(str(value)) > 80:
        raise ValueError('rational integer/string required, at most 80 characters')
    if isinstance(value, str) and not re.fullmatch(r'[+-]?\d+(?:/[1-9]\d*)?', value):
        raise ValueError('use integer or integer/positive-integer notation; no exponent parsing')
    x = F(value)
    if x.numerator.bit_length() > 200 or x.denominator.bit_length() > 200:
        raise ValueError('rational bit budget')
    return x


def parse(data, n):
    if not isinstance(data, dict) or len(data) > 64:
        raise ValueError('polynomial must have at most 64 monomials')
    out = {}
    for k, v in data.items():
        if not isinstance(k, str):
            raise ValueError('exponent key')
        e = tuple(int(t) for t in k.split(','))
        if len(e) != n or min(e) < 0 or sum(e) > 12 or ','.join(map(str, e)) != k:
            raise ValueError('canonical exponent tuple, total degree <= 12')
        q = rational(v)
        if q:
            out[e] = q
    return out


def encoded(p):
    return {','.join(map(str, e)): str(v) for e, v in sorted(p.items()) if v}


def add(p, q):
    r = dict(p)
    for e, v in q.items():
        r[e] = r.get(e, F(0)) + v
    return {e: v for e, v in r.items() if v}


def multiply(p, q, meter):
    out = {}
    for (a, b) in product(p.items(), q.items()):
        meter.tick()
        e = tuple(x+y for x, y in zip(a[0], b[0]))
        out[e] = out.get(e, F(0)) + a[1]*b[1]
    return {e: v for e, v in out.items() if v}


def value(p, x, meter):
    result = F(0)
    for e, c in p.items():
        meter.tick()
        v = c
        for xi, ei in zip(x, e):
            v *= xi**ei
        result += v
    return result


def verify_sos(statement, certificate, meter):
    n = len(statement['variables'])
    target = parse(statement['polynomial'], n)
    constraints = [parse(g, n) for g in statement['constraints']]
    if not isinstance(certificate, list) or not 1 <= len(certificate) <= 32:
        raise ValueError('one to 32 SOS summands required')
    total = {}
    for term in certificate:
        if set(term) != {'weight', 'polynomial', 'constraint'}:
            raise ValueError('SOS fields')
        w = rational(term['weight'])
        j = term['constraint']
        if w < 0 or type(j) is not int or not -1 <= j < len(constraints):
            raise ValueError('nonnegative weight and bound constraint index required')
        p = parse(term['polynomial'], n)
        g = {(0,)*n: F(1)} if j == -1 else constraints[j]
        sq = multiply(multiply(p, p, meter), g, meter)
        total = add(total, {e: w*c for e, c in sq.items()})
    if total != target:
        raise ValueError('SOS polynomial identity is false')
    return {'identity': encoded(total), 'nonzero': bool(target), 'summands': len(certificate)}


def counterexample(statement, points, meter):
    n = len(statement['variables'])
    p = parse(statement['polynomial'], n)
    gs = [parse(g, n) for g in statement['constraints']]
    checked = 0
    if not isinstance(points, list) or len(points) > 128:
        raise ValueError('at most 128 rational test points')
    for point in points:
        if len(point) != n:
            raise ValueError('counterexample dimension')
        x = list(map(rational, point))
        if all(value(g, x, meter) >= 0 for g in gs):
            checked += 1
            v = value(p, x, meter)
            if v < 0:
                return {'point': list(map(str, x)), 'value': str(v), 'admissible_checked': checked}
    return {'point': None, 'admissible_checked': checked}
