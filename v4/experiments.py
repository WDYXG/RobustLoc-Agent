"""Predeclared small scientific tasks, distinct from verifier decisions."""
from itertools import combinations
from fractions import Fraction as F
import random
from .core.geometry import enclosing_ball,independent_radius2
from .core.research import search_ambiguity
from .core.arithmetic import dot
from .core.corruption import residual_interval2
from .problems.phase_retrieval import PhaseRetrieval,acquisition_upper,verify_acquisition
from .problems.range_localization import RangeLocalization


def grid():
    return [[str(F(i,2)),str(F(j,2))] for i in range(-4,5) for j in range(-4,5) if i or j]


def recovery_case(kind,index,seed):
    rng=random.Random(seed+index); candidates=grid()
    problem=PhaseRetrieval([(1,t) for t in (-2,-1,0,1,2)]) if kind=='phase' else RangeLocalization()
    x=candidates[rng.randrange(len(candidates))]; predicted=problem.observe(x); eps=F(1,10000)
    values=[(lo+hi)/2+F(rng.choice((-1,0,1)),1000000) for lo,hi in predicted]
    bad=rng.randrange(len(values)); values[bad]+=F(rng.choice((-37,23,100)),7)
    transcript=dict(values=list(map(str,values)),q=1,epsilon=str(eps),tolerance='1/10')
    private=dict(target=x,corrupt_coordinates=[bad])
    return problem,transcript,candidates,private


def measurement_model(problem,targets,parameters,costs,tolerance='1/10',semantics='complete-finite-prior'):
    worlds=[dict(id='w'+str(i),target=list(map(str,x))) for i,x in enumerate(targets)]; actions=[]
    for j,(p,c) in enumerate(zip(parameters,costs)):
        extended=problem.with_measurement(p); replies={}
        for w in worlds:
            lo,hi=extended.observe(w['target'])[-1]
            if lo!=hi: raise ValueError('finite active template requires exact reply')
            replies[w['id']]=dict(value=str(lo))
        actions.append(dict(id='measure-'+str(j),parameter=list(map(str,p)),cost=str(c),responses=replies))
    return dict(worlds=worlds,actions=actions,tolerance=tolerance,semantics=semantics)


def active_case(kind,index,seed):
    rng=random.Random(seed+index); unit=F(rng.randint(2,6),4)
    if kind=='phase':
        problem=PhaseRetrieval([(1,0),(0,1)]); states=[(1,1),(1,-1),(-1,-1),(-1,1)]; params=[(1,1),(1,-1)]
    else:
        problem=RangeLocalization([('-3/4',0),('3/4',0)]); states=[(0,1),(0,-1)]; params=[(0,3),(0,-3)]
    model=measurement_model(problem,states,params,[unit,2*unit]); obs=problem.observe(states[0])
    transcript=dict(values=[str((a+b)/2) for a,b in obs],q=0,epsilon='1/10000',tolerance='1/10')
    return problem,transcript,[list(map(str,x)) for x in states],model


def q_vs_2q():
    p=PhaseRetrieval([(1,t) for t in (0,1,2,3)])
    every_q=all(p.complement_property(S)['passed'] for S in combinations(range(4),3))
    every_2q=all(p.complement_property(S)['passed'] for S in combinations(range(4),2))
    witness=search_ambiguity(p,grid(),1)
    if not every_q or every_2q or not witness['found']: raise AssertionError('declared q versus 2q conjecture not refuted')
    return dict(problem=p.design,after_q_deletions=every_q,after_2q_deletions=every_2q,witness=witness,status='refuted')


def quotient_helly_search():
    # Rational points on the unit circle; the search chooses an obstruction.
    pool=[['1','0'],['0','1'],['3/5','4/5'],['-4/5','3/5'],['4/5','3/5'],['-3/5','4/5']]
    checked=0; rho=F(4,5)
    for H in combinations(pool,4):
        checked+=1
        triple=max(independent_radius2(S,'sign') for S in combinations(H,3))
        full=enclosing_ball(H,'sign')
        if triple<=rho*rho<F(full['radius2']):
            return dict(points=list(H),radius2=full['radius2'],maximum_triple_radius2=str(triple),tolerance=str(rho),checked=checked,
                status='refuted',claim='Euclidean three-point witness completeness transfers unchanged to the sign quotient')
    raise AssertionError('predeclared quotient stress test found no counterexample')


def origin_degeneracy():
    p=PhaseRetrieval([(1,t) for t in (-2,-1,0,1,2)],0,3); records=[]
    for k in range(1,9):
        t=F(1,2**k); x=[t,F(0)]; z=[F(0),F(0)]
        ratio2=sum(a*a for a,b in p.observe(x))/p.state_distance2(x,z)
        records.append(dict(scale=str(t),squared_ratio=str(ratio2)))
    return dict(frame=p.design,complement_property=p.complement_property(),sequence=records,
        proof='h(t*u)-h(0)=t^2 h(u); quotient distance=t||u||; ratio tends to zero',
        status='refuted',claim='phase retrievability alone implies a positive intensity margin under d_pm on a domain containing zero')


def robust_active_case(index,seed):
    rng=random.Random(seed+index); unit=F(rng.randint(2,6),4)
    p=PhaseRetrieval([(1,t) for t in (0,1,2)]); witness=search_ambiguity(p,grid(),1)
    if not witness['found']: raise AssertionError('no initial ambiguity')
    states=[witness['left'],witness['right']]
    offers=[dict(id='measure-'+str(j),vector=['1',str(t)],cost=str(unit)) for j,t in enumerate((-1,3))]
    model=measurement_model(p,states,[o['vector'] for o in offers],[o['cost'] for o in offers],semantics='verified-restriction')
    transcript=dict(values=witness['transcript']['values'],q=1,epsilon='1/10000',tolerance='1/10')
    upper=acquisition_upper(p,offers,1,transcript['epsilon'],transcript['tolerance'])
    if upper['cost_upper'] is None: raise AssertionError('no response-uniform active upper found')
    final=verify_acquisition(p,offers,1,transcript['epsilon'],transcript['tolerance'],upper)
    return p,transcript,states,offers,model,upper,final


def validate_measurement_model(problem,transcript,model,offers=None):
    """Full menu plus joint clean-noise budget: finite restriction is physical."""
    if offers is not None:
        expected={o['id']:(o['cost'],o['vector']) for o in offers}
        actual={a['id']:(a['cost'],a['parameter']) for a in model['actions']}
        if actual!=expected: raise ValueError('omitted or modified physical action')
    for w in model['worlds']:
        x=w['target']
        if not problem.in_domain(x): raise ValueError('world outside domain')
        p=problem; values=list(transcript['values'])
        for a in model['actions']:
            p=p.with_measurement(a['parameter']); lo,hi=p.observe(x)[-1]
            reply=a['responses'][w['id']]
            if lo!=hi or reply!=dict(value=str(lo)): raise ValueError('nonphysical exact potential reply')
            values.append(reply['value'])
        if residual_interval2(p.observe(x),values,transcript['q'])[1]>F(transcript['epsilon'])**2: raise ValueError('joint global noise/corruption budget')
    return dict(passed=True,worlds=len(model['worlds']),scope='potential clean replies form an admissible restriction; arbitrary future corruptions are covered only by the separate uniform upper')
