from copy import deepcopy
from fractions import Fraction as F
from itertools import combinations
import json
from pathlib import Path
import pytest
from v2.global_stability.exact import sqrt_interval, point_upper, point, dataset
from v2.global_stability.certificate import build
from v2.global_stability.verifier import verify_certificate, verify_upper
from v2.global_stability.experiments import branch_search

DATA=json.loads((Path(__file__).parents[1]/'config.json').read_text())['data']

@pytest.mark.parametrize('value',['0','1','2','12345678901234567890/13','1/1000000000000000000000000000000000000000'])
def test_outward_sqrt_exact(value):
    v=F(value); lo,hi=sqrt_interval(v)
    assert lo*lo<=v<=hi*hi
    if v in [F(0),F(1)]: assert lo==hi

def test_positive_complete_cover_and_independent_scatter():
    c=build(DATA,0,divisions=8,delta='2',max_leaves=1024)
    result=verify_certificate(c)
    assert F(result['certified_lower'])>1
    assert F(result['raw_cover_lower'])>0
    assert result['unresolved_far_leaves']==0

def test_reject_missing_coverage_leaf():
    c=build(DATA,0,divisions=2,delta='2',max_leaves=16)
    c['leaves'].pop()
    with pytest.raises(ValueError,match='coverage'): verify_certificate(c)

@pytest.mark.parametrize('field',['certified_lower','raw_cover_lower','near_lower'])
def test_reject_forged_bound(field):
    c=build(DATA,2,divisions=1,max_leaves=4); c[field]='100'
    with pytest.raises(ValueError): verify_certificate(c)

def test_reject_missing_subset():
    c=build(DATA,1,divisions=1,max_leaves=2); c['scatter']['subsets'].pop()
    with pytest.raises(ValueError,match='subset completeness'): verify_certificate(c)

def test_exhausted_budget_retains_coverage_and_zero_raw_bound():
    c=build(DATA,2,divisions=2,max_leaves=1)
    r=verify_certificate(c)
    assert r['unresolved_far_leaves']==1 and F(r['raw_cover_lower'])==0
    assert F(r['scatter_lower'])>0

def test_global_certificate_can_contain_anchor():
    d=deepcopy(DATA); d['domain']=['-6','6','-6','6']
    r=verify_certificate(build(d,1,divisions=2,max_leaves=1))
    assert F(r['scatter_lower'])>0 and F(r['local_lower'])==0

def test_exact_reflection_zeros_not_floating_tolerance():
    a,w,_=dataset(DATA); x,z=point([0,'1/2']),point([0,'-1/2'])
    ub,equal=point_upper(a,w,x,z,3)
    assert ub==0 and equal==2
    assert point_upper(a,w,x,z,2)[0]>0

def test_c3_entire_domain_local_positive_but_global_zero():
    e=branch_search()
    assert e['status']=='refuted' and F(e['local_lower'])>0
    assert e['witness']['upper']=='0' and e['witness']['equal_coordinates']==3

def test_declared_float_input_rejected():
    d=deepcopy(DATA); d['weights'][0]=1.0
    with pytest.raises(TypeError): build(d,0)

def test_uniform_geometric_scaling():
    d=deepcopy(DATA); scale=F(7,3)
    d['anchors']=[[str(F(v)*scale) for v in p] for p in d['anchors']]
    d['domain']=[str(F(v)*scale) for v in d['domain']]
    a=build(DATA,1,divisions=1,max_leaves=1)['scatter']['lower2']
    b=build(d,1,divisions=1,max_leaves=1)['scatter']['lower2']
    assert F(a)==F(b)

def test_invalid_candidate_upper_outside_workspace():
    with pytest.raises(ValueError,match='outside D'):
        verify_upper(DATA,0,dict(x=['2','0'],z=['0','0'],upper='0',equal_coordinates=0))

def test_empty_survivor_budget_zero():
    r=verify_certificate(build(DATA,4,divisions=1,max_leaves=1))
    assert r['certified_lower']=='0'
