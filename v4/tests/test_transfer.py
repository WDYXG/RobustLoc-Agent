from copy import deepcopy
from fractions import Fraction as F
from itertools import combinations
from pathlib import Path
import ast
import pytest
from v4.core.symmetry import discover,NEGATION
from v4.core.geometry import enclosing_ball,verify_ball
from v4.core.ambiguity import witnesses
from v4.core.decision import analyze
from v4.core.verify import verify_result
from v4.core.certificate import recover,verify_recovery
from v4.core.corruption import common_corrupted_transcript,residual_interval2
from v4.core.research import research_cycle,execute_policy
from v4.core.diagnostics import classify_pair,classify_scaling
from v4.experiments import (q_vs_2q,quotient_helly_search,origin_degeneracy,
    recovery_case,active_case,robust_active_case,validate_measurement_model)
from v4.problems.phase_retrieval import PhaseRetrieval,verify_acquisition
from v4.problems.range_localization import RangeLocalization


@pytest.mark.parametrize('problem',[RangeLocalization(),PhaseRetrieval([(1,0),(0,1),(1,1)])])
def test_verified_symmetry_family_not_current_design_gauge(problem):
    out=discover(problem)
    assert (NEGATION in out['accepted'])==(problem.symmetry=='sign')
    assert problem.verify_universal_symmetry(((1,0),(0,-1))) is False


def test_sign_equivalence_does_not_create_ambiguity_cost():
    p=PhaseRetrieval([(1,0),(0,1),(1,1)])
    model=dict(worlds=[dict(id='a',target=['1','2']),dict(id='b',target=['-1','-2'])],actions=[],tolerance='0',semantics='complete-finite-prior')
    out=analyze(p,model,'0'); assert out['exact_catalog_cost']=='0' and not out['witnesses']['edges']
    assert verify_result(p,model,out,'0')['passed']


def test_search_rejects_a_naive_literal_pr_state_space():
    p=PhaseRetrieval([(1,0),(0,1),(1,1)]); p.symmetry='identity'
    with pytest.raises(ValueError,match='quotient'): discover(p)


def test_q_versus_2q_exact_counterexample():
    c=q_vs_2q(); w=c['witness']; p=PhaseRetrieval(c['problem'])
    assert c['after_q_deletions'] and not c['after_2q_deletions'] and not p.equivalent(w['left'],w['right'])
    assert all(residual_interval2(p.observe(x),w['transcript']['values'],1)[1]==0 for x in (w['left'],w['right']))


def test_quotient_requires_four_world_witness_and_detects_truncation():
    h=quotient_helly_search(); p=PhaseRetrieval([(0,0)])
    m=dict(worlds=[dict(id=str(i),target=x) for i,x in enumerate(h['points'])],actions=[],tolerance=h['tolerance'],semantics='complete-finite-prior')
    assert not witnesses(p,m,max_size=3)['edges']
    out=analyze(p,m,'100'); assert len(out['witnesses']['edges'][0]['worlds'])==4
    assert out['interval']['lower_infinite'] and verify_result(p,m,out,'100')['passed']
    out['witnesses']['edges']=[]
    with pytest.raises(ValueError,match='witness'): verify_result(p,m,out,'100')


def test_origin_injectivity_does_not_imply_requested_margin():
    c=origin_degeneracy(); p=PhaseRetrieval(c['frame'],0,3)
    assert c['complement_property']['passed'] and p.verify_certificate(p.certificate(0),0)==0
    assert all(F(b['squared_ratio'])==F(a['squared_ratio'])/4 for a,b in zip(c['sequence'],c['sequence'][1:]))
    assert classify_scaling(p,p.scaling_certificate())['classification']=='local-scaling-degeneracy'
    annulus=PhaseRetrieval(c['frame'])
    with pytest.raises(ValueError): classify_scaling(annulus,p.scaling_certificate())


def test_diagnosis_and_feasible_catalog_keep_sign_distinct_from_bad_ambiguity():
    p=PhaseRetrieval([(1,0),(0,1)])
    assert classify_pair(p,['1','1'],['-1','-1'],0)['failure'] is False
    assert classify_pair(p,['1','1'],['1','-1'],0)['classification']=='measurement-design-ambiguity'
    t=dict(values=['1','1'],q=0,epsilon='0')
    filtered=p.feasible_worlds(t,[dict(id='a',target=['1','1']),dict(id='b',target=['2','2'])])
    assert [w['id'] for w in filtered['confirmed']]==['a'] and not filtered['unresolved']


@pytest.mark.parametrize('kind',['range','phase'])
@pytest.mark.parametrize('index',[0,1,2])
def test_common_q1_recovery_uses_continuous_margin(kind,index):
    p,t,c,w=recovery_case(kind,index,440051); out=recover(p,t,c)
    assert out['action']=='recover'
    b=verify_recovery(p,t,out)
    assert p.state_distance2(w['target'],out['position'])<=b*b
    out['radius_upper']='0'
    with pytest.raises(ValueError): verify_recovery(p,t,out)


