"""Shared support-union bound and finite candidate recovery; adapter owns margin."""
from .arithmetic import F,sqrt_interval
from .corruption import residual_interval2,trimmed_difference2


def recover(problem,transcript,candidates):
    q=transcript['q']; eps=F(transcript['epsilon']); rho=F(transcript['tolerance'])
    if eps<0 or rho<0: raise ValueError('noise/tolerance')
    cert=problem.certificate(q); margin=problem.verify_certificate(cert,q)
    feasible=[]
    for x in candidates:
        if not problem.in_domain(x): continue
        _,r2=residual_interval2(problem.observe(x),transcript['values'],q)
        if r2<=eps*eps: feasible.append((r2,list(map(str,x))))
    if not feasible or margin<=0:
        return dict(action='abstain',reason='candidate-search-incomplete' if not feasible else 'margin-not-established',certificate=cert,scope='no impossibility inference')
    r2,x=min(feasible,key=lambda v:(v[0],v[1])); residual=sqrt_interval(r2)[1]
    bound=(eps+residual)/margin
    return dict(action='recover' if bound<=rho else 'abstain',position=x,residual2=str(r2),radius_upper=str(bound),certificate=cert,
        reason='verified-support-union-bound' if bound<=rho else 'bound-too-wide',scope='continuous adapter domain, fixed known design, at most q arbitrary contaminated coordinates')


def verify_recovery(problem,transcript,result):
    if result['action']!='recover': raise ValueError('no recovery')
    q=transcript['q']; b=problem.verify_certificate(result['certificate'],q); x=result['position']
    if not problem.in_domain(x) or b<=0: raise ValueError('domain or margin')
    _,r2=residual_interval2(problem.observe(x),transcript['values'],q)
    eps=F(transcript['epsilon']); bound=(eps+sqrt_interval(r2)[1])/b
    if r2>eps*eps or F(result['residual2'])!=r2 or F(result['radius_upper'])!=bound or bound>F(transcript['tolerance']): raise ValueError('unsafe recovery bound')
    return bound


def support_union_check(problem,left,right,transcript):
    """Executable instance of the generic proof, not a substitute for that proof."""
    q=transcript['q']; y=transcript['values']
    a=problem.observe(left); b=problem.observe(right)
    e1=sqrt_interval(residual_interval2(a,y,q)[1])[1]; e2=sqrt_interval(residual_interval2(b,y,q)[1])[1]
    delta_lo,delta_hi=trimmed_difference2(a,b,q)
    return dict(epsilon_left=str(e1),epsilon_right=str(e2),trimmed_delta2_lower=str(delta_lo),
        trimmed_delta2_upper=str(delta_hi),triangle_consistent=delta_lo<=(e1+e2)**2)
