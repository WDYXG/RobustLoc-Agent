# Global Stable Recoverability of Planar Range Localization under Sparse Adversarial Corruptions

All project proofs below are **proved-in-project** written deductions from known
foundations, not formal verification or claims of novelty. Refuted conjectures
retain their witnesses. Exact known algebra is explicitly distinguished.

## Object and assumptions

Exact fixed anchors p_i∈R², fixed weights w_i>0, n observations and integer
0≤2q<n. Define h_i(x)=||x-p_i||, m=n-2q and a_i=w_i(h_i(x)-h_i(z))².
For a domain D with at least two points,

\[
d_q(x,z)=\min_{|S|=m}\|W_S^{1/2}(h_S(x)-h_S(z))\|,
\qquad \mu_q(D)=\inf_{x\ne z\in D}\frac{d_q(x,z)}{\|x-z\|}.
\]

μ is an operational lower inverse-Lipschitz constant. d_q need not be a metric;
it can vanish for distinct points. If 2q≥n we conventionally retain zero coordinates,
d_q=μ_q=0. Weights are not estimated from residuals. Uncertain anchors, moving
targets and actual unknown corruption counts are outside these guarantees.

## T1 — sorted separation (known; derivation checked in project)

Let a_(1)≤…≤a_(n). For any subset of size m, its ordered selected values are at
least the first m order statistics coordinatewise. Choosing their indices attains
the bound, including ties. Thus d_q²=Σ_{j=1}^m a_(j). For a fixed pair (x,z),
evaluate all ranges in O(n), sort in O(n log n). This does **not** turn the local
minimization over directions, the global four-dimensional infimum, or all subset
scatter certificates into O(n log n). Linear-time selection is also possible.

## T2 — global feasible recovery (proved-in-project)

Let a common observation y have two explanations at x*, xhat∈D. There are bad sets
B*, Bhat of size at most q such that the weighted residual norms on their clean
complements are ≤ε1 and ≤ε2. The complement of their union contains at least m
indices. Choose any m of these as S. Triangle inequality on S gives
d_q(x*,xhat)≤||W_S^(1/2)(h_S(x*)-h_S(xhat))||≤ε1+ε2.
If μ_q(D)>0, its defining lower bound implies

\[
\|\hat x-x^*\|\le(\varepsilon_1+\varepsilon_2)/\mu_q(D).
\]

Using an independently certified b≤μ with b>0 gives the conservative bound
(ε1+ε2)/b. This applies to every feasible candidate in D, with no smallball prior
or finite-pool completeness assumption. It does not assert a specific decoder
finds such a candidate, nor certify truth∈D or the noise/corruption assumptions.

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

## T4 — compact near/far existence proof (proved-in-project)

Suppose D is compact, separated from anchors, and every m-anchor subset contains
three noncollinear anchors. For every x the surviving Jacobian rows span R²:
otherwise all p_i in that subset lie on a line through x. Thus γ(x)>0; continuity
and compactness give γ0=min_D γ>0. Let r0=min_{x∈D,i}||x-p_i||>0. For pairs of
distance t≤δ<r0, the connecting segment is at least r0-δ from every anchor, even
if D is nonconvex. Range Hessian norm is 1/||x-p_i||, so weighted Taylor remainder
≤(1/2)L t² with L=sqrt(Σw_i)/(r0-δ). All subsets obey the bound and hence
d_q/t≥γ0-Lδ/2. Choose δ small enough to make this ≥γ0/2.

For t≥δ the pair set is compact. If d_q=0, equality of ranges at a surviving
noncollinear triple implies x=z by subtracting squared distance equations. Thus
d_q/t is positive and continuous there and attains a positive minimum. Combine
near and far; μ>0. If the far set is empty the near bound suffices.
This is sufficient, not necessary for arbitrary restricted D. Global full-plane
injectivity does not by itself give a uniform positive constant on an unbounded D.

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

## C3 / R-branch — local does not determine global (refuted)

Take anchors (-2,0),(0,0),(2,0),(1,3), w=1, q=1. Let c±=(3/10,±1) and
D be the union of closed squares of halfside 1/10000 centered at c±.
At c± every two surviving Jacobian rows are independent: the three horizontal
anchors have distinct bearings; vectors to the fourth are not parallel to them
(check their rational determinants). Exact centre Gram det/trace bounds, minus
the uniform derivative perturbation over each square, certify inf_D γ>0.
Yet the first three ranges agree at c+,c−, so at least m=2 agree and d_1=0.
Thus μ_1(D)=0<inf_D γ. This disproves C3 over compact full-dimensional domains,
including domains that are closures of their interiors. D here is disconnected;
this witness does not settle an additional connected/convex-domain conjecture.

**refuted R-unbounded:** with any fixed noncollinear triple, q=0, D=R²,
x_R=(R,0), z_R=(R,1) have unit separation. Their ith range difference is
(1-2p_iy)/(h_i(x_R)+h_i(z_R))→0. Thus μ_0(R²)=0 despite exact global injectivity.

## T6 — conditional corruption profile (known monotonicity; deduction checked)

Increasing q retains fewer smallest nonnegative coordinates: d_(q+1)≤d_q and
μ_(q+1)≤μ_q. Decreasing domain D increases μ; changing weights changes the object.
For κ>0, the ideal q_cert=max{q:μ_q≥κ}. Verified lower and upper bounds [b_q,U_q]
give a certified lower budget max{q:b_q≥κ} and a possible upper budget
max{q:U_q≥κ}; missing certificates do not imply μ=0. A witness U_q=0 does.
These are conditional guarantees for each assumed q, not an estimate of the
corruption count in observed data.

## Computed near/far certificate

On a convex rational rectangle avoiding anchors, subdivide into 2D cells. At each
centre compute surviving weighted Gram matrices exactly and γcentre≥sqrt(det/trace).
Let ρ bound the cell circumradius, and r_i bound anchor distance below on the cell.
Then γ(x)≥γcentre-sqrt(Σw_i/r_i²)ρ. Taking all cells gives γ_D lower.
The whole-domain Hessian bound L_D gives a near-pair lower bound
b_near=max(0,γ_D-L_D δ/2) for ||x-z||≤δ.

For a 4D pair box X×Z, range intervals [l_i(X),u_i(X)] and [l_i(Z),u_i(Z)]
give gaps g_i=max(0,l_i(X)-u_i(Z),l_i(Z)-u_i(X)). Let M bound ||x-z|| above.
The node lower ratio is sqrt(Σ smallest m w_i g_i²)/M. It is valid for all
distinct pairs in the box. Boxes with M≤δ use b_near; others are bisected or
retained as unresolved leaves with their valid (possibly zero) bounds. Complete
binary coverage must be checked. Every leaf can also use T5's independent bound.
The combined certificate is max(b_scatter,min(b_near,min_far b_leaf)); the raw
near/far-only result is reported separately to expose interval dependency/budget
limitations. A zero raw result is not proof of instability. All square roots are
rounded outward with integer arithmetic; no binary floating-point claim supports
the lower certificate. Feasible sampled pairs produce only certified upper bounds.
