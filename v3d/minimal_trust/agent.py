"""Cost intervals and auditable epistemic states; no private true-world access."""
from fractions import Fraction as F
from .finite import analyze
from .finite_verify import verify
from .worlds import validate_restriction,translated_restriction
from .subsets import uniform_upper
from .subset_verify import verify_uniform_upper


def diagnose(lower,upper,budget,lower_infinite=False):
    B=F(budget)
    if B<0: raise ValueError('negative decision budget')
    if lower_infinite:
        if upper is not None: raise ValueError('inconsistent infinite lower and finite upper')
        return dict(state='provably-insufficient-information-budget',cost_lower=None,cost_upper=None,lower_infinite=True,gap=None,relative_gap=None)
    L=F(lower)
    if L<0 or (upper is not None and F(upper)<L): raise ValueError('inconsistent cost interval')
    U=F(upper) if upper is not None else None
    state=('provably-insufficient-information-budget' if L>B else
           'certifiably-recoverable' if U is not None and U<=B else 'unresolved-certificate-or-search-gap')
    return dict(state=state,cost_lower=str(L),cost_upper=str(U) if U is not None else None,lower_infinite=False,
        gap=str(U-L) if U is not None else None,relative_gap=str((U-L)/U) if U else ('0' if U==0 else None))


def finite_decision(obs,model,budget):
    physics=validate_restriction(obs,model); result=analyze(model); verified=verify(model,result)
    c=result['adaptive_cost']
    interval=diagnose(c or '0',c,budget,lower_infinite=c is None)
    return dict(interval=interval,finite=result,verification=verified,physics=physics,
        scope='complete finite prior ONLY: equality is not transferred to the continuous nuisance model')


def continuous_decision(obs,cfg,budget,node_limit=None):
    model=translated_restriction(obs,cfg); result=analyze(model); verified=verify(model,result)
    physics=validate_restriction(obs,model); upper=uniform_upper(obs,node_limit=node_limit)
    if upper['cost_upper'] is not None: verify_uniform_upper(obs,upper)
    lower=result['adaptive_cost']
    return dict(interval=diagnose(lower or '0',upper['cost_upper'],budget,lower_infinite=lower is None),
        finite_witness_model=model,finite_restriction=result,verification=verified,physics=physics,upper=upper,
        scope='continuous physical contract: checked finite restriction gives LB; response-uniform subset policy gives UB; None UB means unknown')
