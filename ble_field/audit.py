"""Refit models and replay the verifier and all predictions from sealed inputs."""
import argparse
from pathlib import Path

import numpy as np
from static_localization.service import INCUMBENT

from .analysis import acceptance, diagnostics, evaluate
from .campaign import Campaign, load, require, save
from .study import (calibration_models, code_hashes, current, research_hashes,
                    score_methods, verify_development)
from .verifier import verify


def audit(campaign, run):
    verify_development(campaign, run)
    lock = load(run / "FINAL_LOCK.json")
    require(lock["code"] == code_hashes() and lock["research"] == research_hashes(run),
            "Final lock integrity failure")
    require(load(run / "test-inputs.json") == campaign.hashes(("test",)), "Final test inputs changed")
    campaign.verify_split_positions()
    models = load(run / "models.json")
    require(calibration_models(campaign.assemble("calibration")) == models, "Calibration refit differs")
    primary = lock["primary"]
    datasets = {split: campaign.assemble(split) for split in ("development", "validation", "test")}
    reference = {}
    replays = 0
    for split in ("development", "validation"):
        replay = score_methods(datasets[split], models, primary, INCUMBENT)
        require(replay == load(run / f"{split}-baselines.json"), f"{split} baseline replay differs")
        reference[split] = replay["selected"]
        replays += sum(map(len, replay.values()))
    for folder in sorted(run.glob("round-*")):
        proposal = load(folder / "proposal.json")
        outcomes = {}
        for split in reference:
            outcomes[split] = evaluate(datasets[split], models[primary], "cauchy", proposal["config"])
            require(outcomes[split] == load(folder / f"{split}.json"), f"{folder.name} prediction replay differs")
            replays += len(outcomes[split])
        result = verify(outcomes["validation"], reference["validation"])
        require(result == load(folder / "verdict.json"), "Verifier replay differs")
        if result["accepted"]:
            reference = outcomes
    name, config, _, decisions = current(run)
    require(lock["selected"] == name and lock["config"] == config, "Final method differs from replay")
    require(lock["decisions"] == [item["verdict"]["accepted"] for item in decisions],
            "Final verdict sequence differs")
    truth = {row["trial_id"]: row for row in datasets["test"]}
    actual = load(run / "test-predictions.json")
    require(actual == score_methods(datasets["test"], models, primary, config), "Test predictions differ")
    summary = load(run / "test-summary.json")
    require(summary["evidence"] == campaign.plan["evidence"]
            and summary["field_result"] == (campaign.plan["evidence"] == "field"),
            "Evidence label differs")
    require(summary["trials"] == datasets["test"]
            and summary["measurement_diagnostics"] == diagnostics(datasets["test"], models[primary]),
            "Test inputs or measurement diagnostics differ")
    error_checks = 0
    for method, predictions in actual.items():
        require(acceptance(predictions) == summary["methods"][method], f"Metric replay differs: {method}")
        for item in predictions:
            record = truth[item["seed"]]
            require(item["n"] == sum(p["reason"] == "usable" for p in record["phones"]),
                    "Reporter count differs from distinct usable phones")
            error = item["error"]
            if item["estimate"] is None:
                require(error is None, "No-output trial carries an error")
            else:
                delta = np.array(item["estimate"]) - record["truth"]
                require(np.isclose(np.sqrt(delta @ delta), error, atol=1e-9, rtol=0), "Error replay differs")
            error_checks += 1
    audit_record = dict(passed=True, evidence=summary["evidence"], field_result=summary["field_result"],
                        calibration_refit=True, disjoint_survey_positions=True, verifier_replays=len(decisions),
                        solver_and_baseline_replays=replays + error_checks,
                        final_error_checks=error_checks, scheduled_test_trials=len(truth))
    save(run / "audit.json", audit_record)
    return audit_record


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("campaign", type=Path)
    parser.add_argument("run", type=Path)
    args = parser.parse_args()
    print(audit(Campaign(args.campaign), args.run))
