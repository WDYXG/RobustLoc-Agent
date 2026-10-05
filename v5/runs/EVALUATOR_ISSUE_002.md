# Metric issue 002 — rejected repair was incorrectly called successful

Observed after the completed v2 trajectory. No proposal, mathematical result,
raw metric, earlier source or provider record is changed.

`researcher/gate.py::ledger_event` used any accepted, nonduplicate disposition
as the success criterion for a changed claim following a refuted/unresolved
parent. A verified refutation is an accepted research result, but it is not a
successful repair of the revised conjecture. Codex r12 follows refuted r11 and
is itself refuted; the old `successful_revision=true` label is therefore wrong.

This affects the Codex aggregate's claimed successful revisions (2 rather than
1 under the original changed-formal-statement interpretation). It does not
affect the mathematical `refuted` disposition, the two exact witnesses,
acceptance count or productive-ledger count. The mislabel is in the last slot,
so it was never exposed as feedback for a later model decision. The scripted
trajectory contains no such false-positive repair.

The separately frozen evaluator_v3 reporting consumer regrades **both recorded
trajectories**, after complete mathematical replay. It distinguishes:

* successful formal revisions: changed formal statement, parent refuted or
  unresolved, new result proved-in-project;
* successful repairs of refuted claims: the preceding condition with a refuted
  parent specifically;
* successful post-rejection corrections: a failed verification followed by a
  proved result, including correction of a certificate without changing claim;
* failed repairs: a changed conjecture following a refuted parent is refuted
  again. This remains useful counterexample research, not successful repair.

The legacy count remains visible for provenance. This is a metric correction
on the same frozen recordings, not fresh stochastic generation, additional
research rounds, or an improvement to either policy. No mathematical outcome
is promoted or demoted by this reporting consumer.
