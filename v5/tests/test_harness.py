import copy
import json
import subprocess
from pathlib import Path
import pytest
from v5.researcher.io import read, write_new, digest, check_hashes, file_hash, ROOT
from v5.researcher.prompt import initial_state, research_state, build
from v5.researcher.codex_client import command, verify_receipt
from v5.researcher.runner import math_worker, CONFIG, summary
from v5.researcher.baseline import propose
from v5.researcher.gate import evaluate, ledger_event


def test_one_worker_actual_execution():
    r=math_worker(propose(6,{}),CONFIG)
    assert r['verdict']['status']=='proved-in-project'


def test_prompt_state_changes_after_a_refutation_but_has_no_schedule():
    initial=initial_state();p=propose(5,{});r=evaluate(p);e=ledger_event('r01',p,r,[])
    before=build(research_state(initial,[],[],12));after=build(research_state(initial,[e],[r],11))
    assert before!=after and '"point":["1","1"]' in after
    assert 'TASKS=' not in before and 'baseline.py' not in before


def test_write_once_outputs(tmp_path):
    p=tmp_path/'record.json';write_new(p,{'a':1})
    with pytest.raises(FileExistsError):write_new(p,{'a':2})
    assert read(p)=={'a':1}


def test_old_file_integrity_check_does_not_modify_anything():
    frozen=read(ROOT/'v5/PREVIOUS_FREEZE.json')
    assert frozen['count']==4083 and len(frozen['files'])==4083
    assert check_hashes(frozen['files'])==4083
    bad=dict(frozen['files']);name=next(iter(bad));bad[name]='0'*64
    with pytest.raises(RuntimeError):check_hashes(bad)


def test_cli_has_no_source_write_permissions(tmp_path):
    argv=command(tmp_path,tmp_path/'schema.json',tmp_path/'model_output.json')
    assert argv[argv.index('--sandbox')+1]=='read-only'
    assert '--ignore-user-config' in argv and '--ephemeral' in argv
    assert 'features.shell_tool=false' in argv and 'features.unified_exec=false' in argv
    assert 'features.plugins=false' in argv and 'features.hooks=false' in argv
    assert '--dangerously-bypass-approvals-and-sandbox' not in argv


def receipts(tmp_path, proposal):
    usage={'input_tokens':111,'output_tokens':22,'cached_input_tokens':50}
    events=[{'type':'thread.started','thread_id':'test-receipt-only-not-a-real-provider-run'},
            {'type':'item.completed','item':{'type':'agent_message','text':json.dumps(proposal)}},
            {'type':'turn.completed','usage':usage}]
    (tmp_path/'events.jsonl').write_text('\n'.join(json.dumps(e) for e in events),encoding='utf-8')
    write_new(tmp_path/'model_output.json',proposal)
    return {'usage':[usage],'thread_ids':[events[0]['thread_id']], 'unexpected_tool_items':0,
            'timed_out':False,'returncode':0}


def test_receipt_fixture_binds_actual_output_and_usage(tmp_path):
    p=propose(5,{});meta=receipts(tmp_path,p)
    assert verify_receipt(tmp_path,p,meta)
    bad=copy.deepcopy(meta);bad['usage'][0]['input_tokens']=0
    with pytest.raises(ValueError):verify_receipt(tmp_path,p,bad)
    p['claim']='changed after model returned'
    with pytest.raises(ValueError):verify_receipt(tmp_path,p,meta)


def test_forbidden_tool_receipt_cannot_pass(tmp_path):
    p=propose(5,{});meta=receipts(tmp_path,p)
    with (tmp_path/'events.jsonl').open('a',encoding='utf-8') as f:
        f.write('\n'+json.dumps({'type':'item.completed','item':{'type':'command_execution','command':'bad'}}))
    with pytest.raises(ValueError):verify_receipt(tmp_path,p,meta)


def test_non_object_proposal_does_not_crash_ledger():
    p=['I proved it'];r=evaluate(p);e=ledger_event('r01',p,r,[])
    assert e['status']=='unresolved' and e['failure_kind']=='invalid-proposal'


def test_failure_counts_in_metrics_denominator():
    p={};r=evaluate(p);e=ledger_event('r01',p,r,[])
    m=summary([e],[r],[{'wall_seconds':0,'usage':[]}],'scripted')
    assert m['rounds']==1 and m['acceptance_rate']==0 and m['invalid_proposals']==1


@pytest.mark.parametrize('bad',['1e999999999999','1/0','-1/-2',0.5,True])
def test_rational_resource_and_type_limits(bad):
    from v5.researcher.polynomial import rational
    with pytest.raises((ValueError,ZeroDivisionError)):rational(bad)
