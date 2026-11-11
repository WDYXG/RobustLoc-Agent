"""Independent validation gate for paired observations with abstention."""
import argparse
from pathlib import Path

from .experiment import load, summarize
from .prepare import save


def verify(candidate, incumbent):
    identity = ("seed", "label", "scenario", "n", "hosts", "geometry")
    if len(candidate) != len(incumbent) or any(
        tuple(a[k] for k in identity) != tuple(b[k] for k in identity)
        for a, b in zip(candidate, incumbent)
    ):
        raise ValueError("Validation cases are not paired")
    c, b = summarize(candidate), summarize(incumbent)
    gain = (b["overall"]["cep90"] - c["overall"]["cep90"]) / b["overall"]["cep90"]
    regressions = [scenario for scenario, metrics in c["by_scenario"].items()
                   if metrics["cep90"] > 1.15 * b["by_scenario"][scenario]["cep90"]
                   or metrics["coverage"] < b["by_scenario"][scenario]["coverage"] - 1e-12
                   or metrics["success30"] < b["by_scenario"][scenario]["success30"] - .02]
    lost = [a["seed"] for a, old in zip(candidate, incumbent)
            if a["error"] is None and old["error"] is not None]
    paired = [(a["error"] - old["error"], a, old) for a, old in zip(candidate, incumbent)
              if a["error"] is not None and old["error"] is not None and a["error"] > old["error"]]
    worst = [dict(case=a["seed"], scenario=a["scenario"], candidate=a["error"],
                  incumbent=old["error"], excess=gap)
             for gap, a, old in sorted(paired, key=lambda p: p[0], reverse=True)[:10]]
    return dict(accepted=bool(gain >= .02 and not regressions and not lost), relative_gain=gain,
                candidate=c, incumbent=b, regression_scenarios=regressions,
                lost_outputs=lost, worst_positive_excess=worst)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate")
    parser.add_argument("incumbent")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    save(args.output, verify(load(args.candidate), load(args.incumbent)))
