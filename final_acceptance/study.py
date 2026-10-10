"""Paired application acceptance. Truth lives only in the synthetic evaluator."""
import argparse
from copy import deepcopy
from fractions import Fraction as F
import hashlib
import json
import math
from pathlib import Path
import platform
import random
import subprocess
import time

import numpy as np
import scipy
from scipy.optimize import least_squares

from v3.certified_agent.decoder import solve
from v3b.assumption_agent.contracts import check_observation, deliver, preview, ISSUERS
from v3b.assumption_agent.policy import choose, profile, quality
from v3b.assumption_agent.certificates import zeta
from v3b.assumption_agent.verifier import root, verify_recovery

ROOT = Path(__file__).resolve().parents[1]
HOME = Path(__file__).resolve().parent
VALID = {'spread', 'clustered', 'collinear', 'sparse', 'noisy', 'uncertain-anchors'}
METHODS = ('wls', 'cauchy', 'certified')


def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))


def write(p, obj):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(obj, f, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        f.write('\n')


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def verify_hashes(mapping):
    bad = [p for p, h in mapping.items() if not (ROOT/p).is_file() or sha(ROOT/p) != h]
    if bad:
        raise ValueError('Changed frozen files: ' + repr(bad[:8]))
    return len(mapping)


def git(*args):
    return subprocess.check_output(['git', '-c', 'safe.directory=' + ROOT.as_posix(), *args], cwd=ROOT)


def freeze_previous():
    paths = git('ls-files', '-z').decode().split('\0')
    paths = [p for p in paths if p and not p.startswith('final_acceptance/')]
    snapshot = {'baseline_commit': git('rev-parse', 'HEAD').decode().strip(),
                'count': len(paths), 'files': {p: sha(ROOT/p) for p in paths}}
    write(HOME/'PREVIOUS_FREEZE.json', snapshot)
    return snapshot


def source_hashes():
    paths = [p for p in HOME.rglob('*') if p.is_file() and 'runs' not in p.parts
             and '__pycache__' not in p.parts and p.suffix in ('.py', '.json', '.md')]
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(paths)}


def rational(v):
    return str(F(format(float(v), '.9f')))


def episode(scenario, index, cfg, seed):
    rng = random.Random(seed + cfg['scenarios'].index(scenario)*10000 + index)
    n = 4 if scenario == 'collinear' else 3 if scenario == 'sparse' else 6
    target = [rational(rng.uniform(-1.5, 1.5)) for _ in range(2)]
    if scenario == 'collinear':
        target[1] = rational(rng.choice([-1, 1])*rng.uniform(0.8, 1.5))
    if scenario == 'target-outside-domain':
        target[0] = '16/5'
    nominal = []
    for i in range(n):
        if scenario == 'collinear':
            nominal.append([rational((-10, -6, 6, 10)[i] + rng.uniform(-0.3, 0.3)), '0'])
            continue
        theta = rng.uniform(-0.2, 0.2) if scenario == 'clustered' else 2*math.pi*i/n + rng.uniform(-0.25, 0.25)
        radius = rng.uniform(7, 12)
        nominal.append([rational(radius*math.cos(theta)), rational(radius*math.sin(theta))])
    for _ in range(cfg['candidate_count']):
        theta, radius = rng.uniform(0, 2*math.pi), rng.uniform(7, 12)
        nominal.append([rational(radius*math.cos(theta)), rational(radius*math.sin(theta))])
    total = len(nominal)
    delta = F('2/5') if scenario == 'uncertain-anchors' else F('1/50')
    noise_cap = F('3/10') if scenario == 'noisy' else F('1/125')
    actual_cap = F('3/10') if scenario == 'understated-noise' else noise_cap
    # Identity-fixed corruption: on alternate episodes a future reporter is bad.
    bad = [rng.randrange(n) if index % 2 else n + rng.randrange(cfg['candidate_count'])]
    if scenario == 'excess-corruption':
        bad = rng.sample(list(range(n)), 2)
    all_records = {}
    for i, anchor in enumerate(nominal):
        offset = [rational(float(delta)*rng.uniform(-1/3, 1/3)) for _ in range(2)]
        if scenario == 'understated-anchor-error':
            offset = ['3/5', '0']
        actual = [str(F(a)+F(e)) for a, e in zip(anchor, offset)]
        factor = (F(1), F('3/2'), F(2))[i % 3]
        noise = rational(float(actual_cap*factor)*rng.uniform(-1, 1))
        dist = math.sqrt(sum(float(F(a)-F(x))**2 for a, x in zip(actual, target)))
        outlier = rational(rng.uniform(1.5, 5)) if i in bad else '0'
        value = str(F(format(dist, '.12f')) + F(noise) + F(outlier))
        all_records[str(i)] = dict(nominal=anchor, actual=actual, value=value,
                                  weight=str(1/factor**2), radius=str(delta), bad=i in bad)
    # A single E bounds all potential clean observations, hence every acquired subset.
    E = str(F(math.ceil(math.sqrt(total)*float(noise_cap)*10**6)+1, 10**6))
    offers = [dict(id=str(i), kind='new-range', cost='1',
                   update=dict(anchor=nominal[i], weight=all_records[str(i)]['weight'], radius=str(delta)))
              for i in range(n, total)]
    rng.shuffle(offers)
    public = dict(episode_id=f'e{cfg["scenarios"].index(scenario):02d}-{index:03d}',
                  anchors=nominal[:n], weights=[all_records[str(i)]['weight'] for i in range(n)],
                  measurements=[all_records[str(i)]['value'] for i in range(n)],
                  radii=[str(delta)]*n, domain=cfg['domain'], q_max=1, epsilon_max=E,
                  error_tolerance=cfg['error_tolerance'], budget=str(cfg['max_acquisitions']),
                  offers=offers, receipts=[])
    private = dict(truth=target, records=all_records, initial_ids=[str(i) for i in range(n)],
                   scenario=scenario, expected_valid=scenario in VALID)
    check_observation(public)
    return public, private


