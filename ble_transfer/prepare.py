"""Fetch the pinned stationary logs and create fixed observation windows."""
import argparse
import hashlib
import json
import re
import tarfile
import urllib.request
from collections import Counter
from pathlib import Path

import numpy as np

REVISION = "77474b69dc7d73fc5b07b74d7b4b65f3235a663e"
URL = f"https://codeload.github.com/philotuxo/Position-Annotated-BLE-RSSI-Dataset/tar.gz/{REVISION}"
PACKAGE = Path(__file__).resolve().parent
SUPPORT_FILES = {"README.md", "LICENSE.md", "cnf/tetam.dev", "cnf/tetam.par",
                 "cnf/README.md", "hst/README.md"}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
                    encoding="utf-8")


def fetch(directory):
    directory.mkdir(parents=True, exist_ok=False)
    hashes = {}
    with urllib.request.urlopen(URL, timeout=75) as response, tarfile.open(
        fileobj=response, mode="r|gz"
    ) as archive:
        for member in archive:
            name = member.name.split("/", 1)[-1]
            if name.startswith("hst/set_2/"):
                break
            selected = name in SUPPORT_FILES or re.fullmatch(
                r"hst/set_1/sensor[1-4][0-2]_(?:\d+\.\d+_){2}\d+\.\d+\.mbd", name
            )
            if member.isfile() and selected:
                contents = archive.extractfile(member).read()
                path = directory / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(contents)
                hashes[name] = sha(contents)
    if len(hashes) != 978:
        raise ValueError(f"Expected 978 pinned members, found {len(hashes)}")
    save(directory / "manifest.json", {"revision": REVISION, "url": URL, "sha256": hashes})


def windows(raw, output):
    manifest = json.loads((raw / "manifest.json").read_text())
    if manifest["revision"] != REVISION or len(manifest["sha256"]) != 978:
        raise ValueError("Unexpected release manifest")
    original = PACKAGE / "source-manifest.json"
    if original.exists() and json.loads(original.read_text()) != manifest:
        raise ValueError("Downloaded members differ from the verified release snapshot")
    for path, expected in manifest["sha256"].items():
        if sha((raw / path).read_bytes()) != expected:
            raise ValueError(f"Hash mismatch: {path}")
    config = (raw / "cnf/tetam.dev").read_text().splitlines()
    sensors = json.loads(config[0].split(":", 1)[1])
    transmitter, = json.loads(config[1].split(":", 1)[1])
    receivers = sorted((entry[2], mac, entry[0]) for mac, entry in sensors.items())
    positions = sorted({Path(name).stem.split("_", 1)[1]
                        for name in manifest["sha256"] if name.endswith(".mbd")},
                       key=lambda key: sha(("ble-transfer-20261111/" + key).encode()))
    if len(positions) != 81 or len(receivers) != 12:
        raise ValueError("Unexpected stationary layout or position count")
    split = dict(zip(("calibration", "development", "validation", "test"),
                     (positions[:40], positions[40:50], positions[50:61], positions[61:])))
    coverage = {name: {str(seconds): Counter() for seconds in (1, 5, 30)} for name in split}
    rows = {name: [] for name in split}
    total_packets = 0
    invalid_packets = []
    for partition, keys in split.items():
        for key in keys:
            truth = [float(v) for v in key.split("_")]
            packets = []
            for alias, mac, _ in receivers:
                path = raw / "hst" / "set_1" / f"{alias}_{key}.mbd"
                pairs = []
                for line in path.read_text().splitlines():
                    timestamp, sender, beacon, rssi = line.split(",")
                    if sender != mac or beacon != transmitter:
                        raise ValueError(f"Inconsistent IDs in {path}")
                    total_packets += 1
                    if int(rssi) >= 0:
                        invalid_packets.append({"file": path.name, "timestamp": timestamp, "rssi": int(rssi)})
                    else:
                        pairs.append((float(timestamp), int(rssi)))
                values = np.array(pairs, dtype=float).reshape(-1, 2)
                if not np.isfinite(values).all() or np.any(values[:, 1] >= 0):
                    raise ValueError(f"Invalid packet in {path}")
                packets.append(values)
            begin = min(v[:, 0].min() for v in packets if len(v))
            end = max(v[:, 0].max() for v in packets if len(v))
            for seconds in (1, 5, 30):
                count = int((end - begin) // seconds)
                matrix = np.full((count, len(receivers)), np.nan)
                for j, values in enumerate(packets):
                    bins = ((values[:, 0] - begin) // seconds).astype(int)
                    order = np.argsort(bins, kind="stable")
                    bin_ids, starts, sizes = np.unique(bins[order], return_index=True, return_counts=True)
                    for bin_id, start, size in zip(bin_ids, starts, sizes):
                        if bin_id < count:
                            matrix[bin_id, j] = np.median(values[order[start:start + size], 1])
                coverage[partition][str(seconds)].update(map(int, np.sum(np.isfinite(matrix), axis=1)))
                if seconds == 5:
                    for index in range(0, count, 6):
                        rows[partition].append({"label": key, "key": f"{key}:{index}",
                                                "truth": truth[:2],
                                                "public": {"device": "stationary-beacon",
                                                           "rssi": [float(v) if np.isfinite(v) else None
                                                                    for v in matrix[index]]}})
    output.mkdir(parents=True, exist_ok=False)
    save(output / "layout.json", {"receivers": [r[0] for r in receivers],
                                 "anchors": [r[2][:2] for r in receivers], "split": split,
                                 "packet_count": total_packets, "invalid_packets": invalid_packets,
                                 "coverage": coverage})
    for partition, observations in rows.items():
        save(output / f"{partition}.json", observations)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["fetch", "windows"])
    parser.add_argument("raw", type=Path)
    parser.add_argument("output", type=Path, nargs="?")
    args = parser.parse_args()
    if args.action == "fetch":
        fetch(args.raw)
    else:
        windows(args.raw, args.output)
