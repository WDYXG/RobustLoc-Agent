"""Resume interrupted v2 execution without replacing or retrying a partial round.

The interrupted slot is a provider failure with unknown inference cost. Source
and prior-iteration hashes are protected. Mathematical policy/budgets stay v2.
"""
import argparse
import json
from pathlib import Path
from v5.researcher import runner
from v5.researcher.io import ROOT,read,write_new,file_hash,check_hashes,canonical
from v5.researcher.prompt import research_state,build
from v5.researcher.gate import ledger_event
from v5.researcher.codex_client import verify_receipt
from v5.runs.evaluator_v2 import run as v2

HERE=Path(__file__).resolve().parent


def operation_sources():
    return {p.relative_to(ROOT).as_posix():file_hash(p) for p in sorted(HERE.glob('*.py'))}


def interrupted_runtime():
    return {'provider':'codex-cli','error':'execution interrupted before a completion receipt was captured; this slot is consumed without retry',
            'wall_seconds':0.0,'wall_seconds_is_lower_bound':True,'uncaptured_wall_seconds':None,
            'returncode':None,'timed_out':False,'usage':[],'dollar_cost':None,
            'dollar_cost_reason':'interrupted capture; actual inference usage unknown, not zero',
            'thread_ids':[],'completed_turns':0,'unexpected_tool_items':0,'model_id':None,
            'requested_model':v2.REQUESTED_MODEL,'transport_version':2,
            'capture_interrupted':True,'inference_tokens_unknown':True}


def resume(envelope):
    envelope=Path(envelope).resolve();path=envelope/'scientific'
    if not envelope.is_relative_to(ROOT/'v5/runs') or (path/'metrics.json').exists():
        raise ValueError('only an incomplete v5 run can be resumed')
    transport=read(envelope/'transport_manifest.json');manifest=read(path/'manifest.json')
    if transport['policy']!='codex' or manifest['policy']!='codex':
        raise ValueError('this continuation is for an interrupted Codex trajectory')
    protected={p.relative_to(ROOT).as_posix():file_hash(p) for p in envelope.rglob('*')
               if p.is_file() and p.name not in ('resume_stdout.log','resume_stderr.log')}
    own=operation_sources()
    write_new(envelope/'RESUME_MANIFEST.json',{'schema':'operational-resume-v1','source_hashes':own,
              'preexisting_artifact_hashes':protected,'policy':'consume an interrupted slot; never retry it',
              'mathematical_or_budget_changes':False,'cost_note':'uncaptured runtime/tokens remain unknown; zero wall_seconds is explicitly only a lower bound'})
    check_hashes(protected);check_hashes(own)
    v2.activate(transport['transport_sources']);runner.frozen_check(manifest)
    initial=read(path/'initial_state.json');events=[];results=[];runtimes=[]
    config=manifest['config'];interrupted=[]
    for i in range(1,config['rounds']+1):
        rid=f'r{i:02d}';p=path/'iterations'/rid
        check_hashes(protected);check_hashes(own);runner.frozen_check(manifest)
        state=research_state(initial,events,results,config['rounds']-i+1);prompt=build(state)
        if (p/'ledger_event.json').exists():
            if read(p/'input_state.json')!=state or (p/'prompt.txt').read_text(encoding='utf-8')!=prompt:
                raise ValueError('completed round input chain mismatch')
            proposal=read(p/'proposal.json');saved=read(p/'verification.json');runtime=read(p/'runtime.json')
            verify_receipt(p,proposal,runtime)
            fresh=runner.math_worker(proposal,config) if proposal is not None else runner.failed_record(runtime['error'])
            fresh['tool_seconds']=saved['tool_seconds']
            event=ledger_event(rid,proposal or {},fresh,events)
            if fresh!=saved or event!=read(p/'ledger_event.json'):
                raise ValueError('previous complete round fails independent replay')
            result=saved
        elif p.exists():
            # Do not silently recover a partly committed mathematical decision.
            if any((p/n).exists() for n in ('runtime.json','proposal.json','verification.json')):
                raise ValueError('partial commit requires a separate reviewed recovery protocol')
            if read(p/'input_state.json')!=state or (p/'prompt.txt').read_text(encoding='utf-8')!=prompt:
                raise ValueError('interrupted input mismatch')
            if (p/'events.jsonl').exists() or (p/'stderr.txt').exists():
                raise ValueError('existing capture requires manual preservation/review')
            runtime=interrupted_runtime();proposal=None
            # Empty files mean no captured bytes, not a fabricated provider event.
            (p/'events.jsonl').touch(exist_ok=False);(p/'stderr.txt').touch(exist_ok=False)
            write_new(p/'INTERRUPTION.json',{'captured_provider_events':0,'completed_turn_known':False,
                      'actual_tokens':None,'actual_wall_seconds':None,'model_output_present':(p/'model_output.json').exists(),
                      'reason':'prior execution process absent at continuation; never classify as a mathematical refutation'})
            write_new(p/'proposal.json',None);write_new(p/'runtime.json',runtime)
            result=runner.failed_record(runtime['error']);event=ledger_event(rid,{},result,events)
            write_new(p/'verification.json',result);write_new(p/'ledger_event.json',event)
            interrupted.append(rid)
        else:
            p.mkdir(parents=True)
            write_new(p/'input_state.json',state)
            (p/'prompt.txt').write_text(prompt,encoding='utf-8')
            before={f.relative_to(ROOT).as_posix():file_hash(f) for f in path.rglob('*') if f.is_file()}
            proposal,runtime=runner.codex_propose(prompt,p,path/'proposal_schema.json',config['proposal_timeout_seconds'])
            check_hashes(before);check_hashes(own);runner.frozen_check(manifest)
            verify_receipt(p,proposal,runtime)
            write_new(p/'proposal.json',proposal);write_new(p/'runtime.json',runtime)
            result=runner.math_worker(proposal,config) if proposal is not None else runner.failed_record(runtime['error'])
            event=ledger_event(rid,proposal or {},result,events)
            write_new(p/'verification.json',result);write_new(p/'ledger_event.json',event)
        events.append(event);results.append(result);runtimes.append(runtime)
        print(f'{rid} {event["status"]} {event["failure_kind"]}; resumed/verified',flush=True)
    write_new(path/'ledger.json',events)
    write_new(path/'metrics.json',runner.summary(events,results,runtimes,'codex'))
    check_hashes(protected);check_hashes(own);runner.frozen_check(manifest)
    write_new(path/'output_hashes.json',{p.relative_to(path).as_posix():file_hash(p) for p in sorted(path.rglob('*')) if p.is_file()})
    audit=v2.audit(envelope);write_new(envelope/'audit.json',audit)
    write_new(envelope/'RESUME_AUDIT.json',{'passed':True,'prior_artifacts_unchanged':len(protected),
              'interrupted_slots':interrupted,'rounds':len(events),'mathematical_budget_unchanged':True,
              'captured_completed_turns':sum(r.get('completed_turns',0) for r in runtimes),
              'total_cost_complete':False,'unknown_cost_slots':interrupted,'source_hashes':own})
    print(json.dumps(audit),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('envelope');args=p.parse_args();resume(args.envelope)
