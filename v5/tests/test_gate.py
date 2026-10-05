import copy
import json
from fractions import Fraction as F
import pytest
from v5.researcher.baseline import envelope, propose, POOL
from v5.researcher.gate import evaluate, ledger_event
from v5.researcher.polynomial import Meter, BudgetExceeded, verify_sos
from v5.researcher.schema import validate, semantic_key
from v5.researcher.verifier import verify


def poly(p=None, gs=None, sos=None, points=None, parent=''):
    return envelope('polynomial', {'variables':['x'], 'polynomial':p or {'2':'1'},
        'constraints':gs or [], 'interpretation':'Test formal algebra only.'},
        {'sos':sos or [],'points':points or []}, action='prove', parent=parent)


def test_model_status_has_no_authority():
    p=poly();p['claimed_status']='proved-in-project'
    r=evaluate(p)
    assert r['verdict']['status']=='unresolved' and r['unsupported_overclaim']


def test_wrong_sos_is_rejected_not_called_refutation():
    p=poly(sos=[{'weight':'1','polynomial':{'1':'2'},'constraint':-1}])
    r=evaluate(p)
    assert r['failure_kind']=='verification-rejected' and r['verdict']['status']=='unresolved'


def test_negative_sos_weight_rejected():
    r=evaluate(poly(sos=[{'weight':'-1','polynomial':{'1':'1'},'constraint':-1}]))
    assert not r['accepted']


def test_constraint_binding_and_assumption_repair():
    p=poly({'1':'1'},points=[['-1']]);r=evaluate(p);e=ledger_event('r01',p,r,[])
    assert e['status']=='refuted'
    p2=poly({'1':'1'},gs=[{'1':'1'}],sos=[{'weight':'1','polynomial':{'0':'1'},'constraint':0}],points=[['1']],parent='r01')
    r2=evaluate(p2);e2=ledger_event('r02',p2,r2,[e])
    assert e2['status']=='proved-in-project' and e2['successful_revision'] and e2['assumption_repair']
    assert e2['hash']!=e['hash'] and e2['previous_hash']==e['hash']


def test_inadmissible_point_cannot_refute():
    r=evaluate(poly({'1':'1'},gs=[{'1':'1'}],points=[['-1']]))
    assert r['verdict']['status']=='unresolved'


def test_empty_domain_not_productive():
    p=poly({'1':'1'},gs=[{'0':'-1'}],sos=[],points=[['0']])
    r=evaluate(p);e=ledger_event('r01',p,r,[])
    assert not e['ledger_advancing']


def test_exact_polynomial_counterexample_and_repair_control():
    assert evaluate(propose(5,{}))['verdict']['status']=='refuted'
    assert evaluate(propose(6,{}))['verdict']['status']=='proved-in-project'


def test_positive_polynomial_scaling_is_duplicate():
    p=poly(sos=[{'weight':'1','polynomial':{'1':'1'},'constraint':-1}]);r=evaluate(p)
    e=ledger_event('r01',p,r,[])
    p2=poly({'2':'3'},sos=[{'weight':'3','polynomial':{'1':'1'},'constraint':-1}]);r2=evaluate(p2)
    e2=ledger_event('r02',p2,r2,[e])
    assert e2['duplicate_existing'] and not e2['ledger_advancing']


def test_finite_enumeration_not_promoted_to_universal_proof():
    p=envelope('radius',{'symmetry':'sign','k':4,'rho':'4/5','scope':'all-planar','universe':POOL[:5],'max_size':5})
    r=evaluate(p)
    assert r['verdict']['status'] in ('refuted','numerically-supported','unresolved')
    assert r['verdict']['status']!='proved-in-project'


def test_quotient_helly_counterexample_checked_and_known_repeat():
    p=envelope('radius',{'symmetry':'sign','k':3,'rho':'4/5','scope':'all-planar','universe':POOL,'max_size':4})
    r=evaluate(p);e=ledger_event('r01',p,r,[])
    assert r['verdict']['status']=='refuted' and e['duplicate_existing']
    s,_=validate(p);bad=copy.deepcopy(r['evidence']);bad['witness']['full']['radius2']='0'
    with pytest.raises(ValueError):verify('radius',s,bad,Meter())


