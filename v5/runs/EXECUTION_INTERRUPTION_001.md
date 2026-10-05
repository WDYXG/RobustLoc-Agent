# Operational interruption and continuation

Continuation date: 2026-10-05 (Asia/Shanghai).

The v2 Codex execution session became unavailable after r06. A host process
query found no matching runner. r07 contained only input_state.json,
invocation.json and prompt.txt, with no model output or captured completion
receipt. The cause of the interruption is unconfirmed.

The separately hashed operations_v1 continuation controller:

1. Protects every existing artifact with a SHA-256 manifest and independently
   replays each completed round before extending the state.
2. Consumes r07 as an unresolved provider failure, with **unknown token cost and
   unknown duration**. Empty capture files explicitly mean no captured bytes;
   they are not simulated provider output. Its numeric wall_seconds=0 is marked
   as a lower bound, not a claim that the attempted inference took no time.
3. Does not retry r07. It proceeds to r08–r12 using the rebuilt ledger and the
   original source hashes, mathematical budget, model request and read-only
   transport. The mathematical verifier and its dispositions are unchanged.
4. Finishes the original output-hash manifest, complete deterministic replay,
   and a RESUME_AUDIT.json that declares the missing cost information.

Consequently the study has 12 planned slots and, if the remaining calls finish,
11 actual proposals with completed provider receipts. The interruption remains
in the denominator. Total observed runtime/tokens are lower bounds on actual
cost, and the study is not an uninterrupted twelve-inference demonstration.

This is an operational recovery, not a new mathematical evaluator or a
post-result repair of an unsuccessful conjecture. The scripted policy receives
no extra budget. Report the raw paired result and this execution asymmetry;
do not infer statistical or general scientific superiority from either score.
