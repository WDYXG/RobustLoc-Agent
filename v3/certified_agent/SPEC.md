# Phase 3A: Certified Adaptive Localization Agent

**conjectured** research goal: certificate-guided abstention and active observation
planning yield useful output with fewer wrong answers and explicit sensing cost.
This is range localization inside a proposed MathResearch-Agent umbrella, not
validated generality across nonlinear inverse problems or automatic mathematics.

Inputs: exact declared rational anchor positions/measurement values/weights;
rectangular D; estimated_corruption (advisory); a separately declared q_budget
(conditional assumption, not estimated truth); epsilon clean weighted residual
budget; error_tolerance; available reporter positions, acquisition budget.
Geometry features are derived from inputs at the workspace centre, never truth.

Actions: recover / abstain / acquire-more-data. Recovery requires verified
b_q≥2 epsilon/error_tolerance and an independently checked candidate with at most
q omitted residuals and clean weighted norm ≤epsilon. T2 then gives
error≤2 epsilon/b_q≤error_tolerance, conditional on actual assumptions.
Absence of a candidate is not proof the feasible set is empty. A zero lower
certificate is not impossibility. Unknown q_budget causes abstention and a
conditional capacity profile, never silent adoption of estimated_corruption.

The numerical decoder uses bounded multi-start Cauchy and iterative trimming.
It need not solve the nonconvex problem globally: failing the final exact
feasibility gate leads to abstention/acquisition. Fixed weights represent a
measurement contract; no residual-dependent rescaling to inflate μ. New weights
are fixed to the same scale. New observations share the episode-wide q budget
and epsilon, which the private evaluator checks again after acquisition.

The planner optimizes a **certified lower bound**, not the unknown true μ, over a
finite declared candidate set. It prefers the fewest acquisitions that cross the
required threshold, then the largest terminal lower bound. Horizon ≤3 reveals
plateaus invisible to immediate-gain greedy. It does not claim global sensor
placement optimality. Strict μ improvement is reported only if post-lower >
pre-upper. Increasing a lower bound alone is recorded as lower-certificate gain.

Learning experiment: logistic surrogate trained on independent synthetic geometry
layouts. Label 1 only if b≥tau, 0 only if feasible-pair U<tau; b<tau≤U is
unknown, excluded with count preserved. Therefore probabilities concern the
audited, partially labeled synthetic distribution; not ground-truth values of μ
or formal P(μ>tau) guarantees. It is advisory in the certified agent. A learned-only
gate is an explicitly uncertified ablation. No held-out selection of thresholds.

Fixed comparison: always-Cauchy; passive certified; random-acquisition certified;
immediate-gain greedy certified; horizon planner certified; learned gate ablation.
Held-out episodes are paired. Design seeds, model training, model test, final
episode seeds and thresholds are frozen separately. Evaluate wrong-output rate,
selective risk, coverage, abstention, acquisition count, lower-margin improvement,
strict μ improvement, certified bound violations and runtime. Out-of-contract
scenarios stay separate; no guarantees for invalid true-domain/noise/q assumptions.

In the new-report-corrupted stress scenario the same environment rule corrupts
the first newly requested reporter for each policy, using the shared per-position
noise realization. This is a controlled reactive adversary, not an identical
fixed bad reporter across policies. No future measurement is visible to planning.

All v1/v2 files are frozen, no v1 comparison is rerun. Original application is
connected conceptually through simulated range reporters; no BLE hardware or
real crowdsourcing deployment. Phase 4 remains future work.
