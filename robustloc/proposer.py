"""Observation-driven bounded research policy, not an LLM novelty generator.

    Mechanisms are authored in advance. Their ordering, parent and thresholds are
    selected from persistent results. Evidence never determines evaluator rules.
"""
from copy import deepcopy

def propose(state, records):
    cfg = deepcopy(state['best_method']['config'])
    tried = {r['proposal']['mechanism'] for r in records}
    worst = max(state['best_validation_metrics']['by_scenario'], key=lambda s: state['best_validation_metrics']['by_scenario'][s]['cep90'])
    tail = state['best_validation_metrics']['by_scenario'][worst]
    if 'robust_loss' not in tried:
        key, change = 'robust_loss', {'loss': 'huber', 'threshold': 1.}
        claim = 'Replacing squared loss with Huber loss reduces contamination-driven tail errors.'
    elif worst == 'poor_geometry' and 'multistart' not in tried:
        key, change = 'multistart', {'multistart': True}
        claim = 'Poor-geometry tail errors partly come from local minima; symmetric multi-start lowers their frequency.'
    elif 'cauchy' not in tried:
        key, change = 'cauchy', {'loss': 'cauchy'}
        claim = 'A redescending Cauchy influence suppresses large distance residuals more effectively than the incumbent loss.'
    elif 'adaptive_scale' not in tried:
        key, change = 'adaptive_scale', {'adaptive': True}
        claim = 'An observation-only MAD scale update improves robustness when nominal scales understate residual spread.'
    elif 'threshold' not in tried:
        key, change = 'threshold', {'threshold': .5 if tail['failure_rate'] > .1 else 2.}
        claim = 'Changing the robust transition threshold addresses the observed worst-scenario tail.'
    elif 'soft_l1' not in tried:
        key, change = 'soft_l1', {'loss': 'soft_l1'}
        claim = 'Smooth soft-L1 curvature improves optimization stability relative to the incumbent loss.'
    elif 'confidence' not in tried:
        key, change = 'confidence', {'confidence': False}
        claim = 'Confidence is weakly informative here; removing it avoids unnecessary random weighting.'
    elif 'uncertainty' not in tried:
        key, change = 'uncertainty', {'uncertainty': False}
        claim = 'Nominal heteroscedastic weights may amplify corrupted low-sigma reports; equal scales can reduce the tail.'
    elif 'multistart' not in tried:
        key, change = 'multistart', {'multistart': True}
        claim = 'Multiple deterministic initializations reduce local-minimum failures.'
    else:
        return None
    cfg.update(change)
    return dict(mechanism=key, hypothesis=claim, config=cfg, parent=state['best_method']['name'],
                motivation=f'Incumbent worst validation scenario: {worst}, CEP90={tail["cep90"]:.3f} m; last verdict={state["last_result"]}.',
                expected_effect='Lower aggregate validation CEP90 without material failure-rate or scenario regression.',
                possible_downside='Biased inlier fit, additional local minima, higher runtime, or poor sparse/geometry behavior.',
                changed_parameters=change, mathematical_reasoning_summary=claim + ' This is an empirical hypothesis, not a proof.')
