"""Project proposal: feasibility-first residual/geometry selection (FFRG).

Trimming and subset fitting are known. Conditional certificate is P2, not a
global solver/completeness/novelty guarantee. Inputs contain no truth or labels.
"""
from dataclasses import dataclass
from itertools import combinations
import numpy as np
from scipy.optimize import least_squares
from .geometry import beta,point_margin

@dataclass(frozen=True)
class Problem:
    anchors: np.ndarray
    distances: np.ndarray
    weights: np.ndarray
    q: int
    epsilon: float
    prior_center: np.ndarray
    prior_radius: float

def residual_score(position,problem):
    residual=np.sqrt(problem.weights)*(np.linalg.norm(position-problem.anchors,axis=1)-problem.distances)
    ids=np.argsort(residual**2,kind='stable')[:len(residual)-problem.q]
    return float(np.linalg.norm(residual[ids])),ids.tolist()

def candidate_pool(problem):
    """Enumerate inlier subsets; finite local searches, explicitly not exhaustive positions."""
    n=len(problem.distances); c=problem.prior_center; R=problem.prior_radius
    starts=[c]+[c+R*.75*np.array(v) for v in [(1,0),(-1,0),(0,1),(0,-1)]]
    pool=[]; failures=0
    for ids in combinations(range(n),n-problem.q):
        ix=np.array(ids)
        def fun(x): return np.sqrt(problem.weights[ix])*(np.linalg.norm(x-problem.anchors[ix],axis=1)-problem.distances[ix])
        for start in starts:
            try:
                fit=least_squares(fun,start,bounds=(c-R,c+R),max_nfev=120)
                if not fit.success or not np.isfinite(fit.x).all(): failures+=1; continue
                # A square bounding box does not establish membership in the prior ball.
                if np.linalg.norm(fit.x-c)>R+1e-10: continue
                if not any(np.linalg.norm(fit.x-p)<1e-7 for p in pool): pool.append(fit.x)
            except (ValueError,FloatingPointError,np.linalg.LinAlgError): failures+=1
    return pool,failures

def select(problem,pool,mode='feasible_geometry',tolerance=1e-7):
    evaluations=[]
    for point in pool:
        if not np.isfinite(point).all() or np.linalg.norm(point-problem.prior_center)>problem.prior_radius+1e-10: continue
        residual,ids=residual_score(point,problem)
        try:
            alpha=point_margin(point,problem.anchors,problem.weights,2*problem.q)['alpha']
            certificate_beta=beta(point,problem.prior_center,problem.prior_radius,problem.anchors,problem.weights,problem.q)
        except ValueError: continue
        evaluations.append(dict(position=np.asarray(point).tolist(),trimmed_norm=residual,retained_indices=ids,alpha_2q=alpha,beta=certificate_beta,feasible=residual<=problem.epsilon+tolerance))
    if mode=='feasible_geometry':
        eligible=[r for r in evaluations if r['feasible'] and r['beta']>0]
        key=lambda r:(-r['beta'],r['trimmed_norm'])
    elif mode=='residual_only':
        eligible=evaluations; key=lambda r:r['trimmed_norm']
    elif mode=='unguarded_ratio':
        eligible=evaluations; key=lambda r:r['trimmed_norm']**2/max(r['alpha_2q'],1e-12)
    else: raise ValueError('Unknown selection mode')
    if not eligible:
        return dict(status='abstain',reason='no feasible positive-certificate candidate in finite search',mode=mode,candidates=evaluations)
    chosen=min(eligible,key=key)
    bound=(2*problem.epsilon+tolerance)/chosen['beta'] if chosen['feasible'] and chosen['beta']>0 else None
    return dict(status='estimate',mode=mode,**chosen,conditional_error_bound=bound,
                conditions='true point in stated prior ball; <=q corruptions; fixed exact anchors and weights; inlier whitened norm<=epsilon',
                candidates=evaluations)
