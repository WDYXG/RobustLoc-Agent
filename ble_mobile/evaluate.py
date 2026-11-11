"""Replay streaming methods on paired frames and score after each prediction."""
from collections import Counter

import numpy as np

from .tracker import Tracker, WINDOW_CONFIGS, Update, window


def public_fixes(data):
    cache = {}
    result = {}
    for track in data["tracks"]:
        site = data["sites"][track["site"]]
        fixes = []
        for frame in track["frames"]:
            positions = frame.get("positions", site["anchors"])
            key = track["site"], tuple(map(tuple, positions)), tuple(frame["rssi"])
            if key not in cache:
                p, rssi = np.array(positions), np.array(frame["rssi"], dtype=float)
                cache[key] = {name: window(p, rssi, site["model"], name) for name in WINDOW_CONFIGS}
            fixes.append(cache[key])
        result[track["id"]] = fixes
    return result


def outcome(update, truth):
    point = update.position
    return dict(point=None if point is None else point.tolist(),
                error=None if point is None else float(np.linalg.norm(point - truth)),
                reason=update.reason, age_s=update.age_s, sd=update.position_sd,
                nis=update.innovation_nis,
                velocity=None if update.velocity is None else update.velocity.tolist())


def replay(data, fixes, configs, baselines=True):
    result = []
    for track in data["tracks"]:
        trackers = {name: Tracker(config) for name, config in configs.items()}
        stationary = Tracker(mode="stationary") if track["kind"] == "static" and baselines else None
        prior = last_fix = None
        frames = []
        for frame, measures in zip(track["frames"], fixes[track["id"]], strict=True):
            t = frame["t"]
            current = measures["cauchy"]
            estimates = {name: tr.step(t, current) for name, tr in trackers.items()}
            if baselines:
                estimates.update({name: Update(point, None, "window" if point is not None else "no-fix",
                                               0. if point is not None else None, None)
                                  for name, point in measures.items()})
                if current is not None:
                    prior, last_fix = current, t
                age = None if last_fix is None else t - last_fix
                held = prior if age is not None and age <= 12 else None
                estimates["hold"] = Update(held, None, "held" if held is not None else "no-fix", age, None)
                if stationary is not None:
                    estimates["declared-static"] = stationary.step(t, current)
            frames.append(dict(t=t, source_key=frame["source_key"], removed=frame["removed"],
                               n=sum(value is not None for value in frame["rssi"]),
                               out={name: outcome(est, frame["truth"]) for name, est in estimates.items()}))
        result.append({k: track[k] for k in ("id", "site", "kind", "scenario", "route")} | {"frames": frames})
    return result


def weighted_quantile(samples, q):
    if not samples:
        return None
    samples = sorted(samples)
    values, weights = np.asarray(samples).T
    cdf = np.cumsum(weights)
    i = np.searchsorted(cdf, q * cdf[-1] - 1e-12)
    return float(values[i])


def longest_run(flags):
    longest = run = 0
    for flag in flags:
        run = run + 1 if flag else 0
        longest = max(longest, run)
    return longest


def metrics(tracks, method):
    if not tracks:
        return None
    strata = Counter((track["site"], track["scenario"]) for track in tracks)
    errors, gaps, ages = [], [], []
    totals = Counter()
    for track in tracks:
        frames = track["frames"]
        weight = 1 / (len(strata) * strata[track["site"], track["scenario"]])
        w = weight / len(frames)
        records = [frame["out"][method] for frame in frames]
        emitted = [r["error"] is not None for r in records]
        good = [r["error"] is not None and r["error"] <= 10 for r in records]
        times = [f["t"] for f, valid in zip(frames, emitted) if valid]
        intervals = np.diff(times)
        if len(intervals):
            gaps.extend((dt, weight / len(intervals)) for dt in intervals)
        totals["longest_output_fraction"] += weight * longest_run(emitted) / len(emitted)
        totals["longest_success10_fraction"] += weight * longest_run(good) / len(good)
        totals["complete_tracks_rate"] += weight * all(emitted)
        totals["adjacent_output_rate"] += weight * sum(a and b for a, b in zip(emitted, emitted[1:])) / (len(emitted) - 1)
        for r in records:
            totals["frames"] += 1
            if r["error"] is None:
                totals["no_output"] += 1
                continue
            totals["coverage"] += w
            totals["predicted_outputs"] += r["reason"] in ("predicted", "held") and r["age_s"] > 0
            errors.append((r["error"], w))
            ages.append((r["age_s"], w))
            for threshold in (5, 10, 30):
                totals[f"success{threshold}"] += w * (r["error"] <= threshold)
    for key in ("coverage", "success5", "success10", "success30"):
        totals[key] = min(1., float(totals[key]))
    return dict(totals, tracks=len(tracks), abstention=1 - totals["coverage"],
                no_output=totals["no_output"], predicted_outputs=totals["predicted_outputs"],
                cep50=weighted_quantile(errors, .5), cep90=weighted_quantile(errors, .9),
                update_interval_p50_s=weighted_quantile(gaps, .5),
                update_interval_p90_s=weighted_quantile(gaps, .9),
                emitted_fix_age_p90_s=weighted_quantile(ages, .9))


def summarize(records):
    answer = {}
    for kind in ("mobile", "static"):
        tracks = [r for r in records if r["kind"] == kind]
        methods = tuple(tracks[0]["frames"][0]["out"])
        groups = {"all": tracks}
        for site in sorted({r["site"] for r in tracks}):
            groups[site] = [r for r in tracks if r["site"] == site]
        for scenario in sorted({r["scenario"] for r in tracks}):
            groups[scenario] = [r for r in tracks if r["scenario"] == scenario]
            for site in ("A", "B"):
                selected = [r for r in groups[scenario] if r["site"] == site]
                if selected:
                    groups[f"{site}/{scenario}"] = selected
        answer[kind] = {key: {name: metrics(group, name) for name in methods}
                        for key, group in groups.items()}
    return answer
