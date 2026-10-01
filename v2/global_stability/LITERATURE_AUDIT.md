# Targeted prior-art audit, 2026-10-01

**known**. Project names “global q-corruption stability margin” and “corruption–
stability profile” do not establish novelty. This audit is targeted, not exhaustive.

| Primary source / inspected material | Established scope | Boundary for Phase 2 |
|---|---|---|
| Luc Jaulin, *Set-membership localization with probabilistic errors*, Robotics and Autonomous Systems 59(6), 489–495 (2011), DOI [10.1016/j.robot.2011.03.005](https://doi.org/10.1016/j.robot.2011.03.005). [Author full text](https://webperso.ensta.fr/jaulin/paper_probintk_ras.pdf), §II.A–B, PDF pp.3–5. | q-relaxed intersection retains points consistent with all but at most q measurement sets; robust set-membership observers; interval outer approximation. Sorting interval endpoints already yields O(n log n). | Neither feasible sets, tolerance of q outliers, interval subdivision nor sorting is new here. Their probabilistic observer is different from our deterministic static inverse constant. |
| Giuseppe C. Calafiore, *Set-Membership Localization via Range Measurements*, SIAM J. Optim. 36(2), 1100–1124 (2026), [publisher](https://epubs.siam.org/doi/10.1137/25M1750652), DOI 10.1137/25M1750652; online 23 June 2026. [Author preprint](https://arxiv.org/abs/2603.04867). Publisher abstract, references and bibliographic history inspected; full-text preprint extraction unavailable through web reader in this audit. | Bounded range errors; nonconvex consistency region; containing ball/polytope localization set; convex-programming box/ellipsoid outer bounds. Squared measurement differences already underlie geometry. | Cannot claim set-valued range localization, complete consistency region, box/ellipsoid enclosure or squared-range algebra as new. Abstract-level audit cannot establish absence of a quantitative stability theorem in the full paper. |
| Weber et al., *Gordian: Formal Reasoning-based Outlier Detection for Secure Localization*, ACM TCPS 4(4), Article 43 (2020), DOI [10.1145/3386568](https://doi.org/10.1145/3386568). [Author publication record](https://people.eecs.berkeley.edu/~sseshia/pubs/b2hd-weber-tcps20.html); [Berkeley full technical report](https://www2.eecs.berkeley.edu/Pubs/TechRpts/2019/Archive/EECS-2019-1.pdf), abstract, §2 and counterexample generation. | Coordinated adversarial anchor/range attacks; graph geometric inconsistency; noiseless detection conditions; trilateration counterexamples; fewer guarantees with noise. | Geometry consistency and counterexample-guided reasoning for secure ranging are prior art. Our fixed-anchor single-target inverse constant is narrower, not a replacement for network attack detection. |
| Phase 1 [audit](../LITERATURE_AUDIT.md), including FIM/GDOP, Fickus–Mixon erasure-robust frames, Fawzi–Tabuada–Diggavi sparse correction. | Local differential lower bounds and 2q support-union reasoning. | Retain as known. No frame, Fisher-information or sparse-correction novelty claim. |

**conjectured** potential research gap: quantitative global inverse stability of
the nonlinear fixed-anchor range map after worst coordinate deletion, its local
limit, and practical independently checked lower certificates. “Potential gap”
means an investigation target; this audit does not establish originality. T5's
scatter calculation is a direct application of known squared-range and weighted
variance identities. All proved-in-project deductions have novelty = not established.

**known** additional relevant predecessor: Jaulin (2009), *Robust set-membership
state estimation; Application to underwater robotics*, Automatica 45,202–206,
DOI 10.1016/j.automatica.2008.06.013, cited by Calafiore. We inspected its citation,
not its full theorem statements; do not attribute further guarantees to it here.
