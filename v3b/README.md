# MathResearch-Agent — Phase 3B.1

Range localization remains the single case study. This phase moves from fixed
contracts to sufficient assumption frontiers and costed information purchases.
All 1,417 files tracked at f896a3ef remain frozen by PREVIOUS_FREEZE.json.

Read assumption_agent/SPEC.md, THEORY.md and LITERATURE_AUDIT.md for the input
assumptions, derivations, counterexamples and prior-art limits. In particular,
positive shared-map robust margin does not remove unknown-anchor translation
ambiguity: nominal estimation must include anchor model error zeta_q.

Input: rational anchors/weights/ranges, q upper set {0,...,Q}, clean norm
budget [0,E], D, anchor ball radii, costs, credible service offers and budget.
Output: conditional frontier; recover/abstain/acquire-more-data. Acquisition
type: new range / anchor recalibration / tighter independent domain / stronger
q bound. Source checks cannot establish physical issuer honesty. This is a
finite deterministic planning system, not an autonomous LLM scientist.

Use ../.venv/Scripts/python.exe from repository root:

```powershell
..\.venv\Scripts\python.exe -m pytest tests v2 v3/certified_agent/tests v3b/assumption_agent/tests -q
..\.venv\Scripts\python.exe -m v3b.assumption_agent.run --run v3b/runs/assumption-frontier-reproduce
..\.venv\Scripts\python.exe -m v3b.assumption_agent.audit --run v3b/runs/assumption-frontier-001
..\.venv\Scripts\python.exe -m v3b.assumption_agent.cli --input v3b/examples/anchor-uncertainty.json --output v3b/runs/cli-preview/decision.json
```

Never overwrite a historical run or its source/config manifest. Outcomes,
all failures, private evaluator state, hash-linked actions, independently
checked exact certificates, and theory tasks are retained in each run. Report
new certified outputs / information cost, prior assumption-volume contraction,
risk, coverage and costs together. Actual result: runs/assumption-frontier-001/REPORT.md.

The volume metric excludes new-anchor dimensions and is not posterior target
volume. Conclusions are conditional math or finite synthetic numerical evidence.
No priority claim, real BLE/GNSS validation, second inverse problem, stochastic
service planner or Codex research generation is included.
