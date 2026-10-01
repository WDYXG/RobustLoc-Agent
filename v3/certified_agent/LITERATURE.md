# Phase 3A provenance audit (2026-10-01)

**known**: selective prediction / reject option and risk–coverage tradeoff predate
this project: [El-Yaniv & Wiener, JMLR 2010](https://jmlr.org/papers/v11/el-yaniv10a.html).
[SelectiveNet, ICML 2019](https://proceedings.mlr.press/v97/geifman19a.html) learns
prediction and rejection. We borrow risk/coverage accounting; we do not establish
its statistical guarantees for this localization simulation.

**known**: sensor geometry design and optimal placement are existing research:
[Zhao, Chen & Lee, Optimal Sensor Placement for Target Localization and Tracking
in 2D and 3D](https://arxiv.org/abs/1210.7397) includes range-only sensors and
optimal geometric configurations. Maximizing geometry or acquiring observations
is not a new idea. The project instead uses its inherited global sparse-deletion
certificate as a finite action criterion. Novelty is not established.

**known**: [SciPy least_squares documentation](https://docs.scipy.org/doc/scipy-1.15.1/reference/generated/scipy.optimize.least_squares.html)
provides bounds and robust losses but finds a local minimum. Our candidate search
must not claim completeness. Final candidate residuals are verified using rational
intervals. Actual installed versions are recorded in the run manifest.

**known / proved-in-project**: Phase 2 THEORY.md T2/T5 supply the mathematical
basis. All prior-art limits from v2 remain, including the incomplete Calafiore
full-text theorem comparison. The contribution here is an implemented and tested
decision loop within this case study, with numerical evidence labeled separately.
