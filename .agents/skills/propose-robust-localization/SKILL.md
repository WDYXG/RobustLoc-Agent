---
name: propose-robust-localization
description: Form one bounded localization hypothesis from persistent metrics and failure cases before a research iteration.
---

Read state.json, the hash-verified research_log.jsonl and previous verification.
Compare current best with WLS on development/validation only. State one hypothesis,
motivation, expected effect and downside. Identify a worst scenario and at least
one contrary case. Change one mechanism relative to incumbent; record parent and
exact parameter/code diff. Solver inputs exclude truth and corruption labels.
Do not alter protected files or view held-out results before freeze. Submit
candidate outputs to verify-robust-localization; do not assign your own success.
Runtime policy is robustloc/proposer.py; Markdown guides Codex-assisted extension.
