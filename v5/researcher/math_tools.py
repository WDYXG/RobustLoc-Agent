"""Bounded search producers. Only verifier.py is allowed to decide status."""
from fractions import Fraction as F
from itertools import combinations
from v4.core.geometry import enclosing_ball
from v4.core.decision import analyze
from v4.core.arithmetic import distance2, dot
from v4.problems.phase_retrieval import PhaseRetrieval
from v4.problems.range_localization import RangeLocalization
from .polynomial import counterexample
from .schema import fields
from .io import read, PACKAGE


def radius_search(s, meter):
    P = s['universe']; k = s['k']; rho2 = F(s['rho'])**2
    checked = 0; certificates = []
    for n in range(k+1, s['max_size']+1):
        for indices in combinations(range(len(P)), n):
            H = [P[i] for i in indices]
            meter.tick((2**(n-1) if s['symmetry'] == 'sign' else 1) * (1+n+n*n+n**3))
            checked += 1
            # Monotonicity reduces <=k subset checks to exactly k.
            small = [enclosing_ball(list(S), s['symmetry']) for S in combinations(H, k)]
            maximum = max(F(c['radius2']) for c in small)
            if maximum > rho2:
                continue
            full = enclosing_ball(H, s['symmetry'])
            row = {'indices': list(indices), 'full': full, 'small': small}
            certificates.append(row)
            if F(full['radius2']) > rho2:
                return {'witness': row, 'checked': checked, 'feasible_small_covers': certificates}
    return {'witness': None, 'checked': checked, 'feasible_small_covers': certificates}


def finite_model(s):
    W = [{'id': f'w{i}', 'target': x} for i, x in enumerate(s['worlds'])]
    A = []
    for j, (a, c) in enumerate(zip(s['parameters'], s['costs'])):
        values = {w['id']: {'value': str(distance2(a, w['target']) if s['problem'] == 'range'
                                       else dot(a, w['target'])**2)} for w in W}
        A.append({'id': f'a{j}', 'cost': c, 'parameter': a, 'responses': values})
    # Squaring nonnegative ranges preserves exact noiseless reply partitions.
    return {'worlds': W, 'actions': A, 'tolerance': s['tolerance'],
            'semantics': 'complete-finite-prior' if s['scope'] == 'finite-prior' else 'verified-restriction'}


def metric_problem(s):
    return RangeLocalization() if s['problem'] == 'range' else PhaseRetrieval([(1, 0), (0, 1)])


def pr_certificate(s, meter):
    p = PhaseRetrieval(s['design'], 0, 100)
    survivors = max(0, len(s['design'])-2*s['q'])
    checked = []
    for S in combinations(range(len(s['design'])), survivors):
        meter.tick(2**len(S))
        cp = p.complement_property(S)
        checked.append({'survivors': list(S), 'cp': cp})
        if not cp['passed']:
            def kernel(indices):
                for i in indices:
                    a, b = map(F, s['design'][i])
                    if a or b:
                        return (-b, a)
                return (F(1), F(0))
            u, v = map(kernel, cp['partition'])
            x, z = [a+b for a, b in zip(u, v)], [a-b for a, b in zip(u, v)]
            hx = [dot(a, x)**2 for a in s['design']]
            hz = [dot(a, z)**2 for a in s['design']]
            differing = [i for i, (a, b) in enumerate(zip(hx, hz)) if a != b]
            y = list(hx)
            for i in differing[:s['q']]:
                y[i] = hz[i]
            return {'survivors': checked, 'witness': {'x': list(map(str, x)), 'z': list(map(str, z)), 'y': list(map(str, y))}}
    return {'survivors': checked, 'witness': None}


def execute(family, s, request, meter):
    if family == 'polynomial':
        fields(request, 'sos points')
        c = counterexample(s, request['points'], meter)
        return {'counterexample': c, 'sos': request['sos'], 'sample_points': request['points']}
    fields(request, '')
    if family == 'radius':
        return radius_search(s, meter)
    if family == 'finite_cost':
        n = len(s['worlds'])
        meter.tick((2**n)*(2**(n-1) if s['problem'] == 'pr' else 1)*(n**3 + 1))
        model = finite_model(s)
        return {'model': model, 'result': analyze(metric_problem(s), model, s['bound'])}
    if family == 'pr_injectivity':
        return pr_certificate(s, meter)
    if family == 'literature':
        meter.tick()
        corpus = read(PACKAGE/'literature.json')
        return {'record': corpus.get(s['topic_id']), 'search_scope': 'frozen audited primary-source topic registry; not open-web novelty search'}
    if family == 'open':
        meter.tick()
        return {'reason': 'no deterministic proof consumer registered for this formal statement'}
    raise ValueError('unsupported mathematical tool')
