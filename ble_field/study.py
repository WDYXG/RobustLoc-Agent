"""Field study lifecycle with calibration, validation and a locked final test."""
import argparse
import subprocess
import sys
from pathlib import Path

from robustloc.proposer import propose
from static_localization.service import INCUMBENT

from .analysis import FIXED, acceptance, calibration, diagnostics, evaluate
from .campaign import SPLITS, Campaign, digest, load, require, save
from .verifier import verify

ROOT = Path(__file__).resolve().parents[1]
DEVELOPMENT_SPLITS = SPLITS[:3]


def code_hashes():
    paths = ["ble_field/campaign.py", "ble_field/analysis.py", "ble_field/study.py",
             "ble_field/verifier.py", "ble_field/PROTOCOL.md", "ble_transfer/experiment.py",
             "ble_transfer/verifier.py", "robustloc/proposer.py", "robustloc/candidate.py",
             "robustloc/optimizer.py", "robustloc/baseline.py", "robustloc/simulator.py",
             "static_localization/service.py"]
    return {name: digest(ROOT / name) for name in paths}


def calibration_models(rows):
    values = {"fixed": FIXED}
    for name, per_phone in (("global", False), ("per-phone", True)):
        fitted = calibration(rows, per_phone)
        if fitted is not None:
            values[name] = fitted
    return values


def score_methods(rows, fitted, primary, selected):
    result = {"layout-centre": evaluate(rows, FIXED, "centre")}
    for name, model in fitted.items():
        for method in ("wls", "cauchy"):
            result[f"{name}-{method}"] = evaluate(rows, model, method)
    result["surveyed-receiver-diagnostic"] = evaluate(rows, fitted[primary], "cauchy", surveyed=True)
    result["selected"] = evaluate(rows, fitted[primary], "cauchy", selected)
    return result


def primary_name(fitted):
    return next(key for key in ("per-phone", "global", "fixed") if key in fitted)


def prepare(campaign, run):
    initial = campaign.hashes(DEVELOPMENT_SPLITS)
    campaign.verify_split_positions(DEVELOPMENT_SPLITS)
    run.mkdir(parents=True, exist_ok=False)
    trained = calibration_models(campaign.assemble("calibration"))
    primary = primary_name(trained)
    save(run / "models.json", trained)
    save(run / "development-lock.json", {
        "evidence": campaign.plan["evidence"], "campaign_id": campaign.plan["campaign_id"],
        "primary": primary, "inputs": initial,
        "code": code_hashes(), "models_sha256": digest(run / "models.json"),
    })
    for split in ("development", "validation"):
        rows = campaign.assemble(split)
        results = score_methods(rows, trained, primary, INCUMBENT)
        save(run / f"{split}-baselines.json", results)
        save(run / f"{split}-summary.json", {k: acceptance(v) for k, v in results.items()})
    verify_development(campaign, run)
    print(f"Prepared {campaign.plan['evidence']} baselines. Primary calibration: {primary}.")


def verify_development(campaign, run):
    lock = load(run / "development-lock.json")
    require(lock["inputs"] == campaign.hashes(DEVELOPMENT_SPLITS) and lock["code"] == code_hashes()
            and lock["models_sha256"] == digest(run / "models.json"),
            "Development inputs, models or source have changed. Use a new run.")
    return lock


def current(run):
    name, config = "frozen-cauchy-mad", INCUMBENT.copy()
    results = {s: load(run / f"{s}-baselines.json")["selected"] for s in ("development", "validation")}
    history = []
    for folder in sorted(run.glob("round-*")):
        candidate = load(folder / "proposal.json")
        verdict = load(folder / "verdict.json")
        require(load(folder / "incumbent-validation.json") == results["validation"]
                and verify(load(folder / "validation.json"), results["validation"]) == verdict,
                f"Stored verdict or incumbent is inconsistent: {folder.name}")
        history.append({"proposal": candidate, "verdict": verdict})
        if verdict["accepted"]:
            name, config = folder.name, candidate["config"]
            results = {s: load(folder / f"{s}.json") for s in results}
    return name, config, results, history


