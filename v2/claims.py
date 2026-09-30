"""Provenance is independent of whether a statement was rederived in this project."""
STATUS={'known','proved-in-project','conjectured','numerically-supported','refuted'}
CLAIMS=[
    dict(id='K1',status='known',claim='Range Gram/frame operator and FIM under specified Gaussian likelihood',source='S1,S2',proof='THEORY.md K1',novelty='known'),
    dict(id='K2',status='known',claim='2D analytic worst surviving lower frame bound and determinant formula',source='S2; elementary spectral algebra',proof='THEORY.md K2',project_derivation=True,novelty='known'),
    dict(id='K3',status='known',claim='2q sparse support/rank condition for linearized correction',source='S4 Proposition 2, T=1',proof='THEORY.md K3',project_derivation=True,novelty='known'),
    dict(id='K4',status='known',claim='2epsilon/gamma linear feasible-decoder bound',source='lower singular value inequality plus S4 support-union argument',proof='THEORY.md K4',project_derivation=True,novelty='known linear algebra corollary'),
    dict(id='P1',status='proved-in-project',claim='Explicit curvature-limited ball and local nonlinear stable recovery',source='K2-K4 and range Hessian calculus',proof='THEORY.md P1',novelty='not claimed; direct specialization, audit not exhaustive',proof_kind='written mathematical proof, not formally verified'),
    dict(id='P2',status='proved-in-project',claim='Candidate-centered conditional beta certificate after residual gate',source='P1 perturbation argument',proof='THEORY.md P2',novelty='not established',proof_kind='written mathematical proof, not formally verified'),
    dict(id='P3',status='proved-in-project',claim='Every n-2q anchor subset noncollinear iff global planar range q-correction',source='S4 generic support criterion plus perpendicular-bisector geometry',proof='THEORY.md P3',novelty='not claimed; elementary range specialization'),
    dict(id='R1',status='refuted',claim='alpha_q positive suffices for unknown q corruptions',source='known distinction S4',proof='THEORY.md R1',novelty='no claim'),
    dict(id='R2',status='refuted',claim='positive alpha_2q at truth implies global nonlinear uniqueness',source='reflection construction',proof='THEORY.md R2',novelty='no claim'),
    dict(id='R3',status='refuted',claim='positive alpha_2q guarantees L1 correction',source='S4 Proposition 6; explicit project witness',proof='THEORY.md R3',novelty='known mechanism'),
    dict(id='R4',status='refuted',claim='zero margin rules out exact pointwise uniqueness',source='circle tangency construction',proof='THEORY.md R4',novelty='no claim'),
    dict(id='C1',status='conjectured',claim='Feasibility-first residual/geometry ranking improves practical stability within trusted basins',source='project proposal; trimming and frame foundations S2,S7',proof=None,novelty='not established; not a new frame or FIM result'),
    dict(id='C2',status='conjectured',claim='Unguarded residual/geometry ratio always improves finite-pool selection',source='project conjecture to be falsified',proof=None,novelty='not established'),
]