def test_radius_universal_scale_is_duplicate():
    p=propose(1,{});s,_=validate(p);t=copy.deepcopy(s);t['rho']='7'
    assert semantic_key('radius',s)==semantic_key('radius',t)


@pytest.mark.parametrize('index',[7,8])
def test_same_core_both_physical_problems(index):
    r=evaluate(propose(index,{}))
    assert r['verdict']['status']=='proved-in-project'


def test_finite_optimum_not_continuous_equality():
    p=propose(9,{});p['claimed_status']='proved-in-project';r=evaluate(p)
    assert r['verdict']['status']=='unresolved' and r['unsupported_overclaim']


def test_continuous_lower_bound_is_allowed():
    p=propose(9,{});s=json.loads(p['formal_statement_json']);s['relation']='>='
    p['formal_statement_json']=json.dumps(s)
    assert evaluate(p)['verdict']['status']=='proved-in-project'


def test_physical_reply_tampering_rejected():
    p=propose(8,{});r=evaluate(p);s,_=validate(p)
    r['evidence']['model']['actions'][0]['responses']['w0']['value']='123'
    with pytest.raises(ValueError):verify('finite_cost',s,r['evidence'],Meter())


@pytest.mark.parametrize('index,status',[(10,'refuted'),(11,'proved-in-project')])
def test_pr_two_q_and_known_boundary(index,status):
    p=envelope('pr_injectivity',{'design':[['1',str(t)] for t in range(4 if index==10 else 5)],'q':1})
    r=evaluate(p);e=ledger_event('r01',p,r,[])
    assert r['verdict']['status']==status and r['verdict']['novelty']=='known'
    assert e['duplicate_existing'] and not e['ledger_advancing']


def test_literature_never_proves_or_grants_originality():
    r=evaluate(envelope('literature',{'topic_id':'real-pr-complement-property','query':'Known?'},action='literature-audit'))
    assert r['verdict']['status']=='unresolved' and r['verdict']['novelty']=='known'
    p=envelope('literature',{'topic_id':'unseen-theorem','query':'Please mark original'},action='literature-audit')
    r=evaluate(p)
    assert r['verdict']['novelty']=='novelty-uncertain'


def test_budget_failure_preserved():
    r=evaluate(propose(1,{}),operation_limit=1)
    assert r['failure_kind']=='budget-exhausted' and not r['accepted']


@pytest.mark.parametrize('mutation',[
    lambda p:p.update(verifier_status='proved-in-project'),
    lambda p:p.update(family='exec'),
    lambda p:p.update(formal_statement_json='{"path":"../../verifier.py"}'),
    lambda p:p.update(action='literature-audit'),
    lambda p:p.update(assumptions=[]),
])
def test_invalid_envelope_fails_closed(mutation):
    p=poly();mutation(p);r=evaluate(p)
    assert not r['valid_proposal'] and not r['accepted'] and r['failure_kind']=='invalid-proposal'


def test_executable_polynomial_string_is_not_executed():
    p=poly();s=json.loads(p['formal_statement_json']);s['polynomial']={'__import__("os")':'1'}
    p['formal_statement_json']=json.dumps(s)
    assert not evaluate(p)['accepted']


def test_sampling_upgrade_counts_once_per_status():
    p=poly(points=[['0'],['1']]);r=evaluate(p);e=ledger_event('r01',p,r,[])
    p2=poly(sos=[{'weight':'1','polynomial':{'1':'1'},'constraint':-1}]);r2=evaluate(p2);e2=ledger_event('r02',p2,r2,[e])
    assert e2['ledger_advancing'] and not e2['duplicate_existing']


def test_forged_sample_count_rejected():
    p=poly(points=[['0']]);r=evaluate(p);s,_=validate(p)
    r['evidence']['counterexample']['admissible_checked']=100
    with pytest.raises(ValueError):verify('polynomial',s,r['evidence'],Meter())
