## T3 — local limit and repaired domain condition (proved-in-project)

For x away from all anchors put A=W^(1/2)J and
γ_q(x)=sqrt(α_2q(x))=min_{|S|=m}σ_min(A_S(x)). Uniform first-order expansion
over unit v gives, for t↓0,

\[
\frac{d_q(x,x+tv)}t\longrightarrow g_x(v):=\min_{|S|=m}\|A_S(x)v\|.
\]

Uniformity follows from the continuous derivative in a closed small ball and
finitely many subsets, using |min f_S-min g_S|≤max|f_S-g_S|. Hence the ambient
liminf over z→x, z≠x is min_{||v||=1}g_x(v)=γ_q(x): both minimizations are over a
finite family and a compact unit circle and commute.

For restricted D define V_D(x) as limit directions of sequences z∈D\{x} tending
to x. When nonempty the restricted liminf is min_{v∈V_D(x)}g_x(v), generally
≥γ_q(x). This follows by subsequence compactness and the same uniform expansion;
each direction in V_D(x) has a realizing sequence. Isolated points have no such
local limit. At interior points V_D(x) is the full circle. If D=closure(int D)
is compact and avoids anchors, continuity of γ yields

\[
\mu_q(D)\le\inf_{x\in\operatorname{int}D}\gamma_q(x)
=\inf_{x\in D}\gamma_q(x).
\]

**refuted R-domain:** arbitrary compact D does not suffice. On
D=[-1,1]×{0}, anchors (2,0),(3,0),(4,0),(5,0), w=1, q=1, γ≡0 while
every surviving distance difference has magnitude ||x-z||, so μ_1(D)=sqrt(2).
The missing ambient direction is perpendicular to the line. Do not label
positive ambient γ a necessary condition for all restricted domains.

The 2D spectrum, **known**, is λ_min(G)=(tr G-sqrt((G11-G22)²+4G12²))/2.


Written deduction authored in the Codex development session; not a runtime formal proof.