def step(campaign, run):
    require(not (run / "FINAL_LOCK.json").exists(), "Final configuration already locked")
    lock = verify_development(campaign, run)
    name, config, baseline, history = current(run)
    development = acceptance(baseline["development"])["usable_ge_11"]
    validation = acceptance(baseline["validation"])["usable_ge_11"]
    if development["cep90"] is None or validation["cep90"] is None:
        print("No usable >=11-phone evidence in development or validation. No proposal.")
        return
    state = {"best_method": {"name": name, "config": config},
             "best_validation_metrics": {"by_scenario": {"field_11": {
                 "cep90": validation["cep90"], "failure_rate": 1 - validation["success30"]}}},
             "last_result": history[-1]["verdict"]["accepted"] if history else "baseline"}
    previous = [{"proposal": {"mechanism": k}} for k in ("cauchy", "adaptive_scale", "confidence")]
    proposal = propose(state, previous + history)
    if proposal is None:
        print("Proposal policy exhausted.")
        return
    proposal["field_context"] = {"development": development, "validation": validation,
                                 "actual_parent": name, "evidence": lock["evidence"]}
    if proposal["mechanism"] == "robust_loss":
        proposal["upstream_hypothesis"] = proposal["hypothesis"]
        proposal["hypothesis"] = "Huber may retain useful moderately inconsistent reports relative to Cauchy."
    folder = run / f"round-{len(history) + 1:02}"
    folder.mkdir()
    save(folder / "proposal.json", proposal)
    model = load(run / "models.json")[lock["primary"]]
    for split in ("development", "validation"):
        result = evaluate(campaign.assemble(split), model, "cauchy", proposal["config"])
        save(folder / f"{split}.json", result)
    save(folder / "incumbent-validation.json", baseline["validation"])
    subprocess.run([sys.executable, "-m", "ble_field.verifier",
                    str(folder / "validation.json"), str(folder / "incumbent-validation.json"),
                    str(folder / "verdict.json")], check=True)
    print(load(folder / "verdict.json")["decision"])


def research_hashes(run):
    names = ["development-lock.json", "models.json", "development-baselines.json", "validation-baselines.json"]
    for folder in sorted(run.glob("round-*")):
        names.extend(str(path.relative_to(run).as_posix()) for path in sorted(folder.glob("*.json")))
    return {name: digest(run / name) for name in names}


def freeze(campaign, run):
    path = run / "FINAL_LOCK.json"
    require(not path.exists(), "Final lock exists")
    development = verify_development(campaign, run)
    name, config, _, history = current(run)
    save(path, {"selected": name, "config": config, "research": research_hashes(run),
                "evidence": development["evidence"], "code": development["code"],
                "primary": development["primary"],
                "decisions": [r["verdict"]["accepted"] for r in history]})
    print(f"Final lock recorded. Selected: {name}.")


def final(campaign, run):
    require(not (run / "test-predictions.json").exists(), "Final predictions already exist")
    verify_development(campaign, run)
    lock = load(run / "FINAL_LOCK.json")
    require(lock["research"] == research_hashes(run) and lock["code"] == code_hashes(),
            "Locked research artifacts or code differ")
    before = campaign.hashes(("test",))
    campaign.verify_split_positions()
    rows = campaign.assemble("test")
    require(bool(rows), "No prescheduled test trials")
    fitted = load(run / "models.json")
    results = score_methods(rows, fitted, lock["primary"], lock["config"])
    require(before == campaign.hashes(("test",)), "Test inputs changed during evaluation")
    summary = {
        "evidence": lock["evidence"], "field_result": lock["evidence"] == "field",
        "campaign_id": campaign.plan["campaign_id"], "selected": lock["selected"],
        "methods": {k: acceptance(v) for k, v in results.items()},
        "measurement_diagnostics": diagnostics(rows, fitted[lock["primary"]]),
        "trials": rows,
    }
    save(run / "test-inputs.json", before)
    save(run / "test-summary.json", summary)
    save(run / "test-predictions.json", results)
    print(f"Final evaluated {len(rows)} {lock['evidence']} trials. "
          f"Summary: {run / 'test-summary.json'}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=("prepare", "step", "freeze", "final"))
    p.add_argument("campaign", type=Path)
    p.add_argument("run", type=Path)
    args = p.parse_args()
    globals()[args.action](Campaign(args.campaign), args.run)
