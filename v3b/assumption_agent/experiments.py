"""Fixed conjecture / proof / counterexample / numerical-check ledger."""
from fractions import Fraction as F
from copy import deepcopy
import random
from v2.global_stability.exact import point_upper,point,distance2,encode
from .certificates import build,frontier
from .verifier import verify_margin,root
from .simulator import CIRCLE


def theory_tasks(cfg):
    data=dict(anchors=deepcopy(CIRCLE),weights=['1']*8,domain=['-1','1','-1','1'],radii=['1/10']*8)
    cert=build(data,0); lower=verify_margin(cert)
    x=[F(0),F(0)]; z=[F('1/10'),F(0)]
    p=[point(a) for a in CIRCLE]; pp=[(a[0]+F('1/10'),a[1]) for a in p]
    squared_A=[distance2(a,x) for a in p]; squared_B=[distance2(a,z) for a in pp]
    assert squared_A==squared_B and lower>0
    translation=encode(dict(id='C1',status='refuted',claim='unknown-anchor error <=2epsilon/shared-map-margin',
        known_mechanism='translation gauge',x=x,z=z,p=p,p_prime=pp,radii=data['radii'],domain=data['domain'],
        epsilon='0',q=0,range2_A=squared_A,range2_B=squared_B,positive_uniform_lower=lower,
        certificate=cert,position_difference2=distance2(x,z)))
    near=dict(anchors=[['-5','1/10'],['-3','-1/10'],['3','1/10'],['5','-1/10']],weights=['1']*4,
              radii=['1/10']*4,domain=data['domain'])
    nominal=dict(near,radii=['0']*4); bn=verify_margin(build(nominal,0)); bc=build(near,0)
    actual=[(F(a[0]),F(0)) for a in near['anchors']]
    u=[F(0),F('1/2')]; v=[F(0),F('-1/2')]
    upper,equal=point_upper(actual,[F(1)]*4,u,v,0)
    assert bn>0 and upper==0
    collapsed=encode(dict(id='C2',status='refuted',claim='positive nominal margin survives all allowed anchor balls',
        nominal=near,actual_anchors=actual,x=u,z=v,upper=upper,equal_coordinates=equal,
        nominal_lower=bn,certificate=bc))
    rng=random.Random(cfg['development_seed']); rows=[]
    for radius in cfg['perturbation_radii']:
        for q in range(3):
            dd=dict(data,radii=[radius]*8); c=build(dd,q); b=verify_margin(c)
            minima=None; violations=0
            for trial in range(cfg['perturbation_trials']):
                a=[(p0[0]+F(radius)*F(rng.randint(-500,500),1000),
                    p0[1]+F(radius)*F(rng.randint(-500,500),1000)) for p0 in p]
                xx=[F(rng.randint(-1000,1000),1000) for _ in range(2)]
                zz=[F(rng.randint(-1000,1000),1000) for _ in range(2)]
                if xx==zz: zz[0]+=F('1/1000000')
                ub,_=point_upper(a,[F(1)]*8,xx,zz,q)
                if ub<b: violations+=1
                minima=ub if minima is None else min(minima,ub)
            rows.append(dict(radius=radius,q=q,lower=str(b),sampled_secant_upper_min=str(minima),
                             trials=cfg['perturbation_trials'],violations=violations,certificate=c,
                             label='numerically-supported',scope='sample checks can refute, never prove a lower bound'))
    obs=dict(data,q_max=3,epsilon_max='1/25',error_tolerance='2/5')
    assumption_frontiers=[]
    for domain in (['-1','1','-1','1'],['-8','8','-8','8']):
        for radius in ('0','1/100','1/10','4/25'):
            f=frontier(dict(obs,domain=domain,radii=[radius]*8))
            assumption_frontiers.append(dict(domain=domain,radius=radius,frontier=f))
    ledger=[dict(id='K1',status='known',claim='scatter, support union, reverse triangle, perturbation and set membership foundations'),
            dict(id='T1',status='proved-in-project',claim='shared-map derivative perturbation',proof='THEORY.md T1'),
            dict(id='T2',status='proved-in-project',claim='robust weighted-scatter lower certificate',proof='THEORY.md T2'),
            dict(id='T3',status='proved-in-project',claim='model-error inflated recovery bound',proof='THEORY.md T3'),
            dict(id='T4',status='proved-in-project',claim='sufficient conditional assumption frontier',proof='THEORY.md T4'),
            dict(id='C1',status='refuted',claim=translation['claim']),dict(id='C2',status='refuted',claim=collapsed['claim']),
            dict(id='N1',status='numerically-supported',claim='no violation in fixed perturbed secant checks'),
            dict(id='H1',status='conjectured',claim='heterogeneous information yields more certification per cost than range-only',
                 adjudication='evaluate pooled and per-scenario results; no universal claim')]
    return dict(ledger=ledger,counterexamples=[translation,collapsed],perturbation=rows,frontiers=assumption_frontiers)
