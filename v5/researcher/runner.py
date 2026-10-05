"""Frozen, append-only 12-round research harness and deterministic replay."""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from .io import ROOT, PACKAGE, read, write_new, file_hash, digest, sources, check_hashes, canonical
from .schema import output_schema
from .prompt import initial_state, research_state, build
from .gate import ledger_event
from .codex_client import preflight, propose as codex_propose, verify_receipt

CONFIG = {'rounds': 12, 'math_requests_per_round': 1, 'operation_limit': 50000,
          'math_timeout_seconds': 60, 'proposal_timeout_seconds': 180}


def frozen_check(manifest):
    check_hashes(read(ROOT/'v5/PREVIOUS_FREEZE.json')['files'])
    check_hashes(manifest['source_hashes'])
    if sources() != manifest['source_hashes']:
        raise RuntimeError('scientific source set changed after run freeze')


def failed_record(reason, kind='provider-failure'):
    return {'valid_proposal': False, 'formal_statement': None, 'semantic_key': None, 'evidence': None,
            'accepted': False, 'failure_kind': kind, 'verdict': {'status':'unresolved',
            'novelty':'novelty-uncertain', 'nontrivial':False, 'scope':'no conclusion authorized', 'reason':reason},
            'operation_units':0, 'tool_seconds':0.0, 'unsupported_overclaim':False}


def math_worker(proposal, config):
    start=time.perf_counter()
    try:
        p = subprocess.run([sys.executable, '-m', 'v5.researcher.worker'],
                           input=canonical({'proposal':proposal, 'operation_limit':config['operation_limit']}),
                           capture_output=True, text=True, encoding='utf-8', cwd=ROOT,
                           timeout=config['math_timeout_seconds'])
        if p.returncode:
            r=failed_record('math worker exited: ' + p.stderr[-2000:], 'worker-failure')
            r['tool_seconds']=time.perf_counter()-start
            return r
        return json.loads(p.stdout)
    except subprocess.TimeoutExpired:
        r=failed_record('mathematical worker exceeded wall-time budget', 'worker-timeout')
        r['tool_seconds']=time.perf_counter()-start
        return r


def summary(events, results, runtimes, policy):
    n = len(events)
    total = lambda name: sum(bool(e.get(name)) for e in events)
    accepted = total('accepted')
    kinds = {}
    for r in results:
        k = r['failure_kind'] or r['verdict']['status']
        kinds[k] = kinds.get(k, 0)+1
    contexts = {e['formal_statement']['problem'] for e in events if e['family'] == 'finite_cost' and e['accepted']}
    usage = [u for r in runtimes for u in r.get('usage', []) if u is not None]
    tokens = {k:sum(u.get(k,0) for u in usage) for k in ('input_tokens','cached_input_tokens','output_tokens')}
    return {'policy':policy, 'rounds':n, 'accepted':accepted, 'rejected_or_unresolved':n-accepted,
            'acceptance_rate':accepted/n if n else None, 'productive_steps_operational':total('ledger_advancing'),
            'duplicate_existing':total('duplicate_existing'), 'duplicate_rate':total('duplicate_existing')/n if n else None,
            'invalid_proposals':sum(not r['valid_proposal'] and r['failure_kind']=='invalid-proposal' for r in results),
            'verifier_rejections':sum(r['failure_kind']=='verification-rejected' for r in results),
            'counterexamples':sum(e['status']=='refuted' for e in events),
            'new_counterexamples':sum(e['status']=='refuted' and e['ledger_advancing'] for e in events),
            'successful_conjecture_revisions':total('successful_revision'),
            'successful_assumption_repairs':total('assumption_repair'),
            'unsupported_overclaims':total('unsupported_overclaim'), 'outcomes':kinds,
            'shared_finite_minimax_calls':sum(e['family']=='finite_cost' and e['accepted'] for e in events),
            'cross_problem_structure_reuse_observed': contexts == {'range','pr'},
            'operation_units':sum(r['operation_units'] for r in results),
            'tool_seconds':sum(r['tool_seconds'] for r in results),
            'proposal_seconds':sum(r.get('wall_seconds',0) for r in runtimes),
            'token_usage':tokens if usage else (tokens if policy=='scripted' else None),
            'usage_receipts':len(usage), 'dollar_cost':0 if policy=='scripted' else None,
            'limits':'Progress is a canonicalized formal-ledger proxy, not an originality, importance, or general autonomous-research score.'}


