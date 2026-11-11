"""Paired fixed-receiver replay and semi-synthetic crowd stress study."""
import argparse
import ast
import csv
import gzip
import hashlib
import itertools
import json
import os
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

for variable in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS"):
    os.environ[variable] = "1"

import numpy as np

from ble_transfer.experiment import geometry, load, locate, project
from robustloc.proposer import propose
from static_localization.service import INCUMBENT

ROOT = Path(__file__).resolve().parents[1]
DATA_A = ROOT / "ble_calibration/data"
RUN_A = ROOT / "ble_research/runs/real-001"
DATA_B = ROOT / "ble_transfer/observations"
RUN_B = ROOT / "ble_transfer/runs/transfer-001"
SITES = ("A", "B")
SEED = "crowd-stress-v1-20261111"
WINDOWS = 4
REPEATS = {"development": 2, "validation": 2, "test": 4}
COUNTS = (3, 4, 6, 8, 10, 12, 15)
LAYOUTS = ("uniform", "random", "cluster", "one-sided")
BASELINES = ("centre", "report-centre", "strongest", "wls", "cauchy")
MODELS = ("local", "local-global", "transferred", "transferred-global", "fixed",
          "slope-75", "slope-125", "offset-minus4", "offset-plus4")
GATE_SCENARIOS = ("real", "count6", "one-sided", "cluster", "coord5", "coord10",
                  "offset", "noise", "joint", "drop50", "sided-coord5-joint")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def seed(*parts):
    return int.from_bytes(hashlib.sha256(repr((SEED, *parts)).encode()).digest()[:8], "little")


def rng(*parts):
    return np.random.default_rng(seed(*parts))


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":")) + "\n").encode()
    path.write_bytes(gzip.compress(data, mtime=0) if path.suffix == ".gz" else data)


def read(path):
    return json.loads(gzip.decompress(path.read_bytes())) if path.suffix == ".gz" else load(path)


def input_hashes():
    paths = [DATA_A / "APS_Positions.txt", *sorted(DATA_A.glob("*.csv")),
             RUN_A / "split.json", RUN_A / "model-global.json", RUN_A / "final-bundle.json",
             DATA_B / "layout.json", *(DATA_B / f"{split}.json" for split in ("calibration", *REPEATS)),
             RUN_B / "models.json", Path(__file__),
             Path(__file__).parent / "PROTOCOL.md",
             *(ROOT / p for p in ("ble_transfer/experiment.py", "ble_transfer/verifier.py",
                                 "robustloc/baseline.py", "robustloc/proposer.py", "robustloc/candidate.py",
                                 "robustloc/optimizer.py", "static_localization/service.py"))]
    return {p.relative_to(ROOT).as_posix(): digest(p) for p in paths}


def a_layout():
    return ast.literal_eval((DATA_A / "APS_Positions.txt").read_text(encoding="utf-8").split("=", 1)[1])


def split_labels(site):
    if site == "B":
        return load(DATA_B / "layout.json")["split"]
    original = load(RUN_A / "split.json")
    if "splits" in original:
        original = original["splits"]
    validation = sorted(original["validation"], key=lambda label: seed("split-A", label))
    return {"calibration": original["calibration"], "development": validation[:16],
            "validation": validation[16:], "test": original["test"]}


