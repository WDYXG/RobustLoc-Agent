"""One minimax engine and one budget decision for both inverse problems."""
from functools import lru_cache
from itertools import combinations
from .arithmetic import F
from .world import validate_model
from .information_action import partitions
from .ambiguity import witnesses


def diagnose(lower,upper,budget,lower_infinite=False):
    B=F(budget)
    if B<0: raise ValueError('negative budget')
    if lower_infinite:
        if upper is not None: raise ValueError('contradictory bounds')
        return dict(cost_lower=None,cost_upper=None,lower_infinite=True,gap=None,relative_gap=None,state='provably-insufficient-information-budget')
    L=F(lower); U=F(upper) if upper is not None else None
    if L<0 or (U is not None and U<L): raise ValueError('reversed interval')
    state='provably-insufficient-information-budget' if L>B else ('certifiably-recoverable' if U is not None and U<=B else 'unresolved-certificate-or-search-gap')
    return dict(cost_lower=str(L),cost_upper=str(U) if U is not None else None,lower_infinite=False,
        gap=str(U-L) if U is not None else None,relative_gap=str((U-L)/U) if U else ('0' if U==0 else None),state=state)


def analyze(problem,model,budget_value,external_upper=None):
    validate_model(model); W=model['worlds']; A=model['actions']; nodes=0
    @lru_cache(None)
    def solve(S,unused):
        nonlocal nodes
        nodes+=1; ball=problem.enclosing_ball([W[i]['target'] for i in S])
        if F(ball['radius2'])<=F(model['tolerance'])**2:
            return F(0),dict(terminal=True,worlds=list(S),ball=ball)
        best=None; tree=None
        for j in unused:
            a=A[j]; parts=partitions(model,S,a)
            if len(parts)<2: continue
            children={r:solve(tuple(V),tuple(k for k in unused if k!=j)) for r,V in sorted(parts.items())}
            if any(v[0] is None for v in children.values()): continue
            cost=F(a['cost'])+max(v[0] for v in children.values())
            if best is None or cost<best:
                best=cost; tree=dict(terminal=False,worlds=list(S),action=a['id'],children={r:v[1] for r,v in children.items()})
        return best,tree
    value,tree=solve(tuple(range(len(W))),tuple(range(len(A))))
    witness=witnesses(problem,model)
    def cover(edges):
        costs=[]
        for size in range(len(A)+1):
            for choices in combinations(A,size):
                ids={a['id'] for a in choices}
                if all(ids.intersection(e['breakers']) for e in edges): costs.append(sum((F(a['cost']) for a in choices),F(0)))
        return min(costs) if costs else None
    incident=[cover([e for e in witness['edges'] if i in e['worlds']]) for i in range(len(W))]
    lower=max(incident) if all(v is not None for v in incident) else None
    upper=value if model['semantics']=='complete-finite-prior' else (F(external_upper) if external_upper is not None else None)
    return dict(exact_catalog_cost=str(value) if value is not None else None,tree=tree,
        interval=diagnose(value or 0,upper,budget_value,lower_infinite=value is None),
        incident_lower=str(lower) if lower is not None else None,witnesses=witness,
        nodes=nodes,semantics=model['semantics'],problem=problem.name)