def select(public, policy, seed):
    """Observation-only policy. Exact gain over finite offers; no future replies."""
    check_observation(public)
    offers = public['offers']
    if policy == 'random':
        return random.Random(seed).choice(offers)['id'], []
    if policy != 'active':
        raise ValueError('unknown policy')
    scores = []
    for offer in offers:
        f = profile(preview(public, offer))
        scores.append(dict(offer_id=offer['id'], quality=str(quality(f, public['error_tolerance'])),
                           bound=f['worst_error_bound']))
    # Unit costs and common current quality: maximizing post-quality maximizes gain.
    selected = max(scores, key=lambda s: F(s['quality']))['offer_id']
    return selected, scores


def acquire(public, private, offer_id):
    offer = next(o for o in public['offers'] if o['id'] == offer_id)
    receipt = dict(issuer=ISSUERS['new-range'], offer_id=offer_id,
                   episode_id=public['episode_id'], update=deepcopy(offer['update']),
                   measurement=private['records'][offer_id]['value'])
    return deliver(public, offer, receipt)


def candidate_input(public):
    out = {k: deepcopy(public[k]) for k in ('anchors', 'weights', 'measurements', 'domain')}
    out.update(q_budget=public['q_max'], epsilon=str(F(public['epsilon_max'])+zeta(public, public['q_max'])),
               error_tolerance=public['error_tolerance'])
    return out


def wls(public, cfg):
    """New comparator wrapper only; no v1 solver or historical benchmark rerun."""
    p = np.array([[float(F(v)) for v in a] for a in public['anchors']])
    y = np.array([float(F(v)) for v in public['measurements']])
    w = np.sqrt([float(F(v)) for v in public['weights']])
    d = list(map(lambda v: float(F(v)), public['domain']))
    lo, hi = np.array([d[0], d[2]]), np.array([d[1], d[3]])
    residual = lambda x: w*(np.linalg.norm(x-p, axis=1)-y)
    jac = lambda x: w[:, None]*(x-p)/np.maximum(np.linalg.norm(x-p, axis=1)[:, None], 1e-12)
    candidates, failures = [], []
    for start in cfg['solver_starts']:
        try:
            result = least_squares(residual, [float(F(v)) for v in start], jac=jac,
                                   bounds=(lo, hi), max_nfev=cfg['solver_max_nfev'])
            if not result.success:
                failures.append(str(result.message))
            if np.all(np.isfinite(result.x)):
                candidates.append(result.x)
        except (ValueError, FloatingPointError) as exc:
            failures.append(str(exc))
    if not candidates:
        candidates = [(lo+hi)/2]
        failures.append('centre fallback: no optimizer candidate')
    x = min(candidates, key=lambda a: float(np.sum(residual(a)**2)))
    return dict(action='recover', position=[format(v, '.12f') for v in x], optimizer_failures=failures,
                certification='none')


def estimate(public, method, cfg):
    check_observation(public)
    if method == 'wls':
        return wls(public, cfg)
    if method == 'cauchy':
        result = solve(candidate_input(public), cfg, trim=False)
        return dict(action='recover', position=result['position'], optimizer_failures=result['optimizer_failures'],
                    certification='none')
    if method != 'certified':
        raise ValueError('unknown estimator')
    passive = deepcopy(public)
    passive.update(offers=[], budget='0')
    decision = choose(passive, 'measurement-only', cfg, 0)
    if decision['action'] == 'recover':
        verify_recovery(public, decision)
    return decision


