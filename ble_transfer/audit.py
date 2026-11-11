"""Recompute results from locked artifacts and replay representative predictions."""
import argparse
import gzip
import json
import subprocess
from collections import defaultdict
from pathlib import Path

import numpy as np

from .experiment import PACKAGE, STRESS, load, locate, models, perturb, summarize, weighted_summary
from .prepare import save, sha
from .study import BASELINES, DATA, INCUMBENT, current, fingerprints, layout
from .verifier import verify


def interval(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[row["label"]].append(row)
    values = list(groups.values())
    random = np.random.default_rng(9103)
    samples = []
    for _ in range(500):
        sampled = []
        for j, source in enumerate(random.integers(len(values), size=len(values))):
            sampled.extend({**row, "label": str(j)} for row in values[source])
        summary = weighted_summary(sampled)
        samples.append([summary[k] for k in ("cep90", "coverage", "success30")])
    limits = np.quantile(samples, [.025, .975], axis=0)
    return {k: limits[:, j].tolist() for j, k in enumerate(("cep90", "coverage", "success30"))}


def audit(run):
    lock = load(run / "FINAL_LOCK.json")
    assert lock["inputs"] == fingerprints()
    assert all(lock["inputs"].get(k) == v for k, v in load(run / "initial-inputs.json").items())
    assert lock["model_hash"] == sha((run / "models.json").read_bytes())
    info, anchors, hosts = layout()
    labels = [key for group in info["split"].values() for key in group]
    assert len(set(labels)) == len(labels) == 81
    for name, group in info["split"].items():
        assert set(group) == {r["label"] for r in load(DATA / f"{name}.json")}
    fitted = models(load(DATA / "calibration.json"), anchors, info["split"]["calibration"])
    assert fitted == load(run / "models.json")
    old = load(run / "incumbent-validation.json")
    gates = []
    for folder in sorted(run.glob("round-*")):
        candidate = load(folder / "validation.json")
        verdict = verify(candidate, old)
        assert verdict == load(folder / "verdict.json")
        gates.append(verdict["accepted"])
        if verdict["accepted"]:
            old = candidate
    assert gates == lock["decisions"]
    config, name, _, _ = current(run)
    assert config == lock["config"] and name == lock["selected"]
    with gzip.open(run / "test-predictions.json.gz", "rt", encoding="utf-8") as stream:
        predictions = json.load(stream)
    summary = load(run / "test-summary.json")
    rows = load(DATA / "test.json")
    scenarios = {"real": ("real",), "stress": STRESS}
    replays, errors = 0, 0
    specs = {**BASELINES, "selected": ("target-receiver", "cauchy")}
    for section, methods in predictions.items():
        for method, result in methods.items():
            model_key, solver = specs[method]
            if section == "real":
                assert weighted_summary(result) == summary["real"][method]
            else:
                assert summarize(result) == summary["stress"][method]
            cases = [(s, r, repeat) for s in scenarios[section] for r in rows
                     for repeat in range(1 if s == "real" else 3)]
            assert len(cases) == len(result)
            seen = set()
            for item, (scenario, row, repeat) in zip(result, cases):
                assert (item["scenario"], item["seed"], item["label"]) == (
                    scenario, f"{row['key']}:{repeat}", row["label"])
                error = None if item["estimate"] is None else np.linalg.norm(
                    np.asarray(item["estimate"]) - row["truth"])
                assert (error is None and item["error"] is None) or np.isclose(
                    error, item["error"], rtol=0, atol=1e-10)
                errors += 1
                key = (scenario, row["label"])
                if key not in seen:
                    seen.add(key)
                    p, rssi = perturb(row["public"], anchors, hosts, scenario, repeat,
                                      row["label"], row["key"])
                    mask = np.isfinite(rssi)
                    assert item["n"] == mask.sum() and item["hosts"] == len(set(hosts[mask]))
                    point, success = locate(p, rssi, fitted[model_key], solver,
                                            config if method == "selected" else INCUMBENT)
                    assert success == item["success"]
                    assert (point is None and item["estimate"] is None) or np.allclose(
                        point, item["estimate"], atol=1e-8, rtol=0)
                    replays += 1
    assert all(sha((PACKAGE / "raw" / k).read_bytes()) == v for k, v in
               load(PACKAGE / "source-manifest.json")["sha256"].items())
    root = PACKAGE.parent
    git = ["git", "-c", f"safe.directory={root.as_posix()}"]
    subprocess.run(git + ["diff", "--exit-code", "a12ba96", "--", ".", ":(exclude)ble_transfer"],
                   cwd=root, check=True)
    count = len(subprocess.check_output(git + ["ls-tree", "-r", "--name-only", "a12ba96"],
                                        cwd=root).splitlines())
    save(run / "audit.json", dict(passed=True, gates_replayed=len(gates), solver_replays=replays,
                                  errors_recomputed=errors, historical_tracked_files_unchanged=count,
                                  raw_members_verified=978, calibration_refit=True,
                                  distinct_positions_by_split={k: len(v) for k, v in info["split"].items()}))
    save(run / "intervals.json", {name: interval(result)
                                  for name, result in predictions["real"].items()})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    audit(parser.parse_args().run)
