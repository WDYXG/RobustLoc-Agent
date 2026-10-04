"""Immutable run: freeze first, execute both models, audit and retain gaps."""
from copy import deepcopy
from fractions import Fraction as F
from pathlib import Path
import argparse
import platform
import time
from v3b.assumption_agent.storage import read,save,Writer
from v3c.trust_agent.simulator import service
from v3c.trust_agent.actions import apply
from v3c.trust_agent.core import basis
from v3c.trust_agent.verifier import feasible_world
from .freeze import ROOT,sources,check,digest
from .worlds import finite_case,response
from .finite import key
from .agent import finite_decision,continuous_decision
from .experiments import continuous_case
from .subsets import recover_subsets,uniform_upper
from .subset_verify import verify_subset_cover
from .analytic import make_case as analytic_case,analyze_case


def execute_tree(obs,model,tree,world,writer,case):
    state=deepcopy(obs); node=tree; cost=F(0); path=[]
    while not node['terminal']:
        o=next(o for o in state['offers'] if o['id']==node['action'])
        reply=response(state,o,world); following=apply(state,o,reply)
        writer.event(dict(mode='finite',case=case,world=world['id'],before=state,offer=o,reply=reply,after=following))
        path.append(o['id']); cost+=F(o['cost']); state=following; node=node['children'][key(reply)]
    circle=node['circle']; error2=sum((F(a)-F(b))**2 for a,b in zip(circle['centre'],world['target']))
    if error2>F(obs['tolerance'])**2 or not feasible_world(state,world): raise AssertionError('unsafe finite tree execution')
    return dict(world=world['id'],cost=str(cost),actions=path,terminal_worlds=node['worlds'],circle=circle,error2=str(error2))


