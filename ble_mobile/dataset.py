"""Construct synthetic schedules over disjoint sets of measured BLE positions."""
from collections import defaultdict
import hashlib

from ble_crowd.study import calibrations, condition, load_site, scenarios, SITES
import numpy as np

SEED = "robustloc-mobile-001"
MOBILE = ("constant", "variable", "stop-go", "turn", "sparse", "outage")
STATIC = ("real", "coord5", "joint", "drop50", "one-sided")
SPLITS = ("development", "validation", "test")
ROUTE_POINTS = 5
ROUTES = 12
REPEATS = 3
STATIC_POINTS = 8
MAX_EDGE = 12.
VELOCITY = .85


def order(*parts):
    return int.from_bytes(hashlib.sha256(repr((SEED, *parts)).encode()).digest()[:8], "little")


def generator(*parts):
    return np.random.default_rng(order(*parts))


def source_id(site, key):
    return key.rsplit(":", 1)[0] if site == "A" else "stationary-beacon"


def source_groups(site, groups):
    result = {}
    for label, rows in groups.items():
        by_device = defaultdict(list)
        for row in rows:
            by_device[source_id(site, row[0])].append(row)
        result[label] = {device: sorted(rows, key=lambda r: int(r[0].rsplit(":", 1)[1]))
                         for device, rows in by_device.items()}
    return result


def shape(xy):
    delta = np.diff(np.asarray(xy), axis=0)
    lengths = np.linalg.norm(delta, axis=1)
    unit = delta / lengths[:, None]
    turns = np.degrees(np.arccos(np.clip(np.sum(unit[1:] * unit[:-1], axis=1), -1, 1)))
    return lengths, turns, float(np.linalg.norm(delta.sum(axis=0)) / lengths.sum())


def routes(site, split, groups, sources):
    labels = sorted(groups)
    xy = np.asarray([groups[label][0][1] for label in labels])
    distances = np.linalg.norm(xy[:, None] - xy, axis=2)
    graph = {i: [int(j) for j in np.argsort(distances[i], kind="stable")[1:6]
                 if distances[i, j] <= MAX_EDGE] for i in range(len(xy))}
    paths = [(i,) for i in graph]
    for _ in range(ROUTE_POINTS - 1):
        paths = [(*path, j) for path in paths for j in graph[path[-1]] if j not in path]
    families = {"straight": {}, "turn": {}}
    for path in paths:
        lengths, turns, efficiency = shape(xy[list(path)])
        max_turn = float(max(turns))
        family = "straight" if efficiency >= .68 and max_turn <= 100 else (
            "turn" if 100 < max_turn <= 155 and efficiency >= .33 else None)
        if family is None:
            continue
        sequence = tuple(labels[i] for i in path)
        # A/B each retain a single transmitter per synthetic trajectory.
        devices = set.intersection(*({d for d, r in sources[label].items() if len(r) >= 3}
                                     for label in sequence))
        if not devices:
            continue
        canonical = min(sequence, sequence[::-1])
        families[family].setdefault(canonical, (sequence, sorted(devices), lengths, max_turn, efficiency))
    result = {}
    for family, paths_by_key in families.items():
        candidates = sorted(paths_by_key, key=lambda key: order(site, split, family, key))
        # Prefer spatial support that is not yet represented by a selected route.
        used = set()
        chosen = []
        while candidates and len(chosen) < ROUTES:
            index = max(range(len(candidates)), key=lambda i: len(set(candidates[i]) - used))
            key = candidates.pop(index)
            chosen.append(paths_by_key[key])
            used.update(key)
        if not chosen:
            raise ValueError(f"No eligible {family} route in {site}/{split}")
        result[family] = chosen
    return result


def encode(rssi):
    return [float(value) if np.isfinite(value) else None for value in rssi]


def frame(t, label, row, rssi, removed, positions=None):
    key, truth, _ = row
    return dict(t=round(float(t), 9), label=label, source_key=key, truth=list(truth),
                rssi=encode(rssi), removed=removed,
                **({"positions": positions.tolist()} if positions is not None else {}))


