"""Calibrate on surveyed training marks and score observation-only predictions."""
from collections import Counter, defaultdict

import numpy as np

from ble_transfer.experiment import geometry, locate, weighted_summary
from static_localization.service import INCUMBENT


FIXED = {"kind": "fixed", "intercept": -59., "slope": -20., "sigma": 4., "phones": {}}


def usable(row):
    return [phone for phone in row["phones"] if phone["reason"] == "usable"]


def calibration(rows, per_phone):
    records = []
    for row in rows:
        for phone in usable(row):
            if phone["survey_position"] is None:
                continue
            distance = np.linalg.norm(np.array(phone["survey_position"]) - row["truth"])
            records.append((row["label"], phone["reporter_id"],
                            np.log10(max(.5, distance)), phone["rssi_dbm"]))
    if not records:
        return None
    positions = defaultdict(set)
    for label, phone, _, _ in records:
        positions[phone].add(label)
    supported = {phone for phone, labels in positions.items() if len(labels) >= 3} if per_phone else set()
    groups = sorted({phone if phone in supported else "" for _, phone, _, _ in records})
    design = np.zeros((len(records), len(groups) + 1))
    counts = Counter(r[0] for r in records)
    scale = np.array([1 / np.sqrt(counts[label]) for label, *_ in records])
    response = np.array([r[3] for r in records])
    for i, (_, phone, distance, _) in enumerate(records):
        design[i, groups.index(phone if phone in supported else "")] = 1
        design[i, -1] = distance
    coef, _, rank, _ = np.linalg.lstsq(design * scale[:, None], response * scale, rcond=None)
    if rank < design.shape[1] or coef[-1] >= 0:
        return None
    residual = response - design @ coef
    pooled = np.average(response - coef[-1] * design[:, -1], weights=scale ** 2)
    intercepts = dict(zip(groups, coef[:-1].tolist()))
    return {"kind": "per-phone" if per_phone else "global",
            "intercept": intercepts.get("", float(pooled)), "slope": float(coef[-1]),
            "sigma": max(2., float(np.sqrt(np.average(residual ** 2, weights=scale ** 2)))),
            "phones": {k: v for k, v in intercepts.items() if k},
            "calibration_locations": len(counts), "calibration_links": len(records),
            "phone_position_counts": {k: len(v) for k, v in positions.items()}}


def prediction(positions, rssi, reporter_ids, model, method, config):
    if not len(positions):
        return None
    applied = dict(model, intercepts=[model["phones"].get(key, model["intercept"]) for key in reporter_ids])
    point, success = locate(positions, rssi, applied, method, config)
    return point if success else None


def evaluate(rows, model, method, config=INCUMBENT, surveyed=False):
    result = []
    for row in rows:
        phones = usable(row)
        positions = np.array([p["reported_position"] for p in phones])
        measured = [p for p in phones if p["survey_position"] is not None]
        if surveyed and len(measured) != len(phones):
            point = None
        else:
            solver_positions = np.array([p["survey_position"] for p in phones]) if surveyed else positions
            point = prediction(solver_positions, np.array([p["rssi_dbm"] for p in phones]),
                               [p["reporter_id"] for p in phones], model, method, config)
        # The surveyed target is only introduced after prediction.
        error = None if point is None else float(np.linalg.norm(point - row["truth"]))
        differences = [np.linalg.norm(np.array(p["reported_position"]) - p["survey_position"]) for p in measured]
        position_error = float(np.median(differences)) if differences else None
        result.append(dict(seed=row["trial_id"], label=row["label"], scenario="real", n=len(phones),
                           hosts=len(phones), heard=sum(p["heard"] for p in row["phones"]),
                           expected=row["expected"], site_id=row["site_id"],
                           layout_id=row["layout_id"], surveyed_usable=len(measured),
                           median_measured_receiver_error_m=position_error,
                           geometry=geometry(positions), error=error,
                           estimate=None if point is None else point.tolist()))
    return result


def acceptance(rows):
    all_planned = weighted_summary(rows)
    result = {"all_planned": all_planned}
    for threshold in (10, 11):
        cohort = [row for row in rows if row["n"] >= threshold]
        metrics = weighted_summary(cohort)
        # Report both the qualifying cohort and the complete planned-trial denominator.
        jointly = [{**row, "error": row["error"] if row["n"] >= threshold else None} for row in rows]
        result[f"usable_ge_{threshold}"] = {
            **metrics,
            "cep90_le_30_in_qualifying_outputs": None if metrics["cep90"] is None else metrics["cep90"] <= 30.,
            "joint_success30_all_planned": weighted_summary(jointly)["success30"],
            "trial_qualification_rate": len(cohort) / len(rows) if rows else None,
        }
    result["by_usable_count"] = {
        str(n): weighted_summary([row for row in rows if row["n"] == n])
        for n in sorted({row["n"] for row in rows})
    }
    result["by_geometry"] = {
        name: weighted_summary([r for r in rows if r["n"] >= 3 and (r["geometry"] < .15) == weak])
        for name, weak in (("clustered_or_linear", True), ("spread", False))
    }
    result["by_layout"] = {
        layout: weighted_summary([row for row in rows if row["layout_id"] == layout])
        for layout in sorted({row["layout_id"] for row in rows})
    }
    measured = [r for r in rows if r["median_measured_receiver_error_m"] is not None]
    result["by_measured_receiver_error"] = {
        name: weighted_summary([r for r in measured if low <= r["median_measured_receiver_error_m"] < high])
        for name, low, high in (("under_5m", 0., 5.), ("5_to_15m", 5., 15.), ("15m_or_more", 15., np.inf))
    }
    return result


def diagnostics(rows, model):
    devices = defaultdict(list)
    missing_survey = 0
    for row in rows:
        for phone in usable(row):
            if phone["survey_position"] is None:
                missing_survey += 1
                continue
            reported_error = float(np.linalg.norm(np.array(phone["reported_position"]) - phone["survey_position"]))
            distance = np.linalg.norm(np.array(phone["survey_position"]) - row["truth"])
            expected_rssi = (model["phones"].get(phone["reporter_id"], model["intercept"])
                             + model["slope"] * np.log10(max(.5, distance)))
            devices[phone["hardware"]].append((reported_error, phone["accuracy_m"],
                                               phone["rssi_dbm"] - expected_rssi, phone["reporter_id"]))
    reasons = Counter(phone["reason"] for row in rows for phone in row["phones"])
    groups = {}
    for hardware, values in devices.items():
        groups[hardware] = dict(phone_trials=len(values), phones=len({row[3] for row in values}),
                                position_error_median_m=float(np.median([row[0] for row in values])),
                                position_error_p90_m=float(np.quantile([row[0] for row in values], .9)),
                                reported_accuracy_median_m=float(np.median([row[1] for row in values])),
                                rssi_mean_residual_db=float(np.mean([row[2] for row in values])))
    return dict(reasons=dict(reasons), usable_phone_trials_without_survey=missing_survey, by_hardware=groups)
