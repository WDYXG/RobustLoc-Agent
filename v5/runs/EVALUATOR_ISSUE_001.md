# Transport issue 001 — preserved first run, versioned correction

Observed 2026-10-04 in codex-001. Frozen original sources are unchanged.

The installed CLI emits `item.completed` with `item.type = error` for the
startup warning that `skip_host_skill_discovery` is an experimental feature.
The v1 transport rejects every item other than agent_message/reasoning, so it
mistook this non-action CLI warning for model tool use. r01 and r02 each have a
real completed-turn token receipt and a JSON proposal, but were denied before
any mathematical tool ran. They must not count as mathematical failures or
successful autonomous research steps. Both raw event streams are retained.

r03/r04 also received an explicit provider usage-limit error and have no
completed-turn receipt. The current CLI read-only account metadata subsequently
reported ordinary usage available; the cause of that discrepancy is unknown.
Do not infer that these errors consumed zero tokens or that the limit was reset.
No reset credit was consumed, credentials were not read, and no purchase occurred.

The affected runner was stopped during r05. That partial round may lack a
captured completion/usage receipt; its cost is unknown, not zero. No original
record is overwritten. codex-001 is an aborted transport pilot, not a completed
12-round researcher trajectory, and is excluded from the primary paired result.

Correction: a separate `runs/evaluator_v2` transport wrapper sets the documented
`suppress_unstable_features_warning=true` flag. The gate still rejects actual
unexpected tool events and requires a completed provider turn. No mathematical
verification, frontier, baseline, budget, or initial state is changed. The
wrapper also explicitly pins `gpt-6.1-sol`, the CLI's read-only model catalog's
available/default model, for reproducible model selection; this is a transport
availability decision after errors, not a selection based on mathematical score.
Requested model is recorded, with actual model ID left unknown unless reported.

Both policies must run again under the same outer v2 manifest. The v2 files
are separately hashed before either run and checked alongside frozen v1 sources.
The original scripted run and its successful deterministic replay are retained.
