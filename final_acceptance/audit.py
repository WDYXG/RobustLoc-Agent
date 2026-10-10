"""Read-only replay of pair binding, contracts, actions and existing exact gates."""
import argparse
from copy import deepcopy
from pathlib import Path
from v3b.assumption_agent.verifier import verify_frontier, verify_recovery
from . import study as s


def audit(folder, output, replay_solvers=False):
    folder = Path(folder).resolve()
    m = s.read(folder/'manifest.json')
    previous = s.read(s.HOME/'PREVIOUS_FREEZE.json')
    checked = s.verify_hashes(previous['files'])
    s.verify_hashes(m['sources'])
    for name, digest in s.read(folder/'output_hashes.json').items():
        if s.sha(folder/name) != digest:
            raise ValueError('changed result ' + name)
    cfg = m['config']
    expected = m['count_per_scenario']*len(cfg['scenarios'])
    files = sorted((folder/'cases').glob('*.json'))
    assert len(files) == expected
    counts = dict(cases=expected, checkpoints=0, verified_recoveries=0, valid_bound_violations=0,
                  invalid_contract_checkpoints=0, solver_replays=0)
    for case_index, path in enumerate(files):
        case = s.read(path)
        original = s.read(folder/'inputs'/path.name)
        assert original == {k: case[k] for k in ('public', 'private')}
        for policy, trajectory in case['tracks'].items():
            assert len(trajectory) == cfg['max_acquisitions']+1
            current = deepcopy(case['public'])
            for k, checkpoint in enumerate(trajectory):
                assert checkpoint['k'] == k and checkpoint['observation'] == current
                assert len(current['receipts']) == k and int(current['budget']) == cfg['max_acquisitions']-k
                verify_frontier(current, checkpoint['decisions']['certified']['frontier'])
                counts['checkpoints'] += 1
                for method, decision in checkpoint['decisions'].items():
                    evaluated = s.evaluate(current, case['private'], decision)
                    assert evaluated == checkpoint['evaluations'][method]
                    if method == 'certified':
                        counts['invalid_contract_checkpoints'] += int(not evaluated['contract_valid'])
                        counts['valid_bound_violations'] += int(evaluated['contract_valid'] and evaluated['bound_violation'])
                        if evaluated['output']:
                            verify_recovery(current, decision)
                            counts['verified_recoveries'] += 1
                    if replay_solvers:
                        assert s.estimate(current, method, cfg) == decision
                        counts['solver_replays'] += 1
                if k < cfg['max_acquisitions']:
                    identity, scores = s.select(current, policy, cfg['random_policy_seed']+case_index*10+k)
                    assert checkpoint['selection']['offer_id'] == identity
                    assert checkpoint['selection']['scores'] == scores
                    current = s.acquire(current, case['private'], identity)
    assert counts['valid_bound_violations'] == 0
    result = dict(passed=True, historical_files_unchanged=checked, counts=counts,
                  solver_replay=replay_solvers, note='Conditional synthetic acceptance; no field or teacher sign-off.')
    s.write(output, result)
    print(result)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('run')
    p.add_argument('--output', required=True)
    p.add_argument('--replay-solvers', action='store_true')
    a = p.parse_args()
    audit(a.run, a.output, a.replay_solvers)
