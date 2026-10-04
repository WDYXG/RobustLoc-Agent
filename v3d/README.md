# Phase 3C — Minimal Trust Optimality Gap

All previous tracked files at a4d5057 are frozen (3,686 byte hashes).
Read minimal_trust/THEORY.md, LITERATURE_AUDIT.md and SPEC.md. Results appear in
runs/minimal-trust-001/REPORT.md after actual execution.

The agent returns lower/upper cost and three budget states. Finite catalog
optima use exact rational enclosing circles and minimax trees. Continuous
lower bounds come from verified world restrictions; upper bounds use initial
hard-ball geometry uniformly over every exact-reference reply and select
measurement subsets. The cost3.6 old miss is a compulsory automatic regression.

Two essential counterexamples: global batch cover3 can exceed adaptive cost2;
pair-safe targets can form an unsafe triple. Finite positive equality is never
silently promoted to continuous optimality. Unresolved physical gaps remain.
One checked algebraic reduction closes a nonzero continuous optimum for an
exact zero-noise tangency prior. Its three scaled instances are explicitly
separated from the general continuous cases and from sampled restrictions.

From repository root:

```powershell
..\.venv\Scripts\python.exe -m pytest tests v2 v3/certified_agent/tests v3b/assumption_agent/tests v3c/trust_agent/tests v3d/minimal_trust/tests -q
..\.venv\Scripts\python.exe -m v3d.minimal_trust.run --run v3d/runs/minimal-trust-reproduce-new
..\.venv\Scripts\python.exe -m v3d.minimal_trust.audit --run v3d/runs/minimal-trust-001
..\.venv\Scripts\python.exe -m v3d.minimal_trust.cli --input v3d/examples/regression.json --output v3d/runs/cli-new.json
```

Do not overwrite existing runs. Runtime measurements are separate from
deterministic scientific artifacts. Finite/continuous scope, search limits,
failure cases, proofs, prior art and claim statuses are retained explicitly.
