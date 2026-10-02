"""Private synthetic environment. Policy never receives this state."""
from copy import deepcopy
from fractions import Fraction as F
import math
import random
from .contracts import ISSUERS
from .verifier import root

CIRCLE=[['5','0'],['3','4'],['0','5'],['-3','4'],['-5','0'],['-3','-4'],['0','-5'],['3','-4']]


def make_episode(scenario,index,cfg,seed):
    rng=random.Random(seed+index); truth=[str(F(rng.randint(-600,600),1000)) for _ in range(2)]
    anchors=deepcopy(CIRCLE); domain=cfg['default_domain']; qmax=1; epsilon='1/25'; radius='1/100'; budget='5'; tolerance=cfg['error_tolerance']
    if scenario=='healthy': epsilon='1/50'
    if scenario in ('anchor-uncertainty','untrusted-receipt','dishonest-calibration'): radius='4/25'
    if scenario=='q-uncertainty': qmax=3
    if scenario=='domain-uncertainty': domain=['-15','15','-15','15']; epsilon='7/100'
    if scenario in ('mixed-premises','budget-limited'):
        domain=['-8','8','-8','8']; qmax=3; radius='3/25'
    if scenario=='budget-limited': budget='3/2'
    if scenario=='geometry-plateau':
        anchors=[['-5','0'],['-3','0'],['3','0'],['5','0']]; radius='1/1000'; epsilon='1/200'; budget='3'
    if scenario=='dishonest-calibration': epsilon='1/1000'; tolerance='1/20'
    n=len(anchors); bad=[0] if scenario!='healthy' else []
    offers=[]
    for k,p in enumerate(cfg['offered_anchors']):
        offers.append(dict(id='range-'+str(k),kind='new-range',cost=cfg['range_cost'],
                           update=dict(anchor=p,weight='1',radius='1/1000')))
    # Only informative nested actions are offered. Their contract is a service promise.
    if F(radius)>F('1/100'):
        offers.append(dict(id='calibrate',kind='anchor-recalibration',cost=cfg['calibration_cost'],
                           update=dict(indices=list(range(n)),radius='1/1000' if scenario=='dishonest-calibration' else '1/100')))
    if domain!=cfg['default_domain']:
        offers.append(dict(id='prior',kind='tighter-domain',cost=cfg['domain_cost'],update=dict(domain=cfg['default_domain'])))
    if qmax>1:
        offers.append(dict(id='support-audit',kind='stronger-q-bound',cost=cfg['q_bound_cost'],update=dict(q_max=1)))
    offsets=[[F(rng.choice([-1,1]),4000),F(rng.choice([-1,1]),4000)] for _ in range(n+3)]
    if scenario=='dishonest-calibration':
        # Actual position is inside original balls but outside dishonest recalibration.
        offsets=[[F('1/10'),F(0)] for _ in range(n)]+offsets[n:]
    all_nominal=anchors+cfg['offered_anchors']; actual=[[str(F(v)+offsets[i][k]) for k,v in enumerate(p)] for i,p in enumerate(all_nominal)]
    values=[]
    for i,p in enumerate(actual):
        distance=math.sqrt(sum((float(F(a)-F(x)))**2 for a,x in zip(p,truth)))
        noise=rng.uniform(-0.0002,0.0002)
        values.append(format(distance+noise+(1.3 if i in bad else 0),'.17f'))
    public=dict(episode_id=scenario+'-'+str(index),anchors=anchors,weights=['1']*n,
        radii=[radius]*n,domain=deepcopy(domain),measurements=values[:n],q_max=qmax,
        epsilon_max=epsilon,error_tolerance=tolerance,budget=budget,offers=offers,
        receipts=[],estimated_corruption=rng.choice([0,1,2,4]),
        premise_sources=dict(initial='simulated-outer-contract',scope='conditional on honest sources'))
    private=dict(truth=truth,actual_anchors=actual,bad_indices=bad,future_measurements=values[n:],
                 initial_count=n,scenario=scenario,index=index,
                 offered_anchors=deepcopy(cfg['offered_anchors']),
                 trusted_service_model=scenario not in ('untrusted-receipt','dishonest-calibration'))
    return public,private


def service(obs,offer,private):
    receipt=dict(offer_id=offer['id'],episode_id=obs['episode_id'],issuer=ISSUERS[offer['kind']],
                 update=deepcopy(offer['update']),evidence='independent simulated service; physical truth not software-certified')
    if offer['kind']=='new-range':
        k=int(offer['id'].split('-')[1]); receipt['measurement']=private['future_measurements'][k]
    if private['scenario']=='untrusted-receipt' and offer['kind']=='anchor-recalibration': receipt['issuer']='untrusted-self-assertion'
    return receipt


def actual_for(obs,private):
    n=private['initial_count']; actual=private['actual_anchors'][:n]
    for p in obs['anchors'][n:]:
        # Offers have unique nominal coordinates in this fixed fixture.
        k=next(i for i,x in enumerate(private['offered_anchors']) if x==p)
        actual.append(private['actual_anchors'][n+k])
    return actual


def evaluate(obs,private,decision):
    x=list(map(F,private['truth'])); d=list(map(F,obs['domain']))
    actual=actual_for(obs,private); valid=d[0]<=x[0]<=d[1] and d[2]<=x[1]<=d[3]
    valid=valid and len(private['bad_indices'])<=obs['q_max']
    violations=[]; clean_error2=F(0)
    for i,(a,bar,delta,w,y) in enumerate(zip(actual,obs['anchors'],obs['radii'],obs['weights'],obs['measurements'])):
        if sum((F(v)-F(b))**2 for v,b in zip(a,bar))>F(delta)**2:
            valid=False; violations.append('anchor-ball-'+str(i))
        if i not in private['bad_indices']:
            lo,hi=root(sum((F(v)-u)**2 for v,u in zip(a,x))); yy=F(y)
            clean_error2+=F(w)*max(abs(lo-yy),abs(hi-yy))**2
    if clean_error2>F(obs['epsilon_max'])**2: valid=False; violations.append('noise-budget')
    output=decision['action']=='recover'; error=bound_violation=None
    if output:
        error=math.sqrt(sum((float(F(v)-u))**2 for v,u in zip(decision['position'],x)))
        bound_violation=error>float(F(decision['error_bound']))+1e-10
    return dict(contract_valid=bool(valid),contract_violations=violations,output=output,error=error,
                wrong_output=bool(output and error>float(F(obs['error_tolerance']))),
                bound_violation=bool(bound_violation),scope='private synthetic evaluator')
