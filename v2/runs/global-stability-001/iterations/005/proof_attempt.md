## T5 — constructive scatter certificate; stronger bounded-domain result (proved-in-project)

Let D be bounded with at least two points; it may contain anchors or be nonconvex.
Choose R_i>0 such that h_i(x)≤R_i for every x∈D. Set ν_i=w_i/R_i². For each
survivor S define weighted centroid pbar_S=Σ_Sν_i p_i/Σ_Sν_i and

\[
C_S=\sum_{i\in S}\nu_i(p_i-\bar p_S)(p_i-\bar p_S)^T.
\]

For distinct x,z put u=x-z, c=(x+z)/2. Exact **known** squared-range algebra gives

\[
h_i(x)-h_i(z)=\frac{2(c-p_i)^Tu}{h_i(x)+h_i(z)}.
\]

The denominator is positive for distinct points, even if one point equals p_i,
and is at most 2R_i. Therefore the squared weighted surviving separation is ≥
Σ_Sν_i((c-p_i)^Tu)². The **known** weighted variance identity gives

\[
\sum_S\nu_i(c-p_i)(c-p_i)^T
=C_S+(\sum_S\nu_i)(c-\bar p_S)(c-\bar p_S)^T\succeq C_S.
\]

Consequently

\[
\boxed{\mu_q(D)\ge\min_{|S|=m}\sqrt{\lambda_{\min}(C_S)}}.
\]

C_S is positive definite exactly when those anchors are not collinear. Finitely
many positive matrices imply a positive minimum. This strengthens T4: boundedness
suffices and anchor avoidance is unnecessary for this global theorem (differential
T3 still needs anchor avoidance). No claim that this bound is tight or novel.

For rational rectangle data take R_i²=max corner ||corner-p_i||² exactly. C_S is
rational. For PSD 2×2 matrices, λ_min≥det(C)/tr(C), with zero assigned for trace=0.
Thus b²=min_S det(C_S)/tr(C_S) is an exact rational lower certificate, and an
outward lower square root yields b≤μ. This implementation enumerates subsets;
its combinatorial cost is explicitly retained. Uniform scaling of D and anchors
leaves μ and this bound invariant for unchanged weights.


Written deduction authored in the Codex development session; not a runtime formal proof.
