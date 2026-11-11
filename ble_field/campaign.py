"""Validate field inputs and form one report per physical phone and trial."""
import argparse
import bisect
import hashlib
import json
import math
import os
import re
import statistics
import tempfile
import uuid
from pathlib import Path

import numpy as np

SPLITS = ("calibration", "development", "validation", "test")
DEVICE_FIELDS = ("reporter_id", "installation_id", "manufacturer", "model", "os_release", "sdk_int")
FIX_AGE_MS = 5000
START_TOLERANCE_MS = 2000
MAX_CLOCK_DRIFT_MS = 1000


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def save(path, value, *, replace=True):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2) + "\n"
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(content.encode("utf-8"))
    try:
        if replace:
            os.replace(temporary, path)
        elif os.name == "nt":
            os.rename(temporary, path)
        else:
            os.link(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def number(value):
    return type(value) in (int, float) and math.isfinite(value)


def code(value):
    return isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,48}", value) is not None


def unique(rows, field):
    result = {row[field]: row for row in rows}
    require(len(result) == len(rows), f"Duplicate {field}")
    return result


def latlon(value):
    lat, lon = value["lat"], value["lon"]
    require(number(lat) and number(lon) and -90 <= lat <= 90 and -180 <= lon <= 180,
            "Invalid WGS84 latitude/longitude")
    return lat, lon


def enu(value, origin):
    """Project WGS84 surface points to a common local east/north frame."""
    def ecef(point):
        latitude, longitude = np.radians(latlon(point))
        a = 6378137.
        e2 = 6.6943799901413165e-3
        radius = a / np.sqrt(1 - e2 * np.sin(latitude) ** 2)
        return radius * np.array([np.cos(latitude) * np.cos(longitude),
                                  np.cos(latitude) * np.sin(longitude),
                                  (1 - e2) * np.sin(latitude)])
    latitude, longitude = np.radians(latlon(origin))
    east = np.array([-np.sin(longitude), np.cos(longitude), 0])
    north = np.array([-np.sin(latitude) * np.cos(longitude),
                      -np.sin(latitude) * np.sin(longitude), np.cos(latitude)])
    return np.stack([east, north]) @ (ecef(value) - ecef(origin))


