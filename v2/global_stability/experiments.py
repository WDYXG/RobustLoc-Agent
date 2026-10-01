"""Counterexample searches, upper witnesses and fixed theorem stress checks."""
from fractions import Fraction as F
from itertools import combinations
import random
import numpy as np
from .exact import (dataset, point_upper, survivors, encode, box, point,
                    distance2, sqrt_interval)
from .certificate import local_bound, build

def witness(anchors,weights,x,z,q):
    ub,equal=point_upper(anchors,weights,x,z,q)
    return encode(dict(x=x,z=z,upper=ub,equal_coordinates=equal))

def algebra(cfg):
    rng=np.random.default_rng(cfg['seed']); maximum=0.0
    for _ in range(cfg['algebra_trials']):
        p=rng.normal(size=(7,2)); w=rng.uniform(.2,2,size=7)
        x,z=rng.normal(size=(2,2)); q=int(rng.integers(0,4)); m=7-2*q
        a=w*(np.linalg.norm(x-p,axis=1)-np.linalg.norm(z-p,axis=1))**2
        sorted_value=float(np.sort(a)[:m].sum())
        brute=min(float(a[list(s)].sum()) for s in combinations(range(7),m))
        maximum=max(maximum,abs(sorted_value-brute))
    return dict(trials=cfg['algebra_trials'],max_discrepancy=maximum,
                status='numerically-supported',proof_status='known')

def domain_witness():
    return dict(domain=['-1','1','0','0'],anchors=[['2','0'],['3','0'],['4','0'],['5','0']],
                q=1,ambient_gamma2='0',restricted_mu2='2',status='refuted',
                claim='Unrestricted compact-domain T3 necessary local condition')

def local_limits(cfg):
    rng=np.random.default_rng(cfg['seed']+3); rows=[]
    anchors,w,_=dataset(cfg['data']); p=np.array(anchors,dtype=float); w=np.array(w,dtype=float)
    for trial in range(cfg['local_limit_trials']):
        x=rng.uniform(-.8,.8,2); q=trial%3; m=len(p)-2*q
        u=(x-p)/np.linalg.norm(x-p,axis=1)[:,None]; A=np.sqrt(w)[:,None]*u
        candidates=[]
        for s in combinations(range(len(p)),m):
            ev,V=np.linalg.eigh(A[list(s)].T@A[list(s)])
            candidates.append((ev[0],V[:,0]))
        ev,v=min(candidates,key=lambda row:row[0]); gamma=float(np.sqrt(ev))
        ratios=[]
        for t in [1e-2,1e-3,1e-4,1e-5]:
            diff=np.linalg.norm(x+t*v-p,axis=1)-np.linalg.norm(x-p,axis=1)
            ratios.append(float(np.sqrt(np.sort(w*diff**2)[:m].sum())/t))
        rows.append(dict(q=q,x=x.tolist(),gamma=gamma,steps=[1e-2,1e-3,1e-4,1e-5],ratios=ratios))
    return dict(rows=rows,status='numerically-supported',scope='ambient limit check; theorem is written separately')

def branch_search():
    """Search a declared rational family; exact equality + positive whole-box local bound."""
    anchors=[point(p) for p in [['-2','0'],['0','0'],['2','0'],['1','3']]]
    weights=[F(1)]*4; q=1; tested=[]
    for k in [3,0,1,2,4,5,6,7,8,9]:
        x=point([F(k,10),1]); z=point([F(k,10),-1]); rho=F(1,10000)
        boxes=[(c[0]-rho,c[0]+rho,c[1]-rho,c[1]+rho) for c in (x,z)]
        lower=[local_bound(anchors,weights,b,q,1)['lower'] for b in boxes]
        ub,equal=point_upper(anchors,weights,x,z,q)
        tested.append(encode(dict(k=k,upper=ub,local_lower=min(lower))))
        if ub==0 and min(lower)>0:
            certificates=[build(encode(dict(anchors=anchors,weights=weights,domain=b)),q,
                                divisions=1,delta='1/100',max_leaves=1) for b in boxes]
            return encode(dict(anchors=anchors,weights=weights,q=q,domain_boxes=boxes,
                witness=witness(anchors,weights,x,z,q),local_lower=min(lower),tested=tested,
                local_certificates=certificates,
                status='refuted',claim='C3 mu equals inf local gamma',
                restriction='disconnected full-dimensional compact domain'))
    return dict(status='conjectured',tested=tested,reason='Family search exhausted, not a proof')

