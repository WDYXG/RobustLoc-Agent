# Tool contract exposed to the proposer

Choose one research question from the state, or propose a different relevant
one. There is no round-to-task schedule. Only one formal claim per proposal.
Use the JSON envelope fields exactly. `formal_statement_json` and
`evidence_request_json` contain JSON **strings**. The mathematical proposition
below is authoritative; prose interpretations and informal assumptions are
unverified. `claimed_status` may stay `conjectured`; do not grade yourself.
`parent_id` is an earlier round ID (e.g. r02), or the empty string.

Rationals are integers or strings such as "3/5"; no floating-point numbers.
The single tool request is dispatched by the controller. Do not use shell,
files, MCP, web, agents, or external tools yourself. You may supply certificates
or search points as JSON. Unsupported questions can use `open` and remain
unresolved. No arbitrary executable code is accepted.

## radius

Statement keys: `symmetry` = identity | sign; `k` = 1..5; `rho` positive rational;
`scope` = all-planar | finite-universe; `universe` = 2..8 distinct rational 2D
points; `max_size` = k+1..6, at most universe size. Request: `{}`.

Proposition: for every finite set H (in all R^2 for all-planar; or a subset of
universe of size <= max_size for finite-universe), if every subset of size <=k
admits a radius-rho ball, then H admits one. Centers are unrestricted planar
centers, distance is Euclidean or d_pm. The tool searches subsets of universe
from k+1 to max_size, enumerates sign lifts when needed, returns an exact
counterexample or a bounded search. A bounded search cannot prove all-planar.
You choose the universe and radius; no built-in sequence of candidate claims.
Sets of size <=k satisfy the implication trivially. Universal positive radii
are identified under scale equivalence for duplicate detection.

## polynomial

Statement keys: `variables` (1..4 unique identifiers), `polynomial` (p),
`constraints` (0..4 polynomials g_i), `interpretation` (unverified prose).
Meaning: p(x)>=0 for ALL real x satisfying every g_i(x)>=0.
Polynomial format: {"2,0":"1", "0,2":"-1"} for u^2-v^2 in two variables.
At most 64 monomials per polynomial; nonnegative integer exponents, total
degree <=12. No Python/sympy strings. Variable ordering is significant.

Request keys: `points` (0..128 rational points for counterexample search),
`sos` (0..32 objects with `weight`, `polynomial`, `constraint`). A term means
w*s(x)^2*g_j(x); weight must be nonnegative; constraint -1 means multiply by 1.
An exact identity p = sum of terms proves the FORMAL inequality. Finding a
negative value at a point satisfying all constraints refutes it. No certificate
and no counterexample gives only sample support (or unresolved with no valid
samples). The gate does not certify the proposed connection to sensing physics.
If changing a conjecture after failure, link the prior round via parent_id.

## finite_cost

Statement keys: `problem` = range | pr; `worlds` = 2..6 rational 2D targets;
`parameters` = 1..4 planar anchors or sensing vectors; `costs` positive rationals
of equal length; `tolerance` nonnegative rational; `relation` = <= | >= | ==;
`bound` nonnegative rational; `scope` = finite-prior | continuous. Request: `{}`.

Model: noiseless q=0, E=0, no initial observations. All actions available once;
costs additive; the objective is worst-case adaptive total cost to achieve a
radius-tolerance cover of all remaining possibilities. Range replies are
encoded by squared distances (exact nonnegative ranges have identical reply
partitions); PR replies are squared inner products, with sign quotient covers.
For finite-prior, worlds are the complete prior. For continuous, the prior is
all R^2 and worlds are only a restriction. In the latter case, finite values
can prove lower bounds or refute upper bounds, never establish a continuous
upper bound or completeness. This tool cannot answer old q=1 acquisition
instances by silently dropping corruption, noise or initial transcripts.

## pr_injectivity

Statement keys: `design` = 1..7 rational planar sensing vectors; `q` integer in
[0,m]. Proposition: every transcript with at most q arbitrary changed squared
intensities has at most one real state modulo sign (all R^2). Request: `{}`.
The tool checks CP on all m-2q survivors or constructs two states and a shared
transcript. This is an instance of already known CP/support-union structure;
it is logged as a known-result repetition, not a new research advance.

## literature

Action must be literature-audit. Statement keys: `topic_id`, `query`; request
`{}`. Audited topic IDs: real-pr-complement-property, intensity-origin-degeneracy,
two-support-union. Other IDs are allowed, with novelty-uncertain result.
This is a frozen primary-source topic registry, NOT open-web literature search.
Only the exact registry statement gets a known label; a model-supplied query
cannot expand its scope. No lookup grants originality or a mathematical proof.

## open

Statement keys: `statement` (nonempty string); request `{}`. An unsupported
question is recorded as unresolved. It is valid to conclude that tools are
insufficient, stop a line of investigation, or select another frontier.

## Limits and scoring

One mathematical tool request per round, including verification, <=50,000
declared operation units and <=60 seconds in its worker. Units are deterministic
charges, not CPU instructions. Oversized cases may exhaust the budget before
search. CLI wall time <=180 seconds per proposal. Twelve rounds per policy.
Invalid proposals, runtime failures and timeouts consume a round; no retries
chosen after seeing a result. Both policies get the identical initial state
and mathematical budget. Codex inference is an additional measured cost.

Progress means a nonduplicated, nonvacuous verified formal ledger step, using a
limited canonicalizer, not an automatic verdict on novelty or importance.
Finite instances and bounded support are always separately reported. You do
not gain progress by declaring proof success, relabeling known CP results,
changing prose, or rescaling an identical polynomial. Honest failures matter.
