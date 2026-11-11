import numpy as np
import pytest

from ble_research.core import estimate
from ble_transfer.experiment import locate, perturb, weighted_summary
from ble_transfer.study import INCUMBENT
from ble_transfer.verifier import verify


def test_frozen_solver_adapter_agrees_on_valid_inputs():
    p = np.array([[0., 0.], [10., 0.], [0., 10.], [10., 10.]])
    public = {"device": "tag", "rssi": [-72., -75., -105., -79.]}
    model = {"intercepts": [-59.] * 4, "slope": -20., "sigma": 4., "device_offsets": {}}
    expected = estimate(public, p, model, "cauchy")
    point, success = locate(p, np.array([-72., -75., np.nan, -79.]), model, "cauchy", INCUMBENT)
    assert success == expected["success"]
    assert np.allclose(point, expected["position"])


def test_shared_host_loss_removes_all_its_links():
    positions = np.arange(24).reshape(12, 2).astype(float)
    hosts = np.repeat(np.arange(4), 3)
    public = {"device": "tag", "rssi": [-75.] * 12}
    p, rssi = perturb(public, positions, hosts, "host1", 0, "site", "window")
    assert np.array_equal(p, positions)
    assert len(set(hosts[np.isnan(rssi)])) == 1
    assert np.isnan(rssi).sum() == 3


def test_missing_observations_count_as_failures_and_cannot_win_gate():
    def row(key, error):
        return dict(seed=key, label=key, scenario="real", n=3, hosts=2, geometry=.5, error=error)

    base = [row("a", 1.), row("b", 40.)]
    candidate = [row("a", 1.), row("b", None)]
    metrics = weighted_summary(candidate)
    assert metrics["cep90"] == 1.
    assert metrics["success30"] == metrics["coverage"] == .5
    assert not verify(candidate, base)["accepted"]
    with pytest.raises(ValueError):
        verify(list(reversed(candidate)), base)
