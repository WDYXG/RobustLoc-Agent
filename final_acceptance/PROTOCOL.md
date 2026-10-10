# Original-question acceptance protocol — 2026-10-10

## Question and provenance

User-supplied attribution: HarmonyOS 难题发布—第七期, 众包离线高精度定位.
The original teacher document and its numeric acceptance targets have not been
independently inspected. A public title search did not identify a verified
primary copy. The supplied description is the source of the application scope;
the thresholds below are project experiment settings, NOT teacher requirements.

Model: y_i = ||x-p_i|| + eta_i + o_i; reported pbar_i differs from true p_i.
Public premises are a domain D, a global corruption upper bound Q, weighted
clean-noise norm E, and anchor balls delta_i. They are assumed external inputs.
The certificate never establishes that a physical premise is truthful.

## Existing evidence and remaining gap

v3 already executed certificate/reject/acquire decisions (132 paired episodes).
v3b already included anchor errors and demonstrated dishonest-receipt failures.
Neither supplies this exact unified comparison of WLS, Cauchy and the unchanged
uncertain-anchor certificate gate on paired randomized reporter layouts, with
every available range reply fixed by reporter identity before any policy runs.
v5's research-step comparison does not measure application localization quality.

## Predeclared experiment (before final data execution)

- 12 new episodes in each of 10 scenarios, final seed 10102673; development seed
  10100131 is disjoint. No training/tuning on final episodes. One fixed final run.
- Six valid-contract strata: spread, clustered, collinear, sparse, noisy,
  uncertain-anchors. Four separate violation stresses: excess-corruption,
  understated-noise, understated-anchor-error, target-outside-domain.
- Coordinates in metres. D=[-2,2]^2, output tolerance 0.5 m (study choice).
  Reporters vary by episode; targets are randomized. Clean errors are bounded,
  heteroscedastic distance-proxy errors, NOT a calibrated BLE/RSSI simulator.
- Six finite candidate reporters per episode. All real anchor positions,
  clean noises, corruption identities and replies are committed before selection.
  The global Q covers both old and potential future observations; selecting a
  different reporter cannot move corruption to a different device.
- Compare fixed-budget random ordering vs one-step geometry-certificate ordering
  at k=0,1,2,3 additional reporters, each of unit cost. Both consume exactly k.
  Active ordering maximizes the existing conservative certificate quality after
  each candidate addition, even if a position was already certifiable. This is
  an equal-cost budget sweep, NOT an early-stopping cost-efficiency experiment.
- At each identical observed dataset run (1) bounded multistart WLS, (2) frozen
  multistart Cauchy, (3) frozen v3b certified recovery (trimmed candidate search).
  WLS/Cauchy always output; their positions are not certified. The certified
  method may abstain. Solver incompleteness is retained as a possible cause.
- Active policy sees only public geometry/contract and previously acquired data;
  it does not see future replies, truth, actual anchors or bad identities.
  The geometry lower bound is conservative, not the true information margin.
- Unknown Q: a separate negative input test must reject certification, not infer
  a guaranteed Q from an estimated corruption count. No field Q-estimator added.

## Outcomes and interpretation

Primary: valid-contract certified correct-output fraction (unconditional), wrong
output fraction (unconditional), coverage/abstention, and equal-k active-minus-
random correct-output difference. Report per-stratum and pooled results at each k.
Also report selective risk, output-only median/P90 error, counts of errors above
2 m, bound violations, conservative bound changes, failures, and wall times.
Undefined risks/quantiles with zero outputs are null, never zero. Pooled strata
are equally weighted by design, not claimed to match deployment prevalence.

Report paired bootstrap 95% percentile intervals (2,000 resamples; fixed seed),
resampling episodes within each scenario and keeping policies paired. Intervals
are descriptive, pointwise and unadjusted for multiple budgets/comparisons.
Bootstrap zero-event intervals do not establish zero population risk.

Acceptance is an evidence verdict, not a threshold optimized for success:
pipeline executable + frozen integrity + truth-isolated inputs + deterministic
replay + valid-contract gate soundness must pass. Zero observed bound violations
is required for an engineering acceptance of the tested valid fixtures; this is
not a proof of software correctness. Active superiority is supported only for
the specified metric/budget if its paired interval lies above zero; retain ties
and regressions. A tiny positive gain cannot justify field relevance.
Real BLE, GNSS/WiFi calibration, mobile targets, latency/energy budgets and
HarmonyOS deployment remain unvalidated; original industrial acceptance stays
unresolved even if the synthetic pipeline passes.

## Freeze and failure handling

Before final run, save SHA256 of every pre-existing tracked file, acceptance
source/config, runtime versions and seed settings. Never overwrite a run.
Final selection may not alter methods, scenarios, thresholds or hyperparameters.
Audit independently checks private contract validity, conditional bounds, action
costs, response binding and exact consumer verdicts. Recompute aggregates and
optionally replay solvers; save audits separately. Retain every wrong output,
abstention, optimizer failure and invalid-contract recovery in the artifacts.
