import pytest
from ble_calibration.audit import parse_anchors, summarize, usable


def record(device='target-a',label='p1',x='1',rss=('-80','-105','-100')):
    return dict(WAP1=rss[0],WAP2=rss[1],WAP3=rss[2],LABEL=label,X=x,Y='2',DEVICE=device,ROOM_ID='r')


def test_observed_receivers_not_transmitters_or_repeated_rows():
    a=record(); b=record(device='target-b')
    s=summarize([a,a,b],['WAP1','WAP2','WAP3'])
    assert s['raw_rows']==3 and s['receiver_columns']==3 and s['target_transmitters']==2
    assert s['effective_receiver_histogram']=={2:3} and s['unique_positions']==1
    assert s['exact_duplicate_rows']==1


def test_union_never_counts_a_receiver_twice():
    rows=[record(rss=('-80','-105','-105')),record(rss=('-80','-90','-105'))]
    s=summarize(rows,['WAP1','WAP2','WAP3'])
    assert s['grouped_union']['histogram']=={2:1}


def test_uncertain_sentinel_does_not_remove_minus100():
    assert not usable(-105) and usable(-100) and usable(-101)


def test_conflicting_labels_and_coordinate_aliases_rejected():
    with pytest.raises(ValueError): summarize([record(),record(x='3')],['WAP1','WAP2','WAP3'])
    with pytest.raises(ValueError): summarize([record(),record(label='alias')],['WAP1','WAP2','WAP3'])


def test_untrusted_assignment_is_not_executed(tmp_path):
    p=tmp_path/'anchors.txt'; p.write_text("x = __import__('os').system('echo unsafe')")
    with pytest.raises(ValueError): parse_anchors(p)
    p.write_text("x = {'WAP1':[1,2]}")
    assert parse_anchors(p)=={'WAP1':[1,2]}
