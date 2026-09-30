# RobustLoc-Agent research contract

## Permanent v1 freeze and theory-driven v2

The user permanently froze runs/run-001 on 2026-09-30. Never modify its bytes,
rerun its solvers, tune its benchmark, or regenerate its reports. v2/ is an
independent research scope authorized by the user: theory, literature, proofs,
counterexamples and new experiments. Its AGENTS.md supersedes v1 research rules
within v2/. Evidence categories are exactly known / proved-in-project /
conjectured / numerically-supported / refuted. Reproving known facts does not
establish novelty. V1_FREEZE.json records all previously tracked run/report bytes.

Use observation-only candidate inputs. Never inspect truth or corruption labels
inside a solver. During research modify candidate.py, candidate_config.json and
proposal policy only. Do not edit simulator, scenarios, metrics, evaluator,
baseline, optimizer, verifier, config or historical outputs after manifest freeze.
If a bug is discovered, append EVALUATOR_ISSUE with evidence and consequence;
version the evaluator and start a new run; compare all methods under that version.

One hypothesis and one mechanism per round. Run tests, development and validation.
The independent verifier makes acceptance decisions. Preserve rejected proposals
and positive-excess failure cases. Do not tune after held-out. Skills live in
.agents/skills. Evidence labels: mathematical fact, empirical support, hypothesis,
conjecture, unresolved. No industrial or novelty claim without evidence.
