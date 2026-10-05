# Phase 5 preregistered protocol — version 1

Authoring date 2026-10-04. Scope: verifier-governed **selection of one next
research action**, after the frozen cross-problem core at commit 1440f9c.
The 4,083 previously tracked files are hashed in PREVIOUS_FREEZE.json. There is
no v6, third inverse problem, CEP90 tuning, or change to prior claims.

## Question and intended comparison

Does a real Codex proposer, receiving frontier and feedback, produce more
nonduplicated checkable ledger advances than a fixed coverage policy, under
the same mathematical tool budget? This is a **single paired pilot**, not a
statistically powered efficacy study. The outcome can be failure or no gain.
Do not select a better model, seed, proposal, or trajectory after results.

Both policies start from researcher/frontier.json and use identical source
hashes and budgets: 12 rounds; one registered mathematical tool request per
round; 50,000 declared operation units and 60-second worker timeout per request.
Each real Codex proposal has a 180-second timeout. No retry or replacement of a
failed round. Codex token/time costs are additional, not matched to a zero-token
baseline. Operation units are conservative declared charges, not equal CPU time.
Actual tool and proposal time, input/cached/output token receipts, and failures
are recorded. Dollar cost is unavailable without a billing receipt.

The baseline is the frozen predefined coverage schedule in baseline.py. It
uses the same interfaces, frontier probes, a preset assumption repair and a
continuous lower-bound fallback; it deliberately does not react to feedback.
Known-result controls belong to tests, not easy-to-beat baseline rounds.
The Codex prompt never imports the
schedule. Its next claim, parameters, action and optional parent link come from
the actual model response. If CLI authentication is unavailable, record a
zero-call blocked preflight; **do not fabricate twelve Codex rounds**.

## Governance and isolation

The controller is trusted infrastructure; the model is an untrusted proposer.
Real invocation: installed Codex CLI, structured output schema, JSONL receipts,
read-only sandbox, no approvals, no user config, disabled shell/exec, plugins,
MCP apps, hooks, multi-agent, browser/computer tools and host skill discovery.
Project instructions are disabled for this nested proposer; all mathematical
context is the serialized current Research State plus TOOLS.md. CLI default
model is used, not inferred from the outer chat; an unreported model ID remains
unavailable. This transport decision is disclosed rather than guessing a model.
The proposer is stricter than workspace-only write access: it has **no direct
write authority at all**. The controller saves output into its iteration folder.
Any unexpected model tool event invalidates the proposal.

Only the deterministic worker/consumer grants mathematical status, and only
the controller appends ledger events. Existing run files and all scientific
source bytes are checked before/after invocation. These checks detect tampering;
the CLI read-only sandbox supplies prevention. This is not a hostile-host
security proof, and a repository owner can always replace the trusted kernel.
The trusted computing base includes Python/Fraction, the frozen v4 arithmetic,
cover and Bellman consumers, v5 schema/kernel/gate/controller and the OS sandbox.

New source, tests, protocol and literature registry are frozen in each manifest
BEFORE the first proposal. Any later evaluator bug requires an issue note,
separate version and both policies rerun. Iterations and run destinations are
write-once. Failure records are not removed from aggregates.

## Mathematical scope

The verified object is the canonical typed formal statement, never its prose
interpretation. Assumptions must be encoded in that statement; the free-text
assumption list is explanatory only. One proposal contains one such object.
Unsupported or over-budget work is recorded unresolved, not silently rewritten.

Registered consumers: rational planar quotient-radius counterexamples and
finite enumeration; weighted SOS identities on nonnegative polynomial domains;
exact rational negative witnesses; noiseless finite minimax and justified
continuous lower-bound transfer; real CP/support-union instantiation. These are
human-supplied **proof rules**, not autonomous discovery of a proof system.

Known reasoning behind the consumers:

* A real sum of squares with nonnegative weights and nonnegative declared
  multipliers is nonnegative. Equality is checked coefficient by coefficient.
  This is a sufficient positivity rule; a failed SOS certificate is not a
  refutation. A feasible rational point with negative value is a refutation.
* Planar Euclidean smallest balls have support <=3. A sign quotient requires
  consistent lifts. All lifts of the full candidate set must be considered;
  checking triples alone cannot prove a quotient cover. The v4 producer and
  independent max-support-radius consumer are reused.
* A worst-case policy for a continuous prior must solve every physically
  realizable finite restriction. Restriction costs give lower bounds, not
  continuous upper bounds. Noiseless squared-range encoding preserves reply
  partitions because nonnegative square root is injective.
* Real CP plus the two-support-union argument are known. New frame instances
  are controls/repetitions, not newly discovered generic mathematics.

No result expands the old q=1 PR cost contract through a q=0 experiment. The
general sensing-uncertainty and continuous-completeness gaps may remain open.
Polynomial physics interpretations require further model-bound reasoning;
accepting an algebraic inequality does not automatically validate them.

Mathematical status: proved-in-project / refuted / numerically-supported /
unresolved. Proposals begin conjectured; initial literature may be known.
Literature has a separate axis: known / novelty-uncertain. Topic lookup only
certifies the exact previously audited registry statement. Missing topic or
unsuccessful lookup never implies originality. This finite corpus is explicitly
not exhaustive or live literature search; it reuses v4's primary-source audit.

## Metrics, denominator and limitations

All 12 scheduled rounds are in the denominator, including malformed output,
failed authentication during a run, timeout, invalid assumptions and rejected
proofs. A blocked preflight is zero rounds and cannot enter a completed paired
comparison. Report status breakdown as well as gate acceptance/rejection.

Operational productive step = accepted, nonvacuous formal result whose status
has not already been accepted for the same canonical statement and which is
not a known historical theorem instantiation. Sample support, finite proofs and
universal proofs/refutations remain distinguishable. This is **ledger progress**,
not scientific importance. Trivial constant inequalities and unverified-empty
constraint domains do not count. Semantic deduplication removes exact rational
formatting, prose, positive polynomial scale and positive universal-radius
scale; it is incomplete for general equivalences or renamed permutations.

Successful conjecture revision requires an explicit valid parent, same formal
family, changed statement and accepted nonduplicated result after a refuted or
unresolved parent. Stricter polynomial assumptions are separately counted.
Unsupported overclaim count checks requested status against authorized status;
it does not pretend to understand every natural-language exaggeration.
Cross-problem calls are counted from executed finite_cost consumers, not a
model's claim to have transferred a structure.

## Reproduction and exit criterion

Preserve starting state, every full prompt, raw provider events, final proposal,
runtime/usage receipts, exact evidence, consumer disposition and ledger hash
chain. Replay validates source/output hashes, rebuilds every state/prompt,
reruns every mathematical tool/gate and reconstructs the ledger and metrics.
Replay fixes the recorded proposals; fresh stochastic regeneration is a
different experiment, not promised byte-identical reproduction.

Phase 5 is complete only with actual authenticated 10–12-round Codex execution,
matched scripted execution, deterministic replay, tests, integrity audit and
an evidence-bounded report. Infrastructure and scripted execution alone do not
answer whether the agent adds value over a fixed workflow.

CLI interface checked against installed 0.160.0 and official documentation:
[non-interactive execution](https://learn.chatgpt.com/docs/non-interactive-mode),
[configuration](https://learn.chatgpt.com/docs/config-file/config-reference).
