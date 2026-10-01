"""Reuse frozen v2 bounds; fast certificate producer + independent consumer."""
from copy import deepcopy
from fractions import Fraction as F
from functools import lru_cache
from itertools import combinations
import json
import numpy as np
from scipy.spatial import ConvexHull,QhullError
from v2.global_stability.certificate import build
from v2.global_stability.verifier import verify_certificate,verify_upper
from v2.global_stability.exact import dataset,point,point_upper,encode,sqrt_interval,distance2

def data_from(obs):
    return dict(anchors=obs['anchors'],weights=obs['weights'],domain=obs['domain'])

@lru_cache(maxsize=8192)
def _geometry(serialized,q):
    data=json.loads(serialized)
    certificate=build(data,q,divisions=1,delta='1',max_leaves=1)
    verified=verify_certificate(certificate)
    anchors,weights,domain=dataset(data)
    pts=[point([domain[0],domain[2]]),point([domain[0],domain[3]]),
         point([domain[1],domain[2]]),point([domain[1],domain[3]]),
         point([(domain[0]+domain[1])/2,domain[2]]),
         point([(domain[0]+domain[1])/2,domain[3]])]
    candidates=[]
    for x,z in combinations(pts,2):
        ub,equal=point_upper(anchors,weights,x,z,q)
        candidates.append(encode(dict(x=x,z=z,upper=ub,equal_coordinates=equal)))
    upper=min(candidates,key=lambda row:F(row['upper']))
    verify_upper(data,q,upper)
    return dict(certificate=certificate,verification=verified,lower=verified['certified_lower'],
                upper=upper['upper'],upper_witness=upper,
                interpretation='certified' if F(verified['certified_lower'])>0 else
                    ('zero-margin-witness' if F(upper['upper'])==0 else 'not-certified'))

def geometry(data,q): return deepcopy(_geometry(json.dumps(data,sort_keys=True),q))

def profile(obs,max_q=2):
    data=data_from(obs); budget=obs.get('q_budget')
    top=max(max_q,budget if budget is not None else 0)
    tau=2*F(obs['epsilon'])/F(obs['error_tolerance'])
    rows=[]
    for q in range(top+1):
        g=geometry(data,q)
        rows.append(dict(q=q,lower=g['lower'],upper=g['upper'],interpretation=g['interpretation']))
    capacity=max((r['q'] for r in rows if F(r['lower'])>=tau),default=None)
    return dict(rows=rows,threshold=str(tau),certified_capacity_lower=capacity,
                profile_max_q=top,scope='conditional capacity lower bound over computed q; actual q not inferred')

def features(obs):
    p=np.array([[float(F(v)) for v in x] for x in obs['anchors']]); w=np.array([float(F(v)) for v in obs['weights']])
    d=[float(F(v)) for v in obs['domain']]; centre=np.array([(d[0]+d[1])/2,(d[2]+d[3])/2])
    u=centre-p; r=np.linalg.norm(u,axis=1); valid=r>1e-12
    J=np.zeros_like(u); J[valid]=u[valid]/r[valid,None]
    eigen=np.linalg.eigvalsh(J.T@(w[:,None]*J)); condition=eigen[1]/max(eigen[0],1e-12)
    angles=np.sort(np.mod(np.arctan2(u[valid,1],u[valid,0]),2*np.pi))
    coverage=1-float(np.max(np.diff(np.r_[angles,angles[0]+2*np.pi])))/(2*np.pi) if len(angles)>1 else 0.
    hull_coverage=0.
    try:
        hull=ConvexHull(p)
        corners=np.array([[d[0],d[2]],[d[0],d[3]],[d[1],d[2]],[d[1],d[3]]])
        hull_coverage=float(np.mean(np.all(corners@hull.equations[:,:2].T+hull.equations[:,2]<=1e-9,axis=1)))
    except QhullError: pass
    q=obs.get('q_budget')
    values=[float(eigen[0]),float(np.log1p(condition)),coverage,hull_coverage,
            float(len(p)),float(q if q is not None else -1),float(np.std(p[:,1])),float(np.std(p[:,0]))]
    return dict(names=['centre_lambda_min','log1p_condition','circular_angular_coverage',
        'hull_domain_corner_coverage','reporter_count','declared_q_budget','y_spread','x_spread'],
        values=values,reference_point=centre.tolist(),centre_at_anchor=bool(np.any(~valid)),
        estimated_corruption_advisory=obs.get('estimated_corruption'),
        scope='diagnostic reference geometry, not truth Jacobian or certification')

def residual_certificate(obs,candidate,q):
    """Producer-independent exact interval feasibility: drop at most q ranges."""
    data=data_from(obs); anchors,weights,domain=dataset(data); x=point(candidate)
    if not(domain[0]<=x[0]<=domain[1] and domain[2]<=x[1]<=domain[3]):
        return dict(feasible=False,reason='candidate-outside-declared-domain')
    values=[]
    for i,(p,w,y) in enumerate(zip(anchors,weights,obs['measurements'])):
        lo,hi=sqrt_interval(distance2(x,p)); y=F(y)
        values.append((w*max(abs(lo-y),abs(hi-y))**2,i))
    selected=sorted(values)[:max(0,len(anchors)-q)]
    norm2=sum(v for v,i in selected); eps=F(obs['epsilon'])
    return dict(feasible=norm2<=eps*eps,clean_indices=[i for v,i in selected],
        norm2_upper=str(norm2),norm_upper=str(sqrt_interval(norm2)[1]),
        omitted_count=len(anchors)-len(selected),epsilon=str(eps),
        scope='there exists a q-sparse residual explanation; actual bad labels unknown')
