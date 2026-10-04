"""Independent verifier: Helly threshold predicates and bottom-up subset recurrence."""
from fractions import Fraction as F
from itertools import combinations
import json


def response_key(x): return json.dumps(x,sort_keys=True,separators=(',',':'))
def d2(a,b): return sum((F(x)-F(y))**2 for x,y in zip(a,b))


def dangerous(points,tol):
    """Independent of producer's enclosing-circle enumeration."""
    t=F(tol)**2
    sides=[d2(a,b) for a,b in combinations(points,2)]
    if any(s>4*t for s in sides): return True
    if len(points)!=3: return False
    # Only an acute triangle needs its circumcircle; an obtuse/right triangle
    # has the longest side as a diameter, already checked above.
    if max(sides)*2>=sum(sides): return False
    a,b,c=[list(map(F,p)) for p in points]
    cross=(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    return bool(cross and sides[0]*sides[1]*sides[2]>4*cross**2*t)


def small_radius2(points):
    sides=[d2(a,b) for a,b in combinations(points,2)]
    if len(points)==2 or max(sides)*2>=sum(sides): return max(sides)/4
    a,b,c=[list(map(F,p)) for p in points]
    cross=(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    return sides[0]*sides[1]*sides[2]/(4*cross**2)


def verify(model,result):
    W=model['worlds']; A=model['actions']; n=len(W); m=len(A); tol=model['tolerance']
    if F(tol)<0 or any(len(w['target'])!=2 for w in W): raise ValueError('radius/planar model')
    if not n or len({w['id'] for w in W})!=n: raise ValueError('invalid world set')
    if len({a['id'] for a in A})!=m or any(F(a['cost'])<=0 or set(a['responses'])!={w['id'] for w in W} for a in A):
        raise ValueError('invalid action contract')
    replies=[[response_key(a['responses'][w['id']]) for w in W] for a in A]
    E=[tuple(H) for k in (2,3) for H in combinations(range(n),k) if dangerous([W[i]['target'] for i in H],tol)]
    recorded=[tuple(e['worlds']) for e in result['witnesses']]
    if E!=recorded: raise ValueError('missing or invalid ambiguity witness')
    for e,H in zip(result['witnesses'],E):
        if e['breakers']!=[a for a in range(m) if len({replies[a][i] for i in H})>1]: raise ValueError('response/witness binding')
        if F(e['radius2'])!=small_radius2([W[i]['target'] for i in H]): raise ValueError('witness radius')
    def covers(S,edges): return all(any(len({replies[a][i] for i in H})>1 for a in S) for H in edges)
    def min_cover(edges):
        values=[]
        for bits in range(1<<m):
            S=[a for a in range(m) if bits>>a&1]
            if covers(S,edges): values.append(sum((F(A[a]['cost']) for a in S),F(0)))
        return min(values) if values else None
    def same(recorded,cost): return recorded==(str(cost) if cost is not None else None)
    for field,edges in [('pair_batch',[H for H in E if len(H)==2]),('hypergraph_batch',E)]:
        c=min_cover(edges)
        if not same(result[field]['cost'],c): raise ValueError('batch optimum')
        if c is not None:
            ids=result[field]['actions']; selected=[next(i for i,a in enumerate(A) if a['id']==x) for x in ids]
            if len(set(ids))!=len(ids) or not covers(selected,edges) or sum((F(A[a]['cost']) for a in selected),F(0))!=c: raise ValueError('batch plan')
    inc=[min_cover([H for H in E if i in H]) for i in range(n)]
    lb=max(inc) if all(x is not None for x in inc) else None
    if not same(result['incident_lower'],lb): raise ValueError('adaptive incident lower bound')
    if result['pair_count']!=sum(len(H)==2 for H in E) or result['triple_count']!=sum(len(H)==3 for H in E): raise ValueError('witness counts')
    # Strict partitions make child states smaller: remaining-action state is
    # unnecessary here; an already used test is constant on each descendant.
    values={}; states=0
    for size in range(1,n+1):
        for S in combinations(range(n),size):
            states+=1
            if not any(set(H)<=set(S) for H in E): values[S]=F(0); continue
            candidates=[]
            for a in range(m):
                parts={}
                for i in S: parts.setdefault(replies[a][i],[]).append(i)
                if len(parts)<2: continue
                child=[values[tuple(V)] for V in parts.values()]
                if all(v is not None for v in child): candidates.append(F(A[a]['cost'])+max(child))
            values[S]=min(candidates) if candidates else None
    optimum=values[tuple(range(n))]
    if not same(result['adaptive_cost'],optimum): raise ValueError('adaptive optimum')
    if result['adaptive_status']!=('finite' if optimum is not None else 'infinite'): raise ValueError('infinity status')
    def tree_cost(tree,S,used):
        if tree['worlds']!=list(S): raise ValueError('tree world partition')
        if tree['terminal']:
            c=tree['circle']; r=F(c['radius2'])
            if r<0 or r>F(tol)**2 or any(d2(c['centre'],W[i]['target'])>r for i in S): raise ValueError('unsafe tree leaf')
            return F(0)
        a=next(i for i,a in enumerate(A) if a['id']==tree['action'])
        if a in used: raise ValueError('repeated action')
        parts={}
        for i in S: parts.setdefault(replies[a][i],[]).append(i)
        if len(parts)<2 or set(parts)!=set(tree['children']): raise ValueError('tree reply coverage')
        return F(A[a]['cost'])+max(tree_cost(tree['children'][r],tuple(V),used|{a}) for r,V in parts.items())
    if optimum is not None and tree_cost(result['optimal_tree'],tuple(range(n)),set())!=optimum: raise ValueError('tree cost')
    if optimum is None and result['optimal_tree'] is not None: raise ValueError('infeasible tree')
    return dict(passed=True,independent_states=states,adaptive_cost=result['adaptive_cost'],witnesses=len(E),
                scope='independent Helly predicate, exhaustive batch costs, bottom-up minimax and full tree traversal')
