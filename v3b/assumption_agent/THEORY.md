# Assumption uncertainty: mathematical ledger

All weights w_i>0 are fixed. D is a nondegenerate compact rectangle. There are
at most q arbitrary bad ranges; clean weighted residual norm <=epsilon.
Write m=max(0,n-2q). The trimmed secant norm retains the m smallest coordinate
squares. Anchor positions lie in product balls ||p_i-pbar_i||<=delta_i.

## K1 [known]: foundations and scope

Reverse triangle inequality, support-union 2q, weighted scatter, det/trace
eigenvalue lower bounds and singular-value perturbation are existing results.
The frozen v2 bounded-domain scatter derivation is reused. FIM is a local
statistical information object; frame/erasure margins concern linear maps;
neither gives global range uniqueness. Set-membership and geometry-aware
selection have direct prior art (see LITERATURE_AUDIT.md). Nothing below
establishes priority or a novel general mathematical object.

## T1 [proved-in-project]: uniform shared-map perturbation

Define mu_rob=inf_{p in P} inf_{x!=z in D} d_{q,p}(x,z)/||x-z||.
For convex D with r_i=dist(pbar_i,D)>delta_i, put
L_i=delta_i/(r_i-delta_i), C_q=sqrt(sum of the m largest w_i L_i^2).
Then mu_rob >= max(0,mu_nom-C_q).

Proof. The derivative of u/||u|| has norm <=1/||u||. Integrate over the
anchor displacement segment, whose distance from D is >=r_i-delta_i:
||grad h_p_i(x)-grad h_pbar_i(x)||<=L_i. Integrate over [x,z] subset D.
For every survivor S, the change of the weighted secant vector has norm
<=sqrt(sum_S w_i L_i^2)||x-z||<=C_q||x-z||. Triangle inequality,
then minimize over S,x,z,p. If separation fails, this bound is unavailable,
not proof of zero margin. Independent balls contain pbar, so mu_rob<=mu_nom.

## T2 [proved-in-project]: computable robust scatter certificate

Let Rbar_i be an upper bound on all nominal ranges on D; choose
R_i>=Rbar_i+delta_i, nu_i=w_i/R_i^2. For every |S|=m, let C0_S be the
weighted centred scatter of nominal anchors with these nu_i. Then

b_scatter = min_S max(0, sqrt(lambda_min(C0_S))
                          - sqrt(sum_S nu_i delta_i^2)) <= mu_rob.

Proof. Frozen v2's range-square subtraction gives, for every actual p and S,
d_{S,p}(x,z)>=sqrt(lambda_min(C_S(p)))||x-z||. For weighted centering,
B(p)=Q diag(sqrt(nu)) P, where Q is the orthogonal projector perpendicular
to vector sqrt(nu), and B(p)^T B(p)=C_S(p). Standard singular-value
perturbation gives sigma_min(B(p)) >= sigma_min(B(pbar))-||B(p)-B(pbar)||.
The perturbation norm is <= its Frobenius norm <=sqrt(sum_S nu_i delta_i^2),
because ||Q||<=1. Minimize over S and p. This works even if D contains an
anchor. The implementation uses det(C)/trace(C)<=lambda_min(C), rational
R_i upper bounds and outward integer square roots. All survivor subsets are
enumerated; complexity is combinatorial. For delta=0, exact squared R_i
recovers the frozen v2 scatter bound. Max of T1/T2 lower bounds is valid.

## C1 [refuted]: positive shared-map margin makes unknown anchors exact

The claim error<=2epsilon/mu_rob for an unknown anchor configuration is false.
Take eight rational circle anchors of radius5, D=[-1,1]^2, delta_i=1/10,
epsilon=0, q=0. Explanation A: x=(0,0), p=pbar. Explanation B:
z=(1/10,0), p'=pbar+(1/10,0). Every squared range agrees exactly. Both
anchor configurations lie in their balls, while x!=z. T2 certifies positive
shared-map mu_rob (the executable witness records its rational bound).
Each secant in mu_rob uses the same p; the two explanations use different p.
The joint-nuisance map has translation ambiguity whenever these translations
are allowed. This is a known gauge mechanism with an explicit project witness,
not a refutation of the valid shared-map definition.

## T3 [proved-in-project]: recovery with nominal anchor model error

Define zeta_q=sqrt(sum of the n-q largest w_i delta_i^2), for q<n.
For a nominal candidate xhat in D with a q-trimmed residual certificate
rhat<=epsilon+zeta_q, a positive T1/T2 uniform lower bound b gives

||xhat-xstar|| <= (epsilon+rhat+zeta_q)/b
               <= 2(epsilon+zeta_q)/b.

Proof. Reverse triangle bounds each weighted range model error by sqrt(w_i)
delta_i. On n-q truly clean coordinates, the true position's nominal residual
norm is <=epsilon+zeta_q, so candidate search has a feasible target but need
not find it. On n-q candidate residual coordinates, its actual-p residual
is <=rhat+zeta_q. Intersect these sets: at least n-2q coordinates remain.
Triangle inequality bounds the actual-p trimmed secant norm by
epsilon+rhat+zeta_q; apply b. Equivalently use nominal margin b_nom and the
true nominal residual. Both are valid; this system intentionally uses uniform
b throughout for a physically robust geometry diagnostic and conservative gate.
The clean set can be padded to exactly n-q; hence largest n-q, not smallest.

## T4 [proved-in-project]: sufficient assumption frontier

For fixed (q,D,delta), eps_max=rmax*b/2-zeta_q. If eps_max>=0, every
epsilon in [0,eps_max] passes the geometry/model-error pre-gate; final recovery
still requires candidate residual feasibility. Rows with b=0 are uncertified,
not impossible. q_cert is max certified q over the complete finite q profile,
not inferred actual q. For q in {0,...,Q}, epsilon in [0,E], every q row <=Q
must pass; the implementation checks all rows rather than presuming certificate
monotonicity (zeta also changes with q). Proposed D/delta reductions are
conditional until externally supported. An estimator cannot manufacture a
better physical noise budget, q budget, prior coverage or anchor calibration.
The final candidate uses a Q-trimmed explanation and T3 at Q, which covers all
actual q<=Q by padding the true bad set. It need not fit all ranges under a
q=0 explanation when q=0 is incompatible with the observed data. Requiring
every row's pre-gate is conservative; the Q theorem alone already covers
the whole upper set. Separate frontier rows permit conditional budgets.

## H1 [conjectured]: heterogeneous information can beat range-only purchases

Under fixed costs and credible service outputs, selecting the limiting premise
can yield more newly certified decisions per cost than adding ranges. This is
an empirical hypothesis for the fixed simulation, not a universal theorem.
Finite-horizon optimality, stochastic service reliability, tight robust mu,
joint nuisance inference, genuine sensor deployment and cross-problem transfer
remain unresolved. Reject/retain H1 per scenario as well as pooled results.
