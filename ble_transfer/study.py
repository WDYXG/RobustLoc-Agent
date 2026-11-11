"""Split-aware runner. Research commands do not load test observations."""
import argparse
import gzip
import json
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
from robustloc.proposer import propose
from static_localization.service import INCUMBENT

from .experiment import PACKAGE, SOURCE, PORTFOLIO, STRESS, evaluate, load, models, summarize, weighted_summary
from .prepare import save, sha

DATA = PACKAGE / "observations"
BASELINES = {
    "centre": ("target-receiver", "centre"),
    "strongest": ("target-receiver", "strongest"),
    "fixed-wls": ("fixed", "wls"),
    "fixed-cauchy": ("fixed", "cauchy"),
    "source-global-wls": ("source-global", "wls"),
    "source-global-cauchy": ("source-global", "cauchy"),
    "source-final-projection": ("source-final-mean", "cauchy"),
    "target-offset8": ("target-offset8", "cauchy"),
    "target-global-wls": ("target-global", "wls"),
    "target-global-cauchy": ("target-global", "cauchy"),
    "target-receiver-wls": ("target-receiver", "wls"),
    "target-receiver-cauchy": ("target-receiver", "cauchy"),
}


def layout():
    info = load(DATA / "layout.json")
    return info, np.array(info["anchors"]), np.array([name[6] for name in info["receivers"]])


def fingerprints():
    files = list(PACKAGE.glob("*.py")) + list(DATA.glob("*.json"))
    files += [PACKAGE / "PROTOCOL.md", PACKAGE / "source-manifest.json",
              SOURCE / "model-global.json", SOURCE / "final-bundle.json"]
    return {p.relative_to(PACKAGE.parent).as_posix(): sha(p.read_bytes()) for p in sorted(files)}


def paired_run(rows, anchors, hosts, model, method, config, scenarios):
    # One process per scenario group. No randomized solver decisions.
    if len(scenarios) == 1:
        return evaluate(rows, anchors, hosts, model, method, config, scenarios)
    with ProcessPoolExecutor(max_workers=4) as pool:
        jobs = [pool.submit(evaluate, rows, anchors, hosts, model, method, config, (s,))
                for s in scenarios]
        return [row for job in jobs for row in job.result()]


def start(run):
    run.mkdir(parents=True, exist_ok=False)
    info, anchors, hosts = layout()
    fitted = models(load(DATA / "calibration.json"), anchors, info["split"]["calibration"])
    save(run / "models.json", fitted)
    save(run / "initial-inputs.json", fingerprints())
    dev = load(DATA / "development.json")
    diagnostic = {}
    for name in ("source-final-projection", "target-offset8", "target-global-cauchy",
                 "target-receiver-wls", "target-receiver-cauchy"):
        model, method = BASELINES[name]
        result = evaluate(dev, anchors, hosts, fitted[model], method, INCUMBENT, ("real",))
        diagnostic[name] = weighted_summary(result)
    save(run / "development-transfer.json", diagnostic)
    for split in ("development", "validation"):
        rows = paired_run(load(DATA / f"{split}.json"), anchors, hosts,
                          fitted["target-receiver"], "cauchy", INCUMBENT, PORTFOLIO)
        save(run / f"incumbent-{split}.json", rows)
        print(split, summarize(rows), flush=True)


def current(run):
    config, name, path = INCUMBENT.copy(), "frozen-local-cauchy", run / "incumbent-validation.json"
    records = []
    for folder in sorted(run.glob("round-*")):
        proposal = load(folder / "proposal.json")
        verdict = load(folder / "verdict.json")
        records.append({"proposal": proposal, "verdict": verdict})
        if verdict["accepted"]:
            config, name, path = proposal["config"], folder.name, folder / "validation.json"
    return config, name, path, records


