# Validation boundary issue, 2026-10-04

After cross-problem-001 froze, interface review found that the original
`experiments.validate_measurement_model` checked physical replies and the
joint corruption budget but did not bind `model.tolerance` to the recovery
transcript's tolerance. A caller could supply two different tasks and still
pass that physical-input checker. This does not invalidate the published
instances: every actual pair uses exactly 1/10, checked again by evaluator v2.
It is a real input-contract gap, not an observed error-bound violation.

All original source and run bytes are retained. Evaluator v2 lives under
`runs/evaluator_v2/` so adding its code does not change the original source
snapshot; its OWN source digests are frozen in each v2 envelope BEFORE rerun.
The wrapper binds the runtime validation entry point to the strengthened
checker, without editing the old module on disk. The entire same experiment
and every legacy regression are rerun; no estimator, data, metric or scientific
method was tuned after held-out evaluation. v2 is validation hardening on the
same data, not a fresh unseen generalization test.

Two malformed-tolerance regression checks document that v1 accepts the
mismatched task contract and v2 rejects it, for both range and PR. Final
acceptance should use the v2 envelope audit, not only the v1 physical checker.

Run: `python -m v4.runs.evaluator_v2.run --run v4/runs/cross-problem-v2-new`
Audit: `python -m v4.runs.evaluator_v2.audit --run v4/runs/cross-problem-v2-001`
