"""Hard gate: rebuild witness arithmetic independently of producer conclusions.

This is a small trusted mathematical kernel, not a general proof assistant.
No natural-language proof, citation or claimed status changes the decision.
"""
from fractions import Fraction as F
from itertools import combinations
from v4.core.geometry import independent_radius2, verify_ball
from v4.core.verify import verify_result
from v4.core.symmetry import metric2
from .polynomial import verify_sos, counterexample, BudgetExceeded
from .math_tools import metric_problem
from .io import PACKAGE, read


def outcome(status, reason, *, novelty='novelty-uncertain', nontrivial=True):
    return {'status': status, 'reason': reason, 'novelty': novelty, 'nontrivial': nontrivial,
            'scope': 'formal statement only; free-text interpretation is not certified'}


def verify_radius(s, e, meter):
    P, k = s['universe'], s['k']; rho2 = F(s['rho'])**2
    witness = e['witness']
    if witness is not None:
        I = witness['indices']
        if len(set(I)) != len(I) or I != sorted(I) or not k < len(I) <= s['max_size'] or any(type(i) is not int or not 0 <= i < len(P) for i in I):
            raise ValueError('radius witness binding')
        H = [P[i] for i in I]
        small = list(combinations(H, k))
        if len(witness['small']) != len(small):
            raise ValueError('all small subsets must be covered')
        for S, c in zip(small, witness['small']):
            meter.tick()
            if verify_ball(S, s['symmetry'], c) > rho2:
                raise ValueError('counterexample violates small-cover antecedent')
        if verify_ball(H, s['symmetry'], witness['full']) <= rho2:
            raise ValueError('not a dangerous whole set')
        return outcome('refuted', 'exact admissible planar radius counterexample')
    checked = 0; antecedents = 0
    for n in range(k+1, s['max_size']+1):
        for H in combinations(P, n):
            meter.tick()
            checked += 1
            small = max(independent_radius2(S, s['symmetry']) for S in combinations(H, k))
            if small <= rho2:
                antecedents += 1
                if independent_radius2(H, s['symmetry']) > rho2:
                    raise ValueError('producer omitted a counterexample')
    if checked != e['checked']:
        raise ValueError('incomplete finite search')
    if s['scope'] == 'finite-universe':
        return outcome('proved-in-project', 'exhaustive rational finite-universe implication only', nontrivial=antecedents > 0)
    return outcome('numerically-supported' if antecedents else 'unresolved',
                   'bounded exact search cannot prove all-planar witness completeness', nontrivial=antecedents > 0)


def verify_pr(s, e, meter):
    A = [list(map(F, a)) for a in s['design']]; q = s['q']; m = len(A)
    w = e['witness']
    if w is not None:
        if set(w) != {'x', 'z', 'y'} or len(w['x']) != 2 or len(w['z']) != 2 or len(w['y']) != m:
            raise ValueError('PR witness shape')
        x, z, y = [list(map(F, w[k])) for k in ('x', 'z', 'y')]
        if metric2(x, z, 'sign') == 0:
            raise ValueError('equivalent states are not a counterexample')
        for v in (x, z):
            if sum((a[0]*v[0]+a[1]*v[1])**2 != yi for a, yi in zip(A, y)) > q:
                raise ValueError('too many corruptions in alleged witness')
        return outcome('refuted', 'exact distinct sign classes share a transcript within each q budget', novelty='known')
    # Independent rank calculation over EVERY surviving subset and bipartition.
    def spans(T):
        return any(A[i][0]*A[j][1]-A[i][1]*A[j][0] != 0 for i, j in combinations(T, 2))
    count = 0
    for S in combinations(range(m), max(0, m-2*q)):
        count += 1
        for bits in range(1 << len(S)):
            meter.tick()
            U = [i for j, i in enumerate(S) if bits >> j & 1]
            V = [i for j, i in enumerate(S) if not bits >> j & 1]
            if not spans(U) and not spans(V):
                raise ValueError('2q survivor CP fails')
    if count != len(e['survivors']):
        raise ValueError('incomplete survivor trace')
    return outcome('proved-in-project', 'known real CP plus two-support-union theorem instantiated exactly', novelty='known')