@pytest.mark.parametrize('change',['q','design','row','lower','annulus'])
def test_pr_certificate_binding_and_all_survivors(change):
    p=PhaseRetrieval([(1,t) for t in (-2,-1,0,1,2)]); c=deepcopy(p.certificate(1))
    if change=='q': c['q']=0
    if change=='design': c['design'][0][0]='2'
    if change=='row': c['rows'].pop()
    if change=='lower': c['lower']='1000'
    if change=='annulus': c['min_norm']='0'
    with pytest.raises(ValueError): p.verify_certificate(c,1)


@pytest.mark.parametrize('kind',['range','phase'])
def test_same_research_loop_and_reply_only_policy(kind):
    p,t,c,m=active_case(kind,0,440051); validate_measurement_model(p,t,m)
    out=research_cycle(p,t,c,m,'2')
    assert len(out['stages'])==5 and out['decision']['interval']['cost_lower']=='1'
    for w in m['worlds']:
        result=execute_policy(m,out['decision'],lambda a:a['responses'][w['id']])
        assert result['action']=='recover' and p.state_distance2(result['position'],w['target'])<=F(result['radius2'])
    low=analyze(p,m,'0'); called=[]
    assert execute_policy(m,low,lambda a:called.append(a))['action']=='abstain' and not called


def test_restriction_never_promotes_finite_upper():
    p,t,c,m=active_case('phase',0,440051); m['semantics']='verified-restriction'
    r=analyze(p,m,'2'); assert r['interval']['cost_lower']=='1' and r['interval']['cost_upper'] is None
    assert r['interval']['state'].startswith('unresolved')
    with_upper=analyze(p,m,'2',external_upper='2')
    called=[]
    assert execute_policy(m,with_upper,lambda a:called.append(a))['reason']=='restriction-tree-is-not-a-continuous-policy' and not called


def test_new_measurements_keep_one_global_q_budget_and_full_menu():
    p,t,s,o,m,u,final=robust_active_case(0,440051)
    assert validate_measurement_model(p,t,m,o)['passed'] and len(u['actions'])==2
    assert verify_acquisition(p,o,1,t['epsilon'],t['tolerance'],u).design==final.design
    m['actions'].pop()
    with pytest.raises(ValueError,match='omitted'): validate_measurement_model(p,t,m,o)


def test_future_corruption_is_allowed_by_uniform_bound():
    p=PhaseRetrieval([(1,t) for t in (0,1,2,-1,3)]); x=['1','1']; values=[str(a) for a,b in p.observe(x)]
    values[-1]='-1000000'  # corruption is in a NEW observation, not original ones
    t=dict(values=values,q=1,epsilon='1/10000',tolerance='1/10')
    out=recover(p,t,[x,['1','-1']]); assert out['action']=='recover'
    verify_recovery(p,t,out)


def test_core_does_not_import_or_switch_on_problem_adapter():
    core=Path(__file__).resolve().parents[1]/'core'
    for file in core.glob('*.py'):
        tree=ast.parse(file.read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            if isinstance(node,ast.ImportFrom): assert 'problems' not in (node.module or '')
            if isinstance(node,ast.Constant) and isinstance(node.value,str): assert node.value not in ('real-phase-retrieval','range-localization')


def test_empty_feasible_catalog_does_not_authorize_free_recovery():
    p=PhaseRetrieval([(1,0)])
    with pytest.raises(ValueError): analyze(p,dict(worlds=[],actions=[],tolerance='1',semantics='complete-finite-prior'),'1')


def test_unknown_reply_abstains_without_fabricated_branch():
    p,t,c,m=active_case('phase',0,440051); d=analyze(p,m,'2')
    assert execute_policy(m,d,lambda a:dict(value='123456'))['reason']=='reply-outside-declared-model'


def test_grid_failure_and_zero_margin_are_not_impossibility():
    p,t,c,w=recovery_case('phase',0,440051)
    assert recover(p,t,[])['reason']=='candidate-search-incomplete'
    x=PhaseRetrieval([(1,0),(0,1)]); t=dict(values=['1','1'],q=0,epsilon='0',tolerance='1/10')
    assert recover(x,t,[['1','1']])['reason']=='margin-not-established'


@pytest.mark.parametrize('kind',['identity','sign'])
def test_radius_consumer_rejects_wrong_cover(kind):
    points=[['1','0'],['0','1'],['-1','0']]; b=enclosing_ball(points,kind)
    verify_ball(points,kind,b); b['radius2']='0'
    with pytest.raises(ValueError): verify_ball(points,kind,b)
