"""Real planar squared-intensity model; all PR algebra stays in this adapter."""
from itertools import combinations
from ..core.problem import MetricProblem
from ..core.arithmetic import F,dot,det3,sqrt_interval
from ..core.symmetry import apply
from ..core.corruption import budget


def gram(rows): return [[sum(r[i]*r[j] for r in rows) for j in range(3)] for i in range(3)]
def lifted_row(a):
    x,y=map(F,a); return (x*x,2*x*y,y*y)


class PhaseRetrieval(MetricProblem):
    name='real-phase-retrieval'; symmetry='sign'
    def __init__(self,design,min_norm='1/2',max_norm='3'):
        self.design=[list(map(str,a)) for a in design]; self.min_norm=F(min_norm); self.max_norm=F(max_norm)
        if any(len(a)!=2 for a in design) or not design or not 0<=self.min_norm<self.max_norm: raise ValueError('planar design/domain')
    def observe(self,state,nuisance=None):
        if nuisance is not None: raise ValueError('PR adapter assumes known fixed sensing vectors')
        return [(dot(a,state)**2,)*2 for a in self.design]
    def with_measurement(self,parameter): return PhaseRetrieval(self.design+[parameter],self.min_norm,self.max_norm)
    def in_domain(self,x): return len(x)==2 and self.min_norm**2<=dot(x,x)<=self.max_norm**2
    def verify_universal_symmetry(self,T):
        # Quadratic forms for a=e1,e2,e1+e2 span all real symmetric 2x2 forms.
        # Equality of their coefficients proves invariance for EVERY sensing a.
        for a in ((1,0),(0,1),(1,1)):
            at=[sum(F(T[j][i])*a[j] for j in range(2)) for i in range(2)]
            if any(at[i]*at[j]!=a[i]*a[j] for i in range(2) for j in range(2)): return False
        return True
    def certificate(self,q):
        budget(q,len(self.design)); k=max(0,len(self.design)-2*q); rows=[]
        for S in combinations(range(len(self.design)),k):
            G=gram([lifted_row(self.design[i]) for i in S]); tr=sum(G[i][i] for i in range(3)); det=det3(G)
            tau=det/(tr*tr) if tr else F(0)
            if tau<0: raise AssertionError('Gram determinant')
            rows.append(dict(survivors=list(S),gram=[[str(v) for v in r] for r in G],eigen_lower=str(tau)))
        lower=min(sqrt_interval(F(r['eigen_lower'])*self.min_norm**2/2)[0] for r in rows)
        return dict(schema='pr-lifted-annulus-margin-v1',design=self.design,q=q,min_norm=str(self.min_norm),max_norm=str(self.max_norm),
            rows=rows,lower=str(lower),scope='continuous annulus; sufficient global squared-intensity margin in sign quotient; conservative det/trace bound')
    def verify_certificate(self,c,q):
        budget(q,len(self.design)); k=max(0,len(self.design)-2*q)
        if c['schema']!='pr-lifted-annulus-margin-v1' or c['design']!=self.design or c['q']!=q or F(c['min_norm'])!=self.min_norm or F(c['max_norm'])!=self.max_norm: raise ValueError('PR margin contract binding')
        if [r['survivors'] for r in c['rows']]!=[list(S) for S in combinations(range(len(self.design)),k)]: raise ValueError('incomplete 2q survivor coverage')
        bounds=[]
        for row in c['rows']:
            # Consumer derives entries directly from monomials, not producer gram.
            S=row['survivors']; G=[[F(0) for j in range(3)] for i in range(3)]
            for idx in S:
                a,b=map(F,self.design[idx]); v=[a*a,2*a*b,b*b]
                for i in range(3):
                    for j in range(3): G[i][j]+=v[i]*v[j]
            # Cauchy--Binet gives an independent nonnegative determinant.
            B=[lifted_row(self.design[i]) for i in S]
            det=sum(det3([list(v) for v in triple])**2 for triple in combinations(B,3))
            trace=sum(G[i][i] for i in range(3)); tau=det/trace**2 if trace else F(0)
            if row['gram']!=[[str(v) for v in r] for r in G] or F(row['eigen_lower'])!=tau: raise ValueError('PR Gram arithmetic')
            bounds.append(sqrt_interval(tau*self.min_norm**2/2)[0])
        lower=min(bounds)
        if F(c['lower'])!=lower: raise ValueError('PR margin scalar')
        return lower
    def complement_property(self,indices=None):
        I=tuple(range(len(self.design))) if indices is None else tuple(indices)
        def spans(S):
            return any(F(self.design[i][0])*F(self.design[j][1])!=F(self.design[i][1])*F(self.design[j][0]) for i,j in combinations(S,2))
        for k in range(len(I)+1):
            for S in combinations(I,k):
                T=tuple(i for i in I if i not in S)
                if not spans(S) and not spans(T): return dict(passed=False,partition=[list(S),list(T)])
        return dict(passed=True)
    def scaling_certificate(self):
        return dict(schema='pr-origin-scaling-v1',design=self.design,min_norm=str(self.min_norm),max_norm=str(self.max_norm),
            direction=['1','0'],observation_degree=2,metric_degree=1)
    def verify_scaling_certificate(self,c):
        if c['schema']!='pr-origin-scaling-v1' or c['design']!=self.design or self.min_norm!=0 or F(c['min_norm'])!=0 or F(c['max_norm'])!=self.max_norm: raise ValueError('origin sequence outside declared domain')
        u=list(map(F,c['direction'])); n=dot(u,u)
        if not 0<n<=self.max_norm**2 or c['observation_degree']!=2 or c['metric_degree']!=1: raise ValueError('scaling exponents/direction')
        if not any(lo>0 for lo,hi in self.observe(u)): raise ValueError('zero-direction signal is exact ambiguity, not this scaling certificate')
        # Model-owned polynomial identity: (a dot (t*u))^2=t^2(a dot u)^2;
        # the sign quotient distance to0 is t||u|| for every t>=0.
        return True