def verify_cost(s, e, meter):
    M = e['model']
    if M['tolerance'] != s['tolerance'] or [w['target'] for w in M['worlds']] != s['worlds']:
        raise ValueError('world/tolerance binding')
    semantics = 'complete-finite-prior' if s['scope'] == 'finite-prior' else 'verified-restriction'
    if M['semantics'] != semantics or len(M['actions']) != len(s['parameters']):
        raise ValueError('completeness/menu binding')
    for j, a in enumerate(M['actions']):
        if a['cost'] != s['costs'][j] or a['parameter'] != s['parameters'][j]:
            raise ValueError('cost/action binding')
        u, v = map(F, a['parameter'])
        for w in M['worlds']:
            meter.tick()
            x, y = map(F, w['target'])
            value = (u-x)**2+(v-y)**2 if s['problem'] == 'range' else (u*x+v*y)**2
            if F(a['responses'][w['id']]['value']) != value:
                raise ValueError('reply is not a physical noiseless observation')
    verify_result(metric_problem(s), M, e['result'], s['bound'])
    raw = e['result']['exact_catalog_cost']; value = F(raw) if raw is not None else None
    b = F(s['bound']); rel = s['relation']
    holds = {'<=': value is not None and value <= b,
             '>=': value is None or value >= b,
             '==': value is not None and value == b}[rel]
    if s['scope'] == 'finite-prior':
        return outcome('proved-in-project' if holds else 'refuted', 'exact noiseless finite-prior minimax; no continuous completeness assertion')
    if rel == '>=' and holds:
        return outcome('proved-in-project', 'physically realizable finite restriction proves this continuous lower bound', nontrivial=b > 0)
    if rel in ('<=', '==') and (value is None or value > b):
        return outcome('refuted', 'finite restriction contradicts proposed continuous cost upper bound')
    return outcome('unresolved', 'finite restriction does not establish the proposed continuous conclusion')


def verify(family, s, evidence, meter):
    if family == 'radius':
        return verify_radius(s, evidence, meter)
    if family == 'pr_injectivity':
        return verify_pr(s, evidence, meter)
    if family == 'finite_cost':
        return verify_cost(s, evidence, meter)
    if family == 'polynomial':
        c = evidence['counterexample']
        recomputed = counterexample(s, evidence['sample_points'], meter)
        if recomputed != c:
            raise ValueError('rational search result/count does not match supplied points')
        if c['point'] is not None:
            checked = counterexample(s, [c['point']], meter)
            if checked['point'] is None or checked['value'] != c['value']:
                raise ValueError('inadmissible/incorrect rational counterexample')
            return outcome('refuted', 'exact negative value satisfying every polynomial constraint')
        if evidence['sos']:
            proof = verify_sos(s, evidence['sos'], meter)
            nonconstant = any(sum(map(int, k.split(','))) > 0 for k in s['polynomial'])
            nonempty = not s['constraints'] or c['admissible_checked'] > 0
            return outcome('proved-in-project', 'exact nonnegative weighted SOS identity on declared semialgebraic domain',
                           nontrivial=proof['nonzero'] and nonconstant and nonempty)
        return outcome('numerically-supported' if c['admissible_checked'] else 'unresolved',
                       'rational samples only; no valid positivity certificate', nontrivial=c['admissible_checked'] > 0)
    if family == 'literature':
        row = read(PACKAGE/'literature.json').get(s['topic_id'])
        if row != evidence['record']:
            raise ValueError('literature registry binding')
        # Status remains unresolved on the mathematical axis. Only novelty moves.
        return outcome('unresolved', 'audited topic match' if row else 'no audited topic match; absence is not originality',
                       novelty='known' if row else 'novelty-uncertain', nontrivial=row is not None)
    return outcome('unresolved', 'no proof consumer exists for this statement', nontrivial=False)