def run(path, policy):
    path = Path(path).resolve()
    if path.exists():
        raise ValueError('run destination already exists; immutable runs require a fresh path')
    if not path.is_relative_to(ROOT/'v5/runs'):
        raise ValueError('run must be inside v5/runs')
    initial = initial_state(); source_hashes = sources()
    check_hashes(read(ROOT/'v5/PREVIOUS_FREEZE.json')['files'])
    path.mkdir(parents=True)
    manifest = {'schema':'phase5-run-v1', 'policy':policy, 'config':CONFIG, 'source_hashes':source_hashes,
                'initial_state_hash':digest(initial), 'prior_files':read(ROOT/'v5/PREVIOUS_FREEZE.json')['count']}
    write_new(path/'manifest.json', manifest)
    write_new(path/'initial_state.json', initial)
    write_new(path/'proposal_schema.json', output_schema())
    auth = preflight() if policy=='codex' else {'provider':'scripted', 'authenticated':False, 'requires_auth':False}
    write_new(path/'preflight.json', auth)
    if policy=='codex' and not auth.get('authenticated'):
        write_new(path/'blocked.json', {'reason':'Codex CLI authentication unavailable', 'rounds_executed':0,
                   'provider_calls':0, 'not_a_codex_research_run':True, 'next_action':'Run codex login, then use a NEW run directory.'})
        print('BLOCKED: no authenticated Codex CLI; zero provider calls', flush=True)
        return
    events, results, runtimes = [], [], []
    for i in range(1, CONFIG['rounds']+1):
        frozen_check(manifest)
        rid = f'r{i:02d}'; iteration = path/'iterations'/rid
        iteration.mkdir(parents=True)
        state = research_state(initial, events, results, CONFIG['rounds']-i+1)
        write_new(iteration/'input_state.json', state)
        prompt = build(state)
        (iteration/'prompt.txt').write_text(prompt, encoding='utf-8')
        if policy=='scripted':
            from .baseline import propose
            start = time.perf_counter(); proposal = propose(i, state)
            runtime = {'provider':'scripted', 'wall_seconds':time.perf_counter()-start, 'usage':[], 'dollar_cost':0}
        else:
            # Every existing run artifact is protected against proposer tampering.
            protected = {p.relative_to(ROOT).as_posix():file_hash(p) for p in path.rglob('*') if p.is_file()}
            proposal, runtime = codex_propose(prompt, iteration, path/'proposal_schema.json', CONFIG['proposal_timeout_seconds'])
            check_hashes(protected)
            verify_receipt(iteration, proposal, runtime)
        frozen_check(manifest)
        write_new(iteration/'proposal.json', proposal)
        write_new(iteration/'runtime.json', runtime)
        result = math_worker(proposal, CONFIG) if proposal is not None else failed_record(runtime['error'])
        frozen_check(manifest)
        event = ledger_event(rid, proposal or {}, result, events)
        write_new(iteration/'verification.json', result)
        write_new(iteration/'ledger_event.json', event)
        events.append(event); results.append(result); runtimes.append(runtime)
        print(f'{rid} {event["family"]}: {event["status"]}; advance={event["ledger_advancing"]}; failure={event["failure_kind"]}', flush=True)
    write_new(path/'ledger.json', events)
    write_new(path/'metrics.json', summary(events, results, runtimes, policy))
    frozen_check(manifest)
    hashes = {p.relative_to(path).as_posix():file_hash(p) for p in sorted(path.rglob('*')) if p.is_file()}
    write_new(path/'output_hashes.json', hashes)


