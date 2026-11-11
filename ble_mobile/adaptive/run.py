"""Adaptive research on existing development/validation trajectories and one final replay."""
import argparse
from pathlib import Path

from ble_crowd.study import ROOT, digest, read, save
from ble_mobile.evaluate import summarize
from ble_mobile.run import inputs as original_inputs, verify_static_freeze
from ble_mobile.verifier import static_guard, verify

from .evaluate import augment, prepare
from .proposer import propose

PREVIOUS = ROOT / "ble_mobile/runs/mobile-001"
MAX_ROUNDS = 4


def inputs():
    package = Path(__file__).parent
    sources = (*sorted(package.glob("*.py")), package / "PROTOCOL.md")
    previous = [PREVIOUS / "FINAL_LOCK.json", *(PREVIOUS / f"{split}-data.json.gz"
                                               for split in ("development", "validation"))]
    return original_inputs() | {p.relative_to(ROOT).as_posix(): digest(p) for p in (*sources, *previous)}


def verify_previous():
    verify_static_freeze()
    lock = read(PREVIOUS / "FINAL_LOCK.json")
    if lock["inputs"] != original_inputs():
        raise ValueError("Original mobile inputs changed")
    return lock["methods"][lock["final_method"]]


def safety(summary, name):
    return all(x["passed"] for x in static_guard(summary, name).values())


def choose(validation, variants, accepted):
    summary = summarize(validation)
    ranked = summary["mobile"]["all"]
    admissible = [name for name in variants if safety(summary, name)]
    passing = [name for name in admissible if name in accepted]
    rank = lambda name: (ranked[name]["success10"], -ranked[name]["cep90"])
    adaptive = max(passing or admissible or list(variants), key=rank)
    retain = [name for name in ("cv-coast", "hold", "cauchy", *passing) if safety(summary, name)]
    preferred = max(retain, key=rank)
    return adaptive, preferred


def research(output):
    if output.exists():
        raise ValueError("Use a fresh output directory")
    kalman = verify_previous()
    snapshot = inputs()
    save(output / "START.json", dict(inputs=snapshot, max_rounds=MAX_ROUNDS,
                                    target_baseline="cauchy", target_threshold_m=10, target_relative_gain=.2))
    datasets = {split: read(PREVIOUS / f"{split}-data.json.gz") for split in ("development", "validation")}
    prepared = {split: prepare(data, kalman) for split, data in datasets.items()}
    development = prepared["development"][1]
    parent = "cv-coast"
    configs, accepted, tried, decisions = {}, [], [], []
    for index in range(1, MAX_ROUNDS + 1):
        proposal = propose(development, parent, configs.get(parent), tried)
        if proposal is None:
            break
        mechanism = proposal["mechanism"]
        candidate = "adaptive-" + mechanism
        tried.append(mechanism)
        configs[candidate] = proposal["config"]
        folder = output / f"round-{index:02}"
        save(folder / "proposal.json", proposal)
        active = {name: configs[name] for name in (parent, candidate) if name in configs}
        records = {split: augment(data, prepared[split], active, kalman) for split, data in datasets.items()}
        for split, scored in records.items():
            save(folder / f"{split}-results.json.gz", scored)
        verdict = verify(records["validation"], candidate, parent)
        save(folder / "verdict.json", verdict)
        decisions.append(dict(round=folder.name, candidate=candidate, parent=parent,
                              proposal_sha256=digest(folder / "proposal.json"),
                              verdict_sha256=digest(folder / "verdict.json")))
        print(f"{folder.name}: {candidate}, validation ΔS10={verdict['success10_gain']:+.4f}, "
              f"static={safety(summarize(records['validation']), candidate)}, accepted={verdict['accepted']}", flush=True)
        if verdict["accepted"]:
            accepted.append(candidate)
        if verdict["accepted"] or index == 1:
            # A rejected seed can serve as a research comparator only.
            parent, development = candidate, records["development"]
    validation = augment(datasets["validation"], prepared["validation"], configs, kalman)
    summary = summarize(validation)
    adaptive, preferred = choose(validation, configs, accepted)
    save(output / "validation-metrics.json", summary)
    if inputs() != snapshot:
        raise ValueError("Inputs changed during development")
    save(output / "FINAL_LOCK.json", dict(inputs=snapshot, kalman=kalman, decisions=decisions,
                                          adaptive=adaptive, preferred=preferred, accepted=accepted,
                                          config=configs[adaptive],
                                          validation_static=static_guard(summary, adaptive),
                                          validation_metrics_sha256=digest(output / "validation-metrics.json")))


def final(output):
    if (output / "FINAL_STARTED.json").exists():
        raise ValueError("Final replay has already started")
    lock = read(output / "FINAL_LOCK.json")
    if inputs() != lock["inputs"] or verify_previous() != lock["kalman"]:
        raise ValueError("Frozen inputs changed")
    for decision in lock["decisions"]:
        for item in ("proposal", "verdict"):
            if digest(output / decision["round"] / f"{item}.json") != decision[f"{item}_sha256"]:
                raise ValueError("A validation artifact changed")
    if digest(output / "validation-metrics.json") != lock["validation_metrics_sha256"]:
        raise ValueError("Validation summaries changed")
    save(output / "FINAL_STARTED.json", dict(lock_sha256=digest(output / "FINAL_LOCK.json")))
    source = PREVIOUS / "test-data.json.gz"
    expected = read(PREVIOUS / "review.json")["hashes"]["test-data.json.gz"]
    if digest(source) != expected:
        raise ValueError("Original test fixture changed")
    dataset = read(source)
    results = augment(dataset, prepare(dataset, lock["kalman"]), {"adaptive": lock["config"]}, lock["kalman"])
    save(output / "test-results.json.gz", results)
    metrics = summarize(results)
    save(output / "test-metrics.json", metrics)
    save(output / "test-static-guard.json", static_guard(metrics, "adaptive"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("research", "final"))
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    (research if args.stage == "research" else final)(args.output)
