"""Protected historical baselines: identical initialization and optimizer budget."""
import numpy as np
from .optimizer import optimize, scales

def solve_unweighted(obs):
    # Ignore confidence as well as uncertainty in the unweighted baseline.
    from dataclasses import replace
    return optimize(replace(obs, confidence=np.ones(len(obs.distances))), np.ones(len(obs.distances)))

def solve_weighted(obs):
    # w_i = confidence_i / (distance_sigma_i^2 + position_sigma_i^2).
    return optimize(obs, scales(obs))
