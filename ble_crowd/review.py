"""Independent metric and pairing checks on a sealed run."""
import argparse
import math
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from ble_transfer.experiment import locate, summarize
from ble_transfer.verifier import verify

from .study import (BASELINES, GATE_SCENARIOS, SITES, calibrations, condition, digest,
                    input_hashes, load_site, read, rng, save, scenarios, verifier_records)


def independent_metrics(rows, method):
    groups = Counter(row["label"] for row in rows)
    weighted = [(row["errors"][method], 1 / (len(groups) * groups[row["label"]])) for row in rows]
    emitted = sorted((error, w) for error, w in weighted if error is not None)
    coverage = math.fsum(w for _, w in emitted)
    success = math.fsum(w for error, w in emitted if error <= 30)
    eligibility = math.fsum(w for row, (_, w) in zip(rows, weighted) if row["eligible"])
    def cep(q):
        threshold = q * coverage
        cumulative = 0
        for error, weight in emitted:
            cumulative += weight
            if cumulative >= threshold - 1e-12:
                return error
        return None
    return dict(coverage=coverage, cep50=cep(.5), cep90=cep(.9), success30=success,
                eligibility=eligibility, eligible_coverage=coverage / eligibility if eligibility else None,
                no_output=len(rows) - len(emitted), outputs=len(emitted), cases=len(rows),
                eligible=sum(row["eligible"] for row in rows), positions=len(groups),
                failure=1 - coverage, failure30=1 - success)


def interval(pairs, site, tag):
    groups = defaultdict(list)
    for a, b in pairs:
        ea, eb = a[1], b[1]
        groups[a[0]].append(((ea is not None and ea <= 30) - (eb is not None and eb <= 30),
                            (ea is not None) - (eb is not None),
                            ea - eb if ea is not None and eb is not None else None))
    if not groups:
        return dict(positions=0, cases=0)
    means = np.asarray([[np.mean([x[i] for x in group if x[i] is not None])
                         if any(x[i] is not None for x in group) else np.nan
                         for i in range(3)] for group in groups.values()])
    generator = rng("review-bootstrap", site, tag)
    estimates = {}
    for i, name in enumerate(("success30", "coverage", "common_output_mae_m")):
        sample = means[np.isfinite(means[:, i]), i]
        if len(sample):
            draws = generator.choice(sample, size=(2000, len(sample)), replace=True).mean(axis=1)
            estimates[name] = dict(estimate=float(sample.mean()), positions=len(sample),
                                   interval=np.quantile(draws, [.025, .975]).tolist())
    return dict(positions=len(groups), cases=len(pairs), **estimates)


def paired_contrasts(panels, method):
    contrasts = [("count6", "count3"), ("count6", "count4"), ("high10", "high6"),
                 ("high12", "high6"), ("uniform", "one-sided"), ("uniform", "cluster"),
                 ("coord5", "ref6"), ("coord10", "ref6"), ("joint", "ref6"),
                 ("drop50", "ref6"), ("sided-coord5-joint", "one-sided"),
                 ("cal-transferred", "real"), ("cal-local-global", "real")]
    output = {}
    for site in SITES:
        result = output[site] = {}
        for candidate, reference in contrasts:
            old = {row["seed"]: row for row in panels.get((site, reference), []) if row["eligible"]}
            pairs = []
            for row in panels.get((site, candidate), []):
                before = old.get(row["seed"])
                if row["eligible"] and before and method in row["errors"] and method in before["errors"]:
                    pairs.append(((row["label"], row["errors"][method]),
                                  (before["label"], before["errors"][method])))
            result[f"{candidate} minus {reference}"] = interval(pairs, site, (candidate, reference))
        for baseline in ("centre", "report-centre", "strongest", "wls"):
            for scenario in ("real", "coord5", "one-sided", "sided-coord5-joint", "joint"):
                pairs = [((row["label"], row["errors"][method]), (row["label"], row["errors"][baseline]))
                         for row in panels.get((site, scenario), []) if row["eligible"]]
                result[f"{scenario}: {method} minus {baseline}"] = interval(pairs, site, (scenario, baseline))
    return output


