"""Render the sealed six-scenario comparison."""
import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from ble_crowd.study import read


def render(run):
    metrics = read(run / "test-metrics.json")["mobile"]
    chosen = read(run / "FINAL_LOCK.json")["final_method"]
    scenarios = ("constant", "variable", "stop-go", "turn", "sparse", "outage")
    x = np.arange(len(scenarios))
    fig, ax = plt.subplots(figsize=(10.2, 4.8), layout="constrained")
    methods = (("cauchy", "Window Cauchy + MAD", "#637181"),
               (chosen, "CV Kalman + Cauchy", "#087483"),
               ("hold", "Hold last fix (12 s)", "#b85a30"))
    for index, (name, label, color) in enumerate(methods):
        ax.bar(x + .23 * (index - 1), [100 * metrics[sc][name]["success10"] for sc in scenarios],
               width=.21, color=color, label=label)
    ax.set(title="Held-out semi-synthetic BLE motion replay",
           ylabel="Success within 10 m (%)", ylim=(0, 113),
           xticks=x, xticklabels=["Constant\nspeed", "Variable\nspeed", "Stop–go", "Sharp turn",
                                   "Sparse\nobservations", "Consecutive\noutage"])
    ax.grid(axis="y", color="#e5e9ec")
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, loc="upper center", ncols=3)
    fig.savefig(run / "scenario-comparison.png", dpi=180, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    render(parser.parse_args().run)
