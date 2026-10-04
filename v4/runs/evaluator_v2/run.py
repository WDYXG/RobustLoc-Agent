"""Freeze the v2 checker before binding it and rerunning all original cases."""
from pathlib import Path
import argparse
import v4.run as original_run
from v4.storage import ROOT,save,read,sources,check_previous
from .audit import evaluator_sources,validate_measurement_model,audit


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--run',required=True); a=parser.parse_args()
    path=ROOT/a.run
    if path.exists(): raise RuntimeError('immutable envelope exists')
    cfg=read(ROOT/'v4/config.json'); prior=check_previous(); path.mkdir(parents=True)
    manifest=dict(evaluator_version=2,evaluator_sources=evaluator_sources(),scientific_sources=sources(),config=cfg,
        previous_files=prior,runtime_binding='v4.run.validate_measurement_model -> evaluator_v2.audit.validate_measurement_model',
        scope='pre-rerun validation freeze; same held-out inputs, not a newly unseen test')
    save(path/'evaluation_manifest_v2.json',manifest)
    original_run.validate_measurement_model=validate_measurement_model
    original_run.execute(path/'scientific',cfg)
    result=audit(path); save(path/'audit_v2.json',result); print(result,flush=True)


if __name__=='__main__': main()
