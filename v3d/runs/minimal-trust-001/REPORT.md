# Phase 3C — Minimal Trust Optimality Gap

Frozen source/config/seeds; 3,686 previous tracked files preserved. This phase implements cost bounds and subset search for one localization case study. It does not claim general minimal trust is solved.

## Main distinctions

- **known:** enclosing-radius/Helly witnesses, set cover, decision trees and restriction monotonicity have direct prior art.
- **proved-in-project:** scoped P1–P8 proofs and exact consumers. Project proofs are not novelty claims or proof-assistant formalizations.
- **refuted:** a global nonadaptive witness cover need not lower-bound adaptive cost; three unit-cost tests give batch3 versus adaptive2 in the fixed development counterexample.
- **refuted:** pair distances<=2rho do not imply enclosing radius<=rho; the rational acute triangle has radius13/12>21/20, while every pair fits.
- **numerically-supported:** subset search automatically repairs the old3.6 example; original frozen results are not overwritten.

## Exact finite models

24 finite instances: 20 exact finite cost optima, 4 proved impossible under their complete menus. Positive equality assumes the finite catalog is the complete prior. The infinite cases also give continuous impossibility lower witnesses because every physical query reply preserves their dangerous pair.

| case | pair batch | hypergraph batch | incident LB | exact adaptive cost | state at budget2 |
|---|---:|---:|---:|---:|---|
| adaptive-four-0 | 3/2 | 3/2 | 1 | 1 | certifiably-recoverable |
| acute-triple-0 | 0 | 1/2 | 1/2 | 1/2 | certifiably-recoverable |
| near-cluster-0 | 0 | 0 | 0 | 0 | certifiably-recoverable |
| unseparable-reflection-0 | infinite | infinite | infinite | infinite | provably-insufficient-information-budget |
| simple-pair-0 | 1/2 | 1/2 | 1/2 | 1/2 | certifiably-recoverable |
| expensive-pair-0 | 9/2 | 9/2 | 9/2 | 9/2 | provably-insufficient-information-budget |

The finite variants change declared prices on six fixed templates; this is controlled exact-instance validation, not held-out geometry generalization. All finite-policy trees are executed in every catalog world, including counterfactual policy checks for underfunded decision budgets. The budget decision itself rejects an underfunded plan. The actual world id is used only by the simulator; the policy input is the public possible-world catalog.

## Exactly closed continuous special cases [proved-in-project]

A separately checked algebraic completeness certificate reduces an initially continuous physical problem to exactly two reflection worlds. Two exact fixed-reference ranges force x=(0,+/-h); an unknown anchor with ||p||<=2h and range3h must satisfy p=-2x by equality in the triangle inequality. This is an exact, zero-noise q=r=0 boundary case, not sampled completeness.

| instance | continuous lower | continuous upper | gap | weaker uniform-ball family UB |
|---|---:|---:|---:|---|
| analytic-reflection-0 | 7/5 | 7/5 | 0 | not found |
| analytic-reflection-1 | 7/10 | 7/10 | 0 | not found |
| analytic-reflection-2 | 21/10 | 21/10 | 0 | not found |

These nonzero continuous optima are authorized by proof of the exact physical reduction. The weaker uniform-ball family misses them because it includes anchor geometries excluded by the observed range equations. This provides explicit evidence of certificate conservatism. It does not solve general positive-noise continuous optimality.

## Continuous physical cost bounds

The lower bound solves a checked finite restriction using EVERY available action. The upper bound quantifies ALL replies consistent with initial hard balls, by uniform geometry and post-purchase nuisance radii. It is stronger in scope than a finite forecast pre-gate.

| case | lower | upper | absolute gap | relative gap | budget diagnosis |
|---|---:|---:|---:|---:|---|
| regression-0 | 0 | 18/5 | 18/5 | 1 | certifiably-recoverable |
| positive-gap-0 | 1 | 18/5 | 13/5 | 13/18 | unresolved-certificate-or-search-gap |
| insufficient-budget-0 | 1 | 18/5 | 13/5 | 13/18 | provably-insufficient-information-budget |
| search-limited-0 | 1 | unknown | unknown | unknown | unresolved-certificate-or-search-gap |
| family-limited-0 | 1 | unknown | unknown | unknown | unresolved-certificate-or-search-gap |

Continuous held-out instances: 15; closed physical gaps: 0; states: {'certifiably-recoverable': 3, 'unresolved-certificate-or-search-gap': 9, 'provably-insufficient-information-budget': 3}.

Unknown upper is not infinity. Search-limited cases stop enumeration after one node; family-limited cases exhaust the declared uniform family without a certificate. Neither establishes physical impossibility. Insufficient-budget cases use lower>budget, not a failed upper search.

Each search-limited input matches its positive-gap counterpart up to episode id; unlimited search supplies upper3.6 on that same physical input. This is concrete evidence of search incompleteness, separate from the analytic certificate-conservatism examples and unseparable-reflection impossibility examples.

## Compulsory old miss

Development regression repaired: True. Held-out old-generator misses repaired automatically: 3/3.

Bundle and measurement subset are selected by enumeration, not by a hardcoded a0/a1/a2 rule. The development bundle costs18/5=3.6 and yields a post-delivery radius near0.0113. Its continuous lower is0, so physical cost3.6 is not claimed optimal. Finite-menu exhaustive optimality applies only to the chosen sufficient uniform family.

## Search and audit evidence

Held-out subset nodes=126; uniform certificate nodes=16014; finite adaptive states=128; witness count=263. Per-case counts are in results.json; measured execution times are in runtime.json.

The independent finite consumer uses acute-triangle/Helly threshold tests and a bottom-up minimax recurrence. Continuous consumers bind every selected coordinate, retained source assertion, geometry certificate, residual and union bound to the original observation. Physical witness verification checks all query replies and the combined future clean-noise budget. Hash-linked histories and immutable source/output manifests are audited.

## Remaining limitations

Finite models are tiny synthetic catalogs with deterministic replies and externally declared completeness. The continuous witness search uses a few feasible translated worlds; it is not complete. The uniform upper family uses exact reference purchases and initial hard balls, and does not yet handle soft-source reply games. It may ignore useful baseline/range information. Nonlinear candidate search and ball-union centering are incomplete. Costs are declared information prices; CPU is reported separately.

Root honesty, q/r, domain/noise coverage and source identities remain external. No autonomous LLM discovery or second inverse problem was added. Scientific source/config changes after evaluation are forbidden. All conclusions retain known / proved-in-project / conjectured / numerically-supported / refuted labels.

Reproduce: `../.venv/Scripts/python.exe -m v3d.minimal_trust.run --run v3d/runs/minimal-trust-reproduce-new`.
Audit: `../.venv/Scripts/python.exe -m v3d.minimal_trust.audit --run <run>`.
Theory and primary-source audit are in ../../minimal_trust/.
