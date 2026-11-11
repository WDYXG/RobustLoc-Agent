"""Run development and validation, then one sealed final evaluation."""
import argparse
from pathlib import Path

from ble_crowd.study import ROOT, digest, input_hashes, read, save
from ble_crowd.verify_freeze import MANIFEST, check_files

from .dataset import build, SEED
from .evaluate import public_fixes, replay, summarize
from .proposer import propose
from .tracker import DEFAULT
from .verifier import static_guard, verify


def inputs():
    package = Path(__file__).parent
    files = (*sorted(package.glob("*.py")), package / "PROTOCOL.md", MANIFEST)
    return input_hashes() | {p.relative_to(ROOT).as_posix(): digest(p) for p in files}


def verify_static_freeze():
    issues = check_files(ROOT, read(MANIFEST)["files"])
    if issues:
        raise ValueError("Static freeze failed: " + ", ".join(issues))


def research(output):
    if output.exists():
        raise ValueError("Use a new output directory")
    verify_static_freeze()
    snapshot = inputs()
    save(output / "START.json", dict(inputs=snapshot, seed=SEED, target_threshold_m=10,
                                     target_relative_gain=.20, target_baseline="cauchy",
                                     default=DEFAULT, max_iterations=4))
    configs = {"cv": DEFAULT}
    parent, tried, decisions = "cv", [], []
    data = {split: build(split) for split in ("development", "validation")}
    fixes = {split: public_fixes(dataset) for split, dataset in data.items()}
    for split, dataset in data.items():
        save(output / f"{split}-data.json.gz", dataset)
    current = {split: replay(dataset, fixes[split], configs) for split, dataset in data.items()}
    for split, rows in current.items():
        save(output / f"incumbent-{split}.json.gz", rows)
    dev_metrics = summarize(current["development"])
    for index in range(1, 5):
        proposal = propose(current["development"], dev_metrics, parent, configs[parent], tried)
        if proposal is None:
            break
        mechanism = proposal["mechanism"]
        candidate = f"cv-{mechanism}"
        tried.append(mechanism)
        folder = output / f"round-{index:02}"
        save(folder / "proposal.json", proposal)
        pair = {parent: configs[parent], candidate: proposal["config"]}
        trials = {split: replay(dataset, fixes[split], pair) for split, dataset in data.items()}
        for split, rows in trials.items():
            save(folder / f"{split}-results.json.gz", rows)
        verdict = verify(trials["validation"], candidate, parent)
        save(folder / "verdict.json", verdict)
        decisions.append(dict(round=folder.name, candidate=candidate, parent=parent,
                              proposal_sha256=digest(folder / "proposal.json"),
                              verdict_sha256=digest(folder / "verdict.json")))
        guard = {site: v["passed"] for site, v in verdict["static_guard"].items()}
        print(f"{folder.name} {candidate}: Δsuccess10={verdict['success10_gain']:+.4f}; "
              f"static={guard}; accepted={verdict['accepted']}", flush=True)
        if verdict["accepted"]:
            configs[candidate] = proposal["config"]
            parent, current = candidate, trials
            dev_metrics = summarize(current["development"])
    if inputs() != snapshot:
        raise ValueError("Inputs changed during research")
    save(output / "FINAL_LOCK.json", dict(inputs=snapshot, methods={name: configs[name]
                                                                    for name in dict.fromkeys(("cv", parent))},
                                          final_method=parent, decisions=decisions,
                                          auto_static_validation=static_guard(summarize(current["validation"]), parent)))


def final(output):
    lock = read(output / "FINAL_LOCK.json")
    if (output / "test-data.json.gz").exists():
        raise ValueError("Final data have already been materialized")
    if inputs() != lock["inputs"]:
        raise ValueError("Frozen inputs changed")
    for decision in lock["decisions"]:
        folder = output / decision["round"]
        for item in ("proposal", "verdict"):
            if digest(folder / f"{item}.json") != decision[f"{item}_sha256"]:
                raise ValueError("A locked decision changed")
    verify_static_freeze()
    data = build("test")
    save(output / "test-data.json.gz", data)
    results = replay(data, public_fixes(data), lock["methods"])
    metrics = summarize(results)
    save(output / "test-results.json.gz", results)
    save(output / "test-metrics.json", metrics)
    save(output / "test-static-guard.json", static_guard(metrics, lock["final_method"]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("research", "final"))
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    (research if args.stage == "research" else final)(args.output)
