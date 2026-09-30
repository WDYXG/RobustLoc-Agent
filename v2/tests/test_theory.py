from itertools import combinations
import numpy as np
import pytest
from v2.geometry import margin,directions,point_margin,curvature_bound,beta
from v2.verifier import independent_margin,check_estimate
from v2.experiments import erasure_witness,nonlinear_witnesses,ratio_counterexample
from v2.estimator import Problem,select

def test_weighted_2d_formula_against_eigenvalues():
    rng=np.random.default_rng(17)
    for _ in range(20):
        angles=rng.uniform(-np.pi,np.pi,7); u=np.column_stack([np.cos(angles),np.sin(angles)]); w=rng.uniform(.2,3,7)
        for k in range(4):
            exact=min(np.linalg.eigvalsh((u[list(ix)]*np.sqrt(w[list(ix)])[:,None]).T@(u[list(ix)]*np.sqrt(w[list(ix)])[:,None]))[0] for ix in combinations(range(7),7-k))
            assert margin(u,w,k)['alpha']==pytest.approx(exact,abs=1e-12)

def test_degenerate_antipodal_directions_and_budget():
    u=np.array([[1.,0],[-1,0],[1,0]])
    assert margin(u,np.ones(3),0)['alpha']==0
    assert margin(u,np.ones(3),2)['alpha']==0
    with pytest.raises(ValueError): margin(u,np.array([1.,0,1]),0)
    with pytest.raises(ValueError): directions([0,0],np.array([[0.,0],[1,0]]))

def test_exact_support_split_and_nonlinear_reflection():
    assert erasure_witness()['verified']
    result=nonlinear_witnesses()
    assert result['global_reflection']['verified'] and result['l1_failure']['verified']
    assert result['global_reflection']['difference_support']==1

def test_feasibility_precedes_geometry_and_verifier_rejects_tampering():
    angles=np.arange(8)*np.pi/4; anchors=10*np.column_stack([np.cos(angles),np.sin(angles)])
    problem=Problem(anchors,np.full(8,10.),np.ones(8),1,.001,np.zeros(2),.1)
    pool=[np.zeros(2),np.array([.09,0])]
    result=select(problem,pool)
    assert np.linalg.norm(result['position'])==0 and check_estimate(problem,result)['verified']
    result['trimmed_norm']=1.
    assert not check_estimate(problem,result)['verified']

def test_geometry_certification_abstains_on_nonrobust_layout():
    anchors=np.column_stack([np.linspace(-10,10,8),np.zeros(8)])
    distances=np.linalg.norm(anchors,axis=1)
    problem=Problem(anchors,distances,np.ones(8),1,.1,np.zeros(2),.2)
    assert select(problem,[np.zeros(2)])['status']=='abstain'

def test_ratio_search_is_reproducible_and_returns_counterexample():
    a=ratio_counterexample(); b=ratio_counterexample()
    assert a==b and a['status']=='refuted' and a['verified']

def test_explicit_ball_radius_has_positive_lower_bound():
    a=np.arange(8)*np.pi/4; p=10*np.column_stack([np.cos(a),np.sin(a)]); w=np.ones(8); c=np.zeros(2)
    gamma=np.sqrt(point_margin(c,p,w,2)['alpha']); R=gamma*10/(4*np.sqrt(w.sum()))
    assert gamma-curvature_bound(c,R,p,w)*R >= gamma/2

def test_v1_freeze_and_controller_refusal():
    import subprocess
    import sys
    from v2.agent import freeze_check,ROOT
    assert freeze_check()==94
    result=subprocess.run([sys.executable,'agent.py','finalize'],cwd=ROOT,capture_output=True,text=True)
    assert result.returncode!=0 and 'permanently frozen' in result.stderr
    assert freeze_check()==94