def continuous_trial(obs,private,budget,limit,cfg,w,case):
    decision=continuous_decision(obs,cfg,budget,node_limit=limit)
    state=deepcopy(obs); cost=F(0); actual=None
    if decision['interval']['state']=='certifiably-recoverable':
        for oid in decision['upper']['offers']:
            o=next(o for o in state['offers'] if o['id']==oid); reply=service(state,o,private); after=apply(state,o,reply)
            w.event(dict(mode='continuous',case=case,before=state,offer=o,reply=reply,after=after))
            state=after; cost+=F(o['cost'])
        old=basis(state); cert=recover_subsets(state,cfg)
        actual=dict(old_all_measurement_pre_certified=old['pre_certified'],old_pre_bound=old['pre_bound'],certificate=cert)
        if cert['certified']:
            radius=verify_subset_cover(state,cert)
            error2=sum((F(a)-F(b))**2 for a,b in zip(cert['position'],private['target']))
            actual.update(error2=str(error2),bound_violation=error2>radius**2,
                          automatic_old_miss_repaired=not old['pre_certified'])
            if actual['bound_violation']: raise AssertionError('continuous bound violated')
        else: actual.update(automatic_old_miss_repaired=False,reason='physical-upper-exists-but-point-candidate-search-incomplete')
    if cost>F(budget) or not feasible_world(state,dict(target=private['target'],positions=private['positions'])):
        raise AssertionError('physical/budget contract failed')
    artifact=dict(observation=obs,private=private,budget=budget,node_limit=limit,decision=decision,final_observation=state,
                  spent=str(cost),actual=actual)
    w.artifact('continuous/'+case+'.json',artifact)
    return dict(case=case,mode='continuous',budget=budget,interval=decision['interval'],
       witness_count=len(decision['finite_restriction']['witnesses']),adaptive_states=decision['finite_restriction']['search']['adaptive_states'],
       uniform_nodes=decision['upper']['search']['nodes'],uniform_search_complete=decision['upper']['search']['complete'],
       subset_nodes=actual['certificate']['search']['subset_nodes'] if actual else 0,
       actual_output=bool(actual and actual['certificate']['certified']),
       automatic_old_miss_repaired=bool(actual and actual['automatic_old_miss_repaired']))


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--run'); args=parser.parse_args()
    cfg=read(Path(__file__).with_name('config.json')); old=read(ROOT/cfg['old_config'])
    path=ROOT/(args.run or cfg['run'])
    if path.exists(): raise RuntimeError('immutable run exists; choose a fresh --run')
    prior=check(); path.mkdir(parents=True); start=time.perf_counter(); timings=[]
    manifest=dict(config=cfg,previous_files=prior,sources=sources(),python=platform.python_version(),
        scope='sources/config/seeds frozen before held-out; finite exact and continuous bounds kept separate')
    save(path/'manifest.json',manifest); w=Writer(path); rows=[]
    # Compulsory old development instance, preserved separately from held-out.
    obs,p,B,limit=continuous_case('regression',0,old['development_seed'],old)
    t=time.perf_counter(); regression=continuous_trial(obs,p,B,limit,old,w,'compulsory-development-regression')
    if not regression['automatic_old_miss_repaired']: raise AssertionError('compulsory regression not fixed')
    timings.append(dict(case=regression['case'],seconds=time.perf_counter()-t))
    w.artifact('compulsory_regression.json',regression)
    for kind in cfg['finite_kinds']:
        for i in range(cfg['finite_variants']):
            name=kind+'-'+str(i); t=time.perf_counter(); obs,model=finite_case(kind,i,cfg['heldout_seed'])
            decision=finite_decision(obs,model,cfg['finite_budget']); result=decision['finite']; outcomes=[]
            if result['optimal_tree'] is not None:
                # Counterfactual execution in EVERY finite prior world checks the
                # mathematical optimum even when the decision budget is too low.
                outcomes=[execute_tree(obs,model,result['optimal_tree'],world,w,name) for world in model['worlds']]
                if max(F(o['cost']) for o in outcomes)!=F(result['adaptive_cost']): raise AssertionError('minimax tree execution')
            w.artifact('finite/'+name+'.json',dict(observation=obs,model=model,budget=cfg['finite_budget'],decision=decision,outcomes=outcomes))
            rows.append(dict(case=name,mode='finite-complete',interval=decision['interval'],
                batch_cost=result['hypergraph_batch']['cost'],pair_batch_cost=result['pair_batch']['cost'],
                incident_lower=result['incident_lower'],witness_count=len(result['witnesses']),
                pair_count=result['pair_count'],triple_count=result['triple_count'],adaptive_states=result['search']['adaptive_states'],
                cover_nodes=result['search']['cover_nodes']))
            timings.append(dict(case=name,seconds=time.perf_counter()-t))
        print('completed finite',kind,flush=True)
    for kind in cfg['continuous_kinds']:
        for i in range(cfg['continuous_variants']):
            t=time.perf_counter(); obs,p,B,limit=continuous_case(kind,i,cfg['heldout_seed']+1000,old)
            row=continuous_trial(obs,p,B,limit,old,w,kind+'-'+str(i)); rows.append(row)
            timings.append(dict(case=row['case'],seconds=time.perf_counter()-t))
        print('completed continuous',kind,flush=True)
    for i in range(cfg['analytic_variants']):
        t=time.perf_counter(); obs,model,proof=analytic_case(i); name=obs['episode_id']; B=cfg['finite_budget']
        decision=analyze_case(obs,model,proof,B)
        weaker=uniform_upper(obs)
        outcomes=[execute_tree(obs,model,decision['finite']['optimal_tree'],world,w,name) for world in model['worlds']]
        w.artifact('analytic/'+name+'.json',dict(observation=obs,model=model,completeness_certificate=proof,budget=B,decision=decision,outcomes=outcomes,uniform_ball_family=weaker))
        rows.append(dict(case=name,mode='continuous-exact-reduction',budget=B,interval=decision['interval'],
            witness_count=len(decision['finite']['witnesses']),adaptive_states=decision['finite']['search']['adaptive_states'],
            uniform_ball_family_upper=weaker['cost_upper']))
        timings.append(dict(case=name,seconds=time.perf_counter()-t))
    print('completed exact continuous reductions',flush=True)
    w.artifact('results.json',rows)
    if sources()!=manifest['sources']: raise RuntimeError('frozen source changed during evaluation')
    check(); save(path/'completion.json',dict(events=w.events,last_hash=w.prev))
    save(path/'runtime.json',dict(elapsed_seconds=time.perf_counter()-start,cases=timings))
    from .reporting import report
    report(path)
    save(path/'output_hashes.json',dict(files={str(p.relative_to(path)).replace('\\','/'):digest(p) for p in sorted(path.rglob('*')) if p.is_file() and p.name not in ('output_hashes.json','audit.json')}))
    from .audit import audit
    result=audit(path); save(path/'audit.json',result); print(result,flush=True)


if __name__=='__main__': main()
