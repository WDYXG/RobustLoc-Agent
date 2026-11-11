import numpy as np
import pytest

from ble_mobile.tracker import Tracker


def test_initialization_velocity_update_and_reacquisition():
    tracker = Tracker()
    assert tracker.step(0., None).reason == "cold-start"
    assert tracker.step(1., np.array([1., 0.])).reason == "initialized"
    correction = tracker.step(4., np.array([4., 0.]))
    assert 1. < correction.position[0] < 4. and correction.velocity[0] > 0.
    prediction = tracker.step(6., None)
    assert prediction.reason == "predicted" and prediction.position[0] > correction.position[0]
    assert tracker.step(20., None).reason == "stale"
    resumed = tracker.step(21., np.array([20., 2.]))
    assert resumed.reason == "initialized"
    np.testing.assert_array_equal(resumed.position, [20., 2.])
    np.testing.assert_array_equal(resumed.velocity, [0., 0.])


def test_position_uncertainty_and_timestamp_guards():
    tracker = Tracker({"max_position_sd": 4.})
    tracker.step(0., np.zeros(2))
    assert tracker.step(9., None).reason == "uncertain"
    with pytest.raises(ValueError, match="strictly increasing"):
        tracker.step(9., None)


def test_declared_stationary_never_extrapolates():
    tracker = Tracker(mode="stationary")
    assert tracker.step(1., np.array([1., 2.])).position.tolist() == [1., 2.]
    assert tracker.step(2., None).position is None
    assert tracker.step(3., np.array([4., 8.])).position.tolist() == [4., 8.]