def load_site(site, split):
    labels = split_labels(site)
    assert sum(map(len, labels.values())) == len(set().union(*map(set, labels.values())))
    wanted = set(labels[split])
    if site == "A":
        coordinates = a_layout()
        ids = tuple(coordinates)
        anchors = np.array(list(coordinates.values()))
        hosts = ids
        rows = []
        for path in sorted(DATA_A.glob("*.csv")):
            with path.open(newline="", encoding="utf-8") as f:
                for i, row in enumerate(csv.DictReader(f)):
                    if row["LABEL"] in wanted:
                        rssi = [float(row[j]) for j in ids]
                        rows.append((f"{path.stem}:{i}", row["LABEL"], (float(row["X"]), float(row["Y"])),
                                     [np.nan if x == -105 else x for x in rssi]))
    else:
        layout = load(DATA_B / "layout.json")
        ids = tuple(layout["receivers"])
        anchors = np.array(layout["anchors"])
        hosts = tuple(j[:-1] for j in ids)
        rows = [(r["key"], r["label"], tuple(r["truth"]), r["public"]["rssi"])
                for r in load(DATA_B / f"{split}.json")]
    assert anchors.shape == (len(ids), 2) and len(set(ids)) == len(ids) and np.isfinite(anchors).all()
    assert {row[1] for row in rows} == wanted and len({row[0] for row in rows}) == len(rows)
    grouped = defaultdict(list)
    for key, label, truth, rss in rows:
        rssi = np.asarray(rss, dtype=float)
        assert rssi.shape == (len(ids),) and np.isfinite(truth).all()
        assert np.all((rssi < 0) | np.isnan(rssi))
        grouped[label].append((key, truth, rssi))
    assert all(len({row[1] for row in group}) == 1 for group in grouped.values())
    assert len({group[0][1] for group in grouped.values()}) == len(grouped)
    return ids, anchors, hosts, grouped


def calibrations(site):
    bundle = load(RUN_A / "final-bundle.json")
    a = bundle["model"]
    b = load(RUN_B / "models.json")
    ag = load(RUN_A / "model-global.json")
    if site == "A":
        assert tuple(bundle["receiver_order"]) == tuple(a_layout())
        assert np.array_equal(bundle["anchors"], list(a_layout().values()))
        assert not any(a["device_offsets"].values()) and not a["hinge"] and "field" not in a
        local, glob, remote, remote_glob = a, ag, b["target-receiver"], b["target-global"]
    else:
        local, glob, remote, remote_glob = b["target-receiver"], b["target-global"], a, ag
    n = len(local["intercepts"])
    return dict(zip(MODELS, (
        local, glob, project(remote, n), project(remote_glob, n),
        dict(intercepts=[-59.] * n, slope=-20., sigma=4.),
        local | {"slope": .75 * local["slope"]},
        local | {"slope": 1.25 * local["slope"]},
        local | {"intercepts": [x - 4 for x in local["intercepts"]]},
        local | {"intercepts": [x + 4 for x in local["intercepts"]]},
    ), strict=True))


@dataclass(frozen=True)
class Scenario:
    name: str
    panel: int = 0
    count: int = 0
    layout: str = "random"
    position_sd: float = 0
    offset_sd: float = 0
    noise: bool = False
    drop: float = 0
    calibration: str = "local"


def scenarios(site):
    high = 10 if site == "A" else 12
    yield Scenario("real")
    for k in COUNTS:
        yield Scenario(f"count{k}", 6, k)
        if k <= high:
            yield Scenario(f"high{k}", high, k)
    for layout in LAYOUTS:
        yield Scenario(layout, 6, 4, layout)
    yield Scenario("ref6", 6, 6)
    for sd in (1, 3, 5, 10):
        yield Scenario(f"coord{sd}", 6, 6, position_sd=sd)
    for model in MODELS[1:]:
        yield Scenario(f"cal-{model}", calibration=model)
    yield Scenario("offset", 6, 6, offset_sd=4)
    yield Scenario("noise", 6, 6, noise=True)
    yield Scenario("joint", 6, 6, offset_sd=4, noise=True)
    yield Scenario("drop25", 6, 6, drop=.25)
    yield Scenario("drop50", 6, 6, drop=.50)
    for layout, sd, hw in itertools.product(("uniform", "one-sided"), (0, 5), (False, True)):
        if sd or hw:
            yield Scenario(f"{'sided' if layout == 'one-sided' else layout}-coord{sd}-{'joint' if hw else 'clean'}",
                           6, 4, layout, sd, 4 if hw else 0, hw)


