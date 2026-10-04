"""Small pre-freeze integration using development inputs only."""
import sys
from pathlib import Path
from v3b.assumption_agent.storage import read
from v3d.minimal_trust import run


def test_complete_development_pipeline_and_independent_audit(tmp_path,monkeypatch):
    original=run.read
    def development_read(path):
        data=original(path)
        if Path(path)==Path(run.__file__).with_name('config.json'):
            data['heldout_seed']=data['development_seed']
            data['finite_variants']=1; data['continuous_variants']=1
        return data
    output=tmp_path/'development-smoke'
    monkeypatch.setattr(run,'read',development_read)
    monkeypatch.setattr(sys,'argv',['run','--run',str(output)])
    run.main()
    audit=read(output/'audit.json')
    assert audit['passed'] and audit['finite_cases']==6
    assert audit['automatic_old_miss_repairs_including_development']==2
