"""Read-only independent arithmetic/numerical verifier subprocess."""
import argparse
from fractions import Fraction as F
from itertools import combinations
import numpy as np
from robustloc.storage import read, save
from .exact import dataset,point,point_upper,sqrt_interval,distance2
from .verifier import verify_certificate,verify_upper,require

def verify(stage,e,cfg,profile_evidence=None):
    details={}; status='numerically-supported'
    if stage==1:
        require(e['trials']==cfg['algebra_trials'] and e['max_discrepancy']<1e-10,'T1 experiments')
        rng=np.random.default_rng(cfg['seed']); discrepancies=[]
        for _ in range(cfg['algebra_trials']):
            p=rng.normal(size=(7,2)); w=rng.uniform(.2,2,size=7)
            x,z=rng.normal(size=(2,2)); q=int(rng.integers(0,4)); m=7-2*q
            vals=[w[i]*(np.linalg.norm(x-p[i])-np.linalg.norm(z-p[i]))**2 for i in range(7)]
            brute=min(sum(vals[i] for i in s) for s in combinations(range(7),m))
            discrepancies.append(abs(brute-sum(sorted(vals)[:m])))
        require(max(discrepancies)<1e-10,'independent T1 recomputation')
        details=dict(trials=len(discrepancies),max_discrepancy=max(discrepancies),proof_label='known')
    elif stage==2:
        a=[point(p) for p in e['anchors']]
        require(e['domain']==['-1','1','0','0'] and e['q']==1,'domain witness')
        require(len(a)==4 and all(p[1]==0 and p[0]>1 for p in a),'segment geometry')
        require(e['ambient_gamma2']=='0' and e['restricted_mu2']=='2','analytic witness')
        status='refuted'; details=dict(repair='T3 requires interior/tangent directions',proof='THEORY.md R-domain')
    elif stage==3:
        a,w,_=dataset(cfg['data']); p=np.array(a,dtype=float); w=np.array(w,dtype=float)
        errors=[]
        require(len(e['rows'])==cfg['local_limit_trials'],'local trials')
        for row in e['rows']:
            x=np.array(row['x']); m=len(p)-2*row['q']
            A=np.sqrt(w)[:,None]*(x-p)/np.linalg.norm(x-p,axis=1)[:,None]
            best=min((np.linalg.svd(A[list(s)],full_matrices=False) for s in combinations(range(len(p)),m)),
                     key=lambda sv:sv[1][-1])
            gamma=best[1][-1]
            require(abs(gamma-row['gamma'])<1e-10,'local singular value')
            errors.append(abs(row['ratios'][-1]-gamma))
            # Ratio is from the producer's chosen minimizing eigenvector; independently
            # check convergence error against a uniform Hessian Taylor bound.
            distance=np.min(np.linalg.norm(x-p,axis=1))
            for t,r in zip(row['steps'],row['ratios']):
                L=np.sqrt(w.sum())/(distance-t)
                require(abs(r-gamma)<=L*t/2+1e-8,'local secant Taylor bound')
        details=dict(trials=len(errors),max_final_limit_error=max(errors),proof='THEORY.md T3 repaired')
    elif stage==4:
        if e['status']!='refuted': return dict(status='conjectured',details=dict(reason='No exact witness found'))
        a=[point(v) for v in e['anchors']]; w=list(map(F,e['weights']))
        x,z=point(e['witness']['x']),point(e['witness']['z'])
        ub,equal=point_upper(a,w,x,z,e['q'])
        require(ub==0 and equal>=len(a)-2*e['q'],'C3 exact global ambiguity')
        require(e['witness']['upper']=='0' and e['witness']['equal_coordinates']==equal,'C3 upper')
        local=[]
        require(len(e['local_certificates'])==2,'two domain components')
        for b,c in zip(e['domain_boxes'],e['local_certificates']):
            require(c['data']==dict(anchors=e['anchors'],weights=e['weights'],domain=b)
                    and c['q']==e['q'],'local certificate binding')
            local.append(F(verify_certificate(c)['local_lower']))
        require(min(local)==F(e['local_lower']) and min(local)>0,'whole-domain local margin')
        for c,b in zip((x,z),e['domain_boxes']):
            b=list(map(F,b)); require(b[0]<=c[0]<=b[1] and b[2]<=c[1]<=b[3],'branch centre membership')
        status='refuted'; details=dict(mu='0',uniform_local_lower=str(min(local)),proof='THEORY.md C3/R-branch')
    elif stage==5:
        c=e['certificate']; require(c['data']['domain']==['-6','6','-6','6'],'anchor-containing D')
        details=verify_certificate(c); require(F(details['scatter_lower'])>0,'T5 positive extension')
        status='proved-in-project'
    elif stage==6:
        a=[point(v) for v in e['anchors']]; w=list(map(F,e['weights']))
        prev=None
        for row in e['rows']:
            R=F(row['R']); require(point(row['x'])==(R,F(0)) and point(row['z'])==(R,F(1)),'far field pair')
            ub,_=point_upper(a,w,point(row['x']),point(row['z']),0)
            require(str(ub)==row['upper'] and (prev is None or ub<prev),'far field upper')
            prev=ub
        status='refuted'; details=dict(proof='THEORY.md R-unbounded',limiting_upper='0')
    elif stage==7:
        lowers=[]; uppers=[]; verified=[]
        require([r['q'] for r in e['rows']]==cfg['q_values'],'profile completeness')
        for row in e['rows']:
            require(row['certificate']['data']==cfg['data'] and row['certificate']['q']==row['q'],'profile binding')
            result=verify_certificate(row['certificate'])
            ub=verify_upper(cfg['data'],row['q'],row['upper_witness'])
            lowers.append(F(result['certified_lower'])); uppers.append(F(ub)); verified.append(result)
            require(lowers[-1]<=uppers[-1],'lower versus witness upper')
        require(all(a>=b for a,b in zip(lowers,lowers[1:])),'certified profile monotonicity')
        k=F(cfg['kappa'])
        low=max((q for q,b in zip(cfg['q_values'],lowers) if b>=k),default=None)
        up=max((q for q,b in zip(cfg['q_values'],uppers) if b>=k),default=None)
        require(e['q_cert_lower']==low and e['q_cert_possible_upper']==up,'q certificate budget')
        status='proved-in-project'; details=dict(certificates=verified,q_cert_lower=low,q_cert_possible_upper=up)
    elif stage==8:
        require(profile_evidence is not None,'profile prerequisite')
        p,w,_=dataset(cfg['data']); p=np.array(p,dtype=float); w=np.array(w,dtype=float); ratios=[]
        require(len(e['rows'])==cfg['recovery_trials'],'recovery trials')
        for row in e['rows']:
            x,z,y=np.array(row['x']),np.array(row['z']),np.array(row['y']); q=row['q']
            require(np.all(abs(x)<=1) and np.all(abs(z)<=1),'recovery D membership')
            hx,hz=np.linalg.norm(x-p,axis=1),np.linalg.norm(z-p,axis=1)
            require(len(set(row['bad1']))<=q and len(set(row['bad2']))<=q,'corruption budgets')
            clean1=[i for i in range(len(p)) if i not in row['bad1']]
            clean2=[i for i in range(len(p)) if i not in row['bad2']]
            e1=np.linalg.norm(np.sqrt(w[clean1])*(y[clean1]-hx[clean1]))
            e2=np.linalg.norm(np.sqrt(w[clean2])*(y[clean2]-hz[clean2]))
            b=float(F(profile_evidence['rows'][q]['certificate']['certified_lower']))
            error=np.linalg.norm(x-z); bound=(e1+e2)/b
            require(abs(e1-row['eps1'])<1e-10 and abs(e2-row['eps2'])<1e-10,'residual budgets')
            require(abs(bound-row['bound'])<1e-10 and abs(error-row['error'])<1e-10,'bound recompute')
            require(error<=bound+1e-10,'T2 numerical bound')
            ratios.append(error/bound)
        details=dict(trials=len(ratios),max_error_to_bound=max(ratios),proof='THEORY.md T2')
    else: raise ValueError('Unknown research stage')
    return dict(status=status,details=details,
        scope='Independent arithmetic/numerical check; written proofs are not formal machine proofs')

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('stage',type=int)
    parser.add_argument('evidence'); parser.add_argument('output'); parser.add_argument('--profile')
    args=parser.parse_args()
    from pathlib import Path
    cfg=read(Path(__file__).with_name('config.json'))
    save(args.output,verify(args.stage,read(args.evidence),cfg,read(args.profile) if args.profile else None))
