"""Versioned task-binding gate; original mathematical consumers stay frozen."""
from fractions import Fraction as F
from pathlib import Path
from copy import deepcopy
from v4.storage import ROOT,read,digest,sources
from v4.audit import audit as original_audit
from v4.serialization import restore
from v4.experiments import validate_measurement_model as original_validate,active_case


def validate_measurement_model(problem,transcript,model,offers=None):
    if F(model['tolerance'])!=F(transcript['tolerance']): raise ValueError('transcript/model tolerance mismatch')
    return original_validate(problem,transcript,model,offers)


def evaluator_sources():
    return {p.relative_to(ROOT).as_posix():digest(p) for p in sorted(Path(__file__).parent.glob('*.py'))}


def regression_checks():
    records=[]
    for kind in ('range','phase'):
        p,t,c,m=active_case(kind,0,440051); wrong=deepcopy(m); wrong['tolerance']='2'
        assert original_validate(p,t,wrong)['passed']
        try: validate_measurement_model(p,t,wrong)
        except ValueError as error:
            if str(error)!='transcript/model tolerance mismatch': raise
        else: raise AssertionError('v2 accepted a mismatched task')
        records.append(dict(problem=kind,old_checker_accepts_mismatch=True,v2_rejects=True))
    return records


def audit(path):
    path=Path(path); manifest=read(path/'evaluation_manifest_v2.json')
    if manifest['evaluator_sources']!=evaluator_sources() or manifest['scientific_sources']!=sources(): raise ValueError('v2 source freeze')
    base=path/'scientific'; result=original_audit(base); bindings=0
    for folder in ('active','robust_active'):
        for p in (base/folder).glob('*.json'):
            a=read(p); validate_measurement_model(restore(a['problem']),a['transcript'],a['model'],a.get('offers')); bindings+=1
    return dict(passed=True,evaluator_version=2,original_mathematical_audit=result,tolerance_bindings_checked=bindings,
        malformed_input_regressions=regression_checks(),scope='same frozen scientific algorithms and inputs; strengthened task binding; no new generalization claim')


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(); p.add_argument('--run',required=True); a=p.parse_args(); print(audit(ROOT/a.run))
