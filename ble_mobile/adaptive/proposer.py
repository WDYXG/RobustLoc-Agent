"""Bounded policy selecting one mechanism from measured development failures."""
from collections import Counter

from ble_mobile.evaluate import summarize

from .tracker import DEFAULT

MECHANISMS = {
    "partial-ranges": ({"partial": True},
                       "A guarded update from one or two measured ranges can correct the history prior when a full fix is unavailable."),
    "uncertainty-horizon": ({"hold_s": 18.},
                            "A hold within the same uncertainty cap can bridge some 12–18 second gaps."),
    "fresh-innovation": ({"innovation": True},
                         "A strong current fix can be more useful than smoothing after an unexpectedly large innovation."),
}


def propose(records, parent, config, tried):
    metrics = summarize(records)["mobile"]["all"]
    if not tried:
        return dict(parent=parent, mechanism="hybrid", config=DEFAULT,
                    hypothesis="Holding a recent fix when motion is unconfirmed can improve coverage over CV alone.",
                    evidence={name: metrics[name] for name in ("cv-coast", "hold")})
    counts = Counter()
    for track in records:
        if track["kind"] != "mobile":
            continue
        for frame in track["frames"]:
            update = frame["out"][parent]
            error, age = update["error"], update["age_s"]
            if error is not None and error <= 10:
                continue
            n = frame["n"]
            if 0 < n <= 2 and age is not None and 0 < age <= 18:
                counts["partial-ranges"] += 1
            if update["reason"] == "stale" and age is not None and 12 < age <= 18:
                counts["uncertainty-horizon"] += 1
            current = frame["out"]["cauchy"]["error"]
            if n >= 4 and (update["nis"] or 0.) >= 4 and current is not None and current <= 10:
                counts["fresh-innovation"] += 1
    remaining = [mechanism for mechanism in MECHANISMS if mechanism not in tried and counts[mechanism]]
    if not remaining:
        return None
    mechanism = max(remaining, key=counts.get)
    change, hypothesis = MECHANISMS[mechanism]
    return dict(parent=parent, mechanism=mechanism, config=config | change, change=change,
                hypothesis=hypothesis, evidence=dict(opportunities=dict(counts), parent=metrics[parent]),
                risk="A stale or misclassified history prior may be more misleading than the current fix.")
