"""Choose one registered mechanism using observed development failures."""
from collections import Counter

from .verifier import static_guard


MECHANISMS = {
    "stationary": ({"adaptation": "stationary"},
                   "Three nearby past fixes can support a low-drift stationary regime."),
    "coast": ({"max_coast_s": 18.},
              "A longer freshness window can recover short gaps whose covariance stays below the same cap."),
    "maneuver": ({"adaptation": "maneuver"},
                 "A large innovation can signal a maneuver. Temporarily increasing process uncertainty gives the new observation more influence."),
    "robust": ({"adaptation": "robust"},
               "An unusually large innovation can be a bad BLE fix. Downweighting it may stabilize trajectories."),
}


def propose(records, metrics, parent, config, tried):
    mobile = [r for r in records if r["kind"] == "mobile"]
    failed = Counter()
    for track in mobile:
        for frame in track["frames"]:
            result = frame["out"][parent]
            if result["error"] is None or result["error"] > 10:
                failed[track["scenario"], result["reason"]] += 1
    recoverable = sum(
        12 < frame["out"][parent]["age_s"] <= 18
        for track in mobile for frame in track["frames"]
        if frame["out"][parent]["reason"] == "stale" and frame["out"][parent]["age_s"] is not None
    )
    guard = static_guard(metrics, parent)
    rank = {"stationary": 0 if not all(x["passed"] for x in guard.values()) else 4,
            "coast": 1 if recoverable else 5,
            "maneuver": 2 if any(sc in ("turn", "variable", "stop-go") for sc, _ in failed) else 6,
            "robust": 3}
    eligible = [name for name, (change, _) in MECHANISMS.items()
                if name not in tried and all(config.get(k) != v for k, v in change.items())
                and (name == "coast" or config["adaptation"] == "none")]
    if not eligible:
        return None
    mechanism = min(eligible, key=rank.get)
    change, hypothesis = MECHANISMS[mechanism]
    return dict(parent=parent, mechanism=mechanism, hypothesis=hypothesis,
                change=change, config=config | change,
                evidence=dict(static_guard=guard, stale_12_to_18_s=recoverable,
                              failures=[dict(scenario=k[0], reason=k[1], count=n) for k, n in failed.most_common()]),
                risk="New predictions may extend old motion through a turn, or suppress a useful new fix.")
