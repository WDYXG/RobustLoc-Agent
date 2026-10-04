"""Contract boundary: observations, metric, domain and margin are adapter-owned."""
from typing import Protocol
from .geometry import enclosing_ball
from .symmetry import metric2
from .corruption import residual_interval2
from .arithmetic import F


class InverseProblem(Protocol):
    name: str
    symmetry: str
    def observe(self,state,nuisance=None): ...
    def state_distance2(self,x,z): ...
    def equivalent(self,x,z): ...
    def in_domain(self,x): ...
    def feasible_worlds(self,transcript,catalog): ...
    def certificate(self,q): ...
    def verify_certificate(self,certificate,q): ...
    def verify_universal_symmetry(self,transform): ...


class MetricProblem:
    def state_distance2(self,x,z): return metric2(x,z,self.symmetry)
    def equivalent(self,x,z): return self.state_distance2(x,z)==0
    def enclosing_ball(self,points): return enclosing_ball(points,self.symmetry)
    def feasible_worlds(self,transcript,catalog):
        """Filter a declared finite catalog; never claim to enumerate a continuum."""
        confirmed=[]; unresolved=[]
        for w in catalog:
            if not self.in_domain(w['target']): continue
            lo,hi=residual_interval2(self.observe(w['target'],w.get('nuisance')),transcript['values'],transcript['q'])
            if hi<=F(transcript['epsilon'])**2: confirmed.append(w)
            elif lo<=F(transcript['epsilon'])**2: unresolved.append(w)
        return dict(confirmed=confirmed,unresolved=unresolved,scope='finite supplied catalog filter only; no continuous completeness claim')
