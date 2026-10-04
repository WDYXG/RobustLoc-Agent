"""Consume immutable records, physical replies and separate mathematical checks."""
from pathlib import Path
from fractions import Fraction as F
from itertools import combinations
import json
from v3b.assumption_agent.storage import hydrate
from .storage import ROOT,read,hash_value,digest,sources,check_previous
from .serialization import restore
from .core.certificate import verify_recovery
from .core.corruption import residual_interval2
from .core.geometry import independent_radius2
from .core.symmetry import discover
from .core.diagnostics import classify_pair,classify_scaling
from .core.verify import verify_result
from .core.information_action import key
from .problems.phase_retrieval import PhaseRetrieval,verify_acquisition
from .problems.range_localization import RangeLocalization
from .experiments import validate_measurement_model


def audit(path):
    path=Path(path); manifest=read(path/'manifest.json'); cfg=manifest['config']
    if manifest['sources']!=sources(): raise ValueError('source freeze')
    previous=check_previous()
    for name,h in read(path/'output_hashes.json')['files'].items():
        if digest(path/name)!=h: raise ValueError('output hash '+name)
    oldbase=ROOT/'v3d/runs/minimal-trust-001'; regression=read(path/'range_regression.json')
    expected={f'{folder}/{p.stem}' for folder in ('finite','analytic','continuous') for p in (oldbase/folder).glob('*.json')}
    if len(regression['rows'])!=43 or {r['case'] for r in regression['rows']}!=expected: raise ValueError('incomplete legacy regression')
    for r in regression['rows']:
        old=hydrate(oldbase,read(oldbase/(r['case']+'.json')))
        if r['interval']!=old['decision']['interval']: raise ValueError('legacy interval mismatch')
        verify_result(RangeLocalization(),r['model'],r['result'],old['budget'],r.get('upper',{}).get('cost_upper'))
    counts=dict(recovery=0,active=0,robust_active=0,recovered=0,physical_bound_violations=0); artifacts={}
    for p in sorted((path/'recovery').glob('*.json')):
        a=read(p); problem=restore(a['problem']); t=a['transcript']; private=a['private']; result=a['result']
        if residual_interval2(problem.observe(private['target']),t['values'],t['q'])[1]>F(t['epsilon'])**2: raise ValueError('invalid evaluation world')
        if result['action']=='recover':
            b=verify_recovery(problem,t,result); error2=problem.state_distance2(result['position'],private['target'])
            if error2>b*b or str(error2)!=a['verification']['error2']: raise ValueError('recovery bound violation')
            counts['recovered']+=1
        counts['recovery']+=1
    for p in sorted((path/'active').glob('*.json')):
        a=read(p); artifacts[p.stem]=a; problem=restore(a['problem']); model=a['model']; cycle=a['cycle']
        validate_measurement_model(problem,a['transcript'],model)
        verify_result(problem,model,cycle['decision'],a['budget'])
        if cycle['symmetry']!=json.loads(json.dumps(discover(problem))): raise ValueError('symmetry search record')
        if {e['world'] for e in a['executions']}!={w['id'] for w in model['worlds']}: raise ValueError('missing policy execution world')
        for e in a['executions']:
            out=e['output']; world=next(w for w in model['worlds'] if w['id']==e['world'])
            if out['action']!='recover':
                if cycle['decision']['interval']['state']=='certifiably-recoverable': raise ValueError('expected finite policy output')
                continue
            node=cycle['decision']['tree']; paid=F(0)
            for event in out['history']:
                action=next(a for a in model['actions'] if a['id']==event['action'])
                if node['terminal'] or node['action']!=action['id'] or event['reply']!=action['responses'][world['id']] or event['cost']!=action['cost']: raise ValueError('policy execution replay')
                paid+=F(action['cost']); node=node['children'][key(event['reply'])]
            if not node['terminal'] or out['position']!=node['ball']['centre'] or out['radius2']!=node['ball']['radius2'] or F(out['spent'])!=paid or paid>F(a['budget']): raise ValueError('execution leaf/cost')
            if problem.state_distance2(out['position'],world['target'])>F(out['radius2']): raise ValueError('actual leaf radius')
        counts['active']+=1
    for p in sorted((path/'robust_active').glob('*.json')):
        a=read(p); artifacts[p.stem]=a; problem=restore(a['problem']); t=a['transcript']
        validate_measurement_model(problem,t,a['model'],a['offers'])
        final=verify_acquisition(problem,a['offers'],t['q'],t['epsilon'],t['tolerance'],a['upper'])
        verify_result(problem,a['model'],a['decision'],a['budget'],a['upper']['cost_upper'])
        actual=a['actual']
        if actual:
            if a['decision']['interval']['state']!='certifiably-recoverable': raise ValueError('unauthorized budget policy')
            values=list(t['values']); paid=F(0); observed=problem
            if [e['action'] for e in actual['replies']]!=a['upper']['actions']: raise ValueError('uniform policy action binding')
            for event in actual['replies']:
                offer=next(o for o in a['offers'] if o['id']==event['action']); observed=observed.with_measurement(offer['vector'])
                lo,hi=observed.observe(actual['target'])[-1]
                if lo!=hi or event['reply']!=dict(value=str(lo)): raise ValueError('actual sensing reply')
                values.append(str(lo)); paid+=F(offer['cost'])
            if actual['transcript']!=dict(t,values=values) or F(actual['paid'])!=paid or paid>F(a['budget']): raise ValueError('active final contract')
            if residual_interval2(final.observe(actual['target']),values,t['q'])[1]>F(t['epsilon'])**2: raise ValueError('active global corruption budget')
            if actual['result']['action']=='recover':
                b=verify_recovery(final,actual['transcript'],actual['result'])
                if final.state_distance2(actual['target'],actual['result']['position'])>b*b: raise ValueError('active output error')
                counts['recovered']+=1
        counts['robust_active']+=1
    if counts['recovery']!=2*cfg['recovery_variants_per_problem'] or counts['active']!=2*cfg['active_variants_per_problem'] or counts['robust_active']!=cfg['robust_active_variants']: raise ValueError('incomplete case set')
    counter=read(path/'counterexamples.json'); qcase=counter['q_vs_2q']; p=PhaseRetrieval(qcase['problem']); w=qcase['witness']
    if not all(p.complement_property(S)['passed'] for S in combinations(range(4),3)) or p.equivalent(w['left'],w['right']): raise ValueError('q deletion counterexample premise')
    if all(p.complement_property(S)['passed'] for S in combinations(range(4),2)): raise ValueError('missing 2q failure')
    for x in (w['left'],w['right']):
        if residual_interval2(p.observe(x),w['transcript']['values'],1)[1]!=0: raise ValueError('false sparse-corruption collision')
    if qcase['diagnosis']!=classify_pair(p,w['left'],w['right'],1): raise ValueError('corruption diagnosis')
    h=counter['quotient_helly']; full=independent_radius2(h['points'],'sign'); triples=max(independent_radius2(S,'sign') for S in combinations(h['points'],3))
    if str(full)!=h['radius2'] or str(triples)!=h['maximum_triple_radius2'] or not triples<=F(h['tolerance'])**2<full: raise ValueError('quotient four-world obstruction')
    s=counter['sign']; p=PhaseRetrieval([(1,0),(0,1),(1,1)])
    if p.observe(s['left'])!=p.observe(s['right']) or not p.equivalent(s['left'],s['right']) or s['left']==s['right']: raise ValueError('sign symmetry witness')
    if s['diagnosis']!=classify_pair(p,s['left'],s['right'],0): raise ValueError('symmetry diagnosis')
    origin=counter['origin']; p=PhaseRetrieval(origin['frame'],0,3)
    if not p.complement_property()['passed']: raise ValueError('origin frame not phase retrievable')
    if origin['diagnosis']!=classify_scaling(p,origin['certificate']): raise ValueError('scaling diagnosis')
    for r in origin['sequence']:
        t=F(r['scale']); ratio=sum(lo*lo for lo,hi in p.observe([t,0]))/(t*t)
        if F(r['squared_ratio'])!=ratio or ratio!=5*t*t: raise ValueError('origin scaling counterexample')
    expected_events=[]
    for name,a in artifacts.items():
        if 'executions' in a:
            for e in a['executions']:
                for event in e['output'].get('history',[]): expected_events.append(dict(case=name,world=e['world'],**event))
        elif a['actual']:
            for event in a['actual']['replies']:
                offer=next(o for o in a['offers'] if o['id']==event['action'])
                expected_events.append(dict(case=name,**event,cost=offer['cost']))
    actual_events=[]; last='0'*64; n=0
    for line in (path/'history.jsonl').read_text(encoding='utf-8').splitlines():
        row=json.loads(line); h=row.pop('hash')
        if row['index']!=n or row['previous']!=last or hash_value(row)!=h: raise ValueError('history chain')
        actual_events.append(row['payload']); last=h; n+=1
    encode=lambda v:json.dumps(v,sort_keys=True)
    if sorted(map(encode,actual_events))!=sorted(map(encode,expected_events)): raise ValueError('history/artifact event binding')
    if read(path/'completion.json')!=dict(events=n,last_hash=last): raise ValueError('completion')
    return dict(passed=True,previous_files_unchanged=previous,range_regressions=43,**counts,history_events=n,
        counterexample_families_verified=4,scope='distinct consumer calculations and exact contract checks; no independent authorship, continuous feasible-set enumeration, or proof-assistant claim')


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(); p.add_argument('--run',default='v4/runs/cross-problem-001'); a=p.parse_args(); print(audit(ROOT/a.run))
