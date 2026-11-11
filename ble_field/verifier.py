"""Independent paired validation gate restricted to actual >=11-phone trials."""
import argparse
from pathlib import Path

from ble_transfer.verifier import verify as paired_gate
from ble_transfer.experiment import weighted_summary

from .campaign import load, require, save


def verify(candidate, incumbent):
    fields = ("seed", "label", "n", "expected", "site_id")
    require(len(candidate) == len(incumbent) and all(
        tuple(a[k] for k in fields) == tuple(b[k] for k in fields)
        for a, b in zip(candidate, incumbent)), "Candidate and incumbent trials differ")
    eligible = [(a, b) for a, b in zip(candidate, incumbent) if a["n"] >= 11]
    if not eligible or not all(any(pair[j]["error"] is not None for pair in eligible) for j in (0, 1)):
        return dict(accepted=False, decision="insufficient paired output evidence")
    if weighted_summary([p[1] for p in eligible])["cep90"] <= 1e-12:
        return dict(accepted=False, decision="incumbent has no measurable tail to improve")
    result = paired_gate([p[0] for p in eligible], [p[1] for p in eligible])
    result["decision"] = "accept" if result["accepted"] else "retain frozen incumbent"
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("candidate", type=Path)
    p.add_argument("incumbent", type=Path)
    p.add_argument("output", type=Path)
    args = p.parse_args()
    save(args.output, verify(load(args.candidate), load(args.incumbent)))
