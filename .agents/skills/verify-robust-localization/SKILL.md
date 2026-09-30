---
name: verify-robust-localization
description: Independently test and reject localization hypotheses using protected evaluation rules and contrary cases.
---

Check the residual, loss scaling, finite behavior and observation-only interface.
Run pytest and the protected development/validation experiments. Compare with WLS
and the proposal's incumbent parent using identical case seeds. Apply the fixed
config.toml acceptance rules via robustloc.verifier; proposer preference cannot
override rejection. Save positive-excess failures, numerical failures and scenario
regressions. Audit protected hashes and historical baselines for metric gaming.
Supported is empirical evidence, never proof. Preserve inconclusive/rejected
branches. Record EVALUATOR_ISSUE before any versioned evaluator repair. Final
held-out access requires a frozen method; forbid further tuning in that run.
