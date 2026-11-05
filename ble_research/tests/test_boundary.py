import numpy as np
import pytest
from ble_research.core import read,estimate,FIXED,fit
from ble_research.runner import summary,gate

def test_position_partition_and_observation_firewall():
    p,g,s=read()
    assert list(map(len,g.values()))==[96,32,32]
    assert not set(g['calibration'])&set(g['test'])
    assert not set(g['validation'])&set(g['test'])
    with pytest.raises(ValueError):estimate(dict(device='x',rssi=[-80]*15,truth=[0,0]),p,FIXED,'wls')

def test_missing_reports_not_promoted_and_coverage_kept():
    p,_,_=read();a=estimate(dict(device='x',rssi=[-80,-90]+[-105]*13),p,FIXED,'wls')
    assert a['position'] is None and a['n']==2
    r=[dict(label='x',error=None,success=False,n=2)]
    assert summary(r)['coverage']==0 and summary(r)['failure_rate']==1

def test_repeated_rows_do_not_change_position_weight():
    a=dict(label='a',error=1.,success=True,n=3);b=dict(label='b',error=40.,success=True,n=3)
    assert summary([a,b])['cep90']==summary([a]*100+[b])['cep90']

def test_calibrator_training_and_sign():
    p,g,s=read();m=fit(s['calibration'],p,'global')
    assert m['slope']<0 and np.isfinite(m['intercepts']).all()
