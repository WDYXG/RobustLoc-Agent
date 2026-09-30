"""Mutable candidate family. Solver sees observations only, never simulator truth."""
from dataclasses import replace
import numpy as np
from .optimizer import optimize, scales

DEFAULT = dict(loss='linear', threshold=1., uncertainty=True, confidence=True, multistart=False, adaptive=False)

def solve(obs, config=None):
    cfg = DEFAULT | (config or {})
    if not cfg['confidence']:
        obs = replace(obs, confidence=np.ones(len(obs.distances)))
    scale = scales(obs) if cfg['uncertainty'] else np.ones(len(obs.distances))
    starts = None
    if cfg['multistart']:
        center = np.mean(obs.positions, axis=0)
        radius = np.median(obs.distances)
        starts = [center] + [center + radius * np.array(v) for v in [(1, 0), (-1, 0), (0, 1), (0, -1)]]
    if cfg['adaptive']:
        preliminary = optimize(obs, scale, cfg['loss'], cfg['threshold'], starts)
        residual = (np.linalg.norm(preliminary.position - obs.positions, axis=1) - obs.distances) / scale
        mad = 1.4826 * np.median(np.abs(residual - np.median(residual)))
        # One scalar scale update, lower bound prevents artificially tiny scales.
        scale = scale * max(1., float(mad))
    return optimize(obs, scale, cfg['loss'], cfg['threshold'], starts)
