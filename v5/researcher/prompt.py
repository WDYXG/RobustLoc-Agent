"""State-only prompt builder; no import or disclosure of the baseline schedule."""
from .io import PACKAGE, read, canonical


def initial_state():
    return read(PACKAGE/'frontier.json')


def research_state(initial, events, results, remaining):
    return {'starting_frontier': initial, 'current_ledger': events,
            'recent_feedback': [{'round': e['id'], 'verdict': r['verdict'],
                                 'evidence': r['evidence'], 'failure_kind': r['failure_kind']}
                                for e, r in list(zip(events, results))[-4:]],
            'remaining_rounds': remaining,
            'instruction': 'Choose the next ONE research action from this state. No fixed task order. Honest unresolved results and assumption revisions are welcome.'}


def build(state):
    return ('You are the Phase 5 Codex mathematical research proposer. Choose your own next '
            'single claim from the frontier and feedback. The deterministic verifier alone '
            'decides mathematical status. Propose a useful, falsifiable, scoped claim; do not '
            'inflate theorem counts with trivial restatements. You have no permission to read '
            'other files, run tools, or edit anything. All context and allowed mathematical '
            'interfaces are supplied here. Respond only using the required JSON envelope.\n\n'
            + (PACKAGE/'TOOLS.md').read_text(encoding='utf-8') + '\n\nRESEARCH STATE\n' + canonical(state))
