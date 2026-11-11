"""Audit sealed comparison, independent scoring, and online safety invariants."""
import argparse
from collections import Counter
import math
from pathlib import Path

from ble_crowd.study import digest, read, save
from ble_mobile.evaluate import summarize
from ble_mobile.review import check_pairing, independent_success
from ble_mobile.verifier import static_guard, verify

from .evaluate import augment, prepare
from .run import PREVIOUS, inputs, verify_previous
from .tracker import MAX_GAP, RISK_CAP

METHODS = ("wls", "cauchy", "soft-l1", "cv-coast", "hold", "adaptive")


def summarize_actions(records):
    motion, actions = Counter(), Counter()
    stale_cases, failed = [], []
    improved, worsened = Counter(), Counter()
    for track in records:
        for i, frame in enumerate(track["frames"]):
            update = frame["out"]["adaptive"]
            error, reason, age, sd = (update[key] for key in ("error", "reason", "age_s", "sd"))
            motion[update["motion"]] += 1
            actions[reason] += 1
            if reason in ("held", "predicted", "partial"):
                assert 0 < age <= MAX_GAP and 0 <= sd <= RISK_CAP
            if reason == "stale":
                stale_cases.append(dict(track=track["id"], frame=i, age_s=age, position_sd=sd))
            if reason in ("held", "predicted", "partial") and error > 10:
                failed.append(dict(track=track["id"], frame=i, action=reason, error=error,
                                   age_s=age, position_sd=sd, state=update["motion"]))
            for name in ("cv-coast", "hold"):
                previous = frame["out"][name]["error"]
                hit = error is not None and error <= 10
                old_hit = previous is not None and previous <= 10
                improved[name] += hit and not old_hit
                worsened[name] += old_hit and not hit
    return dict(motion=dict(motion), actions=dict(actions), improves_10m_count=dict(improved),
                worsens_10m_count=dict(worsened), stale_examples=stale_cases[:10],
                worst_historical_outputs=sorted(failed, key=lambda x: x["error"], reverse=True)[:10])


def review(run):
    lock = read(run / "FINAL_LOCK.json")
    marker = read(run / "FINAL_STARTED.json")
    assert digest(run / "FINAL_LOCK.json") == marker["lock_sha256"]
    assert (run / "FINAL_LOCK.json").stat().st_mtime_ns <= (run / "FINAL_STARTED.json").stat().st_mtime_ns
    assert lock["inputs"] == inputs() == read(run / "START.json")["inputs"]
    assert lock["kalman"] == verify_previous()
    assert digest(run / "validation-metrics.json") == lock["validation_metrics_sha256"]
    adaptive_config = None
    accepted = []
    for item in lock["decisions"]:
        folder = run / item["round"]
        for name in ("proposal", "verdict"):
            assert digest(folder / f"{name}.json") == item[f"{name}_sha256"]
        proposal = read(folder / "proposal.json")
        scores = read(folder / "validation-results.json.gz")
        check_pairing(read(PREVIOUS / "validation-data.json.gz"), scores)
        decision = verify(scores, item["candidate"], item["parent"])
        assert decision == read(folder / "verdict.json")
        if decision["accepted"]:
            accepted.append(item["candidate"])
        if item["candidate"] == lock["adaptive"]:
            adaptive_config = proposal["config"]
    assert accepted == lock["accepted"] and adaptive_config == lock["config"]

    former = read(PREVIOUS / "review.json")["hashes"]
    for name in ("test-data.json.gz", "test-results.json.gz"):
        assert digest(PREVIOUS / name) == former[name]
    test = read(PREVIOUS / "test-data.json.gz")
    records = read(run / "test-results.json.gz")
    check_pairing(test, records)
    old = read(PREVIOUS / "test-results.json.gz")
    static_exact = 0
    for new_track, old_track in zip(records, old, strict=True):
        assert new_track["id"] == old_track["id"]
        for current, previous in zip(new_track["frames"], old_track["frames"], strict=True):
            for method in METHODS[:-1]:
                assert current["out"][method] == previous["out"][method]
            if new_track["kind"] == "static":
                protected, reference = (current["out"][name] for name in ("adaptive-declared-static", "cauchy"))
                assert protected["point"] == reference["point"] and protected["error"] == reference["error"]
                static_exact += 1
    metrics = read(run / "test-metrics.json")
    assert summarize(records) == metrics
    assert static_guard(metrics, "adaptive") == read(run / "test-static-guard.json")
    mobile = [row for row in records if row["kind"] == "mobile"]
    for method in METHODS:
        assert math.isclose(independent_success(mobile, method, 10),
                            metrics["mobile"]["all"][method]["success10"], abs_tol=1e-10)

    # Dropping each chosen route's last frame must leave all earlier decisions unchanged.
    examples = {}
    for track, scored in zip(test["tracks"], records, strict=True):
        examples.setdefault((track["site"], track["kind"], track["scenario"]), (track, scored))
    prefixes = test | {"tracks": [track | {"frames": track["frames"][:-1]} for track, _ in examples.values()]}
    checked = augment(prefixes, prepare(prefixes, lock["kalman"]), {"adaptive": lock["config"]}, lock["kalman"])
    for short, (_, full) in zip(checked, examples.values(), strict=True):
        assert short["frames"] == full["frames"][:-1]

    score = metrics["mobile"]["all"]
    baseline, result = (score[method]["success10"] for method in ("cauchy", "adaptive"))
    policy = "adaptive" if lock["preferred"] == lock["adaptive"] else lock["preferred"]
    report = dict(verified=True, primary=dict(baseline=baseline, adaptive=result,
                                              absolute=result-baseline, relative=(result-baseline)/baseline,
                                              target_met=result >= 1.2 * baseline),
                  lock=dict(adaptive=lock["adaptive"], preferred=policy,
                            preferred_passed_static=all(v["passed"] for v in static_guard(metrics, policy).values())),
                  stationary_exact_frames=static_exact, causal_prefix_replays=len(checked),
                  verdicts_replayed=len(lock["decisions"]), baselines_match_previous=True,
                  diagnostics=summarize_actions(mobile), hashes={name: digest(run / name) for name in
                  ("FINAL_LOCK.json", "FINAL_STARTED.json", "test-results.json.gz", "test-metrics.json", "test-static-guard.json")})
    save(run / "review.json", report)
    print(report["primary"], report["lock"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    review(parser.parse_args().run)
