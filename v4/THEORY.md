# Phase 4: transferable proofs and explicit non-transfers

All results concern real planar states, fixed known measurement designs unless
an explicitly marked legacy nuisance adapter is used, and at most q arbitrary
corrupted measurement coordinates. Proofs below are **proved-in-project**
specializations of known structures; they are not priority claims or formal
proof-assistant theorems. The literature audit separates existing PR theory.

## T1 [proved-in-project]: an observation-map-independent recovery lemma

Let (X,d) be a metric space, including a quotient metric space, and h:X->R^m.
For q>=0 and k=max(0,m-2q), put

    Delta_q(x,z) = min_{|S|=k} ||h_S(x)-h_S(z)||_2,
    mu_q(D) = inf_{x,z in D, d(x,z)>0} Delta_q(x,z)/d(x,z).

Suppose y is compatible with x outside a corruption support C_x of size<=q,
with clean residual norm<=epsilon_x. Suppose it is compatible with z outside
C_z of size<=q, with norm<=epsilon_z. The intersection of their clean sets has
size>=m-2q. Choose S of size k inside it. The triangle inequality gives

    mu_q(D) d(x,z) <= Delta_q(x,z)
                   <= ||h_S(x)-y_S|| + ||y_S-h_S(z)||
                   <= epsilon_x + epsilon_z.

If mu_q(D)>0, this proves d(x,z)<=(epsilon_x+epsilon_z)/mu_q(D).
No differentiability, Euclidean state coordinates, range formula, or PR formula
was used. If m<=2q, Delta=0, and the lemma cannot give a positive margin on a
domain containing two metric-distinct states. In the implementation q is an
integer in [0,m]; larger budgets can be capped at m before entering the API.

A trimmed residual over the smallest m-q coordinate squares constructs the
candidate's possible clean support. Directed rational observation enclosures
give an upper residual; uncertifiable numerical cases abstain. A positive
adapter margin is a lower bound, never inferred from sampled pairs. A finite
candidate grid is a search mechanism only: whenever a candidate is certified,
T1 covers every actual state in the continuous declared domain. Failure to find
a grid candidate does not prove infeasibility.

This same function is used by both adapters. The range margin producer and
consumer are imported from the frozen v3b mathematics; that implementation is
not re-proved or rewritten as PR code.

## T2 [known; project proof recorded]: sign quotient and complement property

For real PR, h_A(x)_i=(a_i^T x)^2 and h_A(-x)=h_A(x). The physical recovery
metric is d_pm(x,z)=min(||x-z||,||x+z||). Sign copies are one state class, not
an unsafe localization branch. With anchored range coordinates the tested
universal state-only symmetry is the identity. Joint target/anchor E(2) gauge
from unknown-reference models is NOT rediscovered by the fixed-design adapter.

For a real frame, quotient injectivity is equivalent to the complement property:
for each partition I,I^c, one part spans R^d. Indeed equality of intensities
implies (a_i^T(x-z))(a_i^T(x+z))=0. If neither x-z nor x+z is zero, the two
parts lie in two proper orthogonal hyperplanes. Conversely, if both parts fail
to span, choose nonzero u and v perpendicular to the respective parts; then
x=u+v and z=u-v have equal measurements but x is not +/-z. This is established
PR theory (Balan--Casazza--Edidin; Bandeira et al.), not a project discovery.

The symmetry search tests eight declared signed coordinate permutations.
For PR, exact coefficient identities for a=e1,e2,e1+e2 span all symmetric
quadratic forms, proving invariance for every sensing vector, not only the
current design. For range, the known-anchor polynomial identity is checked
on the zero/basis anchors and state coefficient probes; signed permutations
are orthogonal, so these probes fix the remaining linear terms. The accepted
sets are {I,-I} and {I}. Current-design symmetries such as independent sign
flips under coordinate-only PR are NOT silently quotiented out: they describe
insufficient measurements, not a universal symmetry of the sensing family.
The adapter supplies this algebraic checker. No unrestricted symbol discovery
or LLM conjecture generation is claimed.

## T3 [proved-in-project]: unknown corruption transfers as 2q deletion

Noiseless recovery modulo the declared symmetry under <=q arbitrary corruptions
is possible iff every m-2q survivor map is injective on the quotient domain.
Sufficiency is T1's support argument with zero residuals, using injectivity
instead of a quantitative margin. For necessity, a collision on m-2q survivors
has at most 2q differing coordinates. Split them into two sets of size<=q and
take y coordinatewise from h(x) on one and h(z) on the other; each state can
explain y with <=q corruptions. When m<=2q any two states admit this split.

**H2 refuted:** four vectors (1,t), t=0,1,2,3 remain phase retrievable after
any ONE deletion. A finite grid search nevertheless finds x=(-2,0), z=(-2,2),
with measurements (4,4,4,4) and (4,0,4,16). The common transcript (4,0,4,4)
requires one changed coordinate in each world. They are not sign-equivalent.
Deleting two rows leaves only two vectors, which fail the real planar CP.
The transcript and both corruption supports are checked independently.

## T4 [proved-in-project]: a conservative continuous PR margin certificate

Let D={x: r0<=||x||<=r1}, with r0>0, in R^2. For every survivor set S of
size m-2q, construct the rows b_i=(a_i1^2,2a_i1*a_i2,a_i2^2) and G_S=B_S^T B_S.
For PSD G with trace>0,

    lambda_min(G) >= tau(G):=det(G)/trace(G)^2 >=0.

