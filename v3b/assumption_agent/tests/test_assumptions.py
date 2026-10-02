from copy import deepcopy
from fractions import Fraction as F
from pathlib import Path
import pytest
from v2.global_stability.certificate import scatter_bound
from v2.global_stability.exact import dataset
from v3b.assumption_agent.storage import read
from v3b.assumption_agent.certificates import build,frontier,geometry_data,zeta
from v3b.assumption_agent.verifier import verify_margin,verify_recovery,verify_frontier
from v3b.assumption_agent.contracts import deliver,preview,volume_ratio
from v3b.assumption_agent.policy import choose
from v3b.assumption_agent.simulator import make_episode,service,evaluate
from v3b.assumption_agent.experiments import theory_tasks
from v3b.assumption_agent.freeze import check

CFG=read(Path(__file__).parents[1]/'config.json')


def episode(name='healthy'):
    return make_episode(name,0,CFG,CFG['development_seed'])


@pytest.mark.parametrize('q',[0,1,2,3,4])
def test_zero_uncertainty_reduces_frozen_scatter(q):
    obs,_=episode(); data=dict(geometry_data(obs),radii=['0']*8)
    p,w,d=dataset(data); old=scatter_bound(p,w,d,q)
    assert verify_margin(build(data,q))==old['lower']


def test_nonzero_uncertainty_consumed_and_subsets_complete():
    obs,_=episode('anchor-uncertainty'); c=build(geometry_data(obs),1)
    assert 0<verify_margin(c)<F(c['nominal_scatter_lower'])
    c['subsets'].pop()
    with pytest.raises(ValueError,match='coverage'): verify_margin(c)


@pytest.mark.parametrize('field',['lower','scatter_lower','nominal_scatter_lower'])
def test_tampered_certificate_rejected(field):
    obs,_=episode(); c=build(geometry_data(obs),1); c[field]='99'
    with pytest.raises(ValueError): verify_margin(c)


def test_domain_containing_anchor_uses_scatter_not_derivative():
    obs,_=episode(); data=dict(geometry_data(obs),domain=['-6','6','-6','6'])
    c=build(data,0)
    assert not c['derivative']['available'] and verify_margin(c)>0


def test_zeta_retains_largest_clean_count():
    obs,_=episode(); obs['radii']=['1','2','3','4','5','6','7','8']
    assert zeta(obs,7)==8
    assert F('10.63')<zeta(obs,6)<F('10.64')  # sqrt(8^2+7^2), not two smallest radii
    assert zeta(obs,0)>zeta(obs,1)>zeta(obs,2)


def test_translation_and_uncertain_collinearity_counterexamples():
    cfg=dict(CFG,perturbation_trials=1); tasks=theory_tasks(cfg)
    a,b=tasks['counterexamples']
    assert a['range2_A']==a['range2_B'] and F(a['positive_uniform_lower'])>0
    assert F(a['position_difference2'])>0 and a['epsilon']=='0'
    assert F(b['nominal_lower'])>0 and F(b['upper'])==0


def test_full_profile_and_conditional_grid():
    obs,_=episode('q-uncertainty'); f=frontier(obs)
    assert f['rows'][-1]['q']==4 and f['q_cert']==2
    assert not f['all_contracts_certified']
    assert any(c['conditional_reduction'] for c in f['grid'])
    assert f['rows'][3]['lower']=='0'


def test_estimated_q_has_no_authority():
    obs,_=episode('q-uncertainty'); obs['estimated_corruption']=0
    d=choose(obs,'multi-step',CFG,2)
    assert d['action']!='recover' and d['kind']=='stronger-q-bound'


def test_unknown_upper_set_not_prediction():
    obs,_=episode(); obs.pop('q_max')
    with pytest.raises((ValueError,KeyError)): choose(obs,'multi-step',CFG,2)


def test_recovery_for_q_upper_set_with_actual_corruption():
    obs,_=episode('q-uncertainty'); obs['q_max']=1
    d=choose(obs,'multi-step',CFG,2)
    assert d['action']=='recover'; assert verify_recovery(obs,d)<=F(obs['error_tolerance'])
    bad=deepcopy(d); bad['error_bound']='0'
    with pytest.raises(ValueError): verify_recovery(obs,bad)


def test_anchor_error_cannot_use_naive_epsilon_gate():
    obs,_=episode('anchor-uncertainty'); f=frontier(obs)
    row=f['rows'][1]; b=F(row['lower']); E=F(obs['epsilon_max']); r=F(obs['error_tolerance'])
    assert 2*E/b<r and not row['certified']
    assert choose(obs,'multi-step',CFG,2)['kind']=='anchor-recalibration'


def test_service_receipt_and_calibration_nested():
    obs,private=episode('anchor-uncertainty'); offer=next(o for o in obs['offers'] if o['kind']=='anchor-recalibration')
    receipt=service(obs,offer,private); new=deliver(obs,offer,receipt)
    assert volume_ratio(obs,new)<1 and new['radii']==['1/100']*8
    receipt['issuer']='self-report'
    with pytest.raises(ValueError): deliver(obs,offer,receipt)
    bad=deepcopy(offer); bad['update']['radius']='1'
    with pytest.raises(ValueError): preview(obs,bad)


def test_domain_and_q_reductions_require_receipts():
    obs,private=episode('mixed-premises'); f=frontier(obs)
    assert not f['all_contracts_certified']
    for kind in ('tighter-domain','stronger-q-bound'):
        offer=next(o for o in obs['offers'] if o['kind']==kind)
        receipt=service(obs,offer,private); receipt['episode_id']='other'
        with pytest.raises(ValueError): deliver(obs,offer,receipt)


def test_positive_cost_and_budget_enforced():
    obs,_=episode('budget-limited'); d=choose(obs,'multi-step',CFG,2)
    assert d['action']!='recover'
    for o in obs['offers']:
        if F(o['cost'])>F(obs['budget']):
            with pytest.raises(ValueError): preview(obs,o)


def test_multistep_crosses_zero_geometry_plateau():
    obs,_=episode('geometry-plateau'); d=choose(obs,'multi-step',CFG,2)
    assert d['action']=='acquire-more-data' and len(d['plan']['ids'])==3 and d['plan']['certified']
    assert all(F(c['gain'])==0 for c in d['choices'])


def test_private_truth_forbidden():
    obs,_=episode(); obs['truth']=['0','0']
    with pytest.raises(ValueError,match='private'): choose(obs,'multi-step',CFG,2)


def test_prior_freeze(): assert check()==1417


def test_frontier_scalar_tamper_rejected():
    obs,_=episode(); f=frontier(obs); verify_frontier(obs,f)
    f['rows'][1]['epsilon_ceiling']='99'
    with pytest.raises(ValueError,match='scalar'): verify_frontier(obs,f)


def test_credible_issuer_name_cannot_certify_physical_truth():
    obs,private=episode('dishonest-calibration')
    offer=next(o for o in obs['offers'] if o['kind']=='anchor-recalibration')
    new=deliver(obs,offer,service(obs,offer,private))
    decision=choose(new,'multi-step',CFG,2)
    assert decision['action']=='recover' and verify_recovery(new,decision)>0
    ev=evaluate(new,private,decision)
    assert not ev['contract_valid'] and ev['wrong_output'] and ev['bound_violation']


def test_range_purchase_not_falsely_called_prior_volume_reduction():
    obs,_=episode('q-uncertainty'); new=preview(obs,obs['offers'][0])
    assert volume_ratio(obs,new)==1
    audit=next(o for o in obs['offers'] if o['kind']=='stronger-q-bound')
    assert volume_ratio(obs,preview(obs,audit))==F(1,2)
