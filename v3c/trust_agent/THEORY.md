# Joint nuisance identifiability and minimal trust

## Model

World w=(x,{p_i},bad range support,bad source groups). Observed ranges y_k
refer to anchor id a_k, with fixed weights. At most q range coordinates are
arbitrary, and clean weighted norm <=E. D is a trusted bounded rectangle.
Untrusted nominal coordinates impose no physical constraint. Hard references
are externally assumed ball constraints on p_i. A registered source group may
assert many balls; at most r whole groups are dishonest. Trusted baselines
specify squared anchor distances, not absolute direction. Root honesty, q/r,
D coverage and the failure-domain registry cannot be certified from the same
range transcript. The joint target feasible set X(T) is the projection of all
continuous worlds satisfying these constraints. Finite forecast layouts used
for planning are not substituted for X(T) in positive recovery certificates.

## K1 [known]: prior-art boundary

Indistinguishability and two-point minimax bounds, Euclidean gauge, anchored
rigidity, support-union error correction, majority redundancy and set membership
are known. T1–T6 are project proofs/instantiations of these mechanisms, not a
new theorem priority claim. See LITERATURE_AUDIT.md, including SLAM, grounded
network rigidity, secure estimation, calibration and Byzantine models.

## T1 [proved-in-project]: observation-only premise validation is impossible

Let worlds A,B admit identical observable responses to every allowed ordinary
query and the same unanchored receipt strings. If a calibration predicate is
true in A and false in B, no observation-only rule can decide it correctly in
both worlds. Deterministic rules output the same value on the same transcript.
Randomized rules coupled to the same random seed have identical output laws;
under equal world priors their binary decision error is >=1/2. If their target
separation is d, any common point estimate has worst-world error >=d/2 by
triangle inequality. If d>2rmax, no universally valid point output at rmax
exists. Induction over query histories proves the adaptive version. This does
not force every algorithm to falsely certify: always abstaining is valid.
The impossibility concerns informative validation/recovery in both worlds.

Ordinary queries here return only ranges of reporter ids in their local world
or internal distances. They have no trusted absolute actuation/coordinates.
Simultaneous rigid transformations preserve all these responses, including
100 added ranges and every anchor–anchor baseline. A new absolute reference
is outside this ordinary query class and can distinguish the worlds.

## T2 [proved-in-project]: planar rigid stabilizers (known geometry)

For g(z)=Rz+t, R in O(2), no fixed reference allows all E(2) transformations.
Fixing one point a implies t=a-Ra: residual O(2) about a, not independent
translation plus rotation. Fixing two distinct points forces R to fix their
baseline vector: identity or reflection in that line. Fixing three noncollinear
points forces R=I,t=0. Proof: subtract fixed-point equations; two independent
baseline vectors form a basis. For SO(2) only, two distinct points already
fix the rigid frame. Range data usually also admits reflection, so O(2) is
the correct group here. These statements concern rigid orbits only.

## C1 [refuted]: the joint star map is identifiable modulo rigid motion

Take x=(0,0), p1=(1,0), p2=(0,1) versus p1=(1,0), p2=(-1,0).
Both target ranges equal1, but the anchor baseline squared changes from2 to4.
They are not congruent. Each unlocated anchor has an independent angular
freedom. Even three exact external frame points do not locate a target unless
the measurement graph connects to usable references. Fix three unmeasured
anchors, translate only target and measured free anchors: ranges stay equal
but the absolute frame is fixed. These exact counterexamples prevent treating
gauge removal as complete graph identifiability.

## T3 [proved-in-project]: trusted star references and sparse corruption

For k exact trusted anchor-range coordinates (positions may repeat), global recovery over R^2
under q unknown arbitrary errors is possible iff for every x!=z the range
vectors differ on more than2q coordinates. Necessity: partition at most2q
disagreements into two supports of size<=q and form a common contaminated y.
Sufficiency: intersect two explanations' clean supports. Equal ranges for
x,z occur exactly at anchors on their perpendicular bisector. Thus every
k-2q survivor subset must contain three noncollinear anchors for unrestricted
global recovery. Equivalently no line contains k-2q anchors. In particular,
distinct general-position trusted anchors need k>=2q+3. This is a star-map specialization
of known sparse observability, not a new secure-estimation threshold. For a
restricted D, the condition is sufficient; necessity needs a feasible reflected
pair inside D. Repeated ranges from two locations do not remove reflection.