def bounded_extension(cfg):
    data=dict(cfg['data']); data['domain']=['-6','6','-6','6']
    return dict(certificate=build(data,1,divisions=2,max_leaves=1),
        status='proved-in-project',claim='T5 anchor-containing bounded-domain extension',
        scope='written derivation plus exact rational scatter certificate')

def profile(cfg):
    data=cfg['data']; anchors,weights,domain=dataset(data)
    rng=random.Random(cfg['seed']); points=[]
    for _ in range(cfg['pair_samples']):
        pair=[]
        for _ in (0,1):
            pair.append((domain[0]+(domain[1]-domain[0])*F(rng.randrange(1000001),1000000),
                         domain[2]+(domain[3]-domain[2])*F(rng.randrange(1000001),1000000)))
        if pair[0]!=pair[1]: points.append(pair)
    points.extend([(point([0,'1/2']),point([0,'-1/2'])),
                   (point(['-1','-1']),point(['1','1'])),
                   (point(['-1','1']),point(['1','-1']))])
    rows=[]
    for q in cfg['q_values']:
        cert=build(data,q,cfg['grid_divisions'],cfg['delta'],cfg['max_leaves'],cfg['far_target'])
        best=min((witness(anchors,weights,x,z,q) for x,z in points),key=lambda row:F(row['upper']))
        rows.append(dict(q=q,certificate=cert,upper_witness=best,
                         status='proved-in-project' if F(best['upper'])==0 else 'numerically-supported'))
    kappa=F(cfg['kappa'])
    lower=[r['q'] for r in rows if F(r['certificate']['certified_lower'])>=kappa]
    upper=[r['q'] for r in rows if F(r['upper_witness']['upper'])>=kappa]
    return dict(rows=rows,kappa=str(kappa),q_cert_lower=max(lower,default=None),
        q_cert_possible_upper=max(upper,default=None),samples=len(points),seed=cfg['seed'],
        status='proved-in-project',scope='conditional q budgets, not actual corruption-count inference')

def recovery(cfg,profile_evidence):
    rng=np.random.default_rng(cfg['seed']+2); anchors,weights,_=dataset(cfg['data'])
    p=np.array(anchors,dtype=float); w=np.array(weights,dtype=float); rows=[]
    for trial in range(cfg['recovery_trials']):
        q=trial%3; cert=profile_evidence['rows'][q]['certificate']; b=float(F(cert['certified_lower']))
        x,z=rng.uniform(-1,1,size=(2,2)); hx=np.linalg.norm(x-p,axis=1); hz=np.linalg.norm(z-p,axis=1)
        # Construct a common observation with two distinct q-sparse explanations.
        perm=rng.permutation(len(p)); B1=perm[:q]; B2=perm[q:2*q]
        y=(hx+hz)/2; y[B1]=hz[B1]; y[B2]=hx[B2]
        clean1=np.ones(len(p),dtype=bool); clean1[B1]=False
        clean2=np.ones(len(p),dtype=bool); clean2[B2]=False
        eps1=float(np.linalg.norm(np.sqrt(w[clean1])*(y[clean1]-hx[clean1])))
        eps2=float(np.linalg.norm(np.sqrt(w[clean2])*(y[clean2]-hz[clean2])))
        bound=(eps1+eps2)/b; error=float(np.linalg.norm(x-z))
        rows.append(dict(q=q,x=x.tolist(),z=z.tolist(),y=y.tolist(),bad1=B1.tolist(),bad2=B2.tolist(),
                         eps1=eps1,eps2=eps2,error=error,bound=bound,ratio=error/bound))
    return dict(rows=rows,status='numerically-supported',
        scope='constructed two-explanation bound stress, no estimator performance claim')

def unbounded_witness(cfg):
    p=cfg['data']['anchors'][:3]; weights=['1']*3
    anchors=[point(v) for v in p]; weightsF=[F(1)]*3
    return dict(anchors=p,weights=weights,q=0,
        rows=[dict(R=R,**witness(anchors,weightsF,point([R,0]),point([R,1]),0)) for R in [10,100,1000,10000]],
        status='refuted',claim='Full-plane injectivity implies uniform inverse stability')
