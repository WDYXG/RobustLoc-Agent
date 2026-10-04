"""Freeze first, execute the same core on both adapters, then audit."""
from pathlib import Path
from fractions import Fraction as F
import argparse,platform,time
from .storage import ROOT,save,read,sources,check_previous,digest,History
from .serialization import specification
from .experiments import (grid,recovery_case,active_case,robust_active_case,q_vs_2q,
    quotient_helly_search,origin_degeneracy,validate_measurement_model)
from .core.certificate import recover,verify_recovery
from .core.research import research_cycle,execute_policy
from .core.decision import analyze
from .core.verify import verify_result
from .core.corruption import residual_interval2
from .core.symmetry import discover
from .core.diagnostics import classify_pair,classify_scaling
from .problems.phase_retrieval import PhaseRetrieval,verify_acquisition
from .regression import run_regression


def execute(path,cfg,development=False):
    path=Path(path)
    if path.exists(): raise RuntimeError('immutable run exists; choose a fresh path')
    previous=check_previous(); path.mkdir(parents=True); clock=time.perf_counter()
    manifest=dict(config=cfg,development=development,seed=cfg['development_seed'] if development else cfg['heldout_seed'],
        sources=sources(),previous_files=previous,python=platform.python_version())
    save(path/'manifest.json',manifest); history=History(path/'history.jsonl'); rows=[]
    regression=run_regression(path/'range_regression.json'); print('range regression',regression['cases'],flush=True)
    counter=dict(q_vs_2q=q_vs_2q(),quotient_helly=quotient_helly_search(),origin=origin_degeneracy())
    p=PhaseRetrieval([(1,0),(0,1),(1,1)]); x=['1','2']; z=['-1','-2']
    counter['sign']=dict(left=x,right=z,same_observation=p.observe(x)==p.observe(z),raw_distance2='20',quotient_distance2=str(p.state_distance2(x,z)),
        symmetry_search=discover(p),status='refuted',claim='equal phase-retrieval measurements imply literal state equality')
    counter['sign']['diagnosis']=classify_pair(p,x,z,0)
    qcase=counter['q_vs_2q']; pw=PhaseRetrieval(qcase['problem']); ww=qcase['witness']
    qcase['diagnosis']=classify_pair(pw,ww['left'],ww['right'],1)
    po=PhaseRetrieval(counter['origin']['frame'],0,3); sc=po.scaling_certificate()
    counter['origin'].update(certificate=sc,diagnosis=classify_scaling(po,sc))
    # Rational serialization only; no floating truth gets into certificates.
    save(path/'counterexamples.json',counter)
    seed=manifest['seed']
    for kind in cfg['problems']:
        for i in range(cfg['recovery_variants_per_problem']):
            problem,t,candidates,private=recovery_case(kind,i,seed)
            result=recover(problem,t,candidates); verified=None
            if result['action']=='recover':
                bound=verify_recovery(problem,t,result)
                error2=problem.state_distance2(private['target'],result['position'])
                if error2>bound**2: raise AssertionError('in-contract recovery bound violated')
                verified=dict(radius_upper=str(bound),error2=str(error2),bound_violation=False)
            if residual_interval2(problem.observe(private['target']),t['values'],t['q'])[1]>F(t['epsilon'])**2: raise AssertionError('private world outside contract')
            name=kind+'-recovery-'+str(i)
            save(path/'recovery'/f'{name}.json',dict(problem=specification(problem),transcript=t,private=private,result=result,verification=verified))
            rows.append(dict(case=name,kind='recovery',problem=kind,action=result['action'],radius_upper=result.get('radius_upper')))
        for i in range(cfg['active_variants_per_problem']):
            problem,t,candidates,model=active_case(kind,i,seed)
            validate_measurement_model(problem,t,model)
            cycle=research_cycle(problem,t,candidates,model,'2'); executions=[]
            for world in model['worlds']:
                # Only the evaluator/service closure sees the actual world.
                def provider(a):
                    reply=a['responses'][world['id']]
                    history.append(dict(case=kind+'-active-'+str(i),world=world['id'],action=a['id'],reply=reply,cost=a['cost']))
                    return reply
                output=execute_policy(model,cycle['decision'],provider)
                if output['action']=='recover' and problem.state_distance2(output['position'],world['target'])>F(output['radius2']): raise AssertionError('unsafe active leaf')
                executions.append(dict(world=world['id'],output=output))
            name=kind+'-active-'+str(i)
            save(path/'active'/f'{name}.json',dict(problem=specification(problem),transcript=t,candidates=candidates,model=model,budget='2',cycle=cycle,executions=executions))
            rows.append(dict(case=name,kind='active-finite',problem=kind,interval=cycle['decision']['interval'],nodes=cycle['decision']['nodes']))
        print('completed common loop',kind,flush=True)
    for i in range(cfg['robust_active_variants']):
        p,t,states,offers,model,upper,final=robust_active_case(i,seed)
        validate_measurement_model(p,t,model,offers)
        unit=F(offers[0]['cost']); budget=str([F(0),unit,3*unit,3*unit][i%4])
        decision=analyze(p,model,budget,upper['cost_upper']); verify_result(p,model,decision,budget,upper['cost_upper'])
        actual=None
        if decision['interval']['state']=='certifiably-recoverable':
            actual_target=states[i%2]; values=list(t['values']); paid=F(0); replies=[]; observed=p
            for oid in upper['actions']:
                a=next(a for a in offers if a['id']==oid); observed=observed.with_measurement(a['vector'])
                lo,hi=observed.observe(actual_target)[-1]
                if lo!=hi: raise AssertionError('exact intensity service')
                reply=dict(value=str(lo)); values.append(reply['value']); paid+=F(a['cost']); replies.append(dict(action=oid,reply=reply))
                history.append(dict(case='phase-robust-active-'+str(i),action=oid,reply=reply,cost=a['cost']))
            final=verify_acquisition(p,offers,t['q'],t['epsilon'],t['tolerance'],upper)
            delivered=dict(t,values=values); result=recover(final,delivered,grid())
            if paid>F(budget): raise AssertionError('budget exceeded')
            if residual_interval2(final.observe(actual_target),values,t['q'])[1]>F(t['epsilon'])**2: raise AssertionError('joint post-acquisition contract')
            if result['action']=='recover':
                bound=verify_recovery(final,delivered,result)
                if final.state_distance2(actual_target,result['position'])>bound**2: raise AssertionError('post-acquisition error')
            actual=dict(target=actual_target,transcript=delivered,result=result,replies=replies,paid=str(paid))
        name='phase-robust-active-'+str(i)
        save(path/'robust_active'/f'{name}.json',dict(problem=specification(p),transcript=t,offers=offers,model=model,upper=upper,budget=budget,decision=decision,actual=actual))
        rows.append(dict(case=name,kind='active-continuous',problem='phase',interval=decision['interval'],nodes=decision['nodes'],actual_recovery=bool(actual and actual['result']['action']=='recover')))
    save(path/'results.json',rows); save(path/'completion.json',dict(events=history.count,last_hash=history.last))
    save(path/'runtime.json',dict(core_execution_seconds=time.perf_counter()-clock))
    if sources()!=manifest['sources']: raise RuntimeError('source changed after manifest freeze')
    check_previous()
    from .reporting import report
    report(path)
    save(path/'output_hashes.json',dict(files={p.relative_to(path).as_posix():digest(p) for p in sorted(path.rglob('*')) if p.is_file() and p.name not in ('audit.json','output_hashes.json')}))
    from .audit import audit
    result=audit(path); save(path/'audit.json',result); print(result,flush=True)
    return result


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--run'); parser.add_argument('--development',action='store_true'); args=parser.parse_args()
    cfg=read(Path(__file__).with_name('config.json')); execute(ROOT/(args.run or cfg['run']),cfg,args.development)


if __name__=='__main__': main()
