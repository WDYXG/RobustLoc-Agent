"""Deterministic synthetic inputs for software verification only."""
import argparse
import uuid
from pathlib import Path

import numpy as np

from .campaign import Campaign, SPLITS, save


def generate(root):
    root.mkdir(parents=True, exist_ok=False)
    origin = dict(lat=31., lon=121.)
    rng = np.random.default_rng(87521)
    campaign_id = "synthetic-software-check"
    phones = [dict(reporter_id=f"P{i+1:02}", installation_id=str(uuid.UUID(int=i + 1)),
                   manufacturer="Fixture", model=f"Virtual-{i % 3}", os_release="fixture", sdk_int=35)
              for i in range(12)]
    trials = []
    survey = {s: dict(schema="robustloc-survey-v1", evidence="synthetic_fixture", targets=[], receivers=[])
              for s in SPLITS}
    inputs = {}

    def coordinates(position):
        return dict(lat=origin["lat"] + float(position[1]) / 110870,
                    lon=origin["lon"] + float(position[0]) / 95500)

    def mark(position):
        return dict(**coordinates(position), method="synthetic_fixture", uncertainty_m=0.)

    count = 0
    for split, size in zip(SPLITS, (8, 4, 5, 8)):
        for index in range(size):
            key = f"T{count:03}"
            location = f"L{count:03}"
            target = np.array([100 * (count % 5), 90 * (count // 5)], dtype=float)
            start = 1900000000000 + 120000 * count
            ids = [p["reporter_id"] for p in phones]
            trials.append(dict(trial_id=key, location_id=location, split=split, site_id="fixture",
                               layout_id="spread", start_utc_ms=start, duration_ms=30000,
                               reporter_ids=ids))
            survey[split]["targets"].append(dict(location_id=location, **mark(target)))
            for j, phone in enumerate(phones):
                angle = 2 * np.pi * j / 12
                radial = np.array([np.cos(angle), np.sin(angle)]) * rng.uniform(10, 55)
                actual = target + radial
                reported = actual + rng.normal(0, 4, 2)
                survey[split]["receivers"].append(dict(trial_id=key, reporter_id=ids[j], **mark(actual)))
                if split == "test" and index == 2:
                    continue
                rssi = -61 - 19 * np.log10(np.linalg.norm(radial)) + (j % 3 - 1) * 3
                packets = [dict(t_utc_ms=start + ms, rssi_dbm=int(round(rssi + rng.normal())))
                           for ms in (1000, 4500, 8500)]
                fixes = [dict(**coordinates(reported), t_utc_ms=start + ms,
                              accuracy_m=6., provider="synthetic", mock=False)
                         for ms in (0, 4000, 8000)]
                status = "complete"
                if split == "test" and index == 1 and j == 0:
                    packets = []
                if split == "test" and index == 1 and j == 1:
                    fixes = [{**fixes[0], "t_utc_ms": start - 10000}]
                if split == "test" and index == 3 and j == 0:
                    status = "interrupted"
                inputs[key, ids[j]] = dict(schema="robustloc-capture-v1", device=phone, status=status,
                                          reason="fixture", armed_utc_ms=start - 20000,
                                          scan_started_utc_ms=start - 1000, ended_utc_ms=start + 30100,
                                          clock_drift_ms=0, packets=packets, fixes=fixes)
            count += 1
    save(root / "plan.json", dict(schema="robustloc-plan-v1", campaign_id=campaign_id,
                                 evidence="synthetic_fixture", origin=origin,
                                 target_uuid=str(uuid.UUID(int=1000)), trials=trials))
    save(root / "roster.json", dict(schema="robustloc-roster-v1", phones=phones))
    for split, marks in survey.items():
        save(root / "survey" / f"{split}.json", marks)
    campaign = Campaign(root)
    for (key, phone), capture in inputs.items():
        capture["ticket"] = campaign.ticket(campaign.trials[key])
    for phone in phones:
        key = phone["reporter_id"]
        path = root / "exports" / f"{key}.json"
        save(path, dict(schema="robustloc-capture-bundle-v1",
                        reports=[report for (_, reporter), report in inputs.items() if reporter == key]))
    campaign.ingest(sorted((root / "exports").glob("*.json")))
    campaign.verify_split_positions()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    generate(args.root)
    if args.verify:
        from .audit import audit
        from .study import final, freeze, prepare, step
        campaign = Campaign(args.root)
        run = args.root / "software-replay"
        prepare(campaign, run)
        step(campaign, run)
        freeze(campaign, run)
        final(campaign, run)
        print(audit(campaign, run))