class Campaign:
    def __init__(self, root):
        self.root = Path(root)
        self.plan = load(self.root / "plan.json")
        p = self.plan
        require(p["schema"] == "robustloc-plan-v1" and code(p["campaign_id"]), "Invalid plan")
        require(p["evidence"] in ("field", "synthetic_fixture"), "Unrecognized evidence type")
        self.target_uuid = str(uuid.UUID(p["target_uuid"]))
        require(p["target_uuid"] == self.target_uuid, "Use the canonical lower-case target UUID")
        latlon(p["origin"])
        roster = load(self.root / "roster.json")
        require(roster["schema"] == "robustloc-roster-v1", "Invalid roster schema")
        self.devices = unique(roster["phones"], "reporter_id")
        unique(roster["phones"], "installation_id")
        self.trials = unique(p["trials"], "trial_id")
        require(self.trials and self.devices, "Plan and roster must be nonempty")
        location_splits, schedules = {}, {}
        for phone in self.devices.values():
            require(code(phone["reporter_id"]), "Invalid reporter ID")
            require(str(uuid.UUID(phone["installation_id"])) == phone["installation_id"],
                    "Use canonical installation UUIDs")
            require(type(phone["sdk_int"]) is int and all(
                isinstance(phone[k], str) and phone[k].strip() for k in DEVICE_FIELDS[2:5]),
                "Incomplete phone metadata")
        for trial in self.trials.values():
            ids = trial["reporter_ids"]
            require(all(code(trial[k]) for k in ("trial_id", "location_id", "site_id")),
                    "Invalid trial, location or site ID")
            require(code(trial.get("layout_id", "unspecified")), "Invalid layout ID")
            require(trial["split"] in SPLITS and type(trial["start_utc_ms"]) is int
                    and trial["start_utc_ms"] > 0 and type(trial["duration_ms"]) is int
                    and 5000 <= trial["duration_ms"] <= 120000, "Invalid trial timing or split")
            require(ids and len(set(ids)) == len(ids) and set(ids) <= self.devices.keys(),
                    "Duplicate or unregistered reporter in plan")
            location = trial["location_id"]
            scope = trial["split"], trial["site_id"]
            require(location_splits.setdefault(location, scope) == scope,
                    f"Location crosses split or site: {location}")
            for phone in ids:
                schedules.setdefault(phone, []).append((trial["start_utc_ms"],
                                                       trial["start_utc_ms"] + trial["duration_ms"]))
        for phone, intervals in schedules.items():
            order = sorted(intervals)
            require(all(a[1] <= b[0] for a, b in zip(order, order[1:])),
                    f"Overlapping trials for {phone}")

    def ticket(self, trial):
        return dict(schema="robustloc-ticket-v1", campaign_id=self.plan["campaign_id"],
                    target_uuid=self.target_uuid, **{k: trial[k] for k in (
                        "trial_id", "start_utc_ms", "duration_ms")})

    def capture_path(self, trial, reporter):
        return self.root / "captures" / trial["split"] / trial["trial_id"] / f"{reporter}.json"

    def validate_capture(self, report):
        require(report["schema"] == "robustloc-capture-v1", "Unknown capture schema")
        trial = self.trials[report["ticket"]["trial_id"]]
        phone = report["device"]["reporter_id"]
        require(report["ticket"] == self.ticket(trial), "Capture ticket does not match plan")
        require(phone in trial["reporter_ids"], "Reporter not scheduled in trial")
        require(all(report["device"][k] == self.devices[phone][k] for k in DEVICE_FIELDS),
                f"Roster identity or phone metadata mismatch: {phone}")
        require(report["status"] in ("complete", "interrupted", "error"), "Invalid capture status")
        require(type(report["armed_utc_ms"]) is int and type(report["ended_utc_ms"]) is int
                and report["armed_utc_ms"] <= report["ended_utc_ms"]
                and type(report["clock_drift_ms"]) is int, "Invalid capture clock metadata")
        scan = report["scan_started_utc_ms"]
        require(scan is None or type(scan) is int and report["armed_utc_ms"] <= scan <= report["ended_utc_ms"],
                "Invalid scan start")
        require(isinstance(report["packets"], list) and isinstance(report["fixes"], list),
                "Packets and fixes must be lists")
        for packet in report["packets"]:
            require(type(packet["t_utc_ms"]) is int and type(packet["rssi_dbm"]) is int,
                    "Invalid packet timestamp or RSSI")
        for fix in report["fixes"]:
            latlon(fix)
            require(type(fix["t_utc_ms"]) is int and number(fix["accuracy_m"])
                    and fix["accuracy_m"] >= 0 and type(fix["mock"]) is bool
                    and isinstance(fix["provider"], str) and bool(fix["provider"]), "Invalid location fix")
        return trial, phone

    def ingest(self, paths):
        pending = {}
        for path in paths:
            item = load(path)
            reports = item["reports"] if item["schema"] == "robustloc-capture-bundle-v1" else [item]
            for report in reports:
                trial, phone = self.validate_capture(report)
                destination = self.capture_path(trial, phone)
                prior = pending.get(destination)
                if destination.exists():
                    prior = load(destination)
                require(prior is None or prior == report, f"Conflicting records for {trial['trial_id']}/{phone}")
                pending[destination] = report
        for path, report in pending.items():
            try:
                save(path, report, replace=False)
            except FileExistsError:
                require(load(path) == report, f"Conflicting records for {path.name}")
        return len(pending)

    def survey(self, split):
        data = load(self.root / "survey" / f"{split}.json")
        require(data["schema"] == "robustloc-survey-v1" and data["evidence"] == self.plan["evidence"],
                "Survey provenance conflicts with plan")
        marks = unique(data["targets"], "location_id")
        trials = [t for t in self.trials.values() if t["split"] == split]
        require(set(marks) == {t["location_id"] for t in trials}, f"Missing or extra target marks: {split}")
        receiver_marks = {(r["trial_id"], r["reporter_id"]): r for r in data["receivers"]}
        require(len(receiver_marks) == len(data["receivers"]) and set(receiver_marks) <= {
            (t["trial_id"], phone) for t in trials for phone in t["reporter_ids"]},
            f"Duplicate or extra surveyed phone marks: {split}")
        for mark in list(marks.values()) + list(receiver_marks.values()):
            latlon(mark)
            require(isinstance(mark["method"], str) and mark["method"].strip()
                    and number(mark["uncertainty_m"]) and mark["uncertainty_m"] >= 0, "Incomplete survey provenance")
        return marks, receiver_marks

    def verify_split_positions(self, splits=SPLITS):
        marks = []
        for split in splits:
            targets, _ = self.survey(split)
            for key, target in targets.items():
                point = enu(target, self.plan["origin"])
                for old_key, old_split, old_point in marks:
                    require(old_split == split or np.linalg.norm(point - old_point) > .5,
                            f"Nearly coincident marks across splits: {old_key}, {key}")
                marks.append((key, split, point))

    def assemble(self, split):
        marks, phone_marks = self.survey(split)
        result = []
        for trial in self.trials.values():
            if trial["split"] != split:
                continue
            scheduled = trial["reporter_ids"]
            survey = marks[trial["location_id"]]
            summaries = []
            for reporter in scheduled:
                path = self.capture_path(trial, reporter)
                if path.exists():
                    report = load(path)
                    recorded_trial, recorded_phone = self.validate_capture(report)
                    require(recorded_trial == trial and recorded_phone == reporter, "Capture path mismatch")
                    entry = summarize_phone(report, trial, self.plan["origin"])
                else:
                    entry = dict(reason="missing_capture", heard=False, packet_count=0)
                entry["reporter_id"] = reporter
                entry["hardware"] = self.devices[reporter]["manufacturer"] + "/" + self.devices[reporter]["model"]
                truth = phone_marks.get((trial["trial_id"], reporter))
                entry["survey_position"] = None if truth is None else enu(truth, self.plan["origin"]).tolist()
                summaries.append(entry)
            result.append(dict(trial_id=trial["trial_id"], label=trial["location_id"],
                               site_id=trial["site_id"], expected=len(scheduled),
                               layout_id=trial.get("layout_id", "unspecified"),
                               truth=enu(survey, self.plan["origin"]).tolist(),
                               target_survey_uncertainty_m=survey["uncertainty_m"], phones=summaries))
        return result

    def hashes(self, splits):
        files = [self.root / "plan.json", self.root / "roster.json"]
        for split in splits:
            files.append(self.root / "survey" / f"{split}.json")
            for trial in self.trials.values():
                if trial["split"] == split:
                    files.extend(p for phone in trial["reporter_ids"]
                                 if (p := self.capture_path(trial, phone)).exists())
        return {p.relative_to(self.root).as_posix(): digest(p) for p in sorted(files)}