def audit(run, results):
    lock = read(run / "FINAL_LOCK.json")
    start = read(run / "START.json")
    assert lock["inputs"] == start["inputs"] == input_hashes()
    assert (run / "FINAL_LOCK.json").stat().st_mtime_ns <= (run / "test-predictions.json.gz").stat().st_mtime_ns
    parent = "cauchy"
    for round_id, expected in lock["decisions"].items():
        prefix = run / round_id
        proposal = read(prefix / "proposal.json")["proposal"]
        assert proposal["parent"] == parent
        validation = read(prefix / "validation.json.gz")
        assert {r["scenario"] for r in validation} == set(GATE_SCENARIOS)
        decision = verify(verifier_records(validation, proposal["mechanism"]), verifier_records(validation, parent))
        assert decision == read(prefix / "verdict.json") and digest(prefix / "verdict.json") == expected
        if decision["accepted"]:
            parent = proposal["mechanism"]
    assert lock["final_method"] == parent
    checked = {}
    for site in SITES:
        seen = set()
        for split in ("calibration", "development", "validation", "test"):
            ids, anchors, hosts, groups = load_site(site, split)
            positions = {group[0][1] for group in groups.values()}
            assert seen.isdisjoint(positions)
            seen.update(positions)
        models = calibrations(site)
        assert start["models"][site] == models
        sources = {f"{site}:{key}": (label, row) for label, group in groups.items() for row in group for key in [row[0]]}
        cases = {sc.name: sc for sc in scenarios(site)}
        paired = Counter()
        stats = Counter()
        all_rows = [row for row in results if row["site"] == site]
        for row in all_rows:
            identifier, repeat = row["seed"].rsplit(":", 1)
            label, original = sources[identifier]
            assert row["label"] == f"{site}:{label}"
            sc = cases[row["scenario"]]
            receiver_ids = row["ids"]
            paired[row["scenario"], row["seed"]] += 1
            assert row["n"] == len(set(receiver_ids)) and row["n"] <= np.isfinite(original[2]).sum()
            assert all(np.isfinite(original[2][i]) for i in receiver_ids)
            assert row["hosts"] == len({hosts[i] for i in receiver_ids})
            assert (row["span"] <= 180 + 1e-8 if row["eligible"] and sc.layout == "one-sided" else True)
            if not row["eligible"]:
                assert not receiver_ids and all(error is None for error in row["errors"].values())
                stats["unsupported_checked"] += 1
            else:
                assert sc.drop or not sc.count or len(receiver_ids) == sc.count
            if stats[sc.name] < 3:
                public = condition(site, "test", sc, label, original, int(repeat), anchors)
                assert (public is not None) == row["eligible"]
                if public is not None:
                    pos, rssi, mask, _ = public
                    assert np.flatnonzero(mask).tolist() == receiver_ids
                    assert sc.position_sd or np.array_equal(pos, anchors)
                    if not sc.noise and not sc.offset_sd:
                        assert np.array_equal(rssi[mask], original[2][mask])
                    for name, error in row["errors"].items():
                        cfg = lock["methods"][name]
                        method = name if name in BASELINES else "cauchy"
                        if method == "report-centre":
                            solution = pos[mask].mean(axis=0) if mask.any() else None
                        else:
                            point, success = locate(pos, rssi, models[sc.calibration], method, cfg)
                            solution = point if success else None
                        expected = None if solution is None else math.dist(solution, original[1])
                        assert expected == error or math.isclose(expected, error, abs_tol=1e-10)
                stats[sc.name] += 1
        assert paired and max(paired.values()) == 1
        index = {(r["scenario"], r["seed"]): r for r in all_rows}
        for row in all_rows:
            if row["scenario"] in ("count3", "count4", "high3", "high4", "high6", "high8", "high10"):
                prefix, count = ("high", int(row["scenario"][4:])) if row["scenario"].startswith("high") else (
                    "count", int(row["scenario"][5:]))
                larger = {3: 4, 4: 6, 6: 8, 8: 10, 10: 12}[count]
                other = index.get((f"{prefix}{larger}", row["seed"]))
                if other and row["eligible"] and other["eligible"]:
                    assert set(row["ids"]) <= set(other["ids"])
            if row["scenario"] == "drop50":
                assert set(row["ids"]) <= set(index["drop25", row["seed"]]["ids"])
        checked[site] = dict(receiver_cases=len(all_rows), checked_scenario_replays=sum(stats[s] for s in cases),
                             unsupported_checked=stats["unsupported_checked"],
                             distinct_physical_positions_across_splits=len(seen))
    return dict(inputs_unchanged=True, verdicts_replayed=True, lock_precedes_test=True, sites=checked)


def review(run):
    results = read(run / "test-predictions.json.gz")
    metrics = read(run / "test-metrics.json")
    verified = audit(run, results)
    panels = defaultdict(list)
    for row in results:
        panels[row["site"], row["scenario"]].append(row)
    for (site, scenario), group in panels.items():
        for name, summary in metrics[site][scenario].items():
            for metric, value in independent_metrics(group, name).items():
                stored = summary[metric]
                # At exact mass boundaries either adjacent observed quantile is
                # valid if the lower endpoint carries exactly the threshold.
                if metric in ("cep50", "cep90") and stored is not None:
                    q = .5 if metric == "cep50" else .9
                    errors = defaultdict(list)
                    for row in group:
                        errors[row["label"]].append(row["errors"][name])
                    lt = math.fsum(sum(x is not None and x < stored for x in e) / len(e) for e in errors.values()) / len(errors)
                    le = math.fsum(sum(x is not None and x <= stored for x in e) / len(e) for e in errors.values()) / len(errors)
                    assert lt <= q * summary["coverage"] + 1e-12 <= le + 2e-12
                    continue
                assert stored == value or math.isclose(stored, value, abs_tol=1e-12)
    verified["method_cells_checked"] = sum(len(methods) for scenarios in metrics.values() for methods in scenarios.values())
    portfolio = [r for r in results if r["scenario"] in GATE_SCENARIOS]
    method = read(run / "FINAL_LOCK.json")["final_method"]
    verified["heldout_gate_portfolio"] = {
        name: summarize(verifier_records(portfolio, name))["overall"]
        for name in dict.fromkeys(("wls", "cauchy", method))
    }
    verified["result_hashes"] = {name: digest(run / name) for name in
                                 ("FINAL_LOCK.json", "test-predictions.json.gz", "test-metrics.json", "test-support.json")}
    verified["review_source_sha256"] = digest(Path(__file__))
    save(run / "review.json", verified)
    contrasts = {name: paired_contrasts(panels, name) for name in dict.fromkeys(("cauchy", method))}
    if method != "cauchy":
        for site in SITES:
            for (s, scenario), group in panels.items():
                if s == site and method in group[0]["errors"]:
                    pairs = [((r["label"], r["errors"][method]), (r["label"], r["errors"]["cauchy"]))
                             for r in group if r["eligible"]]
                    contrasts[method][site][f"{scenario}: {method} minus cauchy"] = interval(pairs, site, scenario)
    save(run / "contrasts.json", contrasts)
    print(verified)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    review(parser.parse_args().run)
