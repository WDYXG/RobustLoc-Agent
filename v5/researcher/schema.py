"""Strict envelope plus typed formal claims. Free text is never a theorem."""
from .polynomial import rational, parse, encoded
from .io import canonical, digest

ACTIONS = ['prove', 'refute', 'literature-audit', 'experiment', 'generalize']
STATUSES = ['conjectured', 'proved-in-project', 'refuted', 'numerically-supported', 'unresolved', 'known']
FAMILIES = ['radius', 'polynomial', 'finite_cost', 'pr_injectivity', 'literature', 'open']
TEXT = ['research_question', 'claim', 'why_this_matters', 'possible_failure_mode', 'stop_condition',
        'formal_statement_json', 'evidence_request_json', 'parent_id']


def output_schema():
    props = {k: {'type': 'string'} for k in TEXT}
    props.update({k: {'type': 'array', 'items': {'type': 'string'}}
                  for k in ('assumptions', 'verification_plan')})
    props.update(action={'type': 'string', 'enum': ACTIONS}, family={'type': 'string', 'enum': FAMILIES},
                 claimed_status={'type': 'string', 'enum': STATUSES})
    return {'type': 'object', 'properties': props, 'required': list(props), 'additionalProperties': False}


def fields(obj, required):
    if not isinstance(obj, dict) or set(obj) != set(required.split()):
        raise ValueError('fields must be exactly: ' + required)


def integer(x, lo, hi):
    if type(x) is not int or not lo <= x <= hi:
        raise ValueError(f'integer in [{lo}, {hi}] required')
    return x


def points(xs, lo=1, hi=8):
    if not isinstance(xs, list) or not lo <= len(xs) <= hi:
        raise ValueError('point count limit')
    out = []
    for x in xs:
        if not isinstance(x, list) or len(x) != 2:
            raise ValueError('planar rational point required')
        out.append(list(map(lambda v: str(rational(v)), x)))
    return out


def normalize(family, s):
    if family == 'radius':
        fields(s, 'symmetry k rho scope universe max_size')
        if s['symmetry'] not in ('identity', 'sign') or s['scope'] not in ('all-planar', 'finite-universe'):
            raise ValueError('radius scope/symmetry')
        s = dict(s, universe=points(s['universe'], 2, 8), rho=str(rational(s['rho'])))
        integer(s['k'], 1, 5); integer(s['max_size'], s['k']+1, 6)
        if rational(s['rho']) <= 0 or len(s['universe']) < s['max_size']:
            raise ValueError('positive radius, enough universe points')
        s['universe'] = sorted(s['universe'], key=canonical)
        if len({canonical(x) for x in s['universe']}) != len(s['universe']):
            raise ValueError('distinct universe representatives required')
    elif family == 'polynomial':
        fields(s, 'variables polynomial constraints interpretation')
        v = s['variables']
        if not isinstance(v, list) or not 1 <= len(v) <= 4 or any(not isinstance(x, str) or not x.isidentifier() for x in v) or len(set(v)) != len(v):
            raise ValueError('one to four unique variable names')
        if not isinstance(s['constraints'], list) or len(s['constraints']) > 4 or not isinstance(s['interpretation'], str):
            raise ValueError('polynomial constraints/interpretation')
        s = dict(s, polynomial=encoded(parse(s['polynomial'], len(v))),
                 constraints=[encoded(parse(g, len(v))) for g in s['constraints']])
    elif family == 'finite_cost':
        fields(s, 'problem worlds parameters costs tolerance relation bound scope')
        if s['problem'] not in ('range', 'pr') or s['relation'] not in ('<=', '>=', '==') or s['scope'] not in ('finite-prior', 'continuous'):
            raise ValueError('finite cost contract')
        s = dict(s, worlds=points(s['worlds'], 2, 6), parameters=points(s['parameters'], 1, 4),
                 costs=list(map(lambda x: str(rational(x)), s['costs'])),
                 tolerance=str(rational(s['tolerance'])), bound=str(rational(s['bound'])))
        if len(s['costs']) != len(s['parameters']) or any(rational(c) <= 0 for c in s['costs']) or min(rational(s['bound']), rational(s['tolerance'])) < 0:
            raise ValueError('positive action costs; nonnegative tolerance and bound')
    elif family == 'pr_injectivity':
        fields(s, 'design q')
        s = dict(s, design=points(s['design'], 1, 7))
        integer(s['q'], 0, len(s['design']))
    elif family == 'literature':
        fields(s, 'topic_id query')
        if not all(isinstance(x, str) for x in s.values()):
            raise ValueError('literature text fields')
    elif family == 'open':
        fields(s, 'statement')
        if not isinstance(s['statement'], str) or not s['statement'].strip():
            raise ValueError('open statement required')
    else:
        raise ValueError('unsupported formal family')
    return s


def validate(proposal):
    import json
    schema = output_schema()
    if not isinstance(proposal, dict) or set(proposal) != set(schema['required']):
        raise ValueError('proposal fields do not match envelope')
    if len(canonical(proposal)) > 40000:
        raise ValueError('proposal exceeds size budget')
    for k in TEXT:
        if not isinstance(proposal[k], str):
            raise ValueError('text field ' + k)
        if k != 'parent_id' and not proposal[k].strip():
            raise ValueError('empty ' + k)
    for k in ('assumptions', 'verification_plan'):
        if not isinstance(proposal[k], list) or not 1 <= len(proposal[k]) <= 12 or any(not isinstance(x, str) or not x.strip() for x in proposal[k]):
            raise ValueError('nonempty bounded string list: ' + k)
    if proposal['action'] not in ACTIONS or proposal['claimed_status'] not in STATUSES:
        raise ValueError('action/status enum')
    s = normalize(proposal['family'], json.loads(proposal['formal_statement_json']))
    evidence = json.loads(proposal['evidence_request_json'])
    if not isinstance(evidence, dict):
        raise ValueError('evidence object required')
    if (proposal['family'] == 'literature') != (proposal['action'] == 'literature-audit'):
        raise ValueError('literature audit must be its own single claim')
    return s, evidence


def semantic_key(family, s):
    # A heuristic canonicalizer, NOT an oracle for logical equivalence.
    import copy
    s = copy.deepcopy(s)
    if family == 'radius' and s['scope'] == 'all-planar':
        s = {k: s[k] for k in ('symmetry', 'k', 'scope')}
        # Positive radius scales out of a universal planar statement.
    if family == 'polynomial':
        s.pop('interpretation')
        s['variables'] = list(range(len(s['variables'])))
        for p in [s['polynomial']] + s['constraints']:
            if p:
                scale = abs(rational(next(iter(p.values()))))
                for e in p:
                    p[e] = str(rational(p[e])/scale)
        s['constraints'].sort(key=canonical)
    if family == 'pr_injectivity':
        s['design'].sort(key=canonical)
    if family == 'literature':
        s.pop('query')
    return digest([family, s])
