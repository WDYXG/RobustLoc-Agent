"""Protected generator; truth and corruption labels never enter solver inputs."""
from dataclasses import dataclass
import numpy as np
from .scenarios import SCENARIOS

@dataclass(frozen=True)
class Observation:
    positions: np.ndarray
    distances: np.ndarray
    position_sigma: np.ndarray
    distance_sigma: np.ndarray
    confidence: np.ndarray
    freshness: np.ndarray

@dataclass(frozen=True)
class Case:
    observation: Observation
    truth: np.ndarray
    outlier_mask: np.ndarray
    seed: int
    scenario: str

def simulate(scenario: str, seed: int) -> Case:
    """Add isotropic reporter error and additive distance-domain RSSI proxy noise.

    This is not a calibrated radio propagation simulator. Reported sigma describes
    the inlier noise only; confidence does NOT identify corrupted measurements.
    """
    rng = np.random.default_rng(seed)
    cfg = SCENARIOS[scenario]
    n = cfg['n']
    truth = rng.uniform(-20, 20, 2)
    angles = rng.uniform(-.18, .18, n) if cfg['geometry'] == 'arc' else rng.uniform(-np.pi, np.pi, n)
    radii = rng.uniform(8, 35, n)
    true_p = truth + np.column_stack((np.cos(angles), np.sin(angles))) * radii[:, None]
    factor = rng.uniform(.4, 2.5, n) if cfg['hetero'] else np.ones(n)
    ps = cfg['position_sigma'] * factor
    ds = cfg['rssi_sigma'] * factor
    positions = true_p + rng.normal(size=(n, 2)) * ps[:, None]
    distances = radii + rng.normal(size=n) * ds
    mask = np.zeros(n, dtype=bool)
    k = int(round(cfg['outliers'] * n))
    if k:
        mask[rng.choice(n, k, replace=False)] = True
        distances[mask] += rng.choice([-1., 1.], k) * rng.uniform(15, 45, k)
    distances = np.maximum(distances, .1)
    confidence = rng.uniform(.65, 1., n)
    obs = Observation(positions, distances, ps, ds, confidence, rng.uniform(0, 5, n))
    for a in (positions, distances, ps, ds, confidence, obs.freshness, truth, mask):
        a.setflags(write=False)
    return Case(obs, truth, mask, seed, scenario)
