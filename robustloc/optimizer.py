"""Shared numerical primitive; finite fallback is explicitly marked unsuccessful."""
from dataclasses import dataclass
import numpy as np
from scipy.optimize import least_squares
from .simulator import Observation

@dataclass
class Solution:
    position: np.ndarray
    success: bool
    message: str
    nfev: int = 0

def scales(obs: Observation) -> np.ndarray:
    return np.sqrt(obs.distance_sigma**2 + obs.position_sigma**2)

def optimize(obs: Observation, scale: np.ndarray, loss='linear', threshold=1., starts=None, max_nfev=150) -> Solution:
    p, d = obs.positions, obs.distances
    weight = np.sqrt(obs.confidence) / np.maximum(scale, .05)
    center = np.average(p, axis=0, weights=weight**2)
    starts = [center] if starts is None else starts
    def residual(x):
        return (np.linalg.norm(x - p, axis=1) - d) * weight
    def jac(x):
        delta = x - p
        return delta / np.maximum(np.linalg.norm(delta, axis=1), 1e-10)[:, None] * weight[:, None]
    best, messages = None, []
    for start in starts:
        try:
            res = least_squares(residual, start, jac=jac, loss=loss, f_scale=threshold, max_nfev=max_nfev)
            if np.isfinite(res.x).all() and res.success and (best is None or res.cost < best.cost):
                best = res
            messages.append(str(res.message))
        except (ValueError, FloatingPointError, np.linalg.LinAlgError) as exc:
            messages.append(repr(exc))
    if best is None:
        return Solution(center, False, 'fallback: ' + '; '.join(messages))
    return Solution(best.x, True, str(best.message), int(best.nfev))
