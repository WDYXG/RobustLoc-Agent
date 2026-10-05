# Verifier-Governed Codex Researcher

Phase 5 asks whether a real model can choose a useful **next research action**
from a mathematical frontier and feedback. The shared Range/PR core and all
4,083 pre-v5 files remain frozen. No new inverse problem is introduced.

Completed pilot: **8–8 productive formal-ledger steps** for scripted and Codex.
Codex completed 11 real proposals across 12 planned slots, including one
interrupted slot. This pilot does not establish superiority over the baseline.
Read the [Phase 5 review](runs/PHASE5_REVIEW.md) and
[final comparison](runs/comparison-v3-001/comparison.json).

The proposer emits one structured conjecture, refutation attempt, scoped
generalization, experiment or literature query. A read-only CLI process cannot
modify the kernel or ledger. Exact consumers decide the status of the formal
statement; the controller alone appends results. A failed attempt remains data.

Start with the [protocol](PROTOCOL.md), [tool grammar](researcher/TOOLS.md),
[initial frontier](researcher/frontier.json) and [hard gate](researcher/verifier.py).
The fixed [baseline](researcher/baseline.py) is absent from the Codex prompt.

Authoritative transport is [evaluator v2](runs/evaluator_v2/run.py). It fixes a
CLI startup-warning misclassification and pins the catalog-default available
model. Original sources/runs are retained; [issue record](runs/EVALUATOR_ISSUE_001.md).
Final repair metrics use [report evaluator v3](runs/evaluator_v3/run.py), which
corrects failed-repair counting without changing any mathematical verdict or
calling the model again; [metric issue](runs/EVALUATOR_ISSUE_002.md).

## Reproduce the evidence

From the repository directory, using its existing environment:

```powershell
..\.venv\Scripts\python.exe -m pytest tests v2 v3/certified_agent/tests v3b/assumption_agent/tests v3c/trust_agent/tests v3d/minimal_trust/tests v4/tests v5/tests v5/runs/evaluator_v2 -q
..\.venv\Scripts\python.exe -m v5.runs.evaluator_v2.run replay v5/runs/paired-v2-scripted-001
..\.venv\Scripts\python.exe -m v5.runs.evaluator_v2.run replay v5/runs/paired-v2-codex-001
..\.venv\Scripts\python.exe -m pytest v5/runs/operations_v1 v5/runs/evaluator_v3 -q
..\.venv\Scripts\python.exe -m v5.runs.evaluator_v3.run v5/runs/paired-v2-scripted-001 v5/runs/paired-v2-codex-001 v5/runs/new-metric-replay
```

Replay reruns mathematics on the **recorded actual proposals**, rebuilds the
research states, validates raw CLI receipts and reconstructs ledger/metrics.
It does not call the model or claim stochastic regeneration is identical.

For a fresh experiment, complete `codex login` in the host user environment,
then choose unused directories:

```powershell
..\.venv\Scripts\python.exe -m v5.runs.evaluator_v2.run scripted v5/runs/new-scripted
..\.venv\Scripts\python.exe -m v5.runs.evaluator_v2.run codex v5/runs/new-codex
..\.venv\Scripts\python.exe -m v5.runs.evaluator_v3.run v5/runs/new-scripted v5/runs/new-codex v5/runs/new-comparison
```

Run-directory reuse is refused. Do not copy credentials into the repository.
Windows host and sandbox credential availability can differ; the nested
research proposer itself must retain its declared **read-only** sandbox.
Never disable that sandbox to work around a failed login or tool call.

## What this system does and does not establish

The proof/search language and initial frontier are human supplied. Codex chooses
one claim, parameters, evidence request, and optional repair link each round.
Accepted algebra is exact, but its proposed physical interpretation is not
automatically certified. Finite samples are not continuous completeness, and
the offline literature registry is not an exhaustive novelty search.

The metric called productive steps is an operational proxy for nonduplicated
formal-ledger progress. It does not decide scientific importance or originality.
A single matched trajectory cannot establish broad superiority over scripted
research. Final claims must follow the actual comparison and retained failures.
