"""A narrow, exactly checked finite reduction of a continuous range problem."""
from fractions import Fraction as F
from .worlds import base_observation,restriction,validate_restriction
from .finite import analyze
from .finite_verify import verify
from .agent import diagnose


def make_case(index):
    h=[F(1),F(1,2),F(3,2)][index]; a=3*h/4; delta=2*h
    p=dict(left=[str(-a),'0'],right=[str(a),'0'])
    worlds=[dict(id='up',target=['0',str(h)],positions=dict(p,u=['0',str(-delta)])),
            dict(id='down',target=['0',str(-h)],positions=dict(p,u=['0',str(delta)]))]
    ref=lambda i,c:dict(id='ref-'+i,kind='absolute-reference',anchors=[i],radius='0',cost=str(c),root='external-position-instrument')
    offers=[ref('left',h),ref('right',6*h/5),ref('u',7*h/5),
            dict(id='repeat',kind='ordinary-range',anchors=['left','right','u'],cost='1/4'),
            dict(id='baseline',kind='baseline',anchors=['left','u'],cost='1/5',root='external-baseline-instrument')]
    obs=base_observation(worlds,offers,str(h/10)); obs['epsilon']='0'; obs['episode_id']='analytic-reflection-'+str(index)
    obs['hard_refs']=[dict(anchor=i,centre=p[i],radius='0',root='external-position-instrument') for i in ('left','right')]
    obs['hard_refs'].append(dict(anchor='u',centre=['0','0'],radius=str(delta),root='external-position-instrument'))
    cert=dict(schema='reflection-tangency-completeness-v1',a=str(a),h=str(h),delta=str(delta))
    model=restriction(obs,worlds); return obs,model,cert


def verify_completeness(obs,model,c):
    """An algebraic physical prior certificate, not a sampled completeness claim.

    Two exact equal circles force x=(0,+/-h). The unknown-anchor ball has radius
    delta about0 and its range equals h+delta. Equality in triangle inequality
    forces that anchor to lie opposite x at distance delta from0.
    """
    a,h,d=F(c['a']),F(c['h']),F(c['delta'])
    if c['schema']!='reflection-tangency-completeness-v1' or min(a,h,d)<=0: raise ValueError('analytic parameters')
    if obs['q']!=0 or obs['r']!=0 or F(obs['epsilon'])!=0 or obs['reports'] or obs['baselines']: raise ValueError('not an exact zero-corruption tangency model')
    if set(obs['nominal'])!={'left','right','u'}: raise ValueError('extra nuisance variables')
    refs={r['anchor']:r for r in obs['hard_refs']}
    if len(obs['hard_refs'])!=3 or set(refs)!={'left','right','u'}: raise ValueError('reference structure')
    expected={'left':([str(-a),'0'],'0'),'right':([str(a),'0'],'0'),'u':(['0','0'],str(d))}
    for i,(p,r) in expected.items():
        rr=refs[i]
        if list(map(F,rr['centre']))!=list(map(F,p)) or F(rr['radius'])!=F(r) or rr['root'] not in obs['external_roots']: raise ValueError('tangency reference binding')
    mm={m['anchor']:m for m in obs['measurements']}
    if len(obs['measurements'])!=3 or set(mm)!=set(expected) or any(F(m['weight'])<=0 for m in mm.values()): raise ValueError('range structure')
    y=F(mm['left']['value'])
    if y<=0 or F(mm['right']['value'])!=y or y*y!=a*a+h*h or F(mm['u']['value'])!=h+d: raise ValueError('exact circle/tangency equations')
    D=list(map(F,obs['domain']))
    if not(D[0]<=0<=D[1] and D[2]<=-h<=h<=D[3]): raise ValueError('domain excludes a reflection world')
    worlds=[]
    for sign,wid in [(1,'up'),(-1,'down')]:
        worlds.append(dict(id=wid,target=['0',str(sign*h)],positions=dict(left=[str(-a),'0'],right=[str(a),'0'],u=['0',str(-sign*d)])))
    if model['worlds']!=worlds: raise ValueError('catalog is not the proved complete physical world set')
    validate_restriction(obs,model)
    return dict(passed=True,world_count=2,scope='continuous target and all anchor positions reduced exactly; zero noise, q=r=0, checked tangency only')


def analyze_case(obs,model,completeness,budget):
    proof=verify_completeness(obs,model,completeness); f=analyze(model); v=verify(model,f); c=f['adaptive_cost']
    return dict(interval=diagnose(c or '0',c,budget,lower_infinite=c is None),finite=f,verification=v,
        completeness=proof,scope='continuous physical cost equality authorized by a checked exact prior reduction; not by sampling')
