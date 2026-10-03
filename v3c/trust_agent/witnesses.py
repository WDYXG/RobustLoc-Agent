"""Find exact continuous-world lower witnesses from public metadata, never truth."""
from fractions import Fraction as F
from copy import deepcopy
from itertools import combinations
from v3.certified_agent.decoder import solve
from v3b.assumption_agent.verifier import root
from .verifier import feasible_world,verify_witness


def transform(p,R,t): return [str(sum(F(R[k][j])*F(p[j]) for j in range(2))+F(t[k])) for k in range(2)]


def layouts(obs):
    values=[{i:transform(p,f['R'],f['t']) for i,p in obs['nominal'].items()} for f in obs['forecast_frames']]
    for report in obs['reports']:
        p=deepcopy(obs['nominal']); p.update({a['anchor']:a['centre'] for a in report['points']}); values.append(p)
    # Align advertised shape to a received single absolute point, without claiming it is true.
    for a in obs['hard_refs'][:1]:
        delta=[str(F(x)-F(y)) for x,y in zip(a['centre'],obs['nominal'][a['anchor']])]
        values.append({i:transform(p,[['1','0'],['0','1']],delta) for i,p in obs['nominal'].items()})
    return values


def reflect(point,a,b):
    z=list(map(F,point)); u=list(map(F,a)); v=[F(x)-y for x,y in zip(b,u)]
    den=sum(x*x for x in v)
    if not den: return list(point)
    dot=sum((x-y)*k for x,y,k in zip(z,u,v))
    return [str(2*(u[k]+dot*v[k]/den)-z[k]) for k in range(2)]


def find(obs,cfg):
    measured={m['anchor'] for m in obs['measurements']}; hard={a['anchor']:a['centre'] for a in obs['hard_refs'] if F(a['radius'])==0 and a['anchor'] in measured}
    for p in layouts(obs):
        # Unmeasured fixed frame points must remain fixed; they do not add range equations.
        for a in obs['hard_refs']:
            if a['anchor'] not in measured: p[a['anchor']]=a['centre']
        model=dict(anchors=[p[m['anchor']] for m in obs['measurements']],weights=[m['weight'] for m in obs['measurements']],
                   measurements=[m['value'] for m in obs['measurements']],domain=obs['domain'],q_budget=obs['q'],
                   epsilon=obs['epsilon'],error_tolerance=obs['tolerance'])
        candidate=solve(model,cfg); A=dict(target=candidate['position'],positions=p)
        if not feasible_world(obs,A): continue
        moves=[]
        if not hard:
            for t in (['1','0'],['-1','0'],['0','1']): moves.append(lambda z,t=t:transform(z,[['1','0'],['0','1']],t))
            first=next(iter(obs['nominal']))
            for other in layouts(obs):
                for R in ([['1','0'],['0','1']],[['1','0'],['0','-1']],[['-1','0'],['0','1']],[['0','-1'],['1','0']]):
                    rp=transform(p[first],R,['0','0']); t=[str(F(a)-F(b)) for a,b in zip(other[first],rp)]
                    if all(transform(p[i],R,t)==other[i] for i in measured):
                        moves.append(lambda z,R=R,t=t:transform(z,R,t))
        if len(hard)==1:
            a=next(iter(hard.values())); moves.append(lambda z,a=a:[str(2*F(x)-F(y)) for x,y in zip(a,z)])
            for sign in ('1','-1'):
                R=[['24/25',str(-F(sign)*F('7/25'))],[str(F(sign)*F('7/25')),'24/25']]
                ra=transform(a,R,['0','0']); t=[str(F(x)-F(y)) for x,y in zip(a,ra)]
                moves.append(lambda z,R=R,t=t:transform(z,R,t))
        for a,b in combinations(hard.values(),2): moves.append(lambda z,a=a,b=b:reflect(z,a,b))
        for move in moves:
            pp={i:(move(a) if i in measured and i not in hard else a) for i,a in p.items()}
            B=dict(target=move(A['target']),positions=pp)
            if not feasible_world(obs,B): continue
            d2=sum((F(x)-F(y))**2 for x,y in zip(A['target'],B['target'])); lo=root(d2)[0]
            if not lo: continue
            w=dict(worlds=[A,B],diameter_lower=str(lo),minimax_radius_lower=str(lo/2),
                   scope='exact feasible continuous worlds; not diameter of a finite hypothesis catalog')
            try: bound=verify_witness(obs,w)
            except ValueError: continue
            if bound>F(obs['tolerance']): return w
    return None
