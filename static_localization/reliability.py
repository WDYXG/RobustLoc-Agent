"""Bounded-contract checks and one executed acquisition trace, separate from Gaussian benchmark."""
import argparse
import copy
import math
from pathlib import Path
import numpy as np
from .service import localize, observations, certify, INCUMBENT, rational
from .study import save, hashes, frozen_history
from v3b.assumption_agent.certificates import build
from v3b.assumption_agent.verifier import verify_margin


def make_case(n, geometry, seed):
    rng=np.random.default_rng(seed)
    angles=np.linspace(0,2*np.pi,n,endpoint=False) if geometry=='surround' else np.linspace(-.15,.15,n)
    p=60*np.column_stack((np.cos(angles),np.sin(angles)))
    if geometry=='line': p=np.column_stack((np.linspace(-65,65,n),np.linspace(-.02,.02,n)))
    truth=rng.uniform(-15,15,2)
    actual=p+rng.uniform(-.02,.02,(n,2))
    d=np.linalg.norm(truth-actual,axis=1)+rng.uniform(-.03,.03,n); d[0]+=80
    reports=[dict(id=f'r{i}',position=p[i].tolist(),position_sigma=.03,
                  distance=float(d[i]),distance_sigma=.03,confidence=1.) for i in range(n)]
    contract=dict(q_max=1,epsilon_max='1/5',domain=['-100','100','-100','100'],
                  radii=['1/20']*n,error_tolerance='30',provenance='Controlled bounded synthetic generator, not field assurance')
    return dict(reports=reports,units='metres',contract=contract,information_available=True),truth


def score(payload, new_position):
    p=[r['position'] for r in payload['reports']]+[new_position]
    data=dict(anchors=[[rational(v) for v in a] for a in p],weights=['1']*len(p),
              radii=payload['contract']['radii']+['1/20'],domain=payload['contract']['domain'])
    # Ties at the worst corruption level are broken with q=0, never truth/error.
    return tuple(verify_margin(build(data,q)) for q in (1,0))


def run(output, config=INCUMBENT):
    out=Path(output); out.mkdir(parents=True,exist_ok=False)
    before=hashes(); save(out/'manifest.json',dict(source_sha256=before,
        scope='Separate conditional certification and deliberate contract-violation study',
        seeds='44000000 + 1000*n + 100*geometry_index + k; k=0..5'))
    rows=[]
    for n in (11,16):
        for j,g in enumerate(('surround','sector','line')):
            for k in range(6):
                seed=44000000+1000*n+100*j+k
                payload,truth=make_case(n,g,seed)
                answer=localize(payload,config)
                save(out/f'case-{seed}.json',dict(observation=payload,output=answer,
                     evaluation_private=dict(truth=truth.tolist(), stress_truth=(truth+np.array([60.,0])).tolist(),
                     stress_model='Shift physical target and all physical reporters by +60m; reported coordinates unchanged')))
                for regime,t in [('valid-contract',truth),('understated-common-position-bias',truth+np.array([60.,0]))]:
                    pos=answer['reliable_position'] if answer['decision']=='recover' else answer['estimate']
                    error=float(np.linalg.norm(np.array(pos)-t)); certified=answer['decision']=='recover'
                    rows.append(dict(seed=seed,n=n,geometry=g,regime=regime,error=error,certified=certified,
                                     bound=answer['reliability'].get('error_bound_metres'),
                                     false_output=certified and error>30))
    payload,truth=make_case(11,'line',44999999)
    # Future measurements are generated once, hidden from the selection function.
    offers=[[-60.,-60.],[0.,-60.],[60.,-60.],[-60.,60.],[0.,60.],[60.,60.]]
    receipts={i:float(np.linalg.norm(truth-np.array(p))) for i,p in enumerate(offers)}
    steps=[]
    for step in range(4):
        answer=localize(payload,config)
        steps.append(dict(step=step,observation=copy.deepcopy(payload),answer=answer,
                          evaluation_error=float(np.linalg.norm(np.array(answer['reliable_position'] if answer['decision']=='recover' else answer['estimate'])-truth))))
        if answer['decision']=='recover' or step==3: break
        remaining=[i for i in range(len(offers)) if f'new-{i}' not in {r['id'] for r in payload['reports']}]
        selected=max(remaining,key=lambda i:score(payload,offers[i]))
        scores={str(i):[str(v) for v in score(payload,offers[i])] for i in remaining}
        steps[-1]['acquisition']=dict(selected=selected,position=offers[selected],public_scores=scores,
              receipt=receipts[selected],executed=True,scope='Synthetic information provider; no physical scan')
        payload['reports'].append(dict(id=f'new-{selected}',position=offers[selected],position_sigma=.03,
                                       distance=receipts[selected],distance_sigma=.03,confidence=1.))
        payload['contract']['radii'].append('1/20')
    save(out/'rows.json',rows); save(out/'acquisition.json',dict(steps=steps,evaluation_truth=truth.tolist()))
    save(out/'completion.json',dict(source_unchanged=hashes()==before,historical_files_unchanged=frozen_history()))


if __name__=='__main__':
    import json
    p=argparse.ArgumentParser(); p.add_argument('output'); p.add_argument('--method',required=True)
    a=p.parse_args(); run(a.output,json.loads(Path(a.method).read_text())['config'])