def acquisition_upper(problem,offers,q,epsilon,tolerance):
    """Response-uniform sufficient design. Future errors share global q and E."""
    if F(epsilon)<0 or F(tolerance)<=0 or len({o['id'] for o in offers})!=len(offers) or any(F(o['cost'])<=0 for o in offers): raise ValueError('acquisition contract')
    bundles=[(sum((F(o['cost']) for o in S),F(0)),S) for k in range(len(offers)+1) for S in combinations(offers,k)]
    bundles.sort(key=lambda z:(z[0],len(z[1]),[o['id'] for o in z[1]])); nodes=0
    for cost,S in bundles:
        nodes+=1; final=PhaseRetrieval(problem.design+[o['vector'] for o in S],problem.min_norm,problem.max_norm)
        c=final.certificate(q); b=final.verify_certificate(c,q)
        if b and 2*F(epsilon)/b<=F(tolerance):
            return dict(cost_upper=str(cost),actions=[o['id'] for o in S],certificate=c,radius_upper=str(2*F(epsilon)/b),nodes=nodes,
                scope='uniform over arbitrary future corruptions with a SINGLE total q and clean-noise E; existence bound, candidate search may abstain')
    return dict(cost_upper=None,nodes=nodes,reason='no sufficient design found; not physical impossibility')


def verify_acquisition(problem,offers,q,epsilon,tolerance,upper):
    chosen=upper['actions']
    if len(set(chosen))!=len(chosen): raise ValueError('duplicate measurement purchase')
    O=[next(o for o in offers if o['id']==i) for i in chosen]
    final=PhaseRetrieval(problem.design+[o['vector'] for o in O],problem.min_norm,problem.max_norm)
    b=final.verify_certificate(upper['certificate'],q)
    cost=sum((F(o['cost']) for o in O),F(0))
    if cost!=F(upper['cost_upper']) or b<=0 or 2*F(epsilon)/b!=F(upper['radius_upper']) or F(upper['radius_upper'])>F(tolerance): raise ValueError('unsafe acquisition')
    return final