def replay(path):
    path = Path(path).resolve(); manifest = read(path/'manifest.json'); frozen_check(manifest)
    if (path/'blocked.json').exists():
        raise ValueError('zero-round auth preflight is not a replayable researcher run')
    for name, h in read(path/'output_hashes.json').items():
        if file_hash(path/name) != h: raise ValueError('run artifact tampered: '+name)
    initial = read(path/'initial_state.json')
    if digest(initial) != manifest['initial_state_hash']: raise ValueError('initial state binding')
    events, results, runtimes = [], [], []
    for i in range(1, manifest['config']['rounds']+1):
        rid=f'r{i:02d}'; p=path/'iterations'/rid
        state = research_state(initial, events, results, manifest['config']['rounds']-i+1)
        if read(p/'input_state.json') != state or (p/'prompt.txt').read_text(encoding='utf-8') != build(state):
            raise ValueError('state-to-proposal input chain mismatch: '+rid)
        proposal=read(p/'proposal.json'); saved=read(p/'verification.json'); runtime=read(p/'runtime.json')
        if manifest['policy']=='codex':
            verify_receipt(p,proposal,runtime)
        if proposal is None:
            if runtime.get('provider') != 'codex-cli' or not runtime.get('error'):
                raise ValueError('unaccounted missing proposal')
            fresh=failed_record(runtime['error'])
        elif saved['failure_kind'] in ('worker-timeout','worker-failure'):
            # Runtime failure timing is not deterministic. Preserve that failure;
            # never turn a later successful replay into historical research credit.
            fresh=failed_record(saved['verdict']['reason'],saved['failure_kind'])
        else:
            fresh=math_worker(proposal, manifest['config'])
        fresh['tool_seconds']=saved['tool_seconds']
        event=ledger_event(rid, proposal or {}, fresh, events)
        if fresh!=saved or event!=read(p/'ledger_event.json'):
            raise ValueError('deterministic disposition mismatch: '+rid)
        events.append(event); results.append(fresh); runtimes.append(runtime)
    if events!=read(path/'ledger.json') or summary(events,results,runtimes,manifest['policy'])!=read(path/'metrics.json'):
        raise ValueError('aggregate replay mismatch')
    return {'passed':True, 'rounds':len(events), 'history_files_unchanged':manifest['prior_files'],
            'scope':'same recorded proposals replayed through frozen tools and verifier; NOT fresh model regeneration'}


def compare(baseline, codex):
    a,b=Path(baseline),Path(codex)
    ma,mb=read(a/'manifest.json'),read(b/'manifest.json')
    if ma['policy']!='scripted' or mb['policy']!='codex': raise ValueError('comparison policy labels')
    for key in ('initial_state_hash','source_hashes','config'):
        if ma[key]!=mb[key]: raise ValueError('unmatched starting state, sources or tool budget')
    replay(a)
    if (b/'blocked.json').exists():
        return {'comparison_complete':False, 'reason':'Codex has zero research rounds; baseline alone cannot measure agent advantage',
                'scripted':read(a/'metrics.json'), 'codex':None}
    replay(b)
    return {'comparison_complete':True, 'scripted':read(a/'metrics.json'), 'codex':read(b/'metrics.json'),
            'limitations':['one trajectory per policy, no statistical superiority claim',
            'matched mathematical budget; Codex inference is extra measured cost',
            'human-authored tool grammar and frontier; no universal autonomous discovery claim',
            'limited semantic deduplication; progress proxy still needs scientific review']}


def main():
    parser=argparse.ArgumentParser()
    sub=parser.add_subparsers(dest='mode',required=True)
    for mode in ('scripted','codex','replay'):
        p=sub.add_parser(mode);p.add_argument('path')
    p=sub.add_parser('compare');p.add_argument('baseline');p.add_argument('codex');p.add_argument('--output',required=True)
    args=parser.parse_args()
    if args.mode=='replay': print(json.dumps(replay(args.path),indent=2))
    elif args.mode=='compare':
        result=compare(args.baseline,args.codex);write_new(args.output,result);print(json.dumps(result,indent=2))
    else: run(args.path,args.mode)


if __name__=='__main__': main()
