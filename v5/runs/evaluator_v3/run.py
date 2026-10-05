import argparse
import copy
from pathlib import Path
from v5.researcher.io import ROOT,read,write_new,file_hash,check_hashes
from v5.researcher import runner
from v5.runs.evaluator_v2 import run as v2

HERE=Path(__file__).resolve().parent


def source_hashes():
    return {p.relative_to(ROOT).as_posix():file_hash(p) for p in sorted(HERE.glob('*.py'))}


def corrected_metrics(events,raw):
    out=copy.deepcopy(raw)
    out['legacy_successful_conjecture_revisions']=out.pop('successful_conjecture_revisions')
    counts={k:0 for k in ('successful_formal_revisions','successful_refuted_claim_repairs',
                          'successful_post_rejection_corrections','failed_refuted_claim_repairs')}
    by_id={};details=[]
    for e in events:
        parent=by_id.get(e['parent_id'])
        if parent and parent['family']==e['family']:
            changed=e['semantic_key']!=parent['semantic_key']
            proved=e['status']=='proved-in-project' and e['ledger_advancing']
            formal=bool(changed and proved and parent['status'] in ('refuted','unresolved'))
            repaired=bool(formal and parent['status']=='refuted')
            correction=bool(proved and parent['failure_kind']=='verification-rejected')
            failed=bool(changed and parent['status']=='refuted' and e['status']=='refuted')
            for key,value in zip(counts,(formal,repaired,correction,failed)):counts[key]+=int(value)
            if formal or repaired or correction or failed:
                details.append({'round':e['id'],'parent':parent['id'],'formal_revision':formal,
                                'refuted_claim_repaired':repaired,'post_rejection_correction':correction,
                                'refuted_claim_repair_failed':failed})
        by_id[e['id']]=e
    out.update(counts)
    out['repair_metric_version']=3
    return out,details


def run(baseline,codex,output):
    baseline,codex,output=map(lambda p:Path(p).resolve(),(baseline,codex,output))
    if output.exists() or not output.is_relative_to(ROOT/'v5/runs'):
        raise ValueError('fresh v5/runs output required')
    output.mkdir(parents=True)
    sources=source_hashes()
    inputs={}
    for p in (baseline,codex):
        for name in ('transport_manifest.json','audit.json','scientific/manifest.json',
                     'scientific/ledger.json','scientific/metrics.json','scientific/output_hashes.json'):
            f=p/name;inputs[f.relative_to(ROOT).as_posix()]=file_hash(f)
    write_new(output/'manifest.json',{'schema':'phase5-metric-regrade-v3','sources':sources,'inputs':inputs,
               'new_model_calls':0,'mathematical_evaluator_changed':False})
    audits={'scripted':v2.audit(baseline),'codex':v2.audit(codex)}
    a,b=read(baseline/'transport_manifest.json'),read(codex/'transport_manifest.json')
    for k in ('transport_sources','scientific_sources','requested_model'):
        if a[k]!=b[k]:raise ValueError('unmatched scientific/transport sources')
    result=runner.compare(baseline/'scientific',codex/'scientific')
    details={}
    for policy,p in (('scripted',baseline),('codex',codex)):
        result[policy],details[policy]=corrected_metrics(read(p/'scientific/ledger.json'),result[policy])
    result['report_evaluator_version']=3
    result['execution_note']={'planned_slots_per_policy':12,'codex_completed_provider_turns':result['codex']['usage_receipts'],
          'codex_unknown_cost_slots':['r07'],'codex_runtime_and_token_totals_are_lower_bounds':True,
          'interrupted_slot_consumes_budget':True,'new_model_calls_during_regrade':0,
          'requested_model':v2.REQUESTED_MODEL,'underlying_mathematical_statuses_unchanged':True}
    check_hashes(sources);check_hashes(inputs)
    write_new(output/'comparison.json',result);write_new(output/'repair_audit.json',details)
    write_new(output/'replay_audits.json',audits)
    write_new(output/'output_hashes.json',{p.name:file_hash(p) for p in sorted(output.iterdir()) if p.is_file()})
    print(result)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('baseline');p.add_argument('codex');p.add_argument('output')
    a=p.parse_args();run(a.baseline,a.codex,a.output)
