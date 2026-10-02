# Phase 3B.1 — Uncertain-Contract Robustness Frontier

Scope: one range-localization case study. A finite agent chooses between new
range, anchor recalibration, an independent tighter domain, and a stronger
corruption bound. Neither cross-problem generality nor autonomous discovery is
claimed. v1/v2/v3A are byte-frozen at f896a3ef.

Inputs: rational nominal anchors, fixed positive weights, ranges, rectangle D,
anchor-ball radii, q in {0,...,Q}, clean weighted noise norm in [0,E], error
tolerance, finite information-service offers, rational costs and total budget.
The outer contract is (Q,E,D,delta). Advisory estimated_corruption has no gate.
Frontier rows are conditional for every q, E and scaled delta on a fixed grid;
the analytic epsilon ceiling also represents a continuous interval. Proposed
smaller domains are conditional until an independent receipt is accepted.

recover requires a consumer-verified robust shared-map margin b>0,
2(E+zeta_Q)/b <= rmax, and exact nominal trimmed residual <= E+zeta_Q.
This conservative pre-gate deliberately does not rely on solver completeness.
The output includes the tighter candidate-specific bound (E+rhat+zeta_Q)/b.
No certificate is a claim that all physically possible contracts are true.

Acquisition offers have advertised deterministic bounds and fixed costs; this
is a finite, honest-service, deterministic-outcome planning model. Receipts
must come from the configured service, match the offer and be nested within
current assumptions. This verifies consistency/provenance, not physical truth
or a digital signature. Each acquired range is really simulated and delivered;
geometry-only planning never sees its value. q bounds cover the entire offered
episode, including future measurements; noise bounds cover their clean vector.
Calibration shrinks same-centre balls and retains all earlier measurements.
Domains come from an independent prior service, never a crop around a solver.

Four fixed comparators: measurement-only, random-information, one-step-gain,
multi-step. The latter enumerates plans of length <=3 and chooses the cheapest
plan crossing the certificate threshold, otherwise best gain/cost, replanning
after each receipt. One-step maximizes decrease of the normalized conservative
error bound per cost. Infinite-bound plateaus have zero one-step gain; tie
breaking is by offer order. This deliberately exposes a finite-horizon failure
mode, not an optimality or adaptive-submodularity theorem.

Primary metrics: newly certified outputs / total acquired-information cost;
normalized residual assumption-volume reduction. Volume is the product measure
|{0,...,Q}| * E * area(D) * product(delta_i^2 / initial_delta_i^2) over the
original anchors (pi cancels), normalized by initial q/E/D factors. Added
anchors are excluded because dimensions change. It measures contracted prior
assumption space, not posterior location volume, probability or entropy.
All evaluated radii and E are positive. Also report risk, coverage, abstention,
cost, action mix, rejections, bound violations and every final failure.

Development checks use separate seeds. Final scenario/seed/config/evaluator
hashes are saved before final evaluation, followed by independent replay.
No benchmark tuning after held-out. Invalid-service cases are evaluated
separately and do not establish that the agent detects false honest-source
claims. Requirements include actual logs, certificates, frontiers, counterexample
witnesses, perturbation experiments, plots, Markdown report and exact audit.
