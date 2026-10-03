# Phase 3B.2: Joint Nuisance Identifiability & Minimal Trust

All pre-Phase3B.2 tracked files are frozen at 1ed4e01 by PREVIOUS_FREEZE.json.
New work is in trust_agent/. Read THEORY.md, SPEC.md and LITERATURE_AUDIT.md.
This remains one range-localization case study with a finite decision agent.

The joint star map has rigid gauges AND nonrigid freedoms. Three noncollinear
fixed points only fix the absolute frame; target range connectivity and sparse
observability must also hold. A baseline alone never supplies absolute position.
Untrusted positions are excluded from a positive certificate unless a surviving
source branch or explicit external reference supports them. All possible source
deletion branches must be covered. Exact world pairs supply impossibility witnesses.

The finite trust frontier chooses the cheapest sufficient bundle under declared
forecast outcomes. Safety after delivery covers continuous worlds; finite
forecasts and nominal metadata do not replace physical trust assumptions.
Root honesty, group independence, q/r and D remain external conditions. Known
SLAM, rigidity, secure-estimation and Byzantine results are not new discoveries.

From repository root:

```powershell
..\.venv\Scripts\python.exe -m pytest tests v2 v3/certified_agent/tests v3b/assumption_agent/tests v3c/trust_agent/tests -q
..\.venv\Scripts\python.exe -m v3c.trust_agent.run --run v3c/runs/trust-identifiability-reproduce
..\.venv\Scripts\python.exe -m v3c.trust_agent.audit --run v3c/runs/trust-identifiability-001
..\.venv\Scripts\python.exe -m v3c.trust_agent.cli --input v3c/examples/no-reference.json --output v3c/runs/cli-preview/decision.json
```

Existing runs cannot be overwritten. Sources, config and seeds are frozen at
run creation. Actual report: runs/trust-identifiability-001/REPORT.md. Claims:
known / proved-in-project / conjectured / numerically-supported / refuted.
No physical root-validation protocol, universal optimality, general rigidity
solver, cross-problem result or autonomous theorem-discovery claim.
