from copy import deepcopy
from fractions import Fraction as F
from pathlib import Path
import pytest
from v3b.assumption_agent.storage import read
from v3c.trust_agent.simulator import make,service
from v3c.trust_agent.actions import apply
from v3c.trust_agent.core import basis
from v3d.minimal_trust.subsets import recover_subsets,uniform_upper
from v3d.minimal_trust.subset_verify import verify_subset_cover,verify_uniform_upper
from v3d.minimal_trust.agent import continuous_decision

CFG=read(Path(__file__).resolve().parents[3]/'v3c/trust_agent/config.json')


def case(): return make('bounded-references',0,CFG,CFG['development_seed'])


def delivered():
    obs,p=case(); u=uniform_upper(obs)
    for oid in u['offers']:
        o=next(o for o in obs['offers'] if o['id']==oid); obs=apply(obs,o,service(obs,o,p))
    return obs,u


def test_compulsory_cost_3_6_regression_is_automatic():
    initial,_=case(); obs,u=delivered()
    assert F(u['cost_upper'])<=F('18/5') and verify_uniform_upper(initial,u)==F('18/5')
    assert not basis(obs)['pre_certified']
    c=recover_subsets(obs,CFG)
    assert c['certified'] and verify_subset_cover(obs,c)<F('12/1000')
    assert c['branches'][0]['measurement_indices']==[0,1,2]
    assert c['search']['subset_enumeration_complete']


def test_search_limit_reports_unknown_and_does_not_invent_impossibility():
    obs,_=case(); u=uniform_upper(obs,node_limit=0); c=recover_subsets(obs,CFG,node_limit=0)
    assert u['cost_upper'] is None and not u['search']['complete']
    assert not c['certified'] and not c['search']['subset_enumeration_complete']
    d=continuous_decision(obs,CFG,'2',node_limit=1)
    assert d['interval']['state'].startswith('unresolved') and not d['interval']['lower_infinite']


def test_added_low_quality_coordinate_can_be_ignored():
    obs,u=delivered(); c=recover_subsets(obs,CFG)
    extra=deepcopy(obs); extra['measurements'].append(deepcopy(obs['measurements'][3]))
    assert verify_subset_cover(extra,c)==verify_subset_cover(obs,c)


def test_arbitrary_coordinate_subset_can_omit_repeat_of_a_selected_anchor():
    obs,_=delivered(); obs['measurements'].append(deepcopy(obs['measurements'][0]))
    c=recover_subsets(obs,CFG,node_limit=1)
    assert c['certified'] and not c['search']['subset_enumeration_complete']
    assert c['branches'][0]['measurement_indices']==[0,1,2]
    assert verify_subset_cover(obs,c)<F('12/1000')


def test_duplicate_indices_cannot_forge_corruption_redundancy():
    obs,_=delivered(); c=recover_subsets(obs,CFG); c['branches'][0]['measurement_indices']=[0,0,2]
    with pytest.raises(ValueError,match='duplicate'): verify_subset_cover(obs,c)


def test_every_source_branch_must_be_covered():
    obs,_=make('three-source-majority',0,CFG,CFG['development_seed']); c=recover_subsets(obs,CFG)
    assert verify_subset_cover(obs,c)<=F(obs['tolerance'])
    c['branches'].pop()
    with pytest.raises(ValueError,match='source union'): verify_subset_cover(obs,c)


def test_actual_bound_and_uniform_geometry_binding_tampering_rejected():
    initial,_=case(); obs,u=delivered(); c=recover_subsets(obs,CFG); c['radius_upper']='0'
    with pytest.raises(ValueError,match='unsafe'): verify_subset_cover(obs,c)
    u['initial_geometry_certificate']['data']['radii'][0]='0'
    with pytest.raises(ValueError,match='initial uncertainty'): verify_uniform_upper(initial,u)


def test_soft_sources_have_explicit_unsupported_uniform_family():
    obs,_=make('two-source-ambiguity',0,CFG,CFG['development_seed']); u=uniform_upper(obs)
    assert u['cost_upper'] is None and 'soft-source' in u['reason']


def test_positive_continuous_gap_not_equal_finite_optimum():
    obs,_=case()
    for a in obs['hard_refs']: a['radius']='1/5'
    obs['tolerance']='1/20'
    d=continuous_decision(obs,CFG,'2')
    assert d['interval']['cost_lower']=='1' and d['interval']['cost_upper']=='18/5'
    assert d['interval']['gap']=='13/5' and d['interval']['state'].startswith('unresolved')
