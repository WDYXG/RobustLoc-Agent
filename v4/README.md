# Phase 4 — Cross-Problem Generalization

One core, two adapters, no LLM proposer. Prior v1–v3d bytes are frozen at
7c16b09 by PREVIOUS_FREEZE.json. See THEORY.md and LITERATURE_AUDIT.md before
interpreting a margin or an exact finite optimum.

`core/` contains the problem protocol, world provenance, symmetry search,
support-union arithmetic, certificates, general ambiguity subsets, actions,
minimax decisions, independent consumers and a deterministic research loop.
`problems/range_localization.py` wraps existing frozen range proofs and legacy
physical contracts. `problems/phase_retrieval.py` supplies squared intensities,
the sign quotient and a continuous annulus margin. PR does not import range
algorithms. Core does not branch on the problem name or import either adapter.

Exact quotient radii currently support planar Euclidean or sign metrics only;
the interface is extensible but arbitrary groups/dimensions are not implemented.
Finite catalog completeness is explicit. Unknown continuous worlds cannot be
enumerated by calling `feasible_worlds`: that method filters a supplied finite
catalog and labels possible numerical uncertainty.

From repository root:

```powershell
..\.venv\Scripts\python.exe -m pytest tests v2 v3/certified_agent/tests v3b/assumption_agent/tests v3c/trust_agent/tests v3d/minimal_trust/tests v4/tests -q
..\.venv\Scripts\python.exe -m v4.run --run v4/runs/cross-problem-reproduce-new
..\.venv\Scripts\python.exe -m v4.audit --run v4/runs/cross-problem-001
```

Use fresh run directories; never overwrite experiments. Final source/config
hashes precede evaluation. Runtime is separated from deterministic artifacts.
The formal run includes all43 Phase3C regressions, both-adapter q=1 noisy
recovery, the same research/action loop, and PR acquisition retaining a GLOBAL
q=1 corruption budget. Finite candidates are a declared grid, not a continuous
solver or sampled evidence of a positive margin. Both bound and error use the
adapter metric. New measurements may be corrupted; their prospective upper
certificate quantifies arbitrary allowed replies.

Four retained refutations: literal PR equality, q instead of2q deletion,
positive intensity margin at zero, and quotient three-point Helly transfer.
Transfer is reported per component with implementation/proof evidence, not as
an arbitrary percentage or a claim of learned research autonomy.
