"""Public possible-world fixtures and checked restrictions of continuous worlds."""
from copy import deepcopy
from fractions import Fraction as F
import random
from v3b.assumption_agent.verifier import root
from v3c.trust_agent.verifier import feasible_world
from v3c.trust_agent.actions import apply
from v3.certified_agent.decoder import solve


def response(obs,offer,world):
    p=world['positions']; x=world['target']; kind=offer['kind']
    if kind=='absolute-reference':
        if F(offer['radius'])!=0: raise ValueError('only exact external reply model implemented')
        return dict(points=[dict(anchor=i,centre=p[i],radius='0',root=offer['root']) for i in offer['anchors']])
    if kind=='baseline':
        a,b=offer['anchors']
        return dict(baseline=dict(a=a,b=b,distance2=str(sum((F(u)-F(v))**2 for u,v in zip(p[a],p[b]))),root=offer['root']))
    if kind=='ordinary-range':
        values=[]
        for i in offer['anchors']:
            lo,hi=root(sum((F(u)-F(v))**2 for u,v in zip(p[i],x)))
            values.append(dict(anchor=i,value=str((lo+hi)/2),weight='1'))
        return dict(measurements=values)
    raise ValueError('every physical action needs a checked response; cannot omit a helpful action from a lower-bound model')


def restriction(obs,worlds):
    return dict(worlds=deepcopy(worlds),tolerance=obs['tolerance'],
        actions=[dict(id=o['id'],cost=o['cost'],responses={w['id']:response(obs,o,w) for w in worlds}) for o in obs['offers']])


def validate_restriction(obs,model):
    """Every world and every available query reply must be physically admissible.

    Checks joint final clean-noise budget after ALL offered queries, not a new
    independent noise budget per measurement. Replies are fixed within a world.
    """
    offers={o['id']:o for o in obs['offers']}
    if set(offers)!={a['id'] for a in model['actions']} or model['tolerance']!=obs['tolerance']: raise ValueError('incomplete menu/tolerance')
    count=0
    for w in model['worlds']:
        if not feasible_world(obs,w): raise ValueError('world outside initial contract')
        state=deepcopy(obs); state['budget']=str(sum((F(o['cost']) for o in obs['offers']),F(0)))
        for a in model['actions']:
            o=offers[a['id']]
            if F(a['cost'])!=F(o['cost']): raise ValueError('action cost binding')
            supplied=a['responses'][w['id']]
            if supplied!=response(obs,o,w): raise ValueError('nonphysical action response')
            state=apply(state,o,supplied); count+=1
        if not feasible_world(state,w): raise ValueError('future joint noise/premise contract violated')
    return dict(passed=True,worlds=len(model['worlds']),responses=count,
        scope='valid finite restriction of the full continuous contract; completeness is not established by sampling')


def translated_restriction(obs,cfg):
    """Witness search uses only observed centers/ranges, never private target."""
    if obs['reports']: raise ValueError('this witness constructor needs hard-ball priors')
    refs={}
    for a in obs['hard_refs']:
        if a['anchor'] not in refs or F(a['radius'])<F(refs[a['anchor']]['radius']): refs[a['anchor']]=a
    if any(m['anchor'] not in refs for m in obs['measurements']): raise ValueError('missing center model')
    solver=dict(anchors=[refs[m['anchor']]['centre'] for m in obs['measurements']],
        measurements=[m['value'] for m in obs['measurements']],weights=[m['weight'] for m in obs['measurements']],
        domain=obs['domain'],q_budget=obs['q'],epsilon=obs['epsilon'],error_tolerance=obs['tolerance'])
    c=solve(solver,cfg)['position']; delta=min(F(a['radius']) for a in refs.values())/2
    shifts=[(0,0),(delta,0),(-delta,0),(0,delta),(0,-delta)]; out=[]
    for j,t in enumerate(shifts):
        w=dict(id='w'+str(j),target=[str(F(v)+d) for v,d in zip(c,t)],
            positions={i:[str(F(v)+d) for v,d in zip(a['centre'],t)] for i,a in refs.items()})
        if feasible_world(obs,w) and not any(w['target']==v['target'] for v in out): out.append(w)
    if not out: raise ValueError('no verified witness found: cannot claim finite lower')
    model=restriction(obs,out); validate_restriction(obs,model); return model


def base_observation(worlds,offers,tolerance):
    p=worlds[0]['positions']; x=worlds[0]['target']
    mm=[]
    for i in p:
        lo,hi=root(sum((F(a)-F(b))**2 for a,b in zip(x,p[i])))
        mm.append(dict(anchor=i,value=str((lo+hi)/2),weight='1'))
    return dict(episode_id='finite',nominal=deepcopy(p),measurements=mm,hard_refs=[],reports=[],failure_groups={},
       external_roots=['external-position-instrument','external-baseline-instrument'],q=0,r=0,epsilon='1/1000000',
       tolerance=tolerance,domain=['-3','3','-3','3'],budget='20',offers=offers,baselines=[],receipts=[],forecast_frames=[])


def finite_case(kind,index,seed):
    rng=random.Random(seed+index); scale=F(rng.randint(2,8),4)
    ref=lambda i,c:dict(id='ref-'+i,kind='absolute-reference',anchors=[i],radius='0',cost=str(c),root='external-position-instrument')
    if kind=='adaptive-four':
        targets=[['-1','-1'],['-1','1'],['1','-1'],['1','1']]; worlds=[]
        for i,x in enumerate(targets):
            worlds.append(dict(id='w'+str(i),target=x,positions=dict(g=['-4','0'] if i<2 else ['4','0'],
                  l=['-2','2'] if i==1 else ['0','0'],r=['2','2'] if i==3 else ['0','0'])))
        offers=[ref(i,scale) for i in ('g','l','r')]; tol='1/10'
    elif kind=='unseparable-reflection':
        p=dict(a=['-3/4','0'],b=['3/4','0'])
        worlds=[dict(id='w0',target=['0','1'],positions=p),dict(id='w1',target=['0','-1'],positions=p)]
        offers=[dict(id='repeat',kind='ordinary-range',anchors=['a','b'],cost='1/4'),ref('a',scale),ref('b',scale)]; tol='1/10'
    else:
        if kind=='acute-triple': targets=[['-1','0'],['1','0'],['0','3/2']]; tol='21/20'
        elif kind=='near-cluster': targets=[['0','0'],['1/10','0'],['0','1/10']]; tol='1/10'
        else: targets=[['-1/2','0'],['1/2','0']]; tol='1/10'
        worlds=[dict(id='w'+str(i),target=x,positions=dict(a=[str(F(x[0])+4),x[1]])) for i,x in enumerate(targets)]
        offers=[ref('a',F('9/2') if kind=='expensive-pair' else scale),dict(id='repeat',kind='ordinary-range',anchors=['a'],cost='1/4')]
    obs=base_observation(worlds,offers,tol)
    if kind=='unseparable-reflection':
        obs['hard_refs']=[dict(anchor=i,centre=p,radius='0',root='external-position-instrument') for i,p in worlds[0]['positions'].items()]
    obs['episode_id']=kind+'-'+str(index)
    model=restriction(obs,worlds); model['model_semantics']='explicit complete finite prior for exact optimum; also a checked restriction of the larger continuous contract'
    validate_restriction(obs,model)
    return obs,model
