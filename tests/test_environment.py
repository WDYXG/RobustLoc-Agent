import numpy as np
import pytest
from dataclasses import replace
from robustloc.simulator import simulate
from robustloc.baseline import solve_weighted, solve_unweighted
from robustloc.candidate import solve
from robustloc.metrics import summarize
from robustloc.evaluator import evaluate, case_seed

def test_simulator_reproducibility_and_source_isolation():
    a, b = simulate('outliers20', 17), simulate('outliers20', 17)
    assert np.array_equal(a.observation.positions, b.observation.positions)
    assert np.array_equal(a.truth, b.truth)
    assert not hasattr(a.observation, 'truth')
    assert not hasattr(a.observation, 'outlier_mask')
    with pytest.raises(ValueError):
        a.observation.distances[0] = 0

def test_metrics():
    rows = [dict(error=e, runtime_s=.1, success=True) for e in [0., 5., 10., 20.]]
    m = summarize(rows)
    assert m['mean'] == 8.75 and m['median'] == 7.5
    assert m['cep90'] == pytest.approx(17.) and m['failure_rate'] == .25

@pytest.mark.parametrize('solver', [solve_weighted, solve_unweighted, solve])
def test_exact_baseline_and_candidate_convergence(solver):
    case = simulate('clean', 23)
    obs = replace(case.observation, distances=np.linalg.norm(case.truth-case.observation.positions, axis=1))
    result = solver(obs)
    assert result.success and np.linalg.norm(result.position-case.truth) < 1e-5

def test_evaluator_determinism():
    a, b = evaluate(solve_weighted, 'development', 3), evaluate(solve_weighted, 'development', 3)
    assert [r['error'] for r in a['rows']] == [r['error'] for r in b['rows']]
    assert a['overall']['cep90'] == b['overall']['cep90']

def test_disjoint_seeds():
    sets = [{case_seed(split,j,k) for j in range(8) for k in range(250)} for split in ['development','validation','heldout']]
    assert all(not sets[i] & sets[j] for i in range(3) for j in range(i))

def test_optimizer_failure_is_visible():
    from robustloc.optimizer import optimize, scales
    obs = simulate('gaussian', 7).observation
    result = optimize(obs, scales(obs), max_nfev=1)
    assert not result.success and 'fallback' in result.message
    assert np.isfinite(result.position).all()
