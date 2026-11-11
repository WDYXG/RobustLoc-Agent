"""Causal selection of a fresh correction, short hold, CV forecast or abstention."""
from collections import deque
from dataclasses import dataclass
from math import hypot

import numpy as np

from ble_mobile.tracker import Tracker, Update, window

I2 = np.eye(2)
MAX_GAP = 18.
RISK_CAP = 9.
DEFAULT = dict(hold_s=12., partial=False, innovation=False)


@dataclass(frozen=True)
class Ranges:
    anchors: np.ndarray
    values: np.ndarray
    sd: np.ndarray

    @classmethod
    def from_window(cls, positions, rssi, model):
        values = np.asarray(rssi, float)
        visible = np.isfinite(values)
        slope = model["slope"]
        distances = 10 ** ((values[visible] - np.asarray(model["intercepts"])[visible]) / slope)
        return cls(np.asarray(positions, float)[visible], distances,
                   np.maximum(1., distances * np.log(10) * model["sigma"] / abs(slope)))

    def linearize(self, point):
        displacement = point - self.anchors
        distances = np.linalg.norm(displacement, axis=1)
        return displacement / np.maximum(distances, .1)[:, None], self.values - distances

    def fix_quality(self, point):
        jacobian, residual = self.linearize(point)
        weighted = jacobian / self.sd[:, None]
        smallest = np.linalg.eigvalsh(weighted.T @ weighted)[0]
        # Damped local sensitivity. The cap is a modeling choice, not a confidence guarantee.
        sd = np.sqrt(1 / (.04 + max(0., smallest)))
        mismatch = max(1., min(1.35, float(np.median(np.abs(residual) / self.sd))))
        return float(max(2.5, sd * mismatch))


@dataclass
class Fix:
    t: float
    point: np.ndarray
    sd: float


def infer_motion(history):
    """Three available fixes supply two velocities. Insufficient evidence stays unknown."""
    if len(history) < 3:
        return "unknown", None
    a, b, c = history
    dt = np.array([b.t - a.t, c.t - b.t])
    if np.max(dt) > MAX_GAP:
        return "unknown", None
    steps = np.stack([b.point - a.point, c.point - b.point])
    lengths = np.linalg.norm(steps, axis=1)
    speed = lengths / dt
    if np.max(lengths) <= 2.8 and np.linalg.norm(c.point - a.point) <= 3.5:
        return "stationary", float(speed[-1])
    if np.min(lengths) < 2.:
        return "unknown", None
    cosine = float(steps[0] @ steps[1] / np.prod(lengths))
    if cosine < .5:
        return "turn", float(speed[-1])
    if cosine >= .7 and abs(speed[1] - speed[0]) >= .45 and max(speed) >= 1.6 * min(speed):
        return "variable", float(speed[-1])
    if cosine >= .8 and max(speed) < 1.6 * min(speed):
        return "constant", float(speed[-1])
    return "unknown", None


def hold_sd(fix, age, state, speed):
    if state == "stationary":
        drift = .25
    elif state == "constant":
        drift = min(1.2, max(.6, speed))
    elif state in ("turn", "variable"):
        drift = min(1.4, max(.8, speed))
    else:
        drift = .6
    return hypot(fix.sd, drift * age)


def partial_update(point, sd, ranges):
    """One guarded range correction; the last full-fix clock is unchanged."""
    jacobian, residual = ranges.linearize(point)
    covariance = I2 * sd**2
    noise = np.diag(ranges.sd**2)
    innovation = jacobian @ covariance @ jacobian.T + noise
    nis = float(residual @ np.linalg.solve(innovation, residual))
    if nis > 9.21:
        return None
    gain = np.linalg.solve(innovation, jacobian @ covariance).T
    shift = gain @ residual
    stable = I2 - gain @ jacobian
    post = stable @ covariance @ stable.T + gain @ noise @ gain.T
    post_sd = float(np.sqrt(max(0., np.linalg.eigvalsh(post)[-1])))
    if np.linalg.norm(shift) > 6. or post_sd > RISK_CAP:
        return None
    return point + shift, post_sd, nis


class AdaptiveTracker:
    def __init__(self, config=None, kalman=None, mode="auto"):
        self.config = DEFAULT | (config or {})
        self.filter = Tracker({"max_coast_s": MAX_GAP} if kalman is None else kalman, mode=mode)
        self.mode = mode
        self.history = deque(maxlen=3)
        self.last = None
        self.motion = "unknown"

    def update(self, timestamp, positions, rssi, model):
        measured = window(np.asarray(positions, float), np.asarray(rssi, float), model)
        return self.step(timestamp, measured, Ranges.from_window(positions, rssi, model))

    def step(self, t, current, ranges):
        cv = self.filter.step(t, current)
        if self.mode == "stationary":
            self.motion = "stationary"
            return cv

        if current is not None:
            sd = ranges.fix_quality(current)
            if self.history and t - self.history[-1].t > MAX_GAP:
                self.history.clear()
            self.history.append(Fix(t, current.copy(), sd))
            self.motion, _ = infer_motion(self.history)
            strong = len(ranges.values) >= 4 and sd <= 4.5
            abrupt = self.config["innovation"] and (cv.innovation_nis or 0.) >= 4.
            if strong and (self.motion in ("turn", "variable") or abrupt):
                fresh = Update(current, cv.velocity, "current", 0., sd, cv.innovation_nis)
            else:
                fresh = cv
            self.last = Fix(t, fresh.position.copy(), sd)
            return fresh

        if self.last is None:
            self.motion = "unknown"
            return cv
        age = t - self.last.t
        if age > MAX_GAP:
            self.motion = "unknown"
            return Update(None, None, "stale", age, None)
        self.motion, speed = infer_motion(self.history)
        sd = hold_sd(self.last, age, self.motion, speed)
        held = age <= self.config["hold_s"] and sd <= RISK_CAP
        coherent = self.motion == "constant" and cv.reason == "predicted"
        if coherent:
            # Prefer extrapolation when recent velocities agree and it predicts material motion.
            shift = np.linalg.norm(cv.position - self.last.point)
            coherent = 1. <= shift <= 1.6 * age and cv.position_sd <= RISK_CAP
        proposal = cv if coherent else Update(self.last.point.copy(), cv.velocity, "held", age, sd)
        if self.config["partial"] and 0 < len(ranges.values) <= 2:
            correction = partial_update(proposal.position, proposal.position_sd, ranges)
            if correction is not None:
                point, post_sd, nis = correction
                return Update(point, proposal.velocity, "partial", age, post_sd, nis)
        if coherent or held:
            return proposal
        return Update(None, None, "uncertain" if sd > RISK_CAP else "stale", age, sd)
