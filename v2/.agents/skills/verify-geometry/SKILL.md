---
name: verify-geometry
description: Verify a range-geometry proof, reject overclaims, and independently reproduce counterexamples or conditional certificates.
---

Check each proof step and assumptions in THEORY.md; pytest is a numerical check,
not proof. Independently compute Gram eigenvalues instead of trusting the analytic
margin routine. Test support-union size, distinct positions, equal ranges and
mirror ambiguity. Include collinear, almost-collinear, sparse and high-leverage
attacks. Certify estimator output only after residual gate and prior assumptions;
do not infer true prior coverage from corrupted observations. Status must be known,
proved-in-project, conjectured, numerically-supported or refuted. Never convert
a classical frame/FIM fact to a novelty claim. Check V1_FREEZE before and after.
