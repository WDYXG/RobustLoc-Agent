"""Add adaptive outcomes to the frozen replay and use its existing metrics."""
from copy import deepcopy

from ble_mobile.evaluate import outcome, public_fixes, replay

from .tracker import AdaptiveTracker, Ranges


def prepare(dataset, kalman):
    fixes = public_fixes(dataset)
    baseline = replay(dataset, fixes, {"cv-coast": kalman})
    public = {}
    for track in dataset["tracks"]:
        site = dataset["sites"][track["site"]]
        frames = []
        for frame, fix in zip(track["frames"], fixes[track["id"]], strict=True):
            ranges = Ranges.from_window(frame.get("positions", site["anchors"]), frame["rssi"], site["model"])
            frames.append((frame["t"], fix["cauchy"], ranges))
        public[track["id"]] = frames
    return public, baseline


def augment(dataset, prepared, candidates, kalman):
    public, baseline = prepared
    result = deepcopy(baseline)
    for track, scored in zip(dataset["tracks"], result, strict=True):
        estimators = {name: AdaptiveTracker(config, kalman=kalman) for name, config in candidates.items()}
        static = AdaptiveTracker(kalman=kalman, mode="stationary") if track["kind"] == "static" else None
        public_frames = public[track["id"]]
        for f, scored_frame, inputs in zip(track["frames"], scored["frames"], public_frames, strict=True):
            for name, tracker in estimators.items():
                estimate = tracker.step(*inputs)
                scored_frame["out"][name] = outcome(estimate, f["truth"]) | {"motion": tracker.motion}
            if static is not None:
                scored_frame["out"]["adaptive-declared-static"] = outcome(static.step(*inputs), f["truth"])
    return result
