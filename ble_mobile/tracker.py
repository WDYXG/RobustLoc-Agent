"""Online localization from current public observations and a CV Kalman state."""
from dataclasses import dataclass
from math import sqrt

import numpy as np

from ble_transfer.experiment import locate
from static_localization.service import INCUMBENT

WINDOW_CONFIGS = {"wls": {}, "cauchy": INCUMBENT,
                  "soft-l1": INCUMBENT | {"loss": "soft_l1"}}
DEFAULT = dict(process_q=.10, measurement_sd=3.5, velocity_sd=1.,
               max_coast_s=12., max_position_sd=9., adaptation="none")
I2 = np.eye(2)
I4 = np.eye(4)
H = I4[:2]


def window(positions, rssi, model, name="cauchy"):
    method = "wls" if name == "wls" else "cauchy"
    point, success = locate(positions, rssi, model, method, WINDOW_CONFIGS[name])
    return point if success else None


@dataclass
class Update:
    position: np.ndarray | None
    velocity: np.ndarray | None
    reason: str
    age_s: float | None
    position_sd: float | None
    innovation_nis: float | None = None


class Tracker:
    """One instance per target, strictly increasing timestamps in seconds."""

    def __init__(self, config=None, mode="auto"):
        if mode not in ("auto", "stationary"):
            raise ValueError("Unknown operating mode")
        self.config = DEFAULT | (config or {})
        self.mode = mode
        self.state = self.cov = self.time = self.last_fix = None
        self.recent = []

    def update(self, timestamp, positions, rssi, model):
        return self.step(timestamp, window(np.asarray(positions, float), np.asarray(rssi, float), model))

    def step(self, timestamp, measurement):
        if not np.isfinite(timestamp) or (self.time is not None and timestamp <= self.time):
            raise ValueError("Timestamps must be finite and strictly increasing")
        dt = None if self.time is None else timestamp - self.time
        self.time = timestamp
        if self.mode == "stationary":
            return Update(measurement, None, "static-window" if measurement is not None else "no-fix",
                          0. if measurement is not None else None, None)
        cfg = self.config
        r = I2 * cfg["measurement_sd"] ** 2
        age = None if self.last_fix is None else timestamp - self.last_fix
        if self.state is None or age > cfg["max_coast_s"]:
            self.state = self.cov = None
            self.recent.clear()
            if measurement is None:
                return Update(None, None, "cold-start" if age is None else "stale", age, None)
            self.state = np.r_[measurement, 0., 0.]
            self.cov = np.diag([cfg["measurement_sd"] ** 2] * 2 + [cfg["velocity_sd"] ** 2] * 2)
            self.last_fix = timestamp
            self.recent.append((timestamp, np.array(measurement)))
            return Update(self.state[:2].copy(), self.state[2:].copy(), "initialized", 0., cfg["measurement_sd"])

        f = I4.copy()
        f[:2, 2:] = dt * I2
        q = cfg["process_q"] * np.kron([[dt**3 / 3, dt**2 / 2], [dt**2 / 2, dt]], I2)
        still = (cfg["adaptation"] == "stationary" and len(self.recent) >= 3
                 and self.recent[-1][0] - self.recent[0][0] <= 16
                 and np.max(np.linalg.norm(np.diff([p for _, p in self.recent], axis=0), axis=1)) <= 2.8
                 and (measurement is None or np.linalg.norm(measurement - self.recent[-1][1]) <= 2.8))
        if still:
            f[:2, 2:] = 0
            f[2:, 2:] = 0
            q *= .25
        self.state = f @ self.state
        self.cov = f @ self.cov @ f.T + q
        sd = self.position_sd()
        if measurement is None:
            if sd > cfg["max_position_sd"]:
                return Update(None, None, "uncertain", age, sd)
            return Update(self.state[:2].copy(), self.state[2:].copy(), "predicted", age, sd)

        innovation = measurement - self.state[:2]
        innovation_cov = self.cov[:2, :2] + r
        nis = float(innovation @ np.linalg.solve(innovation_cov, innovation))
        if cfg["adaptation"] == "robust" and nis > 9.21:
            r *= min(9., nis / 9.21)
        if cfg["adaptation"] == "maneuver" and nis > 6.:
            self.cov += q * min(5., nis / 6.)
        gain = np.linalg.solve(self.cov[:2, :2] + r, self.cov[:2, :]).T
        self.state += gain @ innovation
        stable = I4 - gain @ H
        self.cov = stable @ self.cov @ stable.T + gain @ r @ gain.T
        self.last_fix = timestamp
        self.recent = [*self.recent[-2:], (timestamp, np.array(measurement))]
        return Update(self.state[:2].copy(), self.state[2:].copy(), "corrected", 0., self.position_sd(), nis)

    def position_sd(self):
        return sqrt(max(0., float(np.linalg.eigvalsh(self.cov[:2, :2])[-1])))
