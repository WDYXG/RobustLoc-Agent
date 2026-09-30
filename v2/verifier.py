"""Independent numerical algebra/certificate verifier. No automatic theorem proof."""
from itertools import combinations
import numpy as np

def independent_margin(position,anchors,weights,k):
    delta=np.asarray(position)-anchors; radius=np.linalg.norm(delta,axis=1)
    if np.any(radius<=1e-12): raise ValueError('At anchor')
    rows=delta/radius[:,None]*np.sqrt(weights)[:,None]
    size=len(rows)-k
    if size<2: return 0.
    return float(min(np.linalg.eigvalsh(rows[list(ids)].T@rows[list(ids)])[0] for ids in combinations(range(len(rows)),size)))

def check_estimate(problem,result,tolerance=1e-7):
    if result['status']=='abstain': return dict(verified=True,kind='abstention',guarantee=False)
    x=np.array(result['position']); radial=np.linalg.norm(x-problem.prior_center)
    residual=np.sqrt(problem.weights)*(np.linalg.norm(x-problem.anchors,axis=1)-problem.distances)
    norm=np.sqrt(np.sort(residual**2)[:len(residual)-problem.q].sum())
    alpha=independent_margin(x,problem.anchors,problem.weights,2*problem.q)
    separation=np.linalg.norm(problem.prior_center-problem.anchors,axis=1)-problem.prior_radius
    L=float(np.sqrt(np.sum(problem.weights/separation**2)))
    beta=float(np.sqrt(max(alpha,0.))-L*(problem.prior_radius+radial))
    feasible=norm<=problem.epsilon+tolerance
    expected=(2*problem.epsilon+tolerance)/beta if feasible and beta>0 else None
    checks=[radial<=problem.prior_radius+1e-10,np.isclose(norm,result['trimmed_norm']),np.isclose(alpha,result['alpha_2q'],atol=1e-9),np.isclose(beta,result['beta'],atol=1e-9),result['feasible']==bool(feasible)]
    checks.append((expected is None and result['conditional_error_bound'] is None) or (expected is not None and np.isclose(expected,result['conditional_error_bound'])))
    if result['mode']=='feasible_geometry': checks.extend([feasible,beta>0])
    return dict(verified=bool(all(checks)),kind='conditional local certificate' if expected is not None else 'uncertified estimate',guarantee=expected is not None,independent_beta=beta,independent_trimmed_norm=float(norm))
