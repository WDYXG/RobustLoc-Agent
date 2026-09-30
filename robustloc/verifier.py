"""Independent subprocess decision: proposer cannot set acceptance or split policy."""
import argparse
import numpy as np
from .storage import read, save

def verify(candidate, incumbent, baseline, policy):
    c, b = candidate['overall'], incumbent['overall']
    gain = (b['cep90']-c['cep90']) / max(b['cep90'], 1e-12)
    diff = c['failure_rate']-b['failure_rate']
    regressions = [s for s in c_by(candidate) if candidate['by_scenario'][s]['cep90'] > max(.25, incumbent['by_scenario'][s]['cep90'] * policy['maximum_scenario_cep90_ratio'])]
    valid = c['nonfinite_cases'] == 0 and c['optimization_failures'] <= b['optimization_failures']
    good = valid and gain >= policy['minimum_relative_cep90_gain'] and diff <= policy['maximum_failure_rate_increase'] and not regressions
    bad = not valid or gain < -policy['minimum_relative_cep90_gain'] or diff > policy['maximum_failure_rate_increase'] or bool(regressions)
    verdict = 'supported' if good else 'rejected' if bad else 'inconclusive'
    pairs = list(zip(candidate['rows'], incumbent['rows']))
    assert all(a['seed']==b['seed'] and a['scenario']==b['scenario'] for a,b in pairs)
    failures = sorted([dict(scenario=a['scenario'], seed=a['seed'], candidate_error=a['error'], incumbent_error=b['error'], excess=a['error']-b['error']) for a,b in pairs], key=lambda r:r['excess'], reverse=True)[:10]
    return dict(verdict=verdict, decision='accept candidate' if good else 'reject candidate' if bad else 'retain as research branch',
                relative_cep90_gain=gain, failure_rate_difference=diff, scenario_regressions=regressions,
                comparison_to_baseline=dict(cep90_difference=c['cep90']-baseline['overall']['cep90'], failure_rate_difference=c['failure_rate']-baseline['overall']['failure_rate']),
                failure_cases=failures, evidence_class='empirical evidence; repeated validation selection, no mathematical proof')

def c_by(result):
    return result['by_scenario']

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('request'); parser.add_argument('output')
    args = parser.parse_args()
    request = read(args.request)
    save(args.output, verify(read(request['candidate']), read(request['incumbent']), read(request['baseline']), request['policy']))
