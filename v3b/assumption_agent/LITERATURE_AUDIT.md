# Primary-source audit — 2026-10-02

No novelty claim. Scope is bounded range errors, sparse arbitrary bad ranges,
uncertain anchors and finite costed acquisition across different premise types.
This targeted audit cannot establish absence of prior work.

| Existing result [known] | Checked primary source / access | Project distinction and limitation |
|---|---|---|
| Set-membership uncertainty, sequential membership sets, ignoring redundant information | Fogel & Huang, *On the value of information in system identification—Bounded noise case*, Automatica 18(2),229–238 (1982). [Publisher abstract](https://www.sciencedirect.com/science/article/pii/0005109882901108), DOI10.1016/0005-1098(82)90110-8. Abstract checked; full theorem audit not claimed. | Buying useful bounded-noise information is already an established idea. Our finite decision score is not a new value-of-information theorem. |
| Anchor uncertainty in localization; statistical model, maximum likelihood and SOCP relaxation | Naddafzadeh-Shirazi, Shenouda & Lampe, *Second Order Cone Programming for Sensor Network Localization With Anchor Position Uncertainty*, IEEE TWC13(2),749–763 (2014), [DOI](https://doi.org/10.1109/TWC.2013.120613.130170). Journal DOI inaccessible in this session; [author publication list](https://people.ece.ubc.ca/~lampe/publicat.html) search index confirms earlier 2011 WPNC version. Author-uploaded abstract says statistical uncertainty. | Uncertain anchors and robust relaxation are known. Our explicit deterministic balls plus support-union certificate require their own derivation; journal full-text theorem equivalence remains unaudited. |
| Calibration to mitigate uncertain anchors | *Range-Based Rigid Body Localization With a Calibration Emitter for Mitigating Anchor Position Uncertainties* (2019). [Publisher DOI](https://doi.org/10.1109/TWC.2019.2938761), indexed abstract checked. | Calibration is established; our simulated same-centre radius contraction is a simplified service, not a new physical calibration algorithm. |
| Deterministic directional/diameter/volume bounds and geometry-aware anchor selection | Giuseppe C. Calafiore, *Geometry-Aware Set-Membership Multilateration: Directional Bounds and Anchor Selection*, arXiv2603.14263 (15March2026). [Full primary HTML](https://arxiv.org/html/2603.14263), sectionsIII–IV checked: centred scatter, Proposition1 directional width, Corollary1 diameter, Proposition2 enclosing balls, Proposition3 support, Corollary2 principal-axis box; lambda_min/det E/D scores. | Scatter, worst-direction bounds and geometry selection are direct prior art. Its stated setup is exact anchors with squared-range intervals; our q-support enumeration and deterministic ball perturbation are project derivations using known inequalities, with priority unestablished. Multiple premise types at different costs are the experimental question, not claimed unique in literature. |
| Local FIM/GDOP; robust frames; erasure robustness; global range certificates | Frozen v2/LITERATURE_AUDIT.md and v2/global_stability/LITERATURE_AUDIT.md, reused without changing bytes. | Keep local/statistical, linear erasure and global nonlinear claims distinct. Weighted scatter and singular-value perturbation are known, even when derived again here. |

The arXiv2603.14263 abstract/full text is available, unlike the historical
full-text limitation for arXiv2603.04867 recorded in v2. No use of an aggregator
as theorem evidence. Reading the newer full text strengthens the prior-art
boundary; it does not retroactively change frozen reports.

Claim assessment: T1–T4 are **proved-in-project** derivations, with conventional
building blocks explicitly **known**. C1 is a **refuted** naive extension using
a known translation gauge. H1 begins **conjectured** and can become only
**numerically-supported** in this finite synthetic service model. None is a
demonstrated new discovery or a guarantee that software can validate physical
premises supplied by a dishonest source.
