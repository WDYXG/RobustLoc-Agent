"""No universal two/three-world witness-size assumption."""
from itertools import combinations
from .arithmetic import F
from .information_action import partitions


def witnesses(problem,model,max_size=None):
    W=model['worlds']; out=[]; nodes=0; stop=min(len(W),max_size or len(W))
    for size in range(2,stop+1):
        for S in combinations(range(len(W)),size):
            if any(set(e['worlds'])<=set(S) for e in out): continue
            nodes+=1; ball=problem.enclosing_ball([W[i]['target'] for i in S])
            if F(ball['radius2'])>F(model['tolerance'])**2:
                out.append(dict(worlds=list(S),radius2=ball['radius2'],breakers=[a['id'] for a in model['actions'] if len(partitions(model,S,a))>1]))
    return dict(edges=out,nodes=nodes,complete=stop==len(W),scope='minimal dangerous subsets under adapter quotient radius')
