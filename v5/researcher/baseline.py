"""Predefined coverage policy, frozen before either policy runs.

It receives the identical state but intentionally does not adapt to feedback.
It covers the open frontier, including a preset repair and lower-bound fallback.
No access to the Codex prompts, outputs or run files.
"""
from .io import canonical

POOL = [['1','0'],['0','1'],['3/5','4/5'],['-4/5','3/5'],['4/5','3/5'],['-3/5','4/5']]


def envelope(family, statement, request=None, action='experiment', claim='Test one formal proposition', parent=''):
    return {'research_question': claim, 'claim': claim,
            'assumptions': ['Exactly the assumptions encoded in formal_statement_json.'],
            'why_this_matters': 'Advance or delimit a current mathematical frontier under a bounded check.',
            'action': action, 'verification_plan': ['Use the registered exact consumer; retain failures.'],
            'possible_failure_mode': 'Finite evidence may not justify a universal conclusion.',
            'stop_condition': 'Stop at the per-round tool budget and accept only the verifier disposition.',
            'family': family, 'formal_statement_json': canonical(statement),
            'evidence_request_json': canonical(request or {}), 'claimed_status': 'conjectured', 'parent_id': parent}


def propose(index, state):
    if index in (1, 2, 3, 4):
        symmetry, k = 'sign', (5 if index == 3 else 4)
        return envelope('radius', {'symmetry':symmetry, 'k':k, 'rho':'3/4' if index == 2 else '4/5',
                                  'scope':'finite-universe' if index == 4 else 'all-planar',
                                  'universe':POOL, 'max_size':k+1}, action='refute',
                        claim=f'Are all {k}-point covers sufficient for a planar {symmetry} cover?')
    if index in (5, 6):
        c = 2 if index == 5 else 3
        # c(u^2+v^2)^2 - (2uv+v^2)^2 >= 0, related to intensity perturbations.
        p = {'4,0':str(c), '2,2':str(2*c-4), '1,3':'-4', '0,4':str(c-1)}
        sos = [] if c == 2 else [
            {'weight':'3', 'polynomial':{'2,0':'1'}, 'constraint':-1},
            {'weight':'2', 'polynomial':{'1,1':'1','0,2':'-1'}, 'constraint':-1}]
        return envelope('polynomial', {'variables':['u','v'], 'polynomial':p, 'constraints':[],
                         'interpretation':'A scalar algebraic envelope for the intensity increment 2uv+v^2; physical mapping not certified.'},
                        {'sos':sos, 'points':[['1','1'],['0','1'],['1','0']]},
                        action='prove' if c == 3 else 'refute', claim=f'Constant {c} bounds the squared scalar intensity increment.')
    if index in (7, 8, 9, 11):
        return envelope('finite_cost', {'problem':'range' if index == 7 else 'pr',
            'worlds':[['0','1'],['0','-1']] if index == 7 else [['1','1'],['1','-1']],
            'parameters':[['0','3'],['0','-3']] if index == 7 else [['1','1'],['1','-1']],
            'costs':['1','2'], 'tolerance':'1/10', 'relation':'>=' if index == 11 else '==', 'bound':'1',
            'scope':'continuous' if index in (9,11) else 'finite-prior'}, action='prove',
            claim='The declared noiseless information cost is at least one.' if index == 11 else 'The declared noiseless information cost equals one.',
            parent='r09' if index == 11 else '')
    if index == 10:
        return envelope('polynomial', {'variables':['u','v'],
            'polynomial':{'4,0':'2','1,3':'-4','0,4':'1'},'constraints':[{'1,1':'-1'}],
            'interpretation':'Preset repair: require uv<=0 for the scalar intensity-increment bound.'},
            {'sos':[{'weight':'2','polynomial':{'2,0':'1'},'constraint':-1},
                    {'weight':'1','polynomial':{'0,2':'1'},'constraint':-1},
                    {'weight':'4','polynomial':{'0,1':'1'},'constraint':0}], 'points':[['1','-1']]},
            action='prove',claim='Constant two suffices under the explicit sign restriction uv<=0.',parent='r05')
    return envelope('literature', {'topic_id':'quotient-general-witness-number', 'query':'Does existing literature settle a general sign-quotient witness bound?'},
                    action='literature-audit', claim='Audit the unresolved general quotient-witness literature boundary.')
