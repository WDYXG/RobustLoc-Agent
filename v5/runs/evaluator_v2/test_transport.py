from pathlib import Path
from v5.runs.evaluator_v2 import run as v2
from v5.researcher.io import read


def test_suppress_warning_does_not_enable_model_tools(tmp_path):
    a=v2.v2_command(tmp_path,tmp_path/'schema',tmp_path/'output')
    assert 'suppress_unstable_features_warning=true' in a
    assert a[a.index('--model')+1]=='gpt-6.1-sol'
    assert a[a.index('--sandbox')+1]=='read-only'
    assert 'features.shell_tool=false' in a and 'features.plugins=false' in a
    assert a[-1]=='-'


def test_request_metadata_honestly_distinguishes_actual_model(tmp_path):
    p=tmp_path/'invocation.json'
    v2.v2_write(p,{'model_id':None,'model_selection':'legacy default'})
    obj=read(p)
    assert obj['requested_model']=='gpt-6.1-sol' and obj['model_id'] is None
    assert obj['transport_version']==2
