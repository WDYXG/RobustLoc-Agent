"""Classify checked evidence; an absent certificate is never impossibility."""
from .arithmetic import F
from .corruption import common_corrupted_transcript


def classify_pair(problem,x,z,q):
    if problem.equivalent(x,z):
        return dict(classification='global-symmetry-equivalence',status='proved-in-project',failure=False)
    left,right=problem.observe(x),problem.observe(z)
    if any(F(a)!=F(b) for a,b in left+right):
        return dict(classification='unresolved-interval-evidence',status='conjectured',failure=None)
    common=common_corrupted_transcript(left,right,q)
    if common is None: return dict(classification='this-pair-separated',status='proved-in-project',failure=False)
    label='measurement-design-ambiguity' if left==right else 'sparse-corruption-ambiguity'
    return dict(classification=label,status='proved-in-project',failure=True,witness=common)


def classify_scaling(problem,certificate):
    problem.verify_scaling_certificate(certificate)
    return dict(classification='local-scaling-degeneracy',status='proved-in-project',failure=True,
        scope='adapter-certified homogeneous scaling inside the domain; not inferred from a finite decreasing sequence')
