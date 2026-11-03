"""New metre-scale simulation. Truth is private to evaluator, never to service."""
import itertools
import numpy as np

COUNTS = [8, 11, 16, 32]
NOISE = {'low': (1., 2.), 'medium': (5., 8.), 'high': (15., 20.)}
GEOMETRIES = ['surround', 'sector', 'line']
CONTAMINATION = [0., .1, .3]
SPLITS = {'development': (11000000, 4), 'validation': (22000000, 8), 'test': (33000000, 40)}


def specifications(split):
    base, count = SPLITS[split]
    cells = list(itertools.product(COUNTS, GEOMETRIES, NOISE, CONTAMINATION))
    for j, (n, geometry, noise, frac) in enumerate(cells):
        for k in range(count):
            yield dict(seed=base+j*1000+k, n=n, geometry=geometry, noise=noise,
                       contamination=frac, model='distance-proxy', mismatch=False,
                       scenario=f'{geometry}/{noise}/outliers-{frac}')
    # Separate synthetic RSSI track: same spatial counts, no radio realism claim.
    for j, (n, geometry, mismatch) in enumerate(itertools.product(COUNTS, GEOMETRIES, [False, True])):
        for k in range(count):
            yield dict(seed=base+500000+j*1000+k, n=n, geometry=geometry, noise='medium',
                       contamination=.1, model='synthetic-rssi', mismatch=mismatch,
                       scenario=f'rssi/{geometry}/mismatch-{mismatch}')


def generate(spec):
    rng = np.random.default_rng(spec['seed']); n = spec['n']
    truth = rng.uniform(-100, 100, 2)
    radius = rng.uniform(8, 65, n)
    if spec['geometry'] == 'sector':
        theta = rng.uniform(-.18, .18, n)+rng.uniform(-np.pi, np.pi)
    elif spec['geometry'] == 'line':
        theta = rng.integers(0, 2, n)*np.pi+rng.normal(0, .015, n)
    else:
        theta = rng.uniform(-np.pi, np.pi, n)
    true_positions = truth+np.column_stack((np.cos(theta), np.sin(theta)))*radius[:, None]
    sp, sd = NOISE[spec['noise']]
    sigp = sp*rng.uniform(.7, 1.3, n); sigd = sd*rng.uniform(.7, 1.3, n)
    positions = true_positions+rng.normal(size=(n, 2))*sigp[:, None]
    bad = np.zeros(n, dtype=bool)
    bad[rng.choice(n, int(np.floor(n*spec['contamination'])), replace=False)] = True
    ranges = np.maximum(.05, radius+rng.normal(size=n)*sigd)
    # Both wrong reporter coordinates and wrong ranges are represented separately.
    positions[bad] += rng.normal(0, 35, (sum(bad), 2))
    ranges[bad] += rng.uniform(30, 120, sum(bad))
    reports = []
    for i in range(n):
        r = dict(id=f'reporter-{i}', position=positions[i].tolist(), position_sigma=float(sigp[i]), confidence=1.)
        if spec['model'] == 'synthetic-rssi':
            beta = 2.8 if spec['mismatch'] else 2.
            rssi = -59-10*beta*np.log10(radius[i])+rng.normal(0, 4.)
            if bad[i]: rssi -= rng.uniform(10, 25)
            r.update(rssi_dbm=float(rssi), calibration=dict(a_at_1m_dbm=-59., path_loss_exponent=2., sigma_db=4.))
        else:
            r.update(distance=float(ranges[i]), distance_sigma=float(sigd[i]))
        reports.append(r)
    return dict(reports=reports, units='metres'), dict(truth=truth.tolist(),
        true_reporter_positions=true_positions.tolist(), outlier_mask=bad.tolist())
