"""Observation-only application boundary. Sigmas are NOT hard error bounds."""
import argparse
import json
import math
from copy import deepcopy
from fractions import Fraction as F
from pathlib import Path
import numpy as np
from robustloc.simulator import Observation
from robustloc.candidate import solve
from v3b.assumption_agent.certificates import frontier
from v3b.assumption_agent.verifier import residual, verify_recovery

INCUMBENT = dict(loss='cauchy', threshold=1., uncertainty=True,
                 confidence=False, multistart=False, adaptive=True)


def observations(payload):
    allowed = {'reports', 'units', 'contract', 'information_available'}
    if set(payload) - allowed:
        raise ValueError('Unknown input fields (truth and labels are forbidden)')
    if payload.get('units') != 'metres':
        raise ValueError('Use a common local Cartesian coordinate system in metres')
    reports = payload['reports']
    if len({r['id'] for r in reports}) != len(reports):
        raise ValueError('Repeated packets must be aggregated by reporter id')
    positions, distances, ps, ds, confidence = [], [], [], [], []
    skipped = []
    for r in reports:
        if set(r) - {'id', 'position', 'position_sigma', 'distance', 'distance_sigma',
                     'rssi_dbm', 'calibration', 'confidence'}:
            raise ValueError('Unknown reporter fields')
        if 'distance' in r and 'rssi_dbm' in r:
            raise ValueError('Choose distance or RSSI, not both')
        if 'rssi_dbm' in r:
            s = r['rssi_dbm']
            if s is None or s == -200:
                skipped.append(r['id']); continue
            c = r['calibration']
            a, beta, sd = (float(c[k]) for k in ('a_at_1m_dbm', 'path_loss_exponent', 'sigma_db'))
            if not np.isfinite([s, a, beta, sd]).all() or beta <= 0 or sd <= 0:
                raise ValueError('Invalid externally supplied RSSI calibration')
            # Log-distance point inversion; lognormal errors remain biased in range space.
            d = 10. ** ((a-float(s))/(10*beta))
            sigma = max(.05, d*math.log(10)*sd/(10*beta))
        else:
            d, sigma = float(r['distance']), float(r['distance_sigma'])
        p, sigp, conf = r['position'], float(r['position_sigma']), float(r.get('confidence', 1))
        if (len(p) != 2 or not np.isfinite([*p, d, sigma, sigp, conf]).all()
                or d < 0 or sigma <= 0 or sigp < 0 or not 0 < conf <= 1):
            raise ValueError('Invalid observation or uncertainty')
        positions.append(p); distances.append(d); ps.append(sigp); ds.append(sigma); confidence.append(conf)
    if len(positions) < 3:
        raise ValueError('At least three observed, distinct reporters are required')
    return Observation(np.array(positions, float), np.array(distances), np.array(ps),
                       np.array(ds), np.array(confidence), np.ones(len(ps))), skipped


def rational(v):
    return str(F(str(float(v))))


