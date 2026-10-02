# Phase 3B.1 actual run

This is a finite range-localization decision/planning agent under uncertain premises. Prior 1,417 tracked files remain frozen. No phase retrieval, LLM scientist or novelty claim.

## Mathematical result and correction

**proved-in-project:** shared-map derivative perturbation, robust weighted-scatter certificate, nominal model-error recovery bound and a sufficient conditional frontier. Conventional scatter/perturbation/set-membership foundations are **known**.

**refuted:** naive unknown-anchor error <=2epsilon/mu_rob. Exact simultaneous translation by 0.1 changes the target but preserves every range, with epsilon=0 and positive uniform lower 1.061322. This leaves the shared-map definition valid; it defeats its misuse across two anchor explanations.

Correct conservative gate: B_q=2(E+zeta_q)/b_q, zeta_q^2 is the sum of the n-q largest weighted ball-radius squares. Final nominal residual must be <=E+zeta_Q; error <=(E+rhat+zeta_Q)/b_Q for every actual q<=Q. No q prediction or learned output grants safety.

Example frontier (circle, D=[-1,1]^2, all radii=0.01, rmax=0.4):

| q | uniform lower | epsilon ceiling | error bound at E=.04 | pre-gate |
|---|---:|---:|---:|---|
| 0 | 1.117394 | 0.195194 | 0.122221 | True |
| 1 | 0.816193 | 0.136781 | 0.162847 | True |
| 2 | 0.366079 | 0.048721 | 0.352355 | True |
| 3 | 0.000000 | uncertified | uncertified | False |
| 4 | 0.000000 | uncertified | uncertified | False |

This is a sufficient frontier, not exact mu or an impossibility test. Smaller hypothetical domains/radii are conditional until receipts are accepted.

## Fixed held-out simulation [numerically-supported]

| method | outputs / honest cases | new outputs | cost | new/cost | mean volume reduction | wrong outputs |
|---|---:|---:|---:|---:|---:|---:|
| measurement-only | 12/42 | 6 | 96.00 | 0.0625 | 0.0000 | 0 |
| random-information | 30/42 | 24 | 100.50 | 0.2388 | 0.5338 | 0 |
| one-step-gain | 36/42 | 30 | 84.00 | 0.3571 | 0.5708 | 0 |
| multi-step | 36/42 | 30 | 84.00 | 0.3571 | 0.5708 | 0 |

Numerator excludes already certified episodes; denominator includes all paid requests, including failed or unnecessary purchases. Report costs, abstentions and risk alongside this ratio.

| scenario | range-only outputs/cost | random outputs/cost | one-step outputs/cost | multi-step outputs/cost |
|---|---|---|---|---|
| healthy | 6/6; cost=0.00 | 6/6; cost=0.00 | 6/6; cost=0.00 | 6/6; cost=0.00 |
| anchor-uncertainty | 0/6; cost=18.00 | 6/6; cost=22.00 | 6/6; cost=12.00 | 6/6; cost=12.00 |
| q-uncertainty | 0/6; cost=18.00 | 6/6; cost=14.00 | 6/6; cost=9.00 | 6/6; cost=9.00 |
| domain-uncertainty | 0/6; cost=18.00 | 6/6; cost=12.50 | 6/6; cost=7.50 | 6/6; cost=7.50 |
| mixed-premises | 0/6; cost=18.00 | 0/6; cost=27.50 | 6/6; cost=28.50 | 6/6; cost=28.50 |
| geometry-plateau | 6/6; cost=18.00 | 6/6; cost=18.00 | 6/6; cost=18.00 | 6/6; cost=18.00 |
| budget-limited | 0/6; cost=6.00 | 0/6; cost=6.50 | 0/6; cost=9.00 | 0/6; cost=9.00 |
| untrusted-receipt | 0/6; cost=18.00 | 0/6; cost=30.00 | 0/6; cost=30.00 | 0/6; cost=30.00 |
| dishonest-calibration | 0/6; cost=18.00 | 4/6; cost=18.00 | 6/6; cost=12.00 | 6/6; cost=12.00 |

H1 pooled evaluation: numerically-supported. This is not a universal dominance theorem; the table retains per-scenario ties/failures and the finite horizon/budget limit.

Volume metric is normalized product measure over original q/noise/domain/anchor uncertainty dimensions. It is not feasible-position volume or posterior probability. Range purchases alone score zero contraction here even when they improve recovery. Shrinking eight independent radii creates a very large product reduction; mean log ratio is also recorded in metrics.json.

## Service integrity stress and limits

Untrusted calibration receipts are rejected, with paid cost retained. A dishonest calibration using an allowed issuer can pass provenance/nesting checks while placing actual anchors outside new balls. These episodes are separated from honest-service performance; physical truth cannot be established from a receipt schema. Exact conditional bounds cease to apply there. The final failures are retained in results.json and every action in history.jsonl.

Planning uses advertised deterministic nested information outcomes, finite offers and horizon3; it is not expected-value optimal under stochastic service errors. Calibration shrinks same-centre balls in a synthetic service; no real calibration protocol is implemented. Solver is incomplete. Robust margin bounds may be loose and subset enumeration is combinatorial.

Research cycles are explicit scripted records of this project development, with written proofs and exact verification. They are not evidence of an LLM autonomously discovering or approving theorems.

Perturbation experiment: 15 radius/q cells, 1800 sampled exact interval secants, 0 lower-bound violations. Samples test the derivations and never create certified lower bounds.

## Reproduce and inspect

From repository root using ../.venv/Scripts/python.exe: run `-m pytest tests v2 v3/certified_agent/tests v3b/assumption_agent/tests -q`; create a fresh run with `-m v3b.assumption_agent.run --run v3b/runs/assumption-frontier-reproduce`; audit with `-m v3b.assumption_agent.audit --run <new path>`. Existing run folders cannot be overwritten.

Sources/config are frozen in manifest.json before evaluation. Mathematical certificates are consumed using pairwise variance rather than producer centering arithmetic; hashes, receipt transitions, costs, original-domain volume and private evaluation are replayed independently. The audit verifies conditional math, not issuer honesty.

Figures: information_tradeoffs.png and margin_perturbation.png. Primary-source audit: ../../assumption_agent/LITERATURE_AUDIT.md. Human-readable proofs: ../../assumption_agent/THEORY.md.

Service-integrity stress uses a deliberately stricter rmax=.05 and E=.001 for the dishonest calibration fixture; these rows are not pooled with honest cases.

| method | stress outputs | wrong outputs | violated reported bounds | rejected requests |
|---|---:|---:|---:|---:|
| measurement-only | 0 | 0 | 0 | 0 |
| random-information | 4 | 4 | 4 | 6 |
| one-step-gain | 6 | 6 | 6 | 6 |
| multi-step | 6 | 6 | 6 | 6 |
