"""Single-claim gateway and operational (not semantic omniscient) metrics."""
import time
from .io import digest
from .io import read, PACKAGE
from .schema import validate, semantic_key
from .math_tools import execute
from .verifier import verify
from .polynomial import Meter, BudgetExceeded


def evaluate(proposal, operation_limit=50000):
    meter = Meter(operation_limit)
    t = time.perf_counter()
    record = {'valid_proposal': False, 'formal_statement': None, 'semantic_key': None,
              'evidence': None, 'accepted': False, 'failure_kind': None}
    try:
        s, req = validate(proposal)
        record.update(valid_proposal=True, formal_statement=s, semantic_key=semantic_key(proposal['family'], s))
        evidence = execute(proposal['family'], s, req, meter)
        record['evidence'] = evidence
        decision = verify(proposal['family'], s, evidence, meter)
        record['accepted'] = decision['status'] in ('proved-in-project', 'refuted', 'numerically-supported')
        record['verdict'] = decision
    except Exception as exc:
        # Fail closed, preserving the error instead of dropping a failed round.
        record['failure_kind'] = ('budget-exhausted' if isinstance(exc, BudgetExceeded) else
                                  'verification-rejected' if record['valid_proposal'] else 'invalid-proposal')
        record['verdict'] = {'status': 'unresolved', 'novelty': 'novelty-uncertain', 'nontrivial': False,
                             'scope': 'no conclusion authorized', 'reason': f'{type(exc).__name__}: {exc}'}
    record['operation_units'] = meter.used
    record['tool_seconds'] = time.perf_counter()-t
    claimed = proposal.get('claimed_status') if isinstance(proposal, dict) else None
    actual = record['verdict']
    record['unsupported_overclaim'] = (claimed == 'known' and actual['novelty'] != 'known') or (
        claimed in ('proved-in-project', 'refuted', 'numerically-supported') and claimed != actual['status'])
    return record


def historical_duplicate(family, s):
    if family == 'literature':
        return s['topic_id'] in read(PACKAGE/'literature.json')
    if family == 'radius' and s['symmetry'] == 'identity' and s['k'] >= 3:
        return True
    if family == 'radius' and s['scope'] == 'all-planar':
        return (s['symmetry'] == 'sign' and s['k'] <= 3) or (s['symmetry'] == 'identity' and s['k'] >= 3)
    # All such tests instantiate an already available generic CP criterion.
    if family == 'pr_injectivity':
        return True
    return False


def ledger_event(round_id, proposal, result, previous):
    proposal = proposal if isinstance(proposal, dict) else {}
    prior = next((e for e in previous if e['id'] == proposal.get('parent_id')), None)
    key = result['semantic_key']; family = proposal.get('family')
    matches = [e for e in previous if key is not None and e['semantic_key'] == key]
    accepted_matches = [e for e in matches if e['status'] == result['verdict']['status'] and e['accepted']]
    historical = result['valid_proposal'] and historical_duplicate(family, result['formal_statement'])
    duplicate = bool(accepted_matches) or historical
    result['duplicate_existing'] = duplicate
    result['repeated_attempt'] = bool(matches)
    advancement = result['accepted'] and not duplicate and result['verdict']['nontrivial']
    # A successful proof upgrading earlier sample support counts as an advance.
    revision = bool(prior and prior['family'] == family and prior['status'] in ('refuted', 'unresolved')
                    and prior['semantic_key'] != key and advancement)
    assumption_repair = False
    if revision and family == 'polynomial':
        old, new = prior['formal_statement'], result['formal_statement']
        assumption_repair = (old['polynomial'] == new['polynomial'] and old['variables'] == new['variables']
                             and len(new['constraints']) > len(old['constraints'])
                             and all(c in new['constraints'] for c in old['constraints']))
    event = {'id': round_id, 'family': family, 'semantic_key': key,
             'formal_statement': result['formal_statement'], 'proposal_claim_unverified': proposal.get('claim'),
             'status': result['verdict']['status'], 'novelty': result['verdict']['novelty'],
             'reason': result['verdict']['reason'], 'accepted': result['accepted'],
             'duplicate_existing': duplicate, 'repeated_attempt': bool(matches),
             'ledger_advancing': bool(advancement), 'successful_revision': revision,
             'assumption_repair': assumption_repair,
             'parent_id': proposal.get('parent_id'), 'parent_valid': not proposal.get('parent_id') or prior is not None,
             'unsupported_overclaim': result['unsupported_overclaim'],
             'failure_kind': result['failure_kind'], 'previous_hash': previous[-1]['hash'] if previous else None}
    # Model-supplied parent is only a trace link, never a proof premise.
    event['hash'] = digest(event)
    return event