def evaluate(public, private, decision):
    """Independent private premise checks, including identity-fixed future outliers."""
    selected = private['initial_ids'] + [r['offer_id'] for r in public['receipts']]
    x = list(map(F, private['truth']))
    domain = list(map(F, public['domain']))
    violations = []
    if not (domain[0] <= x[0] <= domain[1] and domain[2] <= x[1] <= domain[3]):
        violations.append('target-outside-domain')
    # Global contract covers all potential observations, not just current selections.
    if sum(r['bad'] for r in private['records'].values()) > public['q_max']:
        violations.append('global-corruption-budget')
    noise2 = F(0)
    for j, identity in enumerate(selected):
        r = private['records'][identity]
        if public['measurements'][j] != r['value'] or public['anchors'][j] != r['nominal']:
            raise ValueError('wrong reporter reply binding')
        if sum((F(a)-F(b))**2 for a, b in zip(r['actual'], public['anchors'][j])) > F(public['radii'][j])**2:
            violations.append('anchor-ball:' + identity)
        if not r['bad']:
            low, high = root(sum((F(a)-b)**2 for a, b in zip(r['actual'], x)))
            noise2 += F(public['weights'][j])*max(abs(low-F(r['value'])), abs(high-F(r['value'])))**2
    if noise2 > F(public['epsilon_max'])**2:
        violations.append('clean-noise-budget')
    output = decision['action'] == 'recover'
    error2 = sum((F(a)-b)**2 for a, b in zip(decision['position'], x)) if output else None
    bound = decision.get('error_bound')
    return dict(contract_valid=not violations, contract_violations=violations,
                output=output, error=math.sqrt(float(error2)) if output else None,
                wrong=bool(output and error2 > F(public['error_tolerance'])**2),
                severe=bool(output and error2 > 4),
                bound_violation=bool(output and bound is not None and error2 > F(bound)**2),
                cost=len(public['receipts']))


def execute_case(public, private, cfg, case_index):
    tracks = {}
    common = None
    for policy in ('random', 'active'):
        current = deepcopy(public)
        checkpoints = []
        for k in range(cfg['max_acquisitions']+1):
            if k == 0 and common is not None:
                checkpoint = deepcopy(common)
            else:
                decisions, evaluations, timing = {}, {}, {}
                for method in METHODS:
                    start = time.perf_counter()
                    decisions[method] = estimate(current, method, cfg)
                    timing[method] = time.perf_counter()-start
                    evaluations[method] = evaluate(current, private, decisions[method])
                checkpoint = dict(k=k, observation=deepcopy(current), decisions=decisions,
                                  evaluations=evaluations, estimator_seconds=timing)
                if k == 0:
                    common = deepcopy(checkpoint)
            checkpoints.append(checkpoint)
            if k < cfg['max_acquisitions']:
                start = time.perf_counter()
                chosen, scores = select(current, policy, cfg['random_policy_seed']+case_index*10+k)
                checkpoint['selection'] = dict(offer_id=chosen, scores=scores, seconds=time.perf_counter()-start)
                current = acquire(current, private, chosen)
        tracks[policy] = checkpoints
    return dict(public=public, private=private, tracks=tracks)


def run(output, development=False):
    output = Path(output).resolve()
    if output.exists() or not output.is_relative_to(HOME/'runs'):
        raise ValueError('Use a fresh directory under final_acceptance/runs')
    previous = read(HOME/'PREVIOUS_FREEZE.json')
    verify_hashes(previous['files'])
    cfg = read(HOME/'config.json')
    count = 1 if development else cfg['episodes_per_scenario']
    seed = cfg['development_seed'] if development else cfg['final_seed']
    sources = source_hashes()
    output.mkdir(parents=True)
    manifest = dict(schema='original-question-acceptance-v1', development=development, seed=seed,
                    config=cfg, count_per_scenario=count, sources=sources,
                    previous_freeze_sha256=sha(HOME/'PREVIOUS_FREEZE.json'),
                    python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__)
    write(output/'manifest.json', manifest)
    start = time.perf_counter()
    for sidx, scenario in enumerate(cfg['scenarios']):
        for index in range(count):
            public, private = episode(scenario, index, cfg, seed)
            # Commit response table and public input before policy execution.
            write(output/'inputs'/f'{public["episode_id"]}.json', dict(public=public, private=private))
            case = execute_case(public, private, cfg, sidx*count+index)
            write(output/'cases'/f'{public["episode_id"]}.json', case)
        print(json.dumps(dict(scenario=scenario, episodes=count, elapsed_seconds=round(time.perf_counter()-start, 2))), flush=True)
    verify_hashes(previous['files'])
    verify_hashes(sources)
    write(output/'completion.json', dict(cases=count*len(cfg['scenarios']), seconds=time.perf_counter()-start,
                                          historical_files_unchanged=len(previous['files'])))
    write(output/'output_hashes.json', {p.relative_to(output).as_posix(): sha(p)
                                       for p in sorted(output.rglob('*')) if p.is_file()})


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['freeze', 'run'])
    parser.add_argument('--output')
    parser.add_argument('--development', action='store_true')
    args = parser.parse_args()
    if args.command == 'freeze':
        print(freeze_previous()['count'])
    else:
        run(args.output, args.development)