def mobile_tracks(site, split, groups, sources):
    for family, paths in routes(site, split, groups, sources).items():
        cases = MOBILE if family == "straight" else ("turn",)
        cases = tuple(c for c in cases if c != "turn") if family == "straight" else cases
        for index, (path, devices, lengths, max_turn, efficiency) in enumerate(paths):
            route = f"{site}/{split}/{family}/{index:02}"
            for repeat in range(REPEATS):
                rng = generator(route, repeat)
                device = devices[int(rng.integers(len(devices)))]
                selected = [rng.choice(len(sources[label][device]), size=3, replace=False) for label in path]
                for scenario in cases:
                    speeds = [.45, .65, 1.25, 1.50] if scenario == "variable" else [VELOCITY] * len(lengths)
                    t = 0.
                    frames = []
                    outage_length = 2 + (repeat % 2)
                    for i, (label, choices) in enumerate(zip(path, selected)):
                        row = sources[label][device][choices[0]]
                        rssi = row[2].copy()
                        missing = "none"
                        if scenario == "sparse" and i in (1, 3, 4):
                            valid = np.flatnonzero(np.isfinite(rssi))
                            kept = generator(route, repeat, i, "sparse").permutation(valid)[:2]
                            rssi[~np.isin(np.arange(len(rssi)), kept)] = np.nan
                            missing = "sparse"
                        if scenario == "outage" and 4 - outage_length <= i < 4:
                            rssi[:] = np.nan
                            missing = "outage"
                        frames.append(frame(t, label, row, rssi, missing))
                        if scenario == "stop-go" and i == 2:
                            for j in (1, 2):
                                t += 4.
                                dwell = sources[label][device][choices[j]]
                                frames.append(frame(t, label, dwell, dwell[2], "none"))
                        if i < len(lengths):
                            t += lengths[i] / speeds[i]
                    yield dict(id=f"{route}/{repeat}/{scenario}", route=route, scenario=scenario, site=site,
                               kind="mobile", source_device=device, frames=frames,
                               path=list(path), segment_speeds=speeds, straightness=efficiency,
                               max_turn_deg=max_turn)


def static_tracks(site, split, anchors, groups, sources):
    old_scenarios = {sc.name: sc for sc in scenarios(site)}
    for label, rows in sorted(groups.items()):
        points = min(STATIC_POINTS, max(map(len, sources[label].values())))
        eligible = sorted(d for d, rs in sources[label].items() if len(rs) >= points)
        if points < 4:
            raise ValueError(f"No stationary window sequence at {site}/{split}/{label}")
        route = f"{site}/{split}/stationary/{label}"
        rng = generator(route)
        device = eligible[int(rng.integers(len(eligible)))]
        series = sources[label][device]
        start = int(rng.integers(len(series) - points + 1))
        block = series[start:start + points]
        valid = [r for r in series if np.isfinite(r[2]).sum() >= 6]
        # Match the frozen stress study's native >=6 eligibility for its four stress scenarios.
        stress = valid[:STATIC_POINTS]
        for scenario in STATIC:
            frames = []
            block_rows = block if scenario == "real" else stress
            if len(block_rows) < 4:
                continue
            for i, row in enumerate(block_rows):
                public = condition(site, split, old_scenarios[scenario], label, row, 0, anchors)
                if public is None:
                    # A design-infeasible one-sided layout is recorded as an empty observation.
                    frames.append(frame(4 * i, label, row, np.full(len(anchors), np.nan), "unsupported"))
                else:
                    p, rssi, _, _ = public
                    frames.append(frame(4 * i, label, row, rssi, scenario, p if scenario == "coord5" else None))
            yield dict(id=f"{route}/{scenario}", route=route, scenario=scenario, site=site,
                       kind="static", source_device=device, frames=frames)


def build(split):
    sites, tracks = {}, []
    for site in SITES:
        ids, anchors, hosts, groups = load_site(site, split)
        source = source_groups(site, groups)
        sites[site] = dict(ids=list(ids), anchors=anchors.tolist(), hosts=list(hosts),
                           model=calibrations(site)["local"], positions=len(groups))
        tracks.extend(mobile_tracks(site, split, groups, source))
        tracks.extend(static_tracks(site, split, anchors, groups, source))
    return dict(split=split, seed=SEED, sites=sites, tracks=tracks,
                data_type="stationary BLE replay with synthetic routes, timing and missingness")