def summarize_phone(report, trial, origin):
    start = trial["start_utc_ms"]
    end = start + trial["duration_ms"]
    packets = sorted((p for p in report["packets"] if start <= p["t_utc_ms"] < end
                      and -127 <= p["rssi_dbm"] < 0), key=lambda p: p["t_utc_ms"])
    entry = dict(heard=bool(packets), packet_count=len(packets),
                 discarded_packets=len(report["packets"]) - len(packets))
    scan = report["scan_started_utc_ms"]
    if report["status"] != "complete":
        return dict(entry, reason=report["status"])
    if abs(report["clock_drift_ms"]) > MAX_CLOCK_DRIFT_MS:
        return dict(entry, reason="clock_changed")
    if scan is None or scan > start + START_TOLERANCE_MS or report["ended_utc_ms"] < end:
        return dict(entry, reason="incomplete_window")
    if not packets:
        return dict(entry, reason="no_target_packet")
    fixes = sorted((f for f in report["fixes"] if not f["mock"] and f["accuracy_m"] > 0
                    and report["armed_utc_ms"] <= f["t_utc_ms"] <= report["ended_utc_ms"]),
                   key=lambda f: f["t_utc_ms"])
    timestamps = [f["t_utc_ms"] for f in fixes]
    matched = []
    for packet in packets:
        j = bisect.bisect_right(timestamps, packet["t_utc_ms"]) - 1
        if j >= 0 and packet["t_utc_ms"] - timestamps[j] <= FIX_AGE_MS:
            matched.append((packet, fixes[j]))
    if not matched:
        return dict(entry, reason="no_fresh_location")
    return dict(entry, reason="usable", paired_packets=len(matched),
                rssi_dbm=statistics.median(p["rssi_dbm"] for p, _ in matched),
                reported_position=np.median([enu(f, origin) for _, f in matched], axis=0).tolist(),
                accuracy_m=statistics.median(f["accuracy_m"] for _, f in matched),
                providers=sorted({f["provider"] for _, f in matched}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("design")
    ticket = commands.add_parser("ticket")
    ticket.add_argument("trial")
    ingest = commands.add_parser("ingest")
    ingest.add_argument("files", type=Path, nargs="+")
    check = commands.add_parser("check")
    check.add_argument("split", choices=SPLITS)
    args = parser.parse_args()
    campaign = Campaign(args.root)
    if args.command == "design":
        campaign.verify_split_positions()
        print("Plan, survey marks and split membership verified")
    elif args.command == "ticket":
        print(json.dumps(campaign.ticket(campaign.trials[args.trial]), ensure_ascii=False))
    elif args.command == "ingest":
        print(f"Verified {campaign.ingest(args.files)} phone/trial records")
    else:
        rows = campaign.assemble(args.split)
        print(json.dumps([{ "trial": r["trial_id"], "planned": r["expected"],
                            "heard": sum(p["heard"] for p in r["phones"]),
                            "usable": sum(p["reason"] == "usable" for p in r["phones"]),
                            "reasons": {p["reporter_id"]: p["reason"] for p in r["phones"]}}
                          for r in rows], ensure_ascii=False, indent=2))