def certify(obs, position, contract, max_subsets=2000):
    contract = deepcopy(contract)  # Response snapshots must not alias later caller mutations.
    required = {'q_max', 'epsilon_max', 'domain', 'radii', 'error_tolerance', 'provenance'}
    if set(contract) != required or not contract['provenance']:
        raise ValueError('A complete externally justified hard contract is required')
    q, n = contract['q_max'], len(obs.distances)
    if type(q) is not int or not 0 <= q < n or len(contract['radii']) != n:
        raise ValueError('Invalid corruption budget or hard radii')
    if F(contract['epsilon_max']) < 0 or F(contract['error_tolerance']) <= 0:
        raise ValueError('Invalid hard noise or tolerance')
    if sum(math.comb(n, max(0, n-2*k)) for k in range(q+1)) > max_subsets:
        return dict(status='not-certified', reason='exact-enumeration-budget-exceeded')
    public = dict(anchors=[[rational(v) for v in p] for p in obs.positions],
                  weights=['1']*n, measurements=[rational(v) for v in obs.distances],
                  **{k: contract[k] for k in required-{'provenance'}})
    f = frontier(public, include_grid=False, complete=False)
    answer = dict(status='not-certified', reason='sufficient-bound-unavailable', frontier=f)
    x = [rational(v) for v in position]
    if f['all_contracts_certified']:
        row = f['rows'][q]; rr = residual(public, x, q)
        decoder = None
        if rr is None or rr > F(public['epsilon_max'])+F(row['zeta_upper']):
            # Reuse the already audited bounded decoder, only after geometry pre-gate.
            from v3.certified_agent.decoder import solve as decode
            domain = list(map(F, public['domain']))
            cx, cy = (domain[0]+domain[1])/2, (domain[2]+domain[3])/2
            dx, dy = (domain[1]-domain[0])/4, (domain[3]-domain[2])/4
            starts = [[str(cx+a*dx), str(cy+b*dy)] for a,b in [(0,0),(-1,-1),(-1,1),(1,-1),(1,1)]]
            decoder_obs = {k:public[k] for k in ('anchors','weights','measurements','domain')}
            decoder_obs.update(q_budget=q, epsilon=str(F(public['epsilon_max'])+F(row['zeta_upper'])),
                               error_tolerance=public['error_tolerance'])
            decoder = decode(decoder_obs, dict(solver_starts=starts, solver_max_nfev=150))
            x = decoder['position']; rr = residual(public, x, q)
        if rr is not None and rr <= F(public['epsilon_max'])+F(row['zeta_upper']):
            bound = (F(public['epsilon_max'])+rr+F(row['zeta_upper']))/F(row['lower'])
            decision = dict(action='recover', position=x, frontier=f, error_bound=str(bound))
            verify_recovery(public, decision)
            answer = dict(status='conditionally-certified', reason='independent-verifier-accepted',
                          error_bound_metres=float(bound), decision=decision, observation=public,
                          bounded_decoder=decoder)
        else:
            answer['reason'] = 'estimate-outside-domain-or-residual-budget'
    answer['contract_provenance'] = contract['provenance']
    answer['scope'] = 'Conditional on physical contract; its truth is not verified by this computation'
    return answer


def localize(payload, config=None):
    obs, skipped = observations(payload)
    sol = solve(obs, INCUMBENT if config is None else config)
    delta = sol.position-obs.positions
    jac = delta/np.maximum(np.linalg.norm(delta, axis=1), 1e-10)[:, None]
    eig = np.linalg.eigvalsh(jac.T@jac)
    reliability = dict(status='not-certified', reason='no-hard-contract')
    if payload.get('contract') is not None and sol.success:
        if skipped:
            raise ValueError('Contract must describe exactly the observed reporters')
        reliability = certify(obs, sol.position, payload['contract'])
    action = 'recover' if reliability['status']=='conditionally-certified' else (
        'acquire-more-data' if payload.get('information_available', False) else 'abstain')
    return dict(n_reporters=len(obs.distances), estimate=sol.position.tolist(),
                optimizer_success=sol.success, nfev=sol.nfev,
                decision=action, reliable_position=[float(F(v)) for v in reliability['decision']['position']] if action=='recover' else None,
                reliability=reliability, skipped_reporters=skipped,
                diagnostics=dict(local_direction_eigenvalues=eig.tolist(),
                    median_abs_residual=float(np.median(abs(np.linalg.norm(delta, axis=1)-obs.distances))),
                    scope='Diagnostics at numerical estimate, not a recoverability certificate'),
                request='Collect spatially diverse reports and justify hard bounds' if action=='acquire-more-data' else None)


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('input'); p.add_argument('output'); p.add_argument('--method')
    a = p.parse_args()
    out = Path(a.output)
    if out.exists(): raise FileExistsError(out)
    cfg = json.loads(Path(a.method).read_text())['config'] if a.method else None
    out.write_text(json.dumps(localize(json.loads(Path(a.input).read_text()), cfg), indent=2)+'\n')
