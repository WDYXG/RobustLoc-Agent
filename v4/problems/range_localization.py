"""Compatibility adapter: frozen range mathematics reused, not copied."""
from ..core.problem import MetricProblem
from ..core.arithmetic import F,distance2,sqrt_interval
from ..core.symmetry import apply
from ..core.decision import analyze
from v3b.assumption_agent.certificates import build
from v3b.assumption_agent.verifier import verify_margin
from v3d.minimal_trust.worlds import validate_restriction,translated_restriction
from v3d.minimal_trust.subsets import uniform_upper,recover_subsets
from v3d.minimal_trust.subset_verify import verify_uniform_upper,verify_subset_cover


class RangeLocalization(MetricProblem):
    name='range-localization'; symmetry='identity'
    def __init__(self,anchors=None,domain=('-2','2','-2','2')):
        self.anchors=[list(map(str,a)) for a in (anchors or [(-4,-3),(4,-3),(4,3),(-4,3),(0,5)])]; self.domain=list(map(str,domain))
    def observe(self,state,nuisance=None):
        p=self.anchors if nuisance is None else nuisance
        return [sqrt_interval(distance2(state,a)) for a in p]
    def with_measurement(self,parameter): return RangeLocalization(self.anchors+[parameter],self.domain)
    def in_domain(self,x):
        d=list(map(F,self.domain)); return len(x)==2 and d[0]<=F(x[0])<=d[1] and d[2]<=F(x[1])<=d[3]
    def verify_universal_symmetry(self,T):
        # Anchored coordinates, with arbitrary known anchor designs. Testing
        # zero and the two basis anchors in the polynomial identity forces I.
        for p in ((0,0),(1,0),(0,1)):
            for x in ((0,0),(1,0),(0,1),(1,1)):
                if distance2(apply(T,x),p)!=distance2(x,p): return False
        return True
    def certificate(self,q):
        return build(dict(anchors=self.anchors,radii=['0']*len(self.anchors),weights=['1']*len(self.anchors),domain=self.domain),q)
    def verify_certificate(self,c,q):
        expected=dict(anchors=self.anchors,radii=['0']*len(self.anchors),weights=['1']*len(self.anchors),domain=self.domain)
        if c['data']!=expected or c['q']!=q: raise ValueError('range margin binding')
        return verify_margin(c)


def legacy_model(obs,model,complete):
    validate_restriction(obs,model)
    return dict(worlds=model['worlds'],actions=model['actions'],tolerance=model['tolerance'],
        semantics='complete-finite-prior' if complete else 'verified-restriction')


def continuous_bounds(obs,cfg,budget,node_limit=None):
    old_model=translated_restriction(obs,cfg); model=legacy_model(obs,old_model,False)
    upper=uniform_upper(obs,node_limit)
    if upper['cost_upper'] is not None: verify_uniform_upper(obs,upper)
    result=analyze(RangeLocalization(),model,budget,upper['cost_upper'])
    return dict(model=model,result=result,upper=upper)


def delivered_cover(obs,cfg):
    c=recover_subsets(obs,cfg)
    if c['certified']: verify_subset_cover(obs,c)
    return c
