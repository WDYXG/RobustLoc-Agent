from v5.runs.operations_v1.resume import interrupted_runtime
from v5.researcher.codex_client import verify_receipt
from v5.researcher.runner import failed_record
from v5.researcher.gate import ledger_event


def test_missing_receipt_never_becomes_research_success(tmp_path):
    (tmp_path/'events.jsonl').touch()
    runtime=interrupted_runtime()
    assert verify_receipt(tmp_path,None,runtime)
    assert runtime['inference_tokens_unknown'] and runtime['uncaptured_wall_seconds'] is None
    assert runtime['wall_seconds_is_lower_bound']
    result=failed_record(runtime['error'])
    event=ledger_event('r07',{},result,[])
    assert event['status']=='unresolved' and not event['accepted'] and not event['ledger_advancing']
