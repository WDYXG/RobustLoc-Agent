"""Create a fresh immutable evaluation run; existing runs cannot be overwritten."""
import argparse
from copy import deepcopy
from fractions import Fraction as F
from pathlib import Path
import platform
import time
from .storage import read,save,Writer
from .freeze import ROOT,check,source_hashes,digest
from .simulator import make_episode,service,evaluate
from .contracts import deliver,volume_ratio
from .certificates import frontier
from .policy import choose
from .experiments import theory_tasks


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--run'); args=parser.parse_args()
    cfg=read(Path(__file__).with_name('config.json')); path=ROOT/(args.run or cfg['run'])
    if path.exists(): raise RuntimeError('Immutable run exists; use a new --run path')
    frozen=check(); path.mkdir(parents=True); start=time.time()
    manifest=dict(schema='assumption-run-v1',previous_files=frozen,sources=source_hashes(),config=cfg,
        environment=dict(python=platform.python_version(),platform=platform.platform()),
        heldout_policy='fixed configuration frozen before simulation; no post-heldout tuning')
    save(path/'manifest.json',manifest); writer=Writer(path)
    tasks=theory_tasks(cfg); writer.artifact('research_tasks.json',tasks)
    results=[]
    for sidx,scenario in enumerate(cfg['scenarios']):
        for index in range(cfg['episodes_per_scenario']):
            initial,private=make_episode(scenario,index,cfg,cfg['heldout_seed']+sidx*1000)
            writer.artifact('episodes/'+initial['episode_id']+'/observation.json',initial)
            writer.artifact('episodes/'+initial['episode_id']+'/private.json',private)
            writer.artifact('episodes/'+initial['episode_id']+'/initial_frontier.json',frontier(initial))
            for midx,method in enumerate(cfg['methods']):
                obs=deepcopy(initial); cost=F(0); acquisitions=[]; rejected=[]; first_certified=None
                for step in range(len(initial['offers'])+1):
                    decision=choose(obs,method,cfg,cfg['random_policy_seed']+sidx*10000+index*100+step)
                    if step==0: first_certified=decision['action']=='recover'
                    event=dict(episode_id=initial['episode_id'],method=method,step=step,
                               observation=obs,decision=decision)
                    if decision['action']!='acquire-more-data':
                        event['evaluation']=evaluate(obs,private,decision); writer.event(event); break
                    offer=next(o for o in obs['offers'] if o['id']==decision['offer_id'])
                    receipt=service(obs,offer,private); cost+=F(offer['cost'])
                    event['receipt']=receipt
                    try:
                        new=deliver(obs,offer,receipt); event['receipt_accepted']=True
                    except ValueError as exc:
                        event.update(receipt_accepted=False,rejection=str(exc)); rejected.append(str(exc))
                        new=deepcopy(obs); new['offers']=[o for o in obs['offers'] if o['id']!=offer['id']]
                        new['budget']=str(F(obs['budget'])-F(offer['cost']))
                    acquisitions.append(dict(kind=offer['kind'],id=offer['id'],cost=offer['cost'],accepted=event['receipt_accepted']))
                    writer.event(event); obs=new
                else: raise RuntimeError('finite action termination invariant failed')
                evaluation=evaluate(obs,private,decision); ratio=volume_ratio(initial,obs)
                row=dict(episode_id=initial['episode_id'],scenario=scenario,method=method,
                    initially_certified=first_certified,new_certified=bool(evaluation['output'] and not first_certified),
                    information_cost=str(cost),volume_ratio=str(ratio),volume_reduction=str(1-ratio),
                    acquisitions=acquisitions,rejected=rejected,evaluation=evaluation,
                    final_action=decision['action'],failure_reason=decision.get('reason'),
                    service_model_valid=private['trusted_service_model'])
                results.append(row)
                writer.artifact('outcomes/'+initial['episode_id']+'/'+method+'.json',dict(summary=row,
                    final_observation=obs,decision=decision,complete_frontier=frontier(obs)))
        print('completed',scenario,flush=True)
    writer.artifact('results.json',results)
    if source_hashes()!=manifest['sources']: raise RuntimeError('Sources changed during frozen evaluation')
    check()
    save(path/'completion.json',dict(events=writer.events,last_hash=writer.prev,elapsed_seconds=time.time()-start,
                                   previous_files_unchanged=frozen))
    from .reporting import report
    report(path)
    save(path/'output_hashes.json',dict(files={str(p.relative_to(path)).replace('\\','/'):digest(p)
        for p in sorted(path.rglob('*')) if p.is_file() and p.name not in ('output_hashes.json','audit.json')}))
    from .audit import audit
    result=audit(path); save(path/'audit.json',result)
    print(result,flush=True)


if __name__=='__main__': main()
