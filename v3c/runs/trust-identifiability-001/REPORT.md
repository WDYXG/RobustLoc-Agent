# Phase 3B.2 — Joint Nuisance Identifiability & Minimal Trust

All files tracked at1ed4e01 remain byte-frozen. New scope is v3c/trust_agent. One range-localization case study, finite decision agent, human-written proofs and exact consumers; no autonomous theorem discovery, second inverse problem or novelty claim.

## Mathematical findings

**known:** observation equivalence, Euclidean gauge, graph rigidity, sparse secure observability, set membership and Byzantine redundancy have direct prior art.

**proved-in-project:** T1 observation-only validation impossibility and two-point error lower bound; T2 rigid stabilizers; T3 star-map sparse identifiability; T4 bounded-reference recovery; T5 all-source-branch covers; T6 finite sufficient trust frontier. Proof status is not proof-assistant formalization or priority.

**refuted:** ordinary ranges validate unanchored calibration; star joint map is identifiable modulo rigidity; three unmeasured frame references locate the target; two measured references eliminate reflection; four exact general-position range coordinates suffice atq=1. Exact witnesses are in research_tasks.json.

Three noncollinear references fix a planar O(2) frame, but target-range connectivity is separate. On unrestricted D, every k−2q range-survivor subset needs three noncollinear trusted positions. k counts range coordinates: repetitions of three locations can provide coordinate-corruption redundancy; they do not automatically handle persistent reporter faults.

100 ordinary range responses and the same alleged calibration receipt remain identical in an exact translated pair; target separation=.8 gives minimax error lower=.4. This proves impossibility for informative observation-only validation in both worlds, not that every agent must falsely certify. Abstaining remains possible.

One-reference and two-reference residual gauges must be feasible inside D. The displayed analytic q=0 hierarchy is a separate exact star example on D=[-3,3]^2, with a full circle at one reference and a reflected pair at two; it is not the diameter of a sampled hypothesis cloud.

| measured references | exact feasible-target diameter |
|---|---:|
| no reference | 8.485281 |
| one measured point | 2.828427 |
| two measured points | 2.000000 |
| three noncollinear points | 0.000000 |

Trusted intrinsic baselines preserve global rigid gauge. Full relative graph rigidity does not itself supply absolute coordinates. Under source budgetr, three identical aliases of one failure domain count as one source, not a majority.

Source deletion probes (complete exact layout reports, independent groups):

| r | groups | continuous cover certified |
|---:|---:|---|
| 1 | 2 | False |
| 1 | 3 | True |
| 2 | 4 | False |
| 2 | 5 | True |

The2r+1 majority statement applies only to independent whole-layout reports with identical exact honest outputs. It is not a general3r+1 Byzantine consensus or arbitrary calibration result. r and group identities remain external premises.

## Fixed held-out experiments [numerically-supported]

| method | outputs / honest cases | new outputs | total cost | new/cost | wrong |
|---|---:|---:|---:|---:|---:|
| range-only | 8/44 | 4 | 27.000 | 0.1481 | 0 |
| random-information | 30/44 | 26 | 123.900 | 0.2098 | 0 |
| trust-directed | 32/44 | 28 | 64.600 | 0.4334 | 0 |

| scenario | range-only outputs/cost | random outputs/cost | trust-directed outputs/cost |
|---|---|---|---|
| no-reference | 0/4; cost=3.000 | 4/4; cost=19.950 | 4/4; cost=14.400 |
| one-reference | 0/4; cost=3.000 | 4/4; cost=13.000 | 4/4; cost=10.400 |
| two-reflection | 0/4; cost=3.000 | 4/4; cost=8.150 | 4/4; cost=5.600 |
| frame-without-ranges | 0/4; cost=3.000 | 4/4; cost=20.200 | 4/4; cost=14.400 |
| sparse-q1 | 0/4; cost=3.000 | 2/4; cost=22.100 | 4/4; cost=16.400 |
| precision-gap | 4/4; cost=1.000 | 4/4; cost=1.000 | 4/4; cost=1.000 |
| bounded-references | 0/4; cost=3.000 | 0/4; cost=27.400 | 0/4; cost=0.000 |
| two-source-ambiguity | 0/4; cost=3.000 | 4/4; cost=6.250 | 4/4; cost=2.400 |
| three-source-majority | 4/4; cost=0.000 | 4/4; cost=0.000 | 4/4; cost=0.000 |
| aliases-one-domain | 0/4; cost=2.000 | 0/4; cost=1.950 | 0/4; cost=0.000 |
| trust-budget-shortfall | 0/4; cost=3.000 | 0/4; cost=3.900 | 0/4; cost=0.000 |
| premise-budget-violated | 4/4; cost=0.000 | 4/4; cost=0.000 | 4/4; cost=0.000 |

Planner optimality is restricted: enumerate affordable bundles and choose cheapest passing a sufficient common-branch geometry pre-gate for every declared finite forecast. Proved-empty forecast source branches are excluded; unresolved ones are retained. Delivered continuous certificates, not the forecast catalog, authorize output. Minimum cost of a sufficient certificate is not universal minimum physical trust or an optimal nonlinear algorithm.

The agent emits structural ambiguity only with checked continuous-world witnesses. Positive exact-reference margin but insufficient noise bound is called precision/certificate gap. Other failures remain unresolved; no lower=0 impossibility shortcut. All failed/exhausted actions and source branches are retained.

## External trust and negative results

A deliberately violated premise-budget fixture has two false groups while declaringr=1. The agreed false layout passes the conditional mathematics and shifts the target by.8. This is outside the admissible-world set; it demonstrates that agreement and a schema cannot validate their own fault budget or physical source independence.

| method | out-of-model outputs | wrong outputs | bound violations |
|---|---:|---:|---:|
| range-only | 4 | 4 | 4 |
| random-information | 4 | 4 | 4 |
| trust-directed | 4 | 4 | 4 |

The evaluated setup has11 in-contract geometry/service templates with4 target/noise instances each, not a broad geometry distribution. q corruption is one fixed initial coordinate; future repeats are clean and their aggregate norm is below the declared globalE. r refers to full layout-source groups. The forecast menu is finite, service outcomes deterministic, and planning CPU is not counted as information cost.

Calibration roots are simulated external point instruments, not real GNSS/signature/provenance verification. Bounded references and source branches can retain ambiguity below the required resolution. Pairwise disjoint-ball tests are sufficient infeasibility proofs, not complete intersections; numerical candidate search is incomplete. Baselines are checked in witnesses but deliberately ignored by positive outer covers, hence may be conservative.

## Reproduce

`../.venv/Scripts/python.exe -m pytest tests v2 v3/certified_agent/tests v3b/assumption_agent/tests v3c/trust_agent/tests -q`

`../.venv/Scripts/python.exe -m v3c.trust_agent.run --run v3c/runs/trust-identifiability-reproduce`

`../.venv/Scripts/python.exe -m v3c.trust_agent.audit --run <new run>`

manifest.json freezes sources/config before evaluation; history.jsonl is hash-linked; continuous certificates are independently consumed; exact witnesses and complete finite cost enumeration are checked. Existing runs cannot be overwritten. Claims in CLAIM_LEDGER.json; source audit and proofs in ../../trust_agent/.
