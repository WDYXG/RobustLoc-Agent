"""Independent paired validation gate for motion policy changes."""
from .dataset import MOBILE
from .evaluate import summarize

EPS = 1e-10
MIN_GAIN = .005


def static_guard(metrics, method):
    checks = {}
    for site in ("A", "B"):
        cell = metrics["static"][f"{site}/real"]
        baseline, trial = cell["cauchy"], cell[method]
        allowed_cep = baseline["cep90"] + max(.25, .05 * baseline["cep90"])
        checks[site] = dict(passed=(trial["coverage"] + EPS >= baseline["coverage"]
                                    and all(trial[f"success{t}"] + .01 + EPS >= baseline[f"success{t}"]
                                            for t in (10, 30))
                                    and trial["cep90"] <= allowed_cep + EPS),
                            coverage_delta=trial["coverage"] - baseline["coverage"],
                            success10_delta=trial["success10"] - baseline["success10"],
                            success30_delta=trial["success30"] - baseline["success30"],
                            cep90_delta=trial["cep90"] - baseline["cep90"], allowed_cep90=allowed_cep)
    return checks


def verify(records, candidate, parent):
    if any(not {candidate, parent, "cauchy"} <= frame["out"].keys()
           for track in records for frame in track["frames"]):
        raise ValueError("Incomplete pairing")
    result = summarize(records)
    a, b = (result["mobile"]["all"][name] for name in (candidate, parent))
    gain = a["success10"] - b["success10"]
    bad = []
    for scenario in MOBILE:
        x, y = (result["mobile"][scenario][name] for name in (candidate, parent))
        if (x["success10"] + .05 + EPS < y["success10"] or x["coverage"] + .05 + EPS < y["coverage"]
                or x["cep90"] > 1.2 * y["cep90"] + EPS):
            bad.append(scenario)
    safety = static_guard(result, candidate)
    excess = []
    lost = []
    for track in records:
        for index, frame in enumerate(track["frames"]):
            new, old = (frame["out"][name]["error"] for name in (candidate, parent))
            if old is not None and new is None:
                lost.append(dict(track=track["id"], frame=index, old_error=old))
            if new is not None and old is not None and new > old:
                excess.append(dict(track=track["id"], frame=index, candidate_error=new,
                                   parent_error=old, excess=new - old))
    return dict(accepted=bool(gain >= MIN_GAIN and not bad and all(s["passed"] for s in safety.values())),
                candidate=candidate, parent=parent, success10_gain=gain, static_guard=safety,
                regression_scenarios=bad, lost_output_count=len(lost), lost_outputs=lost[:20],
                worst_positive_excess=sorted(excess, key=lambda e: e["excess"], reverse=True)[:12])
