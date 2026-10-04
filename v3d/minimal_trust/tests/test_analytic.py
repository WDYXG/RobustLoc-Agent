from copy import deepcopy
from fractions import Fraction as F
import pytest
from v3d.minimal_trust.analytic import make_case,verify_completeness,analyze_case


@pytest.mark.parametrize('index',[0,1,2])
def test_nonzero_continuous_cost_equality_requires_complete_reduction(index):
    obs,m,c=make_case(index); d=analyze_case(obs,m,c,'10')
    assert verify_completeness(obs,m,c)['passed']
    assert F(d['interval']['cost_lower'])==7*F(c['h'])/5
    assert d['interval']['gap']=='0' and d['interval']['cost_lower']==d['interval']['cost_upper']


@pytest.mark.parametrize('change',['noise','radius','missing-world','wrong-range'])
def test_sampled_or_perturbed_worlds_cannot_claim_continuous_completeness(change):
    obs,m,c=make_case(0)
    if change=='noise': obs['epsilon']='1/1000000'
    if change=='radius': obs['hard_refs'][-1]['radius']='201/100'
    if change=='missing-world': m['worlds'].pop()
    if change=='wrong-range': obs['measurements'][-1]['value']='299/100'
    with pytest.raises(ValueError): verify_completeness(obs,m,c)
