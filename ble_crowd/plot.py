"""Plot the paired final-study panels from sealed metrics."""
import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .study import read


def plot(run):
    data = read(run / "test-metrics.json")
    fig, axes = plt.subplots(2, 2, figsize=(10.5, 7.2), layout="constrained")
    colors = {"A": "#096a79", "B": "#bc512c"}
    for site, panels in data.items():
        color = colors[site]
        sizes = [3, 4, 6] if site == "A" else [3, 4, 6, 8, 10, 12]
        for ax, x, labels, metric in (
            (axes[0, 0], sizes, [f"count{n}" for n in sizes], "cep90"),
            (axes[0, 1], range(4), ["uniform", "random", "cluster", "one-sided"], "cep90"),
            (axes[1, 0], [0, 1, 3, 5, 10], ["ref6", "coord1", "coord3", "coord5", "coord10"], "cep90"),
            (axes[1, 1], [0, 25, 50], ["ref6", "drop25", "drop50"], "success30"),
        ):
            y = [panels[label]["cauchy"][metric] for label in labels]
            if metric == "success30":
                y = [100 * value for value in y]
            ax.plot(x, y, "o-", label=f"Site {site}", color=color, lw=2)
    axes[0, 0].set(title="Paired receiver count", xlabel="Distinct RF endpoints", ylabel="CEP90 (m)",
                   xticks=[3, 4, 6, 8, 10, 12])
    axes[0, 1].set(title="Four-receiver layout", ylabel="CEP90 (m)", xticks=range(4),
                   xticklabels=["Spread", "Random", "Cluster", "One-sided"])
    axes[1, 0].set(title="Receiver coordinate errors", xlabel="Per-axis SD (m)", ylabel="CEP90 (m)")
    axes[1, 1].set(title="Missing receivers", xlabel="Removal probability (%)",
                   ylabel="All-case success within 30 m (%)", ylim=(60, 102))
    for ax in axes.flat:
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", color="#e7ebed")
        ax.set_axisbelow(True)
    axes[0, 0].legend(loc="upper right", frameon=False)
    fig.suptitle("Crowd stress on measured BLE RSSI · frozen Cauchy + MAD", fontsize=14, weight="bold")
    fig.savefig(run / "stress-panels.png", dpi=180, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    plot(parser.parse_args().run)
