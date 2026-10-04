"""Independent bottom-up cost consumer; does not call the search producer."""
from itertools import combinations
from .arithmetic import F
from .geometry import independent_radius2,verify_ball
from .information_action import key
from .world import validate_model
from .decision import diagnose


def verify_result(problem,model,result,budget,external_upper=None):
    validate_model(model); W=model['worlds']; A=model['actions']; n=len(W); values={}; radius={}
    def parts(S,a):
        groups={}
        for i in S: groups.setdefault(key(a['responses'][W[i]['id']]),[]).append(i)
        return groups
    for size in range(1,n+1):
        for S in combinations(range(n),size):
            r=independent_radius2([W[i]['target'] for i in S],problem.symmetry); radius[S]=r
            if r<=F(model['tolerance'])**2: values[S]=F(0); continue
            options=[]
            for a in A:
                pp=parts(S,a)
                if len(pp)<2: continue
                costs=[values[tuple(V)] for V in pp.values()]
                if all(v is not None for v in costs): options.append(F(a['cost'])+max(costs))
            values[S]=min(options) if options else None
    full=tuple(range(n)); c=values[full]
    if result['exact_catalog_cost']!=(str(c) if c is not None else None): raise ValueError('catalog optimum mismatch')
    U=c if model['semantics']=='complete-finite-prior' else external_upper
    if result['interval']!=diagnose(c or 0,U,budget,lower_infinite=c is None): raise ValueError('cost scope/budget mismatch')
    expected=[]
    for size in range(2,n+1):
        for S in combinations(range(n),size):
            if any(set(e['worlds'])<=set(S) for e in expected): continue
            if radius[S]>F(model['tolerance'])**2:
                expected.append(dict(worlds=list(S),radius2=str(radius[S]),breakers=[a['id'] for a in A if len(parts(S,a))>1]))
    if not result['witnesses']['complete'] or result['witnesses']['edges']!=expected: raise ValueError('incomplete quotient witnesses')
    incident=[]
    for i in range(n):
        costs=[]; edges=[e for e in expected if i in e['worlds']]
        for bits in range(1<<len(A)):
            chosen=[a for j,a in enumerate(A) if bits>>j&1]; ids={a['id'] for a in chosen}
            if all(ids.intersection(e['breakers']) for e in edges): costs.append(sum((F(a['cost']) for a in chosen),F(0)))
        incident.append(min(costs) if costs else None)
    lb=max(incident) if all(v is not None for v in incident) else None
    if result['incident_lower']!=(str(lb) if lb is not None else None): raise ValueError('incident cost lower')
    def walk(tree,S,used):
        if tree['worlds']!=list(S): raise ValueError('tree world binding')
        if tree['terminal']:
            r=verify_ball([W[i]['target'] for i in S],problem.symmetry,tree['ball'])
            if r>F(model['tolerance'])**2: raise ValueError('unsafe leaf')
            return F(0)
        a=next(a for a in A if a['id']==tree['action'])
        if a['id'] in used: raise ValueError('repeated action')
        pp=parts(S,a)
        if len(pp)<2 or set(pp)!=set(tree['children']): raise ValueError('reply partition')
        return F(a['cost'])+max(walk(tree['children'][r],tuple(V),used|{a['id']}) for r,V in pp.items())
    if c is None:
        if result['tree'] is not None: raise ValueError('impossible tree')
    elif walk(result['tree'],full,set())!=c: raise ValueError('tree worst cost')
    return dict(passed=True,subsets=len(values),exact_catalog_cost=result['exact_catalog_cost'])
