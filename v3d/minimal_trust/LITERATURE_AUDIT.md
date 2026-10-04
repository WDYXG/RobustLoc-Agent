# Primary-source audit — 2026-10-04

Targeted audit, not an exhaustive priority search. All mechanisms below are
known; project proofs specialize them to explicit localization contracts.

| Area | Primary source and checked scope | Boundary |
|---|---|---|
| Smallest enclosing disk | Welzl (1991), *Smallest enclosing disks (balls and ellipsoids)*, [author-hosted full paper](https://people.inf.ethz.ch/emo/PublFiles/SmallEnclDisk_LNCS555_91.pdf), DOI10.1007/BFb0038202. [CMU course proof](https://www.cs.cmu.edu/~15451-s22/lectures/lec21-SEC-beamer.pdf), pp4–7, explicitly derives two/three-point characterization from Helly. | Pair/triple radius witnesses and exact support enumeration are existing geometry. Our code uses exhaustive rational enumeration, not a new smallest-disk algorithm or Welzl runtime claim. |
| Adaptive test costs and restrictions | Cicalese, Laber, Saettler (ICML2014), *Diagnosis determination: decision trees optimizing simultaneously worst and expected testing cost*, [PMLR full paper](https://proceedings.mlr.press/v32/cicalese14.pdf). Section1 defines finite objects/tests/costs and decision trees; section2 Proposition1 states restriction monotonicity; later path-based separation costs are distinct from a fixed batch union. | Known adaptive decision-tree framework. Our stopping rule is enclosing radius, not classification into predefined equivalence classes. We solve tiny instances exactly, without adopting their approximation guarantees. |
| Worst-case adaptive cover | Yuan and Tang (2022 preprint, revised2023), *Worst-Case Adaptive Submodular Cover*, [full primary text](https://arxiv.org/html/2210.13694). Model and section4.1 checked: pointwise submodularity alone does not imply the adaptive guarantee. | Do not infer greedy guarantees or adaptive submodularity from a static witness set-cover formulation. Our algorithm is exhaustive and makes no such assumption. |
| Sparse observability, calibration and joint nuisance | Frozen `v3c/trust_agent/LITERATURE_AUDIT.md` and `THEORY.md`: Fawzi–Tabuada–Diggavi sparse supports, Mahony–Hamel–Trumpf SLAM gauge, Eren grounded rigidity, calibration uncertainty and Byzantine model distinctions. | Those audit scopes and access limits remain unchanged. Source deletion and reference-radius consumers are reused; physical trust cannot be established by provenance alone. |

The new contribution claimed here is an auditable project implementation and
scoped proof/counterexample record, not a novel definition of radius, hitting
set, decision-tree optimality or subset selection. Exact finite equality does
not establish continuous nuisance optimality. The invalid transfer of a global
batch cover to adaptive cost is explicitly refuted in THEORY.md C2.
