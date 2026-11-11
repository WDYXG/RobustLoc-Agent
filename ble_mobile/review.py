"""Verify source identity, split isolation, causal replay and acceptance records."""
import argparse
from collections import Counter
from pathlib import Path
import math

import numpy as np

from ble_crowd.study import ROOT, SITES, digest, load_site, read, save
from .dataset import MAX_EDGE, MOBILE, ROUTE_POINTS, source_id
from .evaluate import public_fixes, replay
from .run import inputs, verify_static_freeze
from .tracker import Tracker
from .verifier import static_guard, verify


def independent_success(tracks, method, threshold):
    strata = {}
    for track in tracks:
        frames = track["frames"]
        errors = [f["out"][method]["error"] for f in frames]
        good = sum(e is not None and e <= threshold for e in errors) / len(errors)
        strata.setdefault((track["site"], track["scenario"]), []).append(good)
    return math.fsum(math.fsum(values) / len(values) for values in strata.values()) / len(strata)


def check_data(run):
    used = {site: set() for site in SITES}
    stats = {}
    for split in ("calibration", "development", "validation", "test"):
        data = read(run / f"{split}-data.json.gz") if split != "calibration" else None
        for site in SITES:
            _, _, _, grouped = load_site(site, split)
            coordinates = {group[0][1] for group in grouped.values()}
            assert used[site].isdisjoint(coordinates)
            used[site].update(coordinates)
            if data is None:
                continue
            sources = {r[0]: (label, r[1], r[2]) for label, group in grouped.items() for r in group}
            tracks = [tr for tr in data["tracks"] if tr["site"] == site]
            assert len({tr["id"] for tr in tracks}) == len(tracks)
            scenarios = Counter()
            labels = set()
            for track in tracks:
                frames = track["frames"]
                scenarios[track["scenario"]] += 1
                assert all(a["t"] < b["t"] for a, b in zip(frames, frames[1:]))
                assert len({f["source_key"] for f in frames}) == len(frames)
                for f in frames:
                    label, truth, rssi = sources[f["source_key"]]
                    assert f["label"] == label and tuple(f["truth"]) == truth
                    assert source_id(site, f["source_key"]) == track["source_device"]
                    labels.add(label)
                    if track["kind"] != "mobile":
                        continue
                    assert "positions" not in f
                    values = f["rssi"]
                    for i, value in enumerate(values):
                        assert value is None or value == rssi[i]
                    visible = sum(x is not None for x in values)
                    assert f["removed"] != "outage" or visible == 0
                    assert f["removed"] != "sparse" or visible <= 2
                    if f["removed"] == "none":
                        assert visible == int(np.isfinite(rssi).sum())
                if track["kind"] == "static":
                    assert len({tuple(f["truth"]) for f in frames}) == 1
                    continue
                moving = [f for i, f in enumerate(frames) if not i or f["label"] != frames[i - 1]["label"]]
                assert [f["label"] for f in moving] == track["path"]
                assert len(set(track["path"])) == ROUTE_POINTS
                for i, (a, b) in enumerate(zip(moving, moving[1:])):
                    distance = math.dist(a["truth"], b["truth"])
                    dwell = 8 if track["scenario"] == "stop-go" and i == 2 else 0
                    assert 0 < distance <= MAX_EDGE and math.isclose(
                        b["t"] - a["t"] - dwell, distance / track["segment_speeds"][i], abs_tol=2e-9)
                if track["scenario"] == "outage":
                    blocked = [i for i, f in enumerate(frames) if f["removed"] == "outage"]
                    assert len(blocked) in (2, 3) and blocked == list(range(blocked[0], len(frames) - 1))
            assert set(MOBILE) <= scenarios.keys()
            stats[f"{site}/{split}"] = dict(tracks=len(tracks), used_positions=len(labels), by_scenario=dict(scenarios))
    return stats


def check_pairing(data, records):
    for tr, replayed in zip(data["tracks"], records, strict=True):
        assert all(tr[k] == replayed[k] for k in ("id", "route", "site", "kind", "scenario"))
        for frame, scored in zip(tr["frames"], replayed["frames"], strict=True):
            assert all(frame[k] == scored[k] for k in ("t", "source_key", "removed"))
            for result in scored["out"].values():
                point, error = result["point"], result["error"]
                assert (point is None) == (error is None)
                if point is not None:
                    assert math.isclose(math.dist(point, frame["truth"]), error, abs_tol=1e-10)


