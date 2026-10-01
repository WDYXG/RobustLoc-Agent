"""Observation-only bounded local candidate search; not a complete decoder."""
from fractions import Fraction as F
import numpy as np
from scipy.optimize import least_squares
from .certificates import residual_certificate

FORBIDDEN={'truth','bad_indices','actual_q','noise','private','scenario','contract_valid'}

def solve(obs,cfg,trim=True):
    if FORBIDDEN.intersection(obs): raise ValueError('Private evaluator fields forbidden in decoder')
    p=np.array([[float(F(v)) for v in x] for x in obs['anchors']]); y=np.array([float(F(v)) for v in obs['measurements']])
    w=np.sqrt(np.array([float(F(v)) for v in obs['weights']]))
    d=[float(F(v)) for v in obs['domain']]; lo=np.array([d[0],d[2]]); hi=np.array([d[1],d[3]])
    q=obs.get('q_budget'); q=q if q is not None else 0
    scale=max(float(F(obs['epsilon']))/np.sqrt(len(p)),1e-4)
    residual=lambda x:w*(np.linalg.norm(x-p,axis=1)-y)
    jac=lambda x: w[:,None]*(x-p)/np.maximum(np.linalg.norm(x-p,axis=1)[:,None],1e-12)
    candidates=[]; failures=[]
    for start in cfg['solver_starts']:
        x0=np.clip(np.array([float(F(v)) for v in start]),lo+1e-8,hi-1e-8)
        try:
            result=least_squares(residual,x0,jac=jac,bounds=(lo,hi),loss='cauchy',
                f_scale=scale,max_nfev=cfg['solver_max_nfev'])
            x=result.x
            if not result.success: failures.append(result.message)
            candidates.append(x.copy())
            if trim and q<len(p):
                for _ in range(4):
                    idx=np.argsort(residual(x)**2)[:len(p)-q]
                    result=least_squares(lambda z:residual(z)[idx],np.clip(x,lo+1e-10,hi-1e-10),
                        jac=lambda z:jac(z)[idx],bounds=(lo,hi),max_nfev=cfg['solver_max_nfev'])
                    x=result.x; candidates.append(x.copy())
        except (ValueError,FloatingPointError) as exc: failures.append(str(exc))
    if not candidates: candidates=[(lo+hi)/2]; failures.append('centroid fallback, no optimizer candidate')
    def objective(x):
        r=residual(x)
        return float(np.sort(r*r)[:len(p)-q].sum()) if trim else float(np.log1p((r/scale)**2).sum())
    selected=min(candidates,key=objective)
    position=[format(v,'.12f') for v in selected]
    return dict(position=position,numeric_objective=objective(selected),search_complete=False,
        optimizer_failures=failures,feasibility=residual_certificate(obs,position,q),
        mechanism='multi-start Cauchy + trimmed LS' if trim else 'multi-start Cauchy')
