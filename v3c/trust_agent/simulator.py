"""Private joint worlds. Public forecasts contain coordinates, never target truth."""
from copy import deepcopy
from fractions import Fraction as F
import random
import math
from .actions import payload
from .witnesses import transform
from .verifier import root

NOMINAL={'a0':['4','0'],'a1':['-4','0'],'a2':['0','4'],'a3':['3','-4'],'a4':['-3','-4'],'a5':['0','-5']}


def make(scenario,index,cfg,seed):
    rng=random.Random(seed+index); x=[str(F(rng.randint(-400,400),1000)),str(F(rng.randint(400,800),1000))]
    frame=cfg['forecast_frames'][index%3]; p={i:transform(v,frame['R'],frame['t']) for i,v in NOMINAL.items()}; target=transform(x,frame['R'],frame['t'])
    epsilon=cfg['epsilon']; tol=cfg['tolerance']; q=1 if scenario=='sparse-q1' else 0; budget=cfg['budget']
    hard=[]; reports=[]; registry={'issuer-A':'group-A','issuer-B':'group-B','issuer-C':'group-C','issuer-new':'group-new'}
    ref=lambda i,rad='0':dict(anchor=i,centre=p[i],radius=rad,root='external-position-instrument')
    if scenario=='one-reference': hard=[ref('a0')]
    if scenario=='two-reflection': hard=[ref('a0'),ref('a1')]
    if scenario=='precision-gap':
        hard=[ref(i) for i in ['a0','a1','a2']]; epsilon='3/200'; tol='1/20'
    if scenario=='bounded-references': hard=[ref(i,'1/20') for i in NOMINAL]
    nominal=deepcopy(NOMINAL)
    if scenario=='frame-without-ranges':
        for i,v in {'u0':['0','0'],'u1':['1','0'],'u2':['0','1']}.items():
            nominal[i]=v; p[i]=v; hard.append(dict(anchor=i,centre=v,radius='0',root='external-position-instrument'))
    points=lambda coords:[dict(anchor=i,centre=coords[i],radius='0') for i in NOMINAL]
    false={i:transform(v,[['1','0'],['0','1']],['4/5','0']) for i,v in p.items()}
    if scenario in ('two-source-ambiguity','three-source-majority','aliases-one-domain','premise-budget-violated'):
        reports=[dict(issuer='issuer-A',points=points(p)),dict(issuer='issuer-B',points=points(false))]
        if scenario=='three-source-majority': reports.append(dict(issuer='issuer-C',points=points(p)))
        if scenario=='aliases-one-domain':
            reports=[dict(issuer=i,points=points(false)) for i in ('issuer-A','issuer-B','issuer-C')]
            registry.update({i:'one-shared-instrument' for i in ('issuer-A','issuer-B','issuer-C')}); budget='3/5'
        if scenario=='premise-budget-violated': reports.append(dict(issuer='issuer-C',points=points(false)))
    if scenario=='trust-budget-shortfall': budget='1'
    noise=lambda:(rng.uniform(-0.0001,0.0001))
    measured=list(NOMINAL)
    if scenario=='precision-gap': measured=['a0','a1','a2']
    measurements=[]
    for j,i in enumerate(measured):
        distance=math.sqrt(sum(float(F(a)-F(b))**2 for a,b in zip(target,p[i])))
        measurements.append(dict(anchor=i,value=format(distance+noise()+(1.2 if q and j==0 else 0),'.17f'),weight='1'))
    offers=[]
    for k in range(3):
        offers.append(dict(id='range-'+str(k),kind='ordinary-range',cost=cfg['ordinary_cost'],anchors=measured[:3]))
    offers.append(dict(id='baseline',kind='baseline',cost=cfg['baseline_cost'],anchors=['a0','a1'],root='external-baseline-instrument'))
    if scenario not in ('precision-gap',):
        for i,c in zip(NOMINAL,cfg['reference_costs']):
            if i in {a['anchor'] for a in hard} and scenario!='bounded-references': continue
            offers.append(dict(id='ref-'+i,kind='absolute-reference',cost=c,anchors=[i],radius=cfg['root_radius'],root='external-position-instrument'))
    if scenario in ('two-source-ambiguity','aliases-one-domain'):
        offers.append(dict(id='independent-source',kind='independent-source',cost=cfg['source_cost'],anchors=list(NOMINAL),issuer='issuer-new'))
    obs=dict(episode_id=scenario+'-'+str(index),nominal=nominal,measurements=measurements,hard_refs=hard,reports=reports,
        failure_groups=registry,external_roots=['external-position-instrument','external-baseline-instrument'],
        q=q,r=1,epsilon=epsilon,tolerance=tol,domain=cfg['domain'],budget=budget,offers=offers,baselines=[],receipts=[],
        forecast_frames=cfg['forecast_frames'],trust_scope='externally assumed physical roots and source-group budget; untrusted nominal centres are metadata')
    # Future ordinary values are measured in this joint world with same noise budget.
    future={}
    for o in offers:
        if o['kind']=='ordinary-range':
            future[o['id']]=dict(measurements=[dict(anchor=i,value=format(math.sqrt(sum(float(F(a)-F(b))**2 for a,b in zip(target,p[i])))+noise(),'.17f'),weight='1') for i in o['anchors']])
    private=dict(target=target,positions=p,future=future,scenario=scenario,
                 contract_valid=scenario!='premise-budget-violated',frame=frame,noise_scope='global clean norm below E for all offered repeats')
    return obs,private


def service(obs,offer,private):
    p=private['positions']
    if offer['kind']=='ordinary-range': return deepcopy(private['future'][offer['id']])
    if offer['kind']=='absolute-reference': return dict(points=[dict(anchor=i,centre=p[i],radius=offer['radius'],root=offer['root']) for i in offer['anchors']])
    if offer['kind']=='independent-source': return dict(report=dict(issuer=offer['issuer'],points=[dict(anchor=i,centre=p[i],radius='0') for i in offer['anchors']]))
    a,b=offer['anchors']; return dict(baseline=dict(a=a,b=b,distance2=str(sum((F(x)-F(y))**2 for x,y in zip(p[a],p[b]))),root=offer['root']))
