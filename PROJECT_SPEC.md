# RobustLoc-Agent specification v1.0

Question: can a persistent bounded research agent reduce CEP90 and >10 m failure
rate versus defined WLS under noisy synthetic static 2D observations?

Phase order: tested baselines and benchmark -> persistent feedback-driven research
-> freeze -> once-only held-out -> evidence-bound report/PDF.

Observation-only API: positions, distances, position sigma, distance sigma,
confidence, freshness. Truth and outlier labels are evaluator-only. Units: metres.
RSSI is a distance-domain proxy, not a physical propagation model.

Eight scenarios and seeds are protected. 100 development, 150 validation,
250 held-out cases per scenario. Fixed split roots: 110000, 220000, 930000;
scenario offset 10000; balanced mixture. Failure: strictly error >10 m.
Report mean, median, CEP50, CEP90, failure, runtime, numerical failures/nonfinite.

Baseline objectives: NLS sum r_i^2; WLS sum confidence_i*r_i^2/s_i^2,
s_i^2=distance_sigma_i^2+position_sigma_i^2. r_i=||x-p_i||-d_i.
Robust family: SciPy linear/Huber/Cauchy/soft-L1, scale/weight ablations,
observation-only MAD, deterministic multi-start. All optimize the specified
range objective. No global optimum, consistency, or novelty theorem is claimed.

Acceptance: validation CEP90 improves >=2%; failure rise <=0.005; every scenario
CEP90 <= max(0.25,1.25*incumbent CEP90); no new nonfinite or increased optimizer
failures. Otherwise reject regression, retain inconclusive branches. Proposer
cannot decide success. Verifier process is independent of proposer decisions.

Policy agent: predefined mathematical mechanisms, feedback-driven ordering,
threshold and parent choice. It is not an LLM and does not autonomously invent
unrestricted code. Skills support Codex/manual extension, not runtime execution.
Future optional LLM proposer must produce the same restricted proposal schema
and use the same verifier; absent credentials are not a blocker for this phase.

Persistent records: state, hash-linked append-only log, each proposal, code/config
snapshot, tests, raw per-case experiments, verifier decision and failures.
Source and historical baseline hashes are integrity guards, not security isolation.
Repeated validation selection is disclosed. Final paired stratified bootstrap is
conditional on the frozen method. Held-out metrics cannot influence further
proposals. Complete means configured budget evaluated/reported; not solved.
