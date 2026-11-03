# Replay issue: mutable descriptive contract metadata

Full acquisition replay found that the first three stored answers' `frontier.assumption_set.radii` lists had length14 after subsequent acquisitions, while their correct lengths at the respective steps were11/12/13. The stored observations, exact certificate data, bounds, selected positions, and performance values were unaffected. The final recovery has no later mutation. An independent recursive diff isolated only these three descriptive fields.

Cause: returned descriptive metadata referenced the caller's mutable contract list. Fix: snapshot the contract with `deepcopy` at the service boundary. Add a caller-mutation regression test. Preserve original source/test snapshots here. Do not overwrite this run's output.

`static-003` repeats the exact same seeds, models, acceptance rules and selected configuration with the snapshot correction. This is a corrective replay, NOT a new independent held-out sample and NOT tuning after seeing the test. All original main benchmark results remain recorded. The previous main audit passed; the additional acquisition audit rejected the metadata discrepancy. Publication uses the corrected run only after both audits pass.
