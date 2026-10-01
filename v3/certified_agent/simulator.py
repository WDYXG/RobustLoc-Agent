"""Private paired episode environment. No truth exposed to the decision policy."""
from copy import deepcopy
from fractions import Fraction as F
import numpy as np
from v2.global_stability.exact import point,sqrt_interval,distance2

RING=[['5','0'],['-5','0'],['0','5'],['0','-5'],['3','4'],['-3','4'],['3','-4'],['-3','-4']]
LINE=[['-5','0'],['-2','0'],['2','0'],['5','0']]
REFLECTION=[['-2','0'],['0','0'],['2','0'],['1','3']]
NEAR=[['-5','1/50'],['-3','-1/50'],['-1','1/50'],['1','-1/50'],['3','1/50'],['5','-1/50']]

def true_range(x,p): return np.sqrt(float(distance2(point(x),point(p))))

def make_episode(scenario,index,cfg,seed=None):
    seed=cfg['episode_seed'] if seed is None else seed
    scene_index=cfg['scenarios'].index(scenario)
    rng=np.random.default_rng(seed+scene_index*10000+index)
    truth=[format(rng.uniform(-.7,.7),'.9f'),format(rng.uniform(.45,.85),'.9f')]
    anchors=deepcopy(RING); q=1; actual_q=1; budget=3; bad_new=False; noise_scale=.003
    if scenario=='collinear-q0': anchors=deepcopy(LINE); q=actual_q=0
    elif scenario=='reflection-q1': anchors=deepcopy(REFLECTION)
    elif scenario=='near-line-q1': anchors=deepcopy(NEAR)
    elif scenario=='budget-limited': anchors=deepcopy(LINE); budget=1
    elif scenario=='missing-q-budget': q=None; actual_q=0; budget=0
    elif scenario=='new-report-corrupted': anchors=deepcopy(LINE); bad_new=True
    elif scenario=='outside-domain': truth=['1.6',truth[1]]
    elif scenario=='over-noise-budget': noise_scale=.35
    elif scenario=='over-corruption-budget': actual_q=3
    offers=[p for p in cfg['offered_anchors'] if p not in anchors]
    noise={tuple(p):float(rng.uniform(-noise_scale,noise_scale)) for p in anchors+offers}
    bad_initial=[] if bad_new else ([len(anchors)-1] if actual_q==1 else list(range(actual_q)))
    bad_positions={tuple(anchors[i]) for i in bad_initial}
    private=dict(truth=truth,noise=noise,bad_positions=bad_positions,bad_new=bad_new,
        initial_anchors=deepcopy(anchors),scenario=scenario,actual_q=actual_q,
        new_bad_position=None,seed=seed+scene_index*10000+index)
    # Coherent reflected attacks expose the ambiguity branch to always-output estimation.
    measurements=[measure(private,p) for p in anchors]
    obs=dict(anchors=anchors,measurements=measurements,weights=['1']*len(anchors),domain=deepcopy(cfg['domain']),
        q_budget=q,estimated_corruption=0 if scenario=='wrong-q-hint' else int(rng.integers(0,3)),
        epsilon=cfg['epsilon'],error_tolerance=cfg['error_tolerance'],
        available_anchors=offers,acquisitions_remaining=budget,
        random_choice_index=int(rng.integers(0,10000)))
    return dict(id=f'{scenario}-{index:03d}',scenario=scenario,observation=obs,private=private)

def measure(private,p):
    key=tuple(p); truth=private['truth']; bad=key in private['bad_positions'] or key==private['new_bad_position']
    target=[truth[0],str(-F(truth[1]))] if bad else truth
    value=true_range(target,p)+private['noise'][key]
    if private['scenario']=='over-corruption-budget' and bad: value+=.6
    return format(max(value,0),'.12f')

def acquire(obs,private,p):
    if p not in obs['available_anchors'] or obs['acquisitions_remaining']<=0:
        raise ValueError('Unavailable or over-budget acquisition')
    new=deepcopy(obs)
    if private['bad_new'] and private['new_bad_position'] is None:
        private['new_bad_position']=tuple(p)
    new['anchors'].append(deepcopy(p)); new['weights'].append('1'); new['measurements'].append(measure(private,p))
    new['available_anchors'].remove(p); new['acquisitions_remaining']-=1
    new['random_choice_index']+=17
    return new

def private_snapshot(private):
    return dict(truth=private['truth'],actual_q=private['actual_q'],scenario=private['scenario'],
        bad_positions=[list(p) for p in sorted(private['bad_positions'])],
        new_bad_position=list(private['new_bad_position']) if private['new_bad_position'] else None,
        seed=private['seed'])

def contract(obs,private):
    truth=point(private['truth']); domain=list(map(F,obs['domain'])); eps=F(obs['epsilon'])
    inside=domain[0]<=truth[0]<=domain[1] and domain[2]<=truth[1]<=domain[3]
    bad=[]; upper2=F(0)
    for i,(p,y,w) in enumerate(zip(obs['anchors'],obs['measurements'],obs['weights'])):
        key=tuple(p)
        if key in private['bad_positions'] or key==private['new_bad_position']:
            bad.append(i); continue
        lo,hi=sqrt_interval(distance2(truth,point(p))); y=F(y)
        upper2+=F(w)*max(abs(lo-y),abs(hi-y))**2
    budget=obs['q_budget']; corruption_ok=budget is not None and len(bad)<=budget
    noise_ok=upper2<=eps*eps
    return dict(valid=bool(inside and corruption_ok and noise_ok),true_inside=bool(inside),
        corruption_ok=bool(corruption_ok),noise_ok=bool(noise_ok),bad_indices=bad,
        true_clean_norm2_upper=str(upper2),q_budget=budget,
        scope='private evaluator only; never passed to policy')
