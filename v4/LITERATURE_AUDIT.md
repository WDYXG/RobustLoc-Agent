# Primary-source audit, 2026-10-04

Targeted correctness audit, not an exhaustive novelty search. No new
phase-retrieval theory is claimed.

| Source | Verified part | Consequence for this project |
|---|---|---|
| Balan, Casazza, Edidin (2006), *On signal reconstruction without phase*, ACHA20,345–356, DOI10.1016/j.acha.2005.07.001. [Original preprint](https://arxiv.org/pdf/math/0412411), with a slightly different title. | Real magnitude reconstruction and the complement-property framework; the real equivalence is also explicitly proved in the next primary paper. | Sign quotient and real CP are existing results. Squaring nonnegative magnitudes preserves injectivity, but does not preserve the same metric stability constant. |
| Bandeira, Cahill, Mixon, Nelson (2014), *Saving phase: Injectivity and stability for phase retrieval*, [author preprint](https://arxiv.org/pdf/1302.4618). | Section2.1, Theorem3 and proof: CP iff real quotient injectivity. Section3 studies quantitative stability and the strong complement property. | Our rank/CP checks and lifted Gram lower bound are scoped conservative implementations, not new frame conditions or claims to their sharp constants. Real theory must not be promoted to complex PR. |
| Balan, Zou (2016), *On Lipschitz Analysis and Lipschitz Synthesis for the Phase Retrieval Problem*, LAA496,152–181, DOI10.1016/j.laa.2015.12.029, [original paper](https://arxiv.org/pdf/1506.02092). | Abstract's distinction between amplitude natural quotient metrics and intensity lifted matrix metrics; Proposition3.1(iv) and its zero-scaling example explain why the metrics are not globally bi-Lipschitz equivalent. | We retain the requested d_pm metric for intensity and restrict the positive certificate to an annulus. The origin-degeneracy counterexample is an audit of this boundary, not a new instability discovery. |
| Frozen v3d primary-source audit | Euclidean smallest disks/Helly, costly adaptive decision trees and witness restrictions. | Bellman/path lower bounds transfer. Convex Euclidean witness-size proofs require rechecking after quotienting. |

Sparse unknown corruption's two-support union is a generic error-correction
argument; it is not attributed as a new PR theorem. The four-world quotient
radius obstruction is an exact project counterexample to an attempted transfer;
its broader priority has not been investigated. Candidate symmetry transforms,
task ordering, reference theorem checks and test designs are human supplied.
