import pytest
from robustloc.storage import save, read, append, history
from robustloc.verifier import verify

def test_state_persistence(tmp_path):
    path = tmp_path/'state.json'
    save(path, {'status':'continue','iteration':2}); assert read(path)['iteration']==2
    save(path, {'status':'complete','iteration':8}); assert read(path)['status']=='complete'

def test_append_only_and_tamper_detection(tmp_path):
    path = tmp_path/'log.jsonl'
    append(path, {'iteration':1}); original=path.read_bytes()
    append(path, {'iteration':2}); assert path.read_bytes().startswith(original)
    assert len(history(path))==2
    path.write_text(path.read_text().replace('"iteration": 1','"iteration": 9'))
    with pytest.raises(RuntimeError): history(path)

def test_verifier_can_reject():
    def data(q):
        m=dict(cep90=q,failure_rate=.1,nonfinite_cases=0,optimization_failures=0)
        return dict(overall=m,by_scenario={'a':m},rows=[dict(seed=1,scenario='a',error=q)])
    policy=dict(minimum_relative_cep90_gain=.02,maximum_failure_rate_increase=.005,maximum_scenario_cep90_ratio=1.25)
    assert verify(data(12),data(10),data(10),policy)['verdict']=='rejected'
    assert verify(data(8),data(10),data(10),policy)['verdict']=='supported'