def ordered_windows(site, split, panel, grouped):
    for label, group in sorted(grouped.items()):
        available = [row for row in group if np.isfinite(row[2]).sum() >= panel]
        yield label, sorted(available, key=lambda row: seed("window", site, split, row[0]))[:WINDOWS]


def support(grouped):
    sizes = {label: [int(np.isfinite(r[2]).sum()) for r in rs] for label, rs in grouped.items()}
    hist = Counter(n for counts in sizes.values() for n in counts)
    return dict(windows=sum(hist.values()), positions=len(sizes), histogram=dict(sorted(hist.items())),
                counts={k: dict(windows=sum(v for n, v in hist.items() if n >= k),
                                positions=sum(max(ns) >= k for ns in sizes.values()))
                        for k in (*COUNTS, 11)})


def arc(angles):
    ordered = np.sort(angles, axis=-1)
    gaps = np.diff(np.concatenate((ordered, ordered[..., :1] + 2 * np.pi), axis=-1), axis=-1)
    return 2 * np.pi - np.max(gaps, axis=-1)


@lru_cache(maxsize=8192)
def angular_choices(angles, visible, count):
    choices = np.array(list(itertools.combinations(visible, count)))
    spans = arc(np.asarray(angles)[choices])
    narrow = int(np.argmin(spans))
    return choices[np.argmax(spans)], choices[narrow] if spans[narrow] <= np.pi + 1e-12 else None


def condition(site, split, sc, label, row, repeat, anchors):
    key, truth, measured = row
    rssi = measured.copy()
    positions = anchors.copy()
    present = np.flatnonzero(np.isfinite(rssi))
    angles = tuple(np.arctan2(*(anchors - truth).T[::-1]))
    identity = (site, split, label, key, repeat)
    if sc.count:
        if len(present) < sc.count:
            return None
        order = rng(*identity, "receiver-order").permutation(present)
        if sc.layout in ("uniform", "one-sided"):
            uniform, sided = angular_choices(angles, tuple(present), sc.count)
            keep = uniform if sc.layout == "uniform" else sided
            if keep is None:
                return None
        elif sc.layout == "cluster":
            distances = np.linalg.norm(anchors[order] - anchors[order[0]], axis=1)
            keep = order[np.argsort(distances, kind="stable")[:sc.count]]
        else:
            keep = order[:sc.count]
        rssi[~np.isin(np.arange(len(rssi)), keep)] = np.nan
    if sc.drop:
        rssi[rng(*identity, "drop").random(len(rssi)) < sc.drop] = np.nan
    if sc.position_sd:
        positions += sc.position_sd * rng(site, split, label, repeat, "coord").normal(size=anchors.shape)
    if sc.offset_sd:
        offsets = rng(site, split, repeat, "hardware-offset").normal(size=len(rssi))
        rssi += sc.offset_sd * offsets
    if sc.noise:
        sd = rng(site, split, repeat, "hardware-scale").uniform(1, 5, len(rssi))
        rssi += sd * rng(*identity, "hardware-noise").normal(size=len(rssi))
    mask = np.isfinite(rssi)
    span = float(np.degrees(arc(np.array(angles)[mask]))) if mask.any() else None
    return positions, rssi, mask, span


def evaluate(job):
    site, split, sc, anchors, hosts, windows, model, methods = job
    result = []
    repeats = REPEATS[split] if sc.count else 1
    for label, rows in windows:
        for row in rows:
            key, truth, _ = row
            for repeat in range(repeats):
                public = condition(site, split, sc, label, row, repeat, anchors)
                record = dict(seed=f"{site}:{key}:{repeat}", label=f"{site}:{label}", scenario=sc.name,
                              site=site, panel=sc.panel, eligible=public is not None,
                              n=0, hosts=0, geometry=0., span=None, ids=[], errors={})
                if public is not None:
                    pos, rssi, mask, span = public
                    record.update(n=int(mask.sum()), hosts=len({hosts[i] for i in np.flatnonzero(mask)}),
                                  geometry=geometry(pos[mask]), span=span, ids=np.flatnonzero(mask).tolist())
                    for name, method, cfg in methods:
                        if method == "report-centre":
                            point, success = locate(pos[mask], rssi[mask], model, "centre", cfg) if mask.any() else (None, False)
                        else:
                            point, success = locate(pos, rssi, model, method, cfg)
                        record["errors"][name] = float(np.linalg.norm(point - truth)) if success else None
                else:
                    record["errors"] = {name: None for name, _, _ in methods}
                result.append(record)
    return result


