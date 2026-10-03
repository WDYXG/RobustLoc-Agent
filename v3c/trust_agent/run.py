"""Fresh immutable joint-world experiment, all decisions and negative results retained."""
import argparse
from copy import deepcopy
from pathlib import Path
from fractions import Fraction as F
import platform
import time
from v3b.assumption_agent.storage import read,save,Writer
from .freeze import ROOT,check,sources,digest
from .simulator import make,service
from .actions import apply
from .policy import choose,trust_frontier
from .tasks import execute
from .verifier import feasible_world,verify_cover


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--run'); args=parser.parse_args()
    cfg=read(Path(__file__).with_name('config.json')); path=ROOT/(args.run or cfg['run'])
    if path.exists(): raise RuntimeError('Immutable run exists: use a new --run folder')
    n=check(); path.mkdir(parents=True); start=time.time()
    manifest=dict(config=cfg,sources=sources(),previous_files=n,python=platform.python_version(),
        evaluation='source/config/seed frozen before held-out; no post-heldout tuning')
    save(path/'manifest.json',manifest); w=Writer(path); tasks=execute(cfg); w.artifact('research_tasks.json',tasks)
    rows=[]
    for sid,scenario in enumerate(cfg['scenarios']):
        for index in range(cfg['episodes_per_scenario']):
            initial,private=make(scenario,index,cfg,cfg['heldout_seed']+sid*1000)
            name=initial['episode_id']; w.artifact('episodes/'+name+'/observation.json',initial); w.artifact('episodes/'+name+'/private.json',private)
            for method in cfg['methods']:
                obs=deepcopy(initial); cost=F(0); actions=[]; diagnoses=[]; first=None
                for step in range(len(initial['offers'])+1):
                    d=choose(obs,method,cfg,cfg['random_seed']+sid*1000+index*100+step)
                    if first is None: first=d['action']=='recover'
                    event=dict(episode_id=name,method=method,step=step,observation=obs,decision=d)
                    diagnoses.append(d['diagnosis'])
                    if d['action']!='acquire-information': w.event(event); break
                    offer=next(o for o in obs['offers'] if o['id']==d['offer_id']); reply=service(obs,offer,private)
                    event['reply']=reply; cost+=F(offer['cost']); actions.append(dict(id=offer['id'],kind=offer['kind'],cost=offer['cost']))
                    new=apply(obs,offer,reply); w.event(event); obs=new
                else: raise AssertionError('termination invariant')
                valid=feasible_world(obs,dict(target=private['target'],positions=private['positions']))
                if private['contract_valid'] and not valid: raise AssertionError('honest fixture out of model')
                error=bound_violation=None
                if d['action']=='recover':
                    verify_cover(obs,d['certificate']); error=sum(float(F(a)-F(b))**2 for a,b in zip(d['position'],private['target']))**.5
                    bound_violation=error>float(F(d['radius_upper']))+1e-10
                row=dict(episode_id=name,scenario=scenario,method=method,initially_certified=first,
                    output=d['action']=='recover',new_certified=d['action']=='recover' and not first,
                    information_cost=str(cost),actions=actions,diagnoses=diagnoses,final_diagnosis=d['diagnosis'],
                    contract_valid=valid,intended_in_contract=private['contract_valid'],error=error,
                    wrong_output=bool(error is not None and error>float(F(obs['tolerance']))),bound_violation=bool(bound_violation),
                    diameter_lower=d.get('witness',{}).get('diameter_lower') if d.get('witness') else None,
                    diameter_upper=d.get('certificate',{}).get('diameter_upper'),reason=d.get('reason'))
                rows.append(row); w.artifact('outcomes/'+name+'/'+method+'.json',dict(result=row,observation=obs,decision=d))
        print('completed',scenario,flush=True)
    w.artifact('results.json',rows)
    if manifest['sources']!=sources(): raise RuntimeError('sources mutated during frozen evaluation')
    check(); save(path/'completion.json',dict(history_events=w.events,last_hash=w.prev,elapsed_seconds=time.time()-start))
    from .reporting import report
    report(path)
    save(path/'output_hashes.json',dict(files={str(p.relative_to(path)).replace('\\','/'):digest(p) for p in sorted(path.rglob('*')) if p.is_file() and p.name not in ('output_hashes.json','audit.json')}))
    from .audit import audit
    result=audit(path); save(path/'audit.json',result); print(result,flush=True)


if __name__=='__main__': main()
