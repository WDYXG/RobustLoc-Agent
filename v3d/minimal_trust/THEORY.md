# Phase 3C: Minimal Trust Optimality Gap

## Scope and status [known]

Chebyshev radius, smallest enclosing disks, Helly witnesses, test-cost decision
trees, set cover, robust set membership and witness-restriction lower bounds are
known. The propositions below are project proofs of the stated model, without
a priority claim. Exhaustive algorithms are for small instances. No claim of
polynomial complexity, proof-assistant verification or autonomous discovery.

A world includes target x, anchors p, corrupt coordinates/source groups, and
consistent potential replies to every offered query. The observed transcript T
and the external physical contract define W(T), and X(T)={x(w):w in W(T)}.
Hard trust roots, domain coverage, clean noise bound E, q/r budgets and failure
group identities remain external assumptions. A complete finite prior is a
different model from a finite subset of continuous worlds.

For nonempty X define R(T)=inf_c sup_{x in X(T)} ||x-c||. The radius is +infinity
for unbounded X. Empty W means inconsistent premises, not free recovery. The
implemented continuous decisions first exhibit admissible worlds. A standalone
positive conditional bound assumes a nonempty physical contract.

For a finite menu of positive-cost, once-only deterministic queries, define
C_adapt*=inf_pi sup_{w in W0} sum_{a on pi's path in w} c(a), subject to
R(T_pi(w))<=rho for every admissible w. If no policy succeeds, C_adapt*=+infinity.
The restriction to deterministic replies is explicit: stochastic/adversarial
future replies can be incorporated into worlds only when jointly admissible.
Our checked continuous restrictions fix particular allowed replies; our finite
exact solver does not solve arbitrary response-set games.

## P1 [proved-in-project]: radius witnesses and monotonicity

Additional truthful constraints shrink W and X, so R cannot increase. Any valid
point-cover certificate U obeys R<=U. U>rho says nothing about R>rho. For two
feasible worlds, triangle inequality gives R>=||x1-x2||/2.

For a finite planar point set, R<=rho iff every subset of at most three points
fits in a disk of radius rho. Apply Helly to the disks B(x,rho) of possible
centers. Necessity is immediate; sufficiency follows because every three such
convex sets intersect. A smallest enclosing disk is supported by one, two or
three points. Two-point radius is half the separation; a three-point acute
triangle uses its circumcircle, whereas an obtuse/right triangle uses the
longest side as a diameter. The implementation compares squared rational
radii exactly, including equality at the threshold.

### C1 [refuted]: pair witnesses are sufficient for a radius guarantee

Targets (-1,0),(1,0),(0,3/2), rho=21/20: all pair distances are <=2rho, but
the circumcenter is (0,5/12) and radius is 13/12>rho. Thus pair-only coverage
can be zero while a triple witness requires a query. This is known enclosing
disk geometry, retained as an exact project counterexample.

## P2 [proved-in-project]: batch hypergraph equivalence

For each dangerous pair/triple H with R(x(H))>rho, an action breaks H when its
replies on H are not all identical. A fixed purchased set A succeeds on a
complete finite world model iff it breaks every dangerous H. Indeed, an
unbroken H survives in one final response cell and prevents recovery.
Conversely, if a response cell fails the radius test, P1 supplies an unbroken
pair/triple in it. Weighted hitting-set minimization is therefore EXACT for
the finite NONADAPTIVE batch problem. A partial witness collection gives only
a lower bound for that batch problem.

### C2 [refuted]: the global batch hitting-set minimum lower-bounds adaptive cost

Four targets are the square vertices, rho=1/10. Three unit-cost tests have
response patterns g=(0,0,1,1), l=(0,1,0,0), r=(0,0,0,1). Any two fixed tests
leave two targets indistinguishable; all three cost3. Query g, then l on its
left branch or r on its right branch: worst cost2. No single query suffices,
so adaptive optimum=2. Hence C_batch=3>C_adapt*=2.

This is physically realized by exact anchor-position queries in worlds with
identical initial target ranges: g anchor is (-4,0) for the two left targets
and (4,0) for the right targets; l anchor is (-2,2) only at target(-1,1),
otherwise(0,0); r anchor is (2,2) only at target(1,1), otherwise(0,0).
Initial squared ranges are10,2,2 in every world. No fictitious oracle test is
needed. All target/anchor worlds and replies are independently checked.

## P3 [proved-in-project]: an adaptive-safe witness lower bound

For each witness world w, minimize the cost of actions breaking every dangerous
hyperedge CONTAINING w. Call this L_w. Then max_w L_w <= C_adapt*.
Proof: take any successful policy and the actual path under w. If its actions
never break an incident H, all worlds of H give the same replies as w at every
step. By induction they follow the same adaptive path and survive at its leaf,
contradicting recovery. Thus this path is a feasible incident hitting set and
its cost>=L_w. Maximize over w and minimize over policies. If an incident edge
cannot be broken by any available action, its cost is infinite and no policy
can succeed. This is path reasoning, not a new generic set-cover theorem.

## P4 [proved-in-project]: exact finite adaptive optimum and restriction bound

For a surviving world set V and remaining menu U, define

    Q(V,U)=0                                      if R(x(V))<=rho,
    Q(V,U)=min_a [c(a)+max_y Q(V_{a,y},U\{a})]     otherwise.

Only nonempty response cells are included. Tests constant on V cannot improve
it and are skipped; no successful option gives +infinity. Induction on |U|
proves equality with the minimax policy cost. The stored tree provides an upper
witness. A separate bottom-up enumeration uses Helly threshold predicates,
not the producer's enclosing-circle algorithm, to verify the optimum and every
leaf. Since all children of useful tests are strict subsets, the consumer can
use V alone: any previously asked test is constant on a descendant.

For a checked finite restriction Wf subset W, every policy for W restricts to a
policy for Wf with no larger worst cost. Therefore

    max_w L_w <= C_adapt*(Wf) <= C_adapt*(W).

All physical actions, costs and possible replies must be represented. Dropping
a helpful action can INCREASE the finite optimum and invalidate the lower
bound. The consumer requires the full menu, validates each world and response,
and checks the joint noise budget after all queries. A finite upper bound is
an upper bound for W only if the finite prior is explicitly complete; merely
sampling worlds does not establish completeness.

## P5 [proved-in-project]: valid subset upper bounds

For each possible honest-source branch, choose any distinct measurement-index
subset S and retained supported anchor balls. Global corruption budget q also
bounds this subset; clean weighted norm remains <=E. Reuse frozen Phase3B.1
uniform shared-map margin b_S and nuisance inflation

    zeta_S=sqrt(sum of the largest |S|-q values w_i delta_i^2).

If a candidate c in D has nominal q-trimmed residual u<=E+zeta_S, the branch's
continuous target set lies in B(c,(E+u+zeta_S)/b_S). This is the frozen bound
applied to S. Ignoring other information enlarges the model and is safe.
Keep every source-deletion branch; only exact contradictory ball assertions
may prove a branch empty. Every unresolved branch prevents a positive output.
Union covers use max_H(||a-c_H||+B_H). Distinct coordinate indices are mandatory:
duplicating one observation in a certificate would fake corruption redundancy.

Enumeration includes arbitrary coordinate subsets, including some repeats of
a selected reporter while omitting others. A found certificate remains valid
when the search is interrupted. Complete subset enumeration does not mean
complete nonlinear candidate search, exact radius computation, or complete
physical recovery characterization. Independently minimizing branch radii need
not minimize the enclosing radius of their union.

## P6 [proved-in-project]: response-uniform continuous policy upper bound

Restrict this construction to initial hard anchor balls p_i in B(a_i,delta_i),
no soft-source reports, and exact absolute-reference purchases. Other services
remain available in the physical problem but this sufficient policy may ignore
them. For a chosen measurement subset S, compute b_S uniformly over INITIAL
balls using the frozen rational margin producer/consumer. After buying A, let
tilde p_i be the actual delivered coordinate for bought references and a_i for
others. Every tilde p_i is in its initial ball. Thus b_S applies to every
possible delivered nominal geometry, not just forecast layouts.

Remaining nuisance radius is delta'_i=0 if bought and delta_i otherwise. Let
zeta'_S use these remaining radii. For any nonempty resulting transcript there
exists a nominal candidate (take a feasible world's target) with residual
<=E+zeta'_S. P5 then gives, for EVERY admissible reply,

    R(T_A) <= 2(E+zeta'_S)/b_S.

If this is <=rho, the fixed purchase policy proves C_adapt*<=sum_A c(a).
Enumerating bundles by increasing cost and subsets exhaustively finds the
cheapest passing member of this sufficient uniform family. Missing a candidate
or exhausting this family proves no physical lower bound. None in the output
means unknown UB, not infinity. Actual delivered point outputs still require
their independently checked residual certificates.

The cost3.6 regression finds a0,a1,a2 automatically, then the delivered subset
certificate radius is about0.0113 on the original development instance. Its
continuous cost LB is currently0, so 3.6 is NOT claimed physically optimal.
The pre-purchase uniform bound differs from the smaller post-delivery bound.

## P7 [proved-in-project]: budget states and unresolved causes

Given L<=C_adapt*<=U and budget B: L>B proves insufficient information budget;
U<=B proves recovery is possible within this policy's assumptions; L<=B<U is
unresolved. Unknown U leaves the third state unless L>B. Equal finite bounds
prove optimality only for their common world/menu/cost/radius model. Report
gap U-L and relative gap (U-L)/U; when U=0 both are0; unknown/infinite endpoints
give undefined numerical gap, not a fabricated finite number.

Search caps are identified by explicit incomplete enumeration. Complete search
with no passing family member only identifies a family gap; it does not prove
which stronger method would succeed. Strictly distinguishing conservatism from
all possible search failures requires additional positive/negative evidence.
The old3.6 example supplies such positive alternative-certificate evidence.

## P8 [proved-in-project]: a complete reduction with nonzero continuous optimum

This special case supplies the extra completeness proof required by P4. Take
h>0, a=3h/4, q=r=E=0, known anchors (-a,0),(a,0), and their equal exact ranges
5h/4. Subtracting the two squared range equations gives x_1=0; either equation
then gives x_2^2=h^2. Thus the target is exactly (0,h) or (0,-h).
An unknown anchor p has the hard prior ||p||<=2h and exact target range3h.
The chain 3h=||p-x||<=||p||+||x||<=2h+h is equality throughout.
Equality in the Euclidean triangle inequality forces p=-2x. Therefore the
entire continuous target/anchor prior consists of exactly two worlds, provided
the domain contains both. This conclusion uses exact zero noise and tangency;
it does not hold for a sampled prior or a perturbed ball/noise contract.

In the declared menu, ordinary range queries repeat the same three exact
ranges, known-anchor reference queries give the same coordinates, and an
intrinsic baseline between the unknown anchor and either known anchor has the
same length in both worlds. Only the unknown anchor's absolute reference
distinguishes them. Their target radius is h>rho=h/10. Hence every successful
policy must buy that reference, and buying it suffices. Its price7h/5 gives
C_adapt*=7h/5>0 for the continuous model. The three declared scales
h in {1,1/2,3/2} give costs7/5,7/10,21/10.

The consumer checks the algebraic equations, all hard references, domain,
noise/corruption restrictions and the full action menu before transferring the
finite tree upper bound. This is a special exact reduction, not general
continuous minimal-trust optimization. The initial hard-ball geometry family
fails on these collinear nominal centers while this alternative proof succeeds,
providing positive evidence of that family's conservatism. Instrument truth
and exact physical contracts remain assumptions, not empirically established
facts.

## H1 [conjectured]

Richer verified continuous-world witnesses and stronger response-uniform
certificate families may close some nonzero continuous cost gaps. No claim that
the finite restriction will converge to the physical optimum, that this radius
utility is adaptively submodular, or that general minimal trust is solved.
