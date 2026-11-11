from copy import deepcopy

import pytest

from ble_field.analysis import acceptance
from ble_field.campaign import Campaign, load, save, summarize_phone
from ble_field.fixture import generate


@pytest.fixture
def campaign(tmp_path):
    root = tmp_path / "campaign"
    generate(root)
    return Campaign(root)


def test_duplicate_import_is_idempotent_and_identity_collision_is_rejected(campaign):
    path = campaign.root / "exports/P01.json"
    first = load(path)["reports"][0]
    trial = campaign.trials[first["ticket"]["trial_id"]]
    original = campaign.capture_path(trial, "P01").read_bytes()
    assert campaign.ingest([path, path]) > 0
    altered = deepcopy(first)
    altered["packets"][0]["rssi_dbm"] -= 1
    path = campaign.root / "altered.json"
    save(path, altered)
    with pytest.raises(ValueError, match="Conflicting"):
        campaign.ingest([path])
    assert campaign.capture_path(trial, "P01").read_bytes() == original
    roster = load(campaign.root / "roster.json")
    roster["phones"][1]["installation_id"] = roster["phones"][0]["installation_id"]
    save(campaign.root / "roster.json", roster)
    with pytest.raises(ValueError, match="installation_id"):
        Campaign(campaign.root)


def test_actual_count_and_no_output_denominator(campaign):
    rows = campaign.assemble("test")
    counts = [sum(p["reason"] == "usable" for p in row["phones"]) for row in rows]
    assert counts[:4] == [12, 10, 0, 11]
    assert sum(p["heard"] for p in rows[1]["phones"]) == 11
    assert {p["reason"] for p in rows[1]["phones"]} >= {"no_target_packet", "no_fresh_location"}
    scored = [dict(label=str(i), scenario="real", n=n, error=None if n == 0 else 1.,
                   geometry=.5, layout_id="spread", median_measured_receiver_error_m=None)
              for i, n in enumerate(counts)]
    metrics = acceptance(scored)
    assert metrics["all_planned"]["success30"] == pytest.approx(7 / 8)
    assert metrics["usable_ge_10"]["rows"] == 7
    assert metrics["usable_ge_11"]["rows"] == 6
    assert metrics["usable_ge_11"]["joint_success30_all_planned"] == pytest.approx(6 / 8)


def test_future_and_mock_fixes_cannot_pair(campaign):
    row = load(campaign.root / "exports/P01.json")["reports"][0]
    trial = campaign.trials[row["ticket"]["trial_id"]]
    packet_time = row["packets"][0]["t_utc_ms"]
    row["packets"] = row["packets"][:1] * 12
    row["fixes"] = [{**row["fixes"][0], "mock": True},
                    {**row["fixes"][0], "t_utc_ms": packet_time + 1}]
    report = summarize_phone(row, trial, campaign.plan["origin"])
    assert report["heard"] and report["packet_count"] == 12
    assert report["reason"] == "no_fresh_location"


def test_renamed_same_physical_point_cannot_leak(campaign):
    calibrate = load(campaign.root / "survey/calibration.json")["targets"][0]
    validation = load(campaign.root / "survey/validation.json")
    validation["targets"][0].update(lat=calibrate["lat"], lon=calibrate["lon"])
    save(campaign.root / "survey/validation.json", validation)
    with pytest.raises(ValueError, match="coincident"):
        campaign.verify_split_positions()


def test_development_does_not_open_final_inputs(campaign, monkeypatch, tmp_path):
    from ble_field.study import prepare, freeze, step
    real = Campaign.assemble

    def restricted(self, split):
        assert split != "test"
        return real(self, split)

    monkeypatch.setattr(Campaign, "assemble", restricted)
    run = tmp_path / "run"
    prepare(campaign, run)
    step(campaign, run)
    freeze(campaign, run)
    assert load(run / "FINAL_LOCK.json")["evidence"] == "synthetic_fixture"
    assert not (run / "test-predictions.json").exists()


def test_missing_phone_survey_keeps_reported_input_and_marks_diagnostic_unavailable(campaign):
    from ble_field.analysis import FIXED, evaluate
    survey_file = campaign.root / "survey/test.json"
    survey = load(survey_file)
    survey["receivers"].pop(0)
    save(survey_file, survey)
    rows = campaign.assemble("test")[:1]
    reported = evaluate(rows, FIXED, "cauchy")[0]
    measured = evaluate(rows, FIXED, "cauchy", surveyed=True)[0]
    assert reported["n"] == 12 and reported["surveyed_usable"] == 11
    assert reported["estimate"] is not None and measured["estimate"] is None
