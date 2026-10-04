from copy import deepcopy
from fractions import Fraction as F
import pytest
from v3d.minimal_trust.finite import minimum_enclosing_circle,analyze
from v3d.minimal_trust.finite_verify import verify,dangerous
from v3d.minimal_trust.worlds import finite_case,validate_restriction
from v3d.minimal_trust.agent import diagnose


def case(kind): return finite_case(kind,0,430051)


def test_triple_witness_needed_when_every_pair_fits():
    obs,m=case('acute-triple'); a=analyze(m)
    assert a['pair_count']==0 and a['triple_count']==1
    assert a['pair_batch']['cost']=='0' and a['adaptive_cost']=='1'
    assert F(minimum_enclosing_circle([w['target'] for w in m['worlds']])['radius2'])==F(169,144)
    assert verify(m,a)['passed']


def test_global_hitting_cost_is_not_adaptive_lower():
    obs,m=case('adaptive-four'); a=analyze(m)
    assert a['hypergraph_batch']['cost']=='3' and a['adaptive_cost']=='2' and a['incident_lower']=='2'
    assert validate_restriction(obs,m)['responses']==12 and verify(m,a)['passed']


@pytest.mark.parametrize('kind',['near-cluster','unseparable-reflection','simple-pair','expensive-pair'])
def test_exact_finite_world_results_independently_consumed(kind):
    obs,m=case(kind); a=analyze(m); assert verify(m,a)['passed']


def test_empty_model_is_not_free_recovery():
    with pytest.raises(ValueError,match='nonempty'): analyze(dict(worlds=[],actions=[],tolerance='1'))


@pytest.mark.parametrize('points,expected',[
    ([['0','0']],'0'),([['0','0'],['0','0']],'0'),
    ([['-2','0'],['0','0'],['2','0']],'4'),
    ([['0','0'],['4','0'],['1','1']],'4')])
def test_degenerate_and_obtuse_mec(points,expected):
    assert minimum_enclosing_circle(points)['radius2']==expected


def test_false_tree_leaf_and_missing_child_are_rejected():
    _,m=case('adaptive-four'); a=analyze(m); b=deepcopy(a)
    b['optimal_tree']['children'].pop(next(iter(b['optimal_tree']['children'])))
    with pytest.raises(ValueError,match='reply coverage'): verify(m,b)
    b=deepcopy(a); b['adaptive_cost']='1'
    with pytest.raises(ValueError,match='adaptive optimum'): verify(m,b)


def test_no_missing_action_in_continuous_lower_restriction():
    obs,m=case('adaptive-four'); m['actions'].pop()
    with pytest.raises(ValueError,match='incomplete menu'): validate_restriction(obs,m)


def test_forged_world_reply_rejected():
    obs,m=case('simple-pair'); m['actions'][0]['responses']['w0']['points'][0]['centre']=['100','100']
    with pytest.raises(ValueError,match='nonphysical'): validate_restriction(obs,m)


def test_three_states_and_unknown_upper_are_not_infinity():
    assert diagnose('2','3','1')['state'].startswith('provably')
    assert diagnose('1','3','3')['state']=='certifiably-recoverable'
    d=diagnose('1',None,'2'); assert d['state'].startswith('unresolved') and not d['lower_infinite']
    assert diagnose('0','0','0')['gap']=='0'
    with pytest.raises(ValueError,match='inconsistent'): diagnose('2','1','4')
    with pytest.raises(ValueError,match='inconsistent'): diagnose('0','1','4',lower_infinite=True)
