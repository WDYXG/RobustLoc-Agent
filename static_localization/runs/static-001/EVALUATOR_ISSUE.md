# Evaluator issue: JSON serialization, aborted run

2026-11-03. `study.py` v1 aborted while saving the first validation baseline: `TypeError: Object of type int64 is not JSON serializable`. The failure count was produced by summing NumPy boolean values. No proposal was selected and no final cases were generated or evaluated. The manifest and original evaluator source are retained here; this run is NOT completed evidence.

Correction for evaluator v2: explicitly convert the failure count to a Python int and test JSON serialization of the actual summary. Metric definition, data configurations, seeds and acceptance policy remain unchanged. Start a new `static-002` run; do not overwrite this record. Final comparisons will all use v2. The earlier 9 functional tests did not catch this serialization defect.
