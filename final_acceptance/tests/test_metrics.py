from final_acceptance.report import summary, paired_intervals
from final_acceptance import study as s


def test_abstention_is_not_zero_error_or_correct_output():
    r = dict(output=False, error=None, wrong=False, severe=False, bound_violation=False,
             contract_valid=True, cost=0, correct_output=False, optimizer_failure_count=0,
             estimator_seconds=0)
    result = summary([r, r])
    assert result['coverage'] == 0 and result['correct_output_fraction'] == 0
    assert result['selective_risk'] is None and result['output_error_p90'] is None


def test_pairing_keeps_matched_policies_together():
    cfg = s.read(s.HOME/'config.json')
    rows = [dict(episode_id=scenario+str(i), scenario=scenario, k=k, method='certified',
                 policy=policy, correct_output=bool(i % 2))
            for scenario in sorted(s.VALID) for i in range(3)
            for k in range(4) for policy in ('active', 'random')]
    for result in paired_intervals(rows, cfg):
        assert result['pairs'] == 18
        assert result['active_minus_random'] == 0 and result['bootstrap95'] == [0, 0]