def run_split(split, configs, workers, gate=False):
    jobs, audit = [], {}
    for site in SITES:
        ids, anchors, hosts, grouped = load_site(site, split)
        models = calibrations(site)
        audit[site] = {"receivers": ids, "hosts": hosts, **support(grouped)}
        selected = [sc for sc in scenarios(site) if not gate or sc.name in GATE_SCENARIOS]
        windows = {panel: list(ordered_windows(site, split, panel, grouped))
                   for panel in {sc.panel for sc in selected}}
        for sc in selected:
            methods = [(name, name if name in BASELINES else "cauchy", cfg)
                       for name, cfg in configs.items() if sc.calibration == "local" or name in ("wls", "cauchy")]
            jobs.append((site, split, sc, anchors, hosts, windows[sc.panel], models[sc.calibration], methods))
    with ProcessPoolExecutor(max_workers=workers) as pool:
        results = [row for batch in pool.map(evaluate, jobs) for row in batch]
    return results, audit


def metrics(rows, method):
    groups = Counter(row["label"] for row in rows)
    if not groups:
        return dict(cases=0, positions=0, eligible=0, outputs=0, no_output=0,
                    eligibility=None, coverage=None, eligible_coverage=None, cep50=None, cep90=None,
                    failure=None, success30=None, failure30=None)
    weights = np.array([1 / (len(groups) * groups[row["label"]]) for row in rows])
    errors = np.array([row["errors"][method] if row["errors"][method] is not None else np.inf for row in rows])
    eligible = np.array([row["eligible"] for row in rows])
    outputs = np.isfinite(errors)
    cover = float(np.clip(weights[outputs].sum(), 0, 1))
    elig = float(np.clip(weights[eligible].sum(), 0, 1))
    order = np.flatnonzero(outputs)[np.argsort(errors[outputs])]
    cdf = np.cumsum(weights[order])
    def percentile(q):
        return float(errors[order[np.searchsorted(cdf, q * cdf[-1])]]) if len(order) else None
    success30 = float(np.clip(weights[errors <= 30].sum(), 0, 1))
    return dict(cases=len(rows), positions=len(groups), eligible=int(eligible.sum()),
                outputs=int(outputs.sum()), no_output=int((~outputs).sum()),
                eligibility=elig, coverage=cover, eligible_coverage=min(1., cover / elig) if elig else None,
                cep50=percentile(.5), cep90=percentile(.9), failure=1 - cover,
                success30=success30, failure30=1 - success30)


def summarize(rows):
    panels = defaultdict(list)
    for row in rows:
        panels[row["site"], row["scenario"]].append(row)
    return {site: {name: {method: metrics(group, method) for method in group[0]["errors"]}
                   for (s, name), group in panels.items() if s == site} for site in SITES}


def verifier_records(rows, method):
    return [dict({key: row[key] for key in ("seed", "label", "scenario", "n", "hosts", "geometry")},
                 scenario=f'{row["site"]}/{row["scenario"]}', error=row["errors"][method])
            for row in rows if row["eligible"]]


def verify(rows, method, parent):
    from ble_transfer.verifier import verify as gate

    return gate(verifier_records(rows, method), verifier_records(rows, parent))


