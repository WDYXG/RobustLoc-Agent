"""Observation-only localization with fixed real and semi-synthetic scenarios."""
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from robustloc.baseline import solve_weighted
from robustloc.candidate import solve
from robustloc.simulator import Observation
from static_localization.service import INCUMBENT

PACKAGE = Path(__file__).resolve().parent
SOURCE = PACKAGE.parent / "ble_research/runs/real-001"
PORTFOLIO = ("real", "iid5", "drop50", "host1")
STRESS = ("iid2", "iid5", "iid10", "iid20", "shift10", "shift30",
          "drop25", "drop50", "host1", "random4", "cluster4")


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def fit(rows, anchors, per_receiver, source=None):
    groups = defaultdict(list)
    for row in rows:
        groups[row["label"]].append(row)
    design, response = [], []
    width = len(anchors) if per_receiver else 1
    for group in groups.values():
        values = np.array([row["public"]["rssi"] for row in group], dtype=float)
        distance = np.maximum(.5, np.linalg.norm(anchors - group[0]["truth"], axis=1))
        for j, column in enumerate(values.T):
            observed = column[np.isfinite(column)]
            if not len(observed):
                continue
            x = np.zeros(width + 1)
            x[j if per_receiver else 0] = 1
            x[-1] = np.log10(distance[j])
            design.append(x)
            response.append(np.mean(observed))
    x = np.array(design)
    y = np.array(response)
    if source is None:
        coef, _, rank, _ = np.linalg.lstsq(x, y, rcond=None)
        if rank != x.shape[1] or coef[-1] >= 0:
            raise ValueError("Unidentified or nondecreasing calibration")
    else:
        coef = np.array([np.mean(y - source["slope"] * x[:, -1]), source["slope"]])
    return dict(intercepts=(coef[:-1].tolist() if per_receiver else [float(coef[0])] * len(anchors)),
                slope=float(coef[-1]), sigma=max(2., float(np.sqrt(np.mean((x @ coef - y) ** 2)))))


def project(model, n):
    return dict(intercepts=[float(np.mean(model["intercepts"]))] * n,
                slope=model["slope"], sigma=model["sigma"])


def models(rows, anchors, calibration_labels):
    n = len(anchors)
    source = project(load(SOURCE / "model-global.json"), n)
    eight = set(calibration_labels[:8])
    return {
        "fixed": dict(intercepts=[-59.] * n, slope=-20., sigma=4.),
        "source-global": source,
        "source-final-mean": project(load(SOURCE / "final-bundle.json")["model"], n),
        "target-global": fit(rows, anchors, False),
        "target-receiver": fit(rows, anchors, True),
        "target-offset8": fit([row for row in rows if row["label"] in eight], anchors, False, source),
    }


def rng(key, repeat, tag):
    seed = int.from_bytes(hashlib.sha256(f"{key}/{repeat}/{tag}".encode()).digest()[:8], "little")
    return np.random.default_rng(seed)


def perturb(public, anchors, hosts, scenario, repeat, label, key):
    positions = anchors.copy()
    rssi = np.array(public["rssi"], dtype=float)
    if scenario.startswith("iid"):
        positions += float(scenario[3:]) * rng(label, repeat, "iid").normal(size=positions.shape)
    elif scenario.startswith("shift"):
        angle = rng(label, repeat, "shift").uniform(0, 2 * np.pi)
        positions += float(scenario[5:]) * np.array([np.cos(angle), np.sin(angle)])
    elif scenario.startswith("drop"):
        rssi[rng(key, repeat, "drop").random(len(rssi)) < float(scenario[4:]) / 100] = np.nan
    elif scenario == "host1":
        host = rng(key, repeat, "host").choice(np.unique(hosts))
        rssi[hosts == host] = np.nan
    elif scenario in ("random4", "cluster4"):
        visible = np.flatnonzero(np.isfinite(rssi))
        if len(visible) > 4:
            order = rng(key, repeat, "keep").permutation(visible)
            if scenario == "cluster4":
                order = order[np.argsort(np.linalg.norm(positions[order] - positions[order[0]], axis=1))]
            rssi[order[4:]] = np.nan
    return positions, rssi


def geometry(positions):
    if len(positions) < 3:
        return 0.
    delta = positions - positions.mean(axis=0)
    eig = np.linalg.eigvalsh(delta.T @ delta)
    return float(max(0., eig[0]) / max(1e-12, eig[1]))


def locate(positions, rssi, model, method, config):
    visible = np.isfinite(rssi)
    if method == "centre":
        return positions.mean(axis=0), True
    if method == "strongest":
        return (positions[np.nanargmax(rssi)], True) if visible.any() else (None, False)
    if visible.sum() < 3:
        return None, False
    distance = 10 ** ((rssi[visible] - np.array(model["intercepts"])[visible]) / model["slope"])
    sigma = np.maximum(.05, distance * np.log(10) * model["sigma"] / abs(model["slope"]))
    n = len(distance)
    obs = Observation(positions[visible], distance, np.full(n, config.get("position_sigma", 0.)),
                      sigma, np.ones(n), np.ones(n))
    answer = solve_weighted(obs) if method == "wls" else solve(obs, config)
    return (answer.position, True) if answer.success and np.isfinite(answer.position).all() else (None, False)


def evaluate(rows, anchors, hosts, model, method, config, scenarios):
    result = []
    for scenario in scenarios:
        for row in rows:
            for repeat in range(1 if scenario == "real" else 3):
                positions, rssi = perturb(row["public"], anchors, hosts, scenario, repeat,
                                          row["label"], row["key"])
                mask = np.isfinite(rssi)
                point, success = locate(positions, rssi, model, method, config)
                # Truth is introduced only after the solver returns.
                error = None if point is None else float(np.linalg.norm(point - row["truth"]))
                result.append(dict(seed=f"{row['key']}:{repeat}", label=row["label"],
                                   scenario=scenario, n=int(mask.sum()), hosts=len(set(hosts[mask])),
                                   geometry=geometry(positions[mask]), error=error, success=success,
                                   estimate=None if point is None else point.tolist()))
    return result


def weighted_summary(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[row["label"], row["scenario"]].append(row["error"])
    if not groups:
        return dict(rows=0, positions=0, outputs=0, cep90=None, coverage=None,
                    success5=None, success10=None, success30=None)
    errors, weights = [], []
    for group in groups.values():
        errors.extend(np.inf if x is None else x for x in group)
        weights.extend([1 / (len(groups) * len(group))] * len(group))
    errors, weights = np.array(errors), np.array(weights)
    visible = np.isfinite(errors)
    ordered = np.argsort(errors[visible])
    coverage = float(weights[visible].sum())
    cep90 = None
    if coverage:
        index = np.searchsorted(np.cumsum(weights[visible][ordered]), .9 * coverage)
        cep90 = float(errors[visible][ordered][index])
    return dict(rows=len(rows), positions=len({r["label"] for r in rows}), outputs=int(visible.sum()), cep90=cep90,
                coverage=coverage, **{f"success{t}": float(weights[errors <= t].sum()) for t in (5, 10, 30)})


def summarize(rows):
    return dict(overall=weighted_summary(rows),
                by_scenario={s: weighted_summary([r for r in rows if r["scenario"] == s])
                             for s in sorted({r["scenario"] for r in rows})})
