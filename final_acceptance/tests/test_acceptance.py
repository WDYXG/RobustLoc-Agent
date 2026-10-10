from copy import deepcopy
from fractions import Fraction as F
import pytest
from final_acceptance import study as s


@pytest.fixture
def cfg():
    return s.read(s.HOME/'config.json')


def test_valid_contracts_hold_after_every_possible_offer(cfg):
    for scenario in sorted(s.VALID):
        obs, secret = s.episode(scenario, 0, cfg, cfg['development_seed'])
        for offer in list(obs['offers'])[:3]:
            obs = s.acquire(obs, secret, offer['id'])
            assert s.evaluate(obs, secret, {'action': 'abstain'})['contract_valid']


def test_future_corruption_is_global_and_identity_bound(cfg):
    obs, secret = s.episode('spread', 0, cfg, cfg['development_seed'])
    assert not any(secret['records'][i]['bad'] for i in secret['initial_ids'])
    bad = next(i for i, r in secret['records'].items() if r['bad'])
    first = next(o['id'] for o in obs['offers'] if o['id'] != bad)
    direct = s.acquire(obs, secret, bad)
    later = s.acquire(s.acquire(obs, secret, first), secret, bad)
    assert direct['measurements'][-1] == later['measurements'][-1] == secret['records'][bad]['value']


def test_private_fields_and_missing_q_cannot_authorize(cfg):
    obs, _ = s.episode('spread', 0, cfg, cfg['development_seed'])
    for change in ({'truth': ['0', '0']}, {'actual_anchors': []}):
        with pytest.raises(ValueError):
            s.estimate(dict(obs, **change), 'certified', cfg)
    del obs['q_max']
    obs['estimated_corruption'] = 0
    with pytest.raises((KeyError, ValueError)):
        s.estimate(obs, 'certified', cfg)


def test_actual_contract_violations_are_separate(cfg):
    for scenario in ('excess-corruption', 'understated-anchor-error', 'target-outside-domain'):
        obs, secret = s.episode(scenario, 0, cfg, cfg['development_seed'])
        verdict = s.evaluate(obs, secret, {'action': 'abstain'})
        assert not verdict['contract_valid'] and verdict['contract_violations']


def test_active_geometry_ignores_reply_values(cfg):
    obs, _ = s.episode('clustered', 0, cfg, cfg['development_seed'])
    other = deepcopy(obs)
    other['measurements'] = ['999']*len(obs['anchors'])
    assert s.select(obs, 'active', 0) == s.select(other, 'active', 0)


def test_budget_and_receipt_tampering(cfg):
    obs, secret = s.episode('spread', 0, cfg, cfg['development_seed'])
    for k in range(3):
        obs = s.acquire(obs, secret, obs['offers'][0]['id'])
        assert F(obs['budget']) == 2-k
        assert len(obs['receipts']) == k+1
    obs['measurements'][-1] = '0'
    with pytest.raises(ValueError, match='binding'):
        s.evaluate(obs, secret, {'action': 'abstain'})


def test_gate_evidence_cannot_be_self_authorized(cfg):
    obs, _ = s.episode('spread', 1, cfg, cfg['development_seed'])
    decision = s.estimate(obs, 'certified', cfg)
    assert decision['action'] == 'recover'
    altered = deepcopy(decision)
    altered['error_bound'] = '0'
    with pytest.raises(ValueError):
        s.verify_recovery(obs, altered)