def step(run, mechanism, rationale):
    if (run / "FINAL_LOCK.json").exists():
        raise ValueError("Final configuration already frozen")
    config, name, old, records = current(run)
    baseline = summarize(load(old))
    if mechanism == "position_sigma":
        proposal = dict(mechanism=mechanism, parent=name, hypothesis=rationale,
                        config={**config, "position_sigma": 5.})
    elif mechanism == "existing":
        tried = [{"proposal": {"mechanism": k}} for k in ("cauchy", "adaptive_scale", "confidence")]
        state = {"best_method": {"name": name, "config": config},
                 "best_validation_metrics": {"by_scenario": {
                     s: {**m, "failure_rate": 1 - m["success30"]}
                     for s, m in baseline["by_scenario"].items()}},
                 "last_result": records[-1]["verdict"]["accepted"] if records else "baseline"}
        proposal = propose(state, tried + records)
        if proposal is None:
            raise ValueError("Existing proposer exhausted")
        proposal["context"] = rationale
    else:
        raise ValueError("Unknown research mechanism")
    folder = run / f"round-{len(records) + 1:02}"
    folder.mkdir()
    save(folder / "proposal.json", proposal)
    _, anchors, hosts = layout()
    model = load(run / "models.json")["target-receiver"]
    for split in ("development", "validation"):
        rows = paired_run(load(DATA / f"{split}.json"), anchors, hosts, model, "cauchy",
                          proposal["config"], PORTFOLIO)
        save(folder / f"{split}.json", rows)
    subprocess.run([sys.executable, "-m", "ble_transfer.verifier", str(folder / "validation.json"),
                    str(old), str(folder / "verdict.json")], check=True)
    print(load(folder / "verdict.json"), flush=True)


def final(run):
    lock = run / "FINAL_LOCK.json"
    if lock.exists():
        raise FileExistsError(lock)
    config, name, _, records = current(run)
    save(lock, dict(config=config, selected=name, inputs=fingerprints(),
                    model_hash=sha((run / "models.json").read_bytes()),
                    decisions=[r["verdict"]["accepted"] for r in records]))
    fitted = load(run / "models.json")
    info, anchors, hosts = layout()
    test = load(DATA / "test.json")
    clean, stress = {}, {}
    for key, (model, method) in {**BASELINES, "selected": ("target-receiver", "cauchy")}.items():
        chosen = config if key == "selected" else INCUMBENT
        clean[key] = evaluate(test, anchors, hosts, fitted[model], method, chosen, ("real",))
        print(key, weighted_summary(clean[key]), flush=True)
        if key in ("strongest", "target-receiver-wls", "target-receiver-cauchy", "selected"):
            stress[key] = paired_run(test, anchors, hosts, fitted[model], method, chosen, STRESS)
    with gzip.open(run / "test-predictions.json.gz", "xt", encoding="utf-8") as stream:
        json.dump({"real": clean, "stress": stress}, stream, ensure_ascii=False, allow_nan=False)
    save(run / "test-summary.json", {
        "real": {k: weighted_summary(v) for k, v in clean.items()},
        "n_ge_11": {k: weighted_summary([r for r in v if r["n"] >= 11]) for k, v in clean.items()},
        "hosts_ge_11": weighted_summary([r for r in clean["selected"] if r["hosts"] >= 11]),
        "stress": {k: summarize(v) for k, v in stress.items()},
        "geometry": {s: {g: weighted_summary([r for r in v if (r["geometry"] < .15) == (g == "weak")])
                         for g in ("weak", "spread")}
                     for s, v in {"real": clean["selected"], "stress": stress["selected"]}.items()},
        "natural_windows_test": info["coverage"]["test"],
    })


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=["start", "step", "final"])
    p.add_argument("run", type=Path)
    p.add_argument("--mechanism", default="existing")
    p.add_argument("--rationale", default="")
    args = p.parse_args()
    if args.action == "start":
        start(args.run)
    elif args.action == "step":
        step(args.run, args.mechanism, args.rationale)
    else:
        final(args.run)
