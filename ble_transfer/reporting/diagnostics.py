"""Post-test diagnostic summaries. This module never participates in selection."""
import argparse
import gzip
import json
from collections import Counter
from pathlib import Path

import matplotlib
import numpy as np

from ble_transfer.experiment import load, weighted_summary
from ble_transfer.prepare import save
from ble_transfer.study import DATA, layout

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def diagnostics(run):
    with gzip.open(run / "test-predictions.json.gz", "rt", encoding="utf-8") as stream:
        prediction = json.load(stream)
    real = prediction["real"]["selected"]
    stress = prediction["stress"]["selected"]
    strata = {}
    for scenario in sorted({r["scenario"] for r in real + stress}):
        rows = [r for r in real + stress if r["scenario"] == scenario]
        strata[scenario] = {
            "receiver_count": Counter(r["n"] for r in rows),
            "host_count": Counter(r["hosts"] for r in rows),
            "weak_geometry": weighted_summary([r for r in rows if r["geometry"] < .15 and r["n"] >= 3]),
            "spread_geometry": weighted_summary([r for r in rows if r["geometry"] >= .15 and r["n"] >= 3]),
            "under_three": weighted_summary([r for r in rows if r["n"] < 3]),
        }
    _, anchors, _ = layout()
    test = load(DATA / "test.json")
    fitted = load(run / "models.json")
    y = np.array([r["public"]["rssi"] for r in test], dtype=float)
    d = np.linalg.norm(np.array([r["truth"] for r in test])[:, None, :] - anchors, axis=2)
    available = np.isfinite(y)
    mismatch = {}
    for name, model in fitted.items():
        intercept = np.array(model["intercepts"])
        residual = y - (intercept + model["slope"] * np.log10(np.maximum(d, .5)))
        estimated = 10 ** ((y - intercept) / model["slope"])
        mismatch[name] = {
            "observed_links": int(available.sum()),
            "rssi_mean_residual_db": float(np.mean(residual[available])),
            "rssi_rmse_db": float(np.sqrt(np.mean(residual[available] ** 2))),
            "horizontal_range_mae_m": float(np.mean(np.abs(estimated[available] - d[available]))),
        }
    save(run / "diagnostics.json", {"strata": strata, "calibration_residuals": mismatch})
    summary = load(run / "test-summary.json")
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
    names = ["centre", "strongest", "fixed-cauchy", "source-final-projection",
             "target-offset8", "target-global-cauchy", "target-receiver-wls", "selected"]
    labels = ["Layout centre", "Strongest receiver", "Fixed Cauchy",
              "Source model (projected)", "Target 8-point offset", "Target global Cauchy",
              "Target receiver WLS", "Selected Cauchy"]
    axes[0].barh(labels, [summary["real"][k]["cep90"] for k in names], color="#287271")
    axes[0].invert_yaxis()
    axes[0].set(xlabel="CEP90 (m)", title="Real BLE on 20 held-out locations")
    by = summary["stress"]["selected"]["by_scenario"]
    cases = ["iid2", "iid5", "iid10", "iid20", "shift10", "shift30", "random4", "cluster4"]
    labels = ["IID 2 m", "IID 5 m", "IID 10 m", "IID 20 m", "Shift 10 m",
              "Shift 30 m", "Random 4", "Clustered 4"]
    axes[1].barh(labels, [by[k]["cep90"] for k in cases], color="#c77737")
    axes[1].axvline(30, color="#434343", linestyle="--", linewidth=1)
    axes[1].invert_yaxis()
    axes[1].set(xlabel="CEP90 among outputs (m)", title="Real RSSI with injected input errors")
    for ax in axes:
        ax.grid(axis="x", alpha=.2)
        ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(run / "comparison.png", dpi=160)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    diagnostics(parser.parse_args().run)