q=0, exact consistent ranges, free untrusted anchors, no additional constraints:
0 measured trusted refs permits every x in D; 1 gives a circle intersect D;
2 gives at most two intersections (usually a reflected pair); 3 noncollinear
gives a singleton. If D contains the whole one-reference circle its diameter
is exactly2d. For two references, exact diameter is2 times target distance
from the reference line. Special on-line/tangent cases and half-plane priors
change count-based necessity and stability; three is not a universal minimum
for arbitrary extra trusted information. Baseline-only information cannot
determine absolute coordinates, even for a globally rigid relative network.
The count k is range coordinates, not necessarily distinct physical sources.
Repeating three measured reference locations can supply sparse-coordinate
redundancy if q counts individual ranges; it cannot guarantee robustness to a
reporter fault that corrupts every repeat unless that fault model is separately
budgeted. The experiment declares coordinate-level q explicitly.

## T4 [proved-in-project]: bounded reference stability

For a selected trusted measured subset, use frozen Phase3B.1 robust shared-map
lower b and zeta_q (largest k-q weighted reference-radius squares). If a nominal
q-trimmed candidate c in D has residual u<=E+zeta_q, all worlds consistent with
that subset obey ||x-c||<=(E+u+zeta_q)/b. A pre-gate uses2(E+zeta_q)/b.
Untrusted free anchors are excluded, not assigned their reported calibration
error as a trusted ball. Bound applies to each possible honest-source branch.
It is conservative and can certify accuracy while strict nuisance uniqueness
fails at scales below the reference uncertainty. Frame fixing is not a claim
of zero-error recovery for positive-radius references.

## T5 [proved-in-project]: two-layer group-corruption cover

For every discarded source-group set H of size min(r,M), retain hard references
and all assertions outside H. Union of these branches covers all admissible
worlds: pad the actual bad groups to r. Group assertions cannot be split into
independent honest coordinates. Ball pairs with centre distance>radius sum
prove a branch empty; other branches remain, even if optimization fails.
Choosing the tightest ball per anchor from retained assertions gives a valid
outer model of that branch (ignoring other constraints weakens, never invalidates,
the cover). T4 produces a ball cover (c_H,B_H) if solver feasibility is checked.
For any reported a, U=max_H(||a-c_H||+B_H) covers X(T). A global diameter upper
is max_{H,K}(||c_H-c_K||+B_H+B_K), including H=K. If one branch is unresolved,
no data-driven positive recovery is authorized. Exact feasible world pairs
give diameter lower witnesses; their half-separation is a minimax radius lower.

Two worlds may remove different range and source supports, so comparison must
allow unions2q and2r. There is no unconditional rule saying3r+1 sources are
needed: that is a different interactive Byzantine consensus model. For M
independent groups each reporting the SAME full exact layout when honest,
M>=2r+1 guarantees an honest majority. All false layouts conflict with it,
so branch deletion leaves only the true layout; target recovery still needs
T3. With2r groups and two inconsistent complete layouts, r per layout, both
can be admissible (target/anchors shift together), hence no unique validation.
Copies from one failure domain are one group, not M independent votes.

## T6 [proved-in-project]: trust–recovery frontier and minimality scope

Define B(T) as a proved sufficient radius upper for a point output covering
X(T), using T4/T5; otherwise uncertified. Exact witnesses give a lower radius
and impossibility at the requested tolerance. The implemented frontier records
finite offered trust bundles, costs, forecast pre-gates, source branches and
post-delivery actual certificates. Minimize cost over bundles whose pre-gate
passes EVERY declared forecast layout. Enumerating all bundles proves minimal
cost for this sufficient certificate and finite forecast model, not a universal
minimum physical trust basis, an optimal nonlinear decoder, or a stochastic
information-value policy. Safety after delivery uses continuous T4/T5, not the
forecast catalog. Forecast failure is not silently repaired with oracle truth.

Diagnoses: exact zero-noise-compatible world pair separated>2rmax proves
structural ambiguity at that resolution; positive exact-reference sparse-map
margin plus an excessive noise pre-bound diagnoses precision/certificate gap;
other loose/incomplete cases are explicitly unresolved. No false binary claim
that every certification failure is fundamentally impossible.

## H1 [conjectured]

In the fixed service menu, a trust-directed agent can avoid purchasing ranges
that preserve a proved structural ambiguity and find a cheaper certificate
than blind range-first/random acquisition. Numerical evidence cannot establish
universal superiority. Trust-root honesty, physical independence, complete
continuous feasible-set calculation, general graphs and optimal adaptive query
trees remain external assumptions or future work.
