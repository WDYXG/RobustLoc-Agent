import numpy as np

from ble_mobile.adaptive.tracker import AdaptiveTracker, Fix, Ranges, infer_motion, partial_update


def test_state_from_two_historical_velocity_segments():
    cases = [
        ([(0, 0), (.2, 0), (.4, 0)], "stationary"),
        ([(0, 0), (4, 0), (8, 0)], "constant"),
        ([(0, 0), (3, 0), (10, 0)], "variable"),
        ([(0, 0), (4, 0), (4, 4)], "turn"),
    ]
    for points, expected in cases:
        history = [Fix(4. * i, np.array(p), 3.) for i, p in enumerate(points)]
        assert infer_motion(history)[0] == expected
        assert infer_motion(history[:2])[0] == "unknown"


def test_abstention_and_partial_age():
    ranges = Ranges(np.array([[0., 0.], [4., 0.], [0., 4.]]), np.full(3, 3.), np.full(3, 2.))
    one = Ranges(np.array([[0., 0.]]), np.array([4.]), np.array([2.]))
    tracker = AdaptiveTracker({"partial": True, "hold_s": 18.})
    assert tracker.step(0., None, one).position is None
    tracker.step(1., np.array([2., 2.]), ranges)
    fixed = tracker.step(6., None, one)
    assert fixed.reason == "partial" and fixed.age_s == 5.
    stale = tracker.step(20., None, one)
    assert stale.position is None and stale.reason == "stale"
    assert partial_update(np.zeros(2), 3., Ranges(one.anchors, np.array([100.]), one.sd)) is None


def test_declared_static_is_passthrough():
    tracker = AdaptiveTracker(mode="stationary")
    ranges = Ranges(np.empty((0, 2)), np.array([]), np.array([]))
    measured = np.array([3., 4.])
    assert tracker.step(0., measured, ranges).position.tolist() == measured.tolist()
    assert tracker.step(1., None, ranges).position is None
