from copy import deepcopy
from fractions import Fraction as F
from pathlib import Path
import pytest
from v3b.assumption_agent.storage import read
from v3c.trust_agent.simulator import make,service
from v3c.trust_agent.core import basis,recover,groups
from v3c.trust_agent.policy import choose,trust_frontier
from v3c.trust_agent.actions import apply
from v3c.trust_agent.verifier import verify_cover,verify_witness,feasible_world
from v3c.trust_agent.witnesses import find
from v3c.trust_agent.tasks import execute
from v3c.trust_agent.audit import verify_minimum
from v3c.trust_agent.freeze import check

CFG=read(Path(__file__).parents[1]/'config.json')


def episode(s='no-reference',i=0): return make(s,i,CFG,CFG['development_seed'])


@pytest.mark.parametrize('s',['no-reference','one-reference','two-reflection','frame-without-ranges'])
@pytest.mark.parametrize('i',[0,1,2])
def test_structural_diagnosis_uses_exact_continuous_worlds(s,i):
    obs,_=episode(s,i); w=find(obs,CFG)
    assert w is not None and verify_witness(obs,w)>F(obs['tolerance'])
    assert not recover(obs,CFG).get('certified')


def test_exact_negative_tasks_and_sparse_q1_positive():
    t=execute(CFG)
    for c in t['counterexamples']: assert verify_witness(c['observation'],c['witness'])>0
    assert t['counterexamples'][0]['identical_ordinary_ranges']==100
    pos=t['five_reference_q1']; assert verify_cover(pos['observation'],pos['certificate'])<=F('1/10')


def test_geometry_frame_without_target_edges_is_not_certificate():
    obs,_=episode('frame-without-ranges'); b=basis(obs)
    assert len(obs['hard_refs'])==3 and b['branches'][0]['model']['anchors']==[]


def test_source_union_cannot_delete_an_admissible_branch():
    obs,_=episode('two-source-ambiguity'); c=recover(obs,CFG)
    assert len(c['branches'])==2 and not c.get('certified')
    bad=deepcopy(c); bad['branches'].pop()
    with pytest.raises(ValueError,match='source deletion'): verify_cover(obs,bad)
    with pytest.raises(ValueError): verify_cover(obs,c)


def test_independent_majority_restores_conditional_continuous_cover():
    obs,_=episode('three-source-majority'); c=recover(obs,CFG)
    assert c['certified'] and verify_cover(obs,c)<=F(obs['tolerance'])
    assert sum(r['status']=='proved-empty' for r in c['branches'])==2


def test_aliases_count_as_one_failure_domain():
    obs,_=episode('aliases-one-domain')
    assert len(obs['reports'])==3 and len(groups(obs))==1
    assert not basis(obs)['pre_certified']
    d=choose(obs,'trust-directed',CFG,1)
    assert d['action']=='abstain'


def test_cheapest_source_redundancy_purchase_not_range():
    obs,_=episode('two-source-ambiguity'); f=trust_frontier(obs); verify_minimum(obs,f)
    assert f['minimum_sufficient_bundle']['ids']==['independent-source']
    assert F(f['minimum_sufficient_bundle']['cost'])==F('3/5')
    d=choose(obs,'trust-directed',CFG,1)
    assert d['kind']=='independent-source'


def test_structural_policy_acquires_absolute_trust_first():
    obs,_=episode(); d=choose(obs,'trust-directed',CFG,1)
    assert d['kind']=='absolute-reference' and d['diagnosis'].startswith('structural')
    assert d['frontier']['minimum_sufficient_bundle']['cost']=='18/5'


def test_precision_gap_buy_range_without_new_absolute_information():
    obs,_=episode('precision-gap'); d=choose(obs,'trust-directed',CFG,1)
    assert d['diagnosis']=='precision-or-certificate-gap' and d['kind']=='ordinary-range'


def test_baseline_does_not_fix_absolute_gauge():
    obs,p=episode(); offer=next(o for o in obs['offers'] if o['kind']=='baseline')
    new=apply(obs,offer,service(obs,offer,p))
    assert verify_witness(new,find(new,CFG))>F(new['tolerance'])
    assert not basis(new)['pre_certified']


def test_more_ordinary_ranges_do_not_turn_metadata_into_references():
    obs,p=episode()
    for offer in list(obs['offers']):
        if offer['kind']=='ordinary-range': obs=apply(obs,offer,service(obs,offer,p))
    assert len(obs['measurements'])==15 and obs['hard_refs']==[]
    assert verify_witness(obs,find(obs,CFG))>F(obs['tolerance'])


def test_no_claim_of_physical_truth_from_wrong_r_budget():
    obs,p=episode('premise-budget-violated'); c=recover(obs,CFG)
    assert c['certified'] and verify_cover(obs,c)>0
    assert not feasible_world(obs,dict(target=p['target'],positions=p['positions']))
    assert abs(float(F(c['position'][0])-F(p['target'][0])))>.7


def test_bounded_references_keep_model_error_floor():
    obs,_=episode('bounded-references'); b=basis(obs)
    assert not b['pre_certified'] and F(b['branches'][0]['zeta'])>0


def test_external_root_cannot_be_self_declared_in_receipt():
    obs,p=episode(); offer=next(o for o in obs['offers'] if o['kind']=='absolute-reference')
    reply=service(obs,offer,p); reply['points'][0]['root']='self-asserted'
    with pytest.raises(ValueError): apply(obs,offer,reply)


def test_minimum_frontier_requires_all_bundles():
    obs,_=episode('trust-budget-shortfall'); f=trust_frontier(obs); f['rows'].pop()
    with pytest.raises(ValueError,match='incomplete'): verify_minimum(obs,f)


def test_cover_radius_tampering_rejected():
    obs,_=episode('three-source-majority'); c=recover(obs,CFG); c['radius_upper']='0'
    with pytest.raises(ValueError,match='union'): verify_cover(obs,c)


def test_inconsistent_premises_can_be_refuted_not_validated():
    obs,_=episode('three-source-majority'); obs['r']=0
    d=choose(obs,'trust-directed',CFG,1)
    assert d['action']=='abstain' and d['diagnosis']=='inconsistent-declared-premises'


def test_zero_noise_exact_rational_case_and_point_output():
    obs,p=episode(); obs['epsilon']='0'; obs['r']=0
    obs['measurements']=[dict(anchor=i,value=str(16**.5 if i in ('a0','a1','a2') else 25**.5),weight='1') for i in p['positions']]
    obs['hard_refs']=[dict(anchor=i,centre=a,radius='0',root='external-position-instrument') for i,a in p['positions'].items()]
    c=recover(obs,CFG); assert c['certified'] and verify_cover(obs,c)==0


def test_solver_inputs_never_receive_private_world():
    obs,_=episode(); obs['truth']=['0','0']
    with pytest.raises(ValueError,match='private'): choose(obs,'trust-directed',CFG,1)


def test_previous_phases_immutable(): assert check()==2855
