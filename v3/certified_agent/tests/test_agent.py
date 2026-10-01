from copy import deepcopy
from fractions import Fraction as F
from pathlib import Path
import json
import pytest
from v3.freeze import check
from v3.certified_agent.simulator import make_episode,acquire,contract
from v3.certified_agent.policy import decide,plan
from v3.certified_agent.certificates import geometry,data_from,residual_certificate
from v3.certified_agent.evaluation import execute
from v3.certified_agent.verifier import verify_record,verify_learning
from v3.certified_agent.learning import train

CFG=json.loads((Path(__file__).parents[1]/'config.json').read_text())

def episode(name): return make_episode(name,0,CFG,seed=10103)

def test_entire_historical_freeze(): assert check()==248

def test_recovery_requires_geometry_and_feasibility():
    e=episode('healthy'); pool={}; r=execute(e,CFG,None,'passive-certified',pool)
    assert r['outcome']['certified'] and not r['outcome']['wrong_output']
    assert verify_record(r,pool,CFG)['certified_outputs']==1

def test_advisory_q_hint_cannot_change_authorized_action():
    obs=episode('healthy')['observation']; a=decide(obs,CFG,mode='passive-certified')
    new=deepcopy(obs); new['estimated_corruption']=99
    b=decide(new,CFG,mode='passive-certified')
    assert a['action']==b['action'] and a['error_bound']==b['error_bound']

def test_missing_q_budget_never_uses_hint_to_recover():
    obs=episode('missing-q-budget')['observation']; obs['estimated_corruption']=0
    assert decide(obs,CFG)['action']=='abstain'

def test_one_new_anchor_not_sufficient_under_q1():
    e=episode('new-report-corrupted'); obs=e['observation']; q=obs['q_budget']
    assert F(geometry(data_from(obs),q)['upper'])==0
    after=acquire(obs,e['private'],obs['available_anchors'][0])
    assert F(geometry(data_from(after),q)['upper'])==0

def test_lookahead_crosses_zero_immediate_gain_plateau():
    obs=episode('new-report-corrupted')['observation']
    assert plan(obs,CFG,'greedy-certified') is None
    proposal=plan(obs,CFG,'active-certified')
    assert proposal and len(proposal['plan'])==3
    assert F(proposal['immediate_lower'])==0 and F(proposal['projected_lower'])>=F('1/5')

def test_actual_acquisition_then_recertification_with_corrupted_new_report():
    e=episode('new-report-corrupted'); pool={}; r=execute(e,CFG,None,'active-certified',pool)
    assert r['outcome']['acquisitions']==3 and r['outcome']['certified']
    assert r['final_contract']['valid'] and r['private_final']['new_bad_position']
    assert r['outcome']['strict_mu_improvement']
    assert verify_record(r,pool,CFG)['verified']

def test_single_acquisition_strictly_improves_q0_margin():
    pool={}; r=execute(episode('collinear-q0'),CFG,None,'active-certified',pool)
    assert r['outcome']['acquisitions']==1 and r['outcome']['strict_mu_improvement']
    assert r['outcome']['certified']

def test_budget_exhausted_is_recorded_not_forced_output():
    pool={}; r=execute(episode('budget-limited'),CFG,None,'active-certified',pool)
    assert not r['outcome']['output'] and r['outcome']['acquisitions']<=1
    assert verify_record(r,pool,CFG)['verified']

def test_good_geometry_with_infeasible_search_does_not_recover():
    obs=episode('healthy')['observation']; obs['available_anchors']=[]
    bad=dict(position=['0','0'],feasibility=dict(feasible=False),search_complete=False)
    dec=decide(obs,CFG,mode='passive-certified',candidate=bad)
    assert dec['action']=='abstain' and 'search incomplete' in dec['reason']

def test_consumer_rejects_forged_certified_position():
    pool={}; r=execute(episode('healthy'),CFG,None,'passive-certified',pool)
    r['trace'][-1]['decision']['candidate']['position']=['0','0']
    with pytest.raises(ValueError): verify_record(r,pool,CFG)

def test_consumer_rejects_changed_weights():
    pool={}; r=execute(episode('healthy'),CFG,None,'passive-certified',pool)
    r['trace'][0]['observation']['weights'][0]='1000'
    r['initial_observation']['weights'][0]='1000'
    r['final_observation']['weights'][0]='1000'
    with pytest.raises(ValueError,match='weight contract'): verify_record(r,pool,CFG)

def test_truth_never_accepted_by_agent_or_decoder():
    obs=episode('healthy')['observation']; obs['truth']=['0','0']
    with pytest.raises(ValueError,match='Private'): decide(obs,CFG)

def test_invalid_prior_is_out_of_contract_not_a_certificate_success():
    e=episode('outside-domain'); assert not contract(e['observation'],e['private'])['valid']
    assert not contract(e['observation'],e['private'])['true_inside']

def test_noisy_budget_violation_kept_separate():
    e=episode('over-noise-budget'); assert not contract(e['observation'],e['private'])['noise_ok']

def test_predictor_preserves_unknown_and_heldout_geometry_separation():
    cfg=deepcopy(CFG); cfg['training_layouts']=24; cfg['model_test_layouts']=12
    cfg['train_seed']=120010; cfg['model_test_seed']=120020
    e=train(cfg); train_ids={r['layout_id'] for r in e['train_rows']}
    assert train_ids.isdisjoint(r['layout_id'] for r in e['test_rows'])
    assert verify_learning(e,cfg)['verified']

def test_residual_feasibility_quantized_position_is_not_float_tolerance():
    obs=episode('healthy')['observation']; c=residual_certificate(obs,['0','0'],1)
    assert not c['feasible'] and F(c['norm2_upper'])>F(obs['epsilon'])**2

def test_capacity_lower_does_not_claim_uncomputed_maximum():
    obs=episode('healthy')['observation']; dec=decide(obs,CFG,mode='passive-certified')
    assert dec['conditional_profile']['profile_max_q']==CFG['q_profile_max']
    assert 'actual q not inferred' in dec['conditional_profile']['scope']