def proposer_input(rows, parent, config, last):
    summary = summarize(rows)
    return dict(best_method=dict(name=parent, config=config),
                best_validation_metrics=dict(by_scenario={
                    f"{site}/{name}": dict(cep90=ms[parent]["cep90"], failure_rate=ms[parent]["failure30"])
                    for site, panels in summary.items() for name, ms in panels.items()
                    if ms[parent]["cep90"] is not None}),
                last_result=last)


def research(output, workers):
    if output.exists():
        raise ValueError("Choose a fresh run directory")
    frozen = input_hashes()
    save(output / "START.json", dict(inputs=frozen, seed=SEED, windows=WINDOWS, repeats=REPEATS,
                                     splits={site: split_labels(site) for site in SITES},
                                     scenarios={site: [vars(sc) for sc in scenarios(site)] for site in SITES},
                                     models={site: calibrations(site) for site in SITES}))
    parent = "cauchy"
    configs = {name: INCUMBENT if name == parent else {} for name in BASELINES}
    validation, audit = run_split("validation", configs, workers, gate=True)
    development, dev_audit = run_split("development", configs, workers, gate=True)
    save(output / "incumbent-validation.json.gz", validation)
    save(output / "incumbent-development.json.gz", development)
    save(output / "pretest-support.json", dict(development=dev_audit, validation=audit))
    records = []
    # The historical transfer run already rejected a loss change. Cauchy and MAD
    # are in the incumbent. Pass those mechanisms to the existing policy as tried.
    history = [{"proposal": {"mechanism": mechanism}} for mechanism in
               ("robust_loss", "cauchy", "adaptive_scale", "confidence")]
    for round_number in (1, 2):
        state = proposer_input(validation, parent, configs[parent], records[-1]["verdict"]["accepted"] if records else "start")
        proposal = propose(state, history + records)
        candidate = proposal["mechanism"]
        prefix = output / f"round-{round_number:02}"
        worst = sorted((row for row in development if row["errors"][parent] is not None),
                       key=lambda row: row["errors"][parent], reverse=True)[:8]
        save(prefix / "proposal.json", dict(state=state, proposal=proposal, development_tail=worst))
        pair = {parent: configs[parent], candidate: proposal["config"]}
        dev, _ = run_split("development", pair, workers, gate=True)
        save(prefix / "development.json.gz", dev)
        val, _ = run_split("validation", pair, workers, gate=True)
        save(prefix / "validation.json.gz", val)
        verdict = verify(val, candidate, parent)
        save(prefix / "verdict.json", verdict)
        records.append(dict(proposal=proposal, verdict=verdict))
        print(f"Round {round_number}: {candidate}, gain {verdict['relative_gain']:.4f}, "
              f"accepted {verdict['accepted']}", flush=True)
        if verdict["accepted"]:
            configs[candidate] = proposal["config"]
            parent, validation, development = candidate, val, dev
    if input_hashes() != frozen:
        raise ValueError("Inputs changed during research")
    save(output / "FINAL_LOCK.json", dict(inputs=frozen, final_method=parent, methods=configs,
                                          decisions={f"round-{i:02}": digest(output / f"round-{i:02}/verdict.json")
                                                     for i in (1, 2)}))


def final(output, workers):
    lock = read(output / "FINAL_LOCK.json")
    if (output / "test-predictions.json.gz").exists():
        raise ValueError("Final results already exist")
    if input_hashes() != lock["inputs"]:
        raise ValueError("Frozen inputs changed")
    if any(digest(output / round_id / "verdict.json") != expected
           for round_id, expected in lock["decisions"].items()):
        raise ValueError("A validation verdict changed")
    rows, audit = run_split("test", lock["methods"], workers)
    save(output / "test-predictions.json.gz", rows)
    save(output / "test-support.json", audit)
    save(output / "test-metrics.json", summarize(rows))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("research", "final"))
    parser.add_argument("output", type=Path)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    (research if args.stage == "research" else final)(args.output, args.workers)


if __name__ == "__main__":
    main()
