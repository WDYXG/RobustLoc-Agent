from .problems.phase_retrieval import PhaseRetrieval
from .problems.range_localization import RangeLocalization


def specification(problem):
    if isinstance(problem,PhaseRetrieval):
        return dict(kind='phase',design=problem.design,min_norm=str(problem.min_norm),max_norm=str(problem.max_norm))
    return dict(kind='range',anchors=problem.anchors,domain=problem.domain)


def restore(spec):
    if spec['kind']=='phase': return PhaseRetrieval(spec['design'],spec['min_norm'],spec['max_norm'])
    if spec['kind']=='range': return RangeLocalization(spec['anchors'],spec['domain'])
    raise ValueError('unknown adapter')