def diagnostics(records, method):
    reasons, prediction = Counter(), Counter()
    failures = []
    for track in records:
        if track["kind"] != "mobile":
            continue
        for i, frame in enumerate(track["frames"]):
            trial = frame["out"][method]
            error = trial["error"]
            if error is None:
                reasons[trial["reason"]] += 1
            elif trial["reason"] == "predicted":
                prediction["outputs"] += 1
                prediction["within10"] += error <= 10
                prediction["within30"] += error <= 30
                held = frame["out"]["hold"]["error"]
                prediction["only_kf_within10"] += error <= 10 and (held is None or held > 10)
                prediction["only_hold_within10"] += error > 10 and held is not None and held <= 10
                if error > 10:
                    failures.append(dict(track=track["id"], frame=i, source_key=frame["source_key"],
                                         scenario=track["scenario"], error=error, age_s=trial["age_s"],
                                         position_sd=trial["sd"], hold_error=held))
    return dict(no_output_reasons=dict(reasons), predictions=dict(prediction),
                worst_predicted_errors=sorted(failures, key=lambda r: r["error"], reverse=True)[:10])


def review(run):
    start, lock = (read(run / f"{name}.json") for name in ("START", "FINAL_LOCK"))
    assert inputs() == start["inputs"] == lock["inputs"]
    verify_static_freeze()
    assert (run / "FINAL_LOCK.json").stat().st_mtime_ns <= (run / "test-data.json.gz").stat().st_mtime_ns
    parent = "cv"
    for row in lock["decisions"]:
        folder = run / row["round"]
        proposal = read(folder / "proposal.json")
        assert row["parent"] == proposal["parent"] == parent
        for item in ("proposal", "verdict"):
            assert digest(folder / f"{item}.json") == row[f"{item}_sha256"]
        validation = read(folder / "validation-results.json.gz")
        check_pairing(read(run / "validation-data.json.gz"), validation)
        verdict = verify(validation, row["candidate"], parent)
        assert verdict == read(folder / "verdict.json")
        if verdict["accepted"]:
            parent = row["candidate"]
    assert parent == lock["final_method"]
    data, scores = (read(run / f"test-{item}.json.gz") for item in ("data", "results"))
    check_pairing(data, scores)
    source_audit = check_data(run)
    mobile = [r for r in scores if r["kind"] == "mobile"]
    static = [r for r in scores if r["kind"] == "static"]
    metrics = read(run / "test-metrics.json")
    pooled = metrics["mobile"]["all"]
    assert static_guard(metrics, parent) == read(run / "test-static-guard.json")
    for name in pooled:
        for threshold in (5, 10, 30):
            assert math.isclose(independent_success(mobile, name, threshold),
                                pooled[name][f"success{threshold}"], abs_tol=1e-10)
    for tr in static:
        for f in tr["frames"]:
            a, b = f["out"]["cauchy"], f["out"]["declared-static"]
            assert a["point"] == b["point"] and a["error"] == b["error"]
    # Replay a prefix of each of the first route in each site/scenario.
    chosen = {}
    for track, score in zip(data["tracks"], scores):
        chosen.setdefault((track["site"], track["kind"], track["scenario"]), (track, score))
    reduced = data | {"tracks": [track | {"frames": track["frames"][:-1]} for track, _ in chosen.values()]}
    sampled = replay(reduced, public_fixes(reduced), lock["methods"])
    assert all(short["frames"] == full["frames"][:-1]
               for short, (_, full) in zip(sampled, chosen.values(), strict=True))
    for name, config in lock["methods"].items():
        tracker = Tracker(config)
        tracker.step(0., np.zeros(2))
        assert tracker.step(config["max_coast_s"] + 1, None).position is None
    before, after = (pooled[name]["success10"] for name in ("cauchy", parent))
    report = dict(verified=True, source_audit=source_audit, passed_static_freeze=True,
                  verdicts_replayed=len(lock["decisions"]), causal_prefix_replays=len(sampled),
                  stationary_exact_frames=sum(len(r["frames"]) for r in static),
                  method=parent, primary=dict(baseline=before, result=after, absolute=after - before,
                                              relative=(after - before) / before,
                                              target_met=after >= 1.20 * before),
                  diagnostics=diagnostics(scores, parent),
                  hashes={name: digest(run / name) for name in ("FINAL_LOCK.json", "test-data.json.gz",
                                                              "test-results.json.gz", "test-metrics.json")})
    save(run / "review.json", report)
    print(f"Reviewed {len(mobile)} motion tracks and {len(static)} stationary tracks; {report['primary']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    review(parser.parse_args().run)