For positive eigenvalues this follows by writing lambda_min=det/(lambda2*
lambda3) and bounding that product by trace^2. Singular G gives tau=0; the
zero Gram is assigned tau=0. For M=xx^T-zz^T, set v=(M11,M12,M22). Then

    ||h_S(x)-h_S(z)||^2 = v^T G_S v
      >= tau(G_S)||v||^2 >= tau(G_S)||M||_F^2/2.

Choose the sign of z so c=<x,z>>=0, and write r=||x||>=s=||z||>=r0.
Since

    ||M||_F^2 = (r^2-s^2)^2 + 2(rs-c)(rs+c),
    d_pm(x,z)^2 = (r-s)^2 + 2(rs-c),

the first expression is >=s^2 times the second: (r+s)^2>=s^2 and
rs+c>=s^2. Consequently

    mu_q^PR(D) >= r0 * sqrt(min_S tau(G_S)/2).

The consumer recomputes Gram entries and uses Cauchy--Binet (sum of squared
3x3 row minors) for the determinant, instead of the producer's Gram determinant
formula. It requires ALL 2q-survivor subsets and original-design/domain binding.
Lower square roots are directed downwards. The certificate may be conservative;
it is not a new optimal PR Lipschitz constant or a general high-dimensional test.

**H3-unqualified refuted:** injectivity alone does not make this d_pm intensity
margin positive near zero. For fixed u!=0, x=t*u, z=0, the numerator scales as
t^2 and the denominator as t. Thus mu=0 on a domain containing this sequence,
even when the frame is phase retrievable. This is local scaling degeneracy,
not a pair of distinct states with exactly equal observations. The standard
lifted distance ||xx^T-zz^T|| is a different metric. The code keeps d_pm and
states the annulus restriction; it does not silently change the user metric.

## T5 [proved-in-project]: quotient radius requires consistent lifts

For a finite set P of sign classes in R^2,

    R_pm(P)^2 = min_{s_i in {+1,-1}} R_Euclidean({s_i x_i})^2.

For any center choose each nearest lift to prove one inequality. A Euclidean
cover of any chosen lifts covers the quotient classes, proving the other.
Common sign reversal preserves radius, so fix s_1=+1. The algorithm checks
2^(n-1) lifts. Its consumer instead takes the maximum pair/acute-triple radius
within each lift (Euclidean Helly), then minimizes over ALL lifts. The center
is checked directly in the quotient distance. Centers are allowed anywhere
in the ambient quotient space; they need not belong to the annulus prior.

**H4 refuted:** a Euclidean three-state witness limit does not transfer.
For P={(1,0),(0,1),(3/5,4/5),(-4/5,3/5)}, every triple has squared quotient
radius<=1/2, but the whole set has squared radius4/5. With tolerance4/5,
the threshold squared is16/25, strictly between those quantities. This exact
four-world obstruction is found by enumeration of a declared rational pool.
Quotient balls lift to unions of Euclidean balls, so the convex Helly argument
cannot simply be applied to them. The common ambiguity engine enumerates
minimal dangerous subsets of arbitrary size in the supplied tiny catalog.
This is a transfer counterexample, without a novelty claim or a theorem that
four always suffice.

## T6 [proved-in-project]: information cost proofs transfer without h

Given any deterministic finite possible-world model and a radius oracle, the
Bellman recurrence C(V)=0 at safe leaves and min_a[c(a)+max_y C(V_a,y)] otherwise
is unchanged. Full reply partitions, positive once-only costs and complete
world/menu contracts are required. Terminal radius is adapter-dependent.
Every successful path in world w must break every dangerous subset containing
w; hence the maximum incident-cover cost is an adaptive lower bound. Global
batch cover is still NOT an adaptive lower bound (frozen v3d counterexample).

A verified finite restriction gives only a continuous cost LOWER bound. The
implementation never transfers its finite tree upper bound unless the prior is
explicitly complete. The three budget states follow from L<=C*<=U exactly as
in v3d. This mathematical reduction does not require a localization formula.
All 43 frozen Phase3C cases are run through the new generic engine and compared
at the interval/decision level; the four actual subset outputs are identical.

## T7 [proved-in-project]: PR acquisition upper with persistent corruption

Let an acquisition bundle append sensing vectors to A, without changing the
single GLOBAL corruption budget q, total clean-noise norm E or annulus prior.
If the adapter certifies mu_new>0 and 2E/mu_new<=rho, then every nonempty future
transcript has target radius<=rho: pick any feasible candidate and apply T1 to
every other feasible state. Thus the fixed bundle's cost is a physical UPPER
bound for arbitrary allowed future replies, not merely the clean simulated
reply. Enumerating cost-ordered bundles finds the cheapest passing member of
this sufficient design family, not necessarily the physical optimum.

Actual output still requires a checked candidate; the implemented grid solver
can abstain if it misses one. New measurements are NOT assumed trustworthy:
they may be among the same q arbitrary corruptions. The lower restriction uses
particular jointly admissible clean future replies; this is valid for a lower
bound but never proves all future replies are clean. Both initial and appended
measurements are checked against one joint residual budget. Formal successful
simulations deliberately retain unresolved continuous optimality gaps.

## H5 [conjectured]

Other nonlinear inverse problems with checkable quotient metrics and global
separation certificates may admit the same support-union/cost/decision core.
Two planar case studies do not establish universality, learned transfer, or an
autonomous mathematical researcher. No complex phase retrieval, uncertain PR
sensing vectors, general gauge solver, continuous minimax game solver or LLM
proposer is implemented in Phase4.
