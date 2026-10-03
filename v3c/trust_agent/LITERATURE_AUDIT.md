# Primary-source audit — 2026-10-03

No novelty claim; this is a targeted audit, not proof of absence of prior work.

| Area [known] | Primary source and checked scope | Project boundary |
|---|---|---|
| Secure estimation / indistinguishability | Fawzi, Tabuada, Diggavi, *Secure estimation and control for cyber-physical systems under adversarial attacks*, [arXiv1205.5073 full PDF](https://arxiv.org/pdf/1205.5073), Proposition2 and its two-support proof checked, pp8–9 in current PDF. | Linear dynamical sparse observability uses >2q support. Our static range-map perpendicular-bisector specialization uses the same known error-correction argument; no new generic theorem claimed. |
| SLAM gauge | Mahony, Hamel, Trumpf, *An Homogeneous Space Geometry for Simultaneous Localisation and Mapping*, Annual Reviews in Control51 (2021), DOI10.1016/j.arcontrol.2021.04.012. [Author-hosted full PDF](https://trumpf.id.au/pubs/mahony_hamel_trumpf_ARControl2021.pdf), section3.3 and symmetry formulation checked. | Gauge invariance and quotient constructions are existing concepts. Our planar O(2) star map has reflection and extra nonrigid freedoms; do not identify it with this paper's SLAM state/observer guarantees. |
| Sensor-network rigidity | Eren et al., *Rigidity, Computation, and Randomization in Network Localization*, INFOCOM2004, DOI10.1109/INFCOM.2004.1354686. [Primary conference PDF](https://courses.csail.mit.edu/6.885/spring06/papers/Eren-etal.pdf), grounded-network unique localizability/global rigidity statements checked. | Three noncollinear anchors need suitable graph constraints. Grounded full-network rigidity is distinct from target-only identifiability and fixed frame gauge. |
| Byzantine estimation versus agreement | Lamport, Shostak, Pease, *The Byzantine Generals Problem* (1982). [Microsoft-hosted full PDF](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/12/The-Byzantine-Generals-Problem.pdf), oral/signed message assumptions and3m+1 oral-message result checked. | Do not transplant3r+1 agreement thresholds into complete-layout report majority or claim signatures establish physical truth. Registered failure groups are still an external assumption. |
| Anchor calibration uncertainty | Frozen v3b/assumption_agent/LITERATURE_AUDIT.md: 2014 SOCP uncertain anchors; 2019 calibration-emitter work, DOI10.1109/TWC.2019.2938761. Earlier access limits retained. | Independent calibration and uncertain positions are known. This phase adds source-deletion covers in the project's model; it does not implement a GNSS/certification protocol or prove physical trust. |
| Bounded geometric recovery | Calafiore, [Geometry-Aware Set-Membership Multilateration](https://arxiv.org/html/2603.14263),2026; frozen v2/v3b audits. | Scatter/eigenvalue geometry certificates and anchor selection remain known. Positive project certificates reuse frozen exact rational consumers. |

Observation equivalence is an elementary instance of known identifiability and
decision-theoretic two-point reasoning. We prove the explicit model statements
in THEORY.md and retain exact witnesses, but make no priority claim. Source
budget r and q are not learned from allegedly reliable messages. Trust cannot
be bootstrapped from a name, a hash, or three copies of a false physical reading.
