"""Post-run independent replay audit; does not change evaluator or selected method."""
import argparse
from fractions import Fraction as F
import json
from pathlib import Path
import numpy as np
from static_localization.service import localize
from static_localization.reliability import make_case, score
from v3b.assumption_agent.verifier import verify_recovery, verify_frontier


def load(p): return json.loads(p.read_text(encoding='utf-8'))


def run(folder, method, output):
    if output.exists(): raise FileExistsError(output)
    cfg=load(method)['config']; rows=load(folder/'rows.json'); count=certs=0
    for file in sorted(folder.glob('case-*.json')):
        obj=load(file); seed=int(file.stem.split('-')[-1]); obs=obj['observation']
        original=obj['output']; result=localize(obs,cfg)
        assert result==original
        r=next(r for r in rows if r['seed']==seed and r['regime']=='valid-contract')
        regenerated,t=make_case(r['n'],r['geometry'],seed)
        assert regenerated==obs
        assert np.allclose(t,obj['evaluation_private']['truth'],atol=0,rtol=0)
        rel=result['reliability']
        if result['decision']=='recover':
            bound=verify_recovery(rel['observation'],rel['decision']); certs+=1
            assert np.linalg.norm(np.array(result['reliable_position'])-t)<=float(bound)
        for regime,target in [('valid-contract',t),('understated-common-position-bias',t+[60.,0])]:
            row=next(r for r in rows if r['seed']==seed and r['regime']==regime)
            p=result['reliable_position'] if result['decision']=='recover' else result['estimate']
            error=float(np.linalg.norm(np.array(p)-target))
            assert abs(error-row['error'])<1e-10
            assert row['false_output']==(result['decision']=='recover' and error>30)
        count+=1
    acq=load(folder/'acquisition.json'); margins=[]
    for step in acq['steps']:
        obs=step['observation']; a=step['answer']; assert localize(obs,cfg)==a
        rel=a['reliability']; f=rel.get('frontier',rel.get('decision',{}).get('frontier'))
        margins.append(float(F(f['rows'][-1]['lower'])))
        if a['decision']=='recover': verify_recovery(rel['observation'],rel['decision'])
        if 'acquisition' in step:
            receipt=step['acquisition']
            assert list(map(str,score(obs,receipt['position'])))==receipt['public_scores'][str(receipt['selected'])]
            best=max(receipt['public_scores'],key=lambda k:tuple(map(F,receipt['public_scores'][k])))
            assert int(best)==receipt['selected']
            nxt=acq['steps'][step['step']+1]['observation']['reports']
            assert nxt[:-1]==obs['reports'] and nxt[-1]['distance']==receipt['receipt']
            assert abs(np.linalg.norm(np.array(acq['evaluation_truth'])-receipt['position'])-receipt['receipt'])<1e-10
    output.write_text(json.dumps(dict(passed=True,full_bounded_solver_replays=count,
        independently_verified_recoveries=certs,acquisition_steps_replayed=len(acq['steps']),
        q1_verified_lower_bounds=margins,valid_contract_error_bound_violations=0,
        invalid_contract_false_outputs=sum(r['false_output'] for r in rows if r['regime']!='valid-contract')),
        indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('folder',type=Path); p.add_argument('method',type=Path); p.add_argument('output',type=Path)
    a=p.parse_args(); run(a.folder,a.method,a.output)
