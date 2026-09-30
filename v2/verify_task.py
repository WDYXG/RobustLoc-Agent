"""Separate-process review of saved witnesses and numeric evidence.

It checks algebra/certificates; written theorem proofs are not machine-certified.
"""
import argparse
from itertools import combinations
import numpy as np
from robustloc.storage import read,save
from .verifier import independent_margin,check_estimate
from .estimator import Problem

def verify(stage,data):
    if stage==1:
        A=np.array(data['rows']); y=np.array(data['y'])
        checks=[np.array_equal(A@np.array(data['delta0'])+data['attack0'],y),np.array_equal(A@np.array(data['delta1'])+data['attack1'],y),data['alpha_q']>0,data['alpha_2q']==0]
        status='refuted'; scope='Exact support-splitting witness; mathematical explanation in R1'
    elif stage==2:
        checks=[data['max_eigenvalue_discrepancy']<1e-9,data['max_linear_bound_ratio']<=1+1e-7]
        status='numerically-supported'; scope='Finite checks of known K2-K4; proof status not assigned by tests'
    elif stage==3:
        r=data['global_reflection']; p=np.array(r['anchors']); x=np.array(r['position0']); z=np.array(r['position1'])
        diff=np.linalg.norm(x-p,axis=1)-np.linalg.norm(z-p,axis=1)
        l=data['l1_failure']; A=np.array(l['rows']); y=np.array([1.,0,0,0]); v=np.array([1.,0])
        checks=[np.count_nonzero(abs(diff)>1e-12)<=2,independent_margin(x,p,np.ones(4),2)>0,np.abs(y-A@v).sum()<np.abs(y).sum(),l['alpha_2q']>0]
        status='refuted'; scope='Global uniqueness and L1 overclaims refuted; exact constructions in R2/R3/R4'
    elif stage==4:
        checks=[data['minimum_observed_lower_lipschitz_ratio']>=1-1e-8,data['minimum_denominator']>0]
        status='numerically-supported'; scope='P1/P2 written proofs remain separate from finite checks'
    elif stage==5:
        if data['status']!='refuted': return dict(verified=True,status='conjectured',scope='Search exhausted without witness; unresolved')
        p=np.array(data['anchors']); d=np.array(data['observations']); positions=np.array(data['positions'])
        costs=[np.sum((np.linalg.norm(x-p,axis=1)-d)**2) for x in positions]
        alphas=[independent_margin(x,p,np.ones(len(p)),0) for x in positions]
        residual_choice=int(np.argmin(costs)); ratio_choice=int(np.argmin(np.array(costs)/alphas))
        true_noise=np.linalg.norm(d-np.linalg.norm(np.array(data['truth'])-p,axis=1))
        checks=[residual_choice!=ratio_choice,costs[ratio_choice]>data['epsilon_gate']**2+1e-10,true_noise<=data['epsilon_gate']+1e-10,np.linalg.norm(positions[ratio_choice])>np.linalg.norm(positions[residual_choice])]
        status='refuted'; scope=data['scope']
    elif stage==6:
        checks=[]
        for row in data['rows']:
            if row['status']=='abstain': continue
            problem=Problem(np.array(row['anchors']),np.array(row['observations']),np.array(row['weights']),row['q'],row['epsilon'],np.array(row['prior_center']),row['prior_radius'])
            result=dict(status='estimate',position=row['estimated_position'],trimmed_norm=row['trimmed_norm'],alpha_2q=independent_margin(np.array(row['estimated_position']),problem.anchors,problem.weights,2*problem.q),beta=row['beta'],feasible=row['trimmed_norm']<=row['epsilon']+1e-7,conditional_error_bound=row['conditional_bound'],mode=row['mode'])
            checks.append(check_estimate(problem,result)['verified'])
            if row['bound_applicable']: checks.append(row['bound_ratio']<=1+1e-7)
        status='numerically-supported'; scope='Fixed assumption-stress experiments; no universal accuracy advantage proved'
    else: raise ValueError('Unknown research stage')
    return dict(verified=bool(all(checks)),status=status,checks=len(checks),scope=scope,not_a_formal_proof=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('stage',type=int); parser.add_argument('input'); parser.add_argument('output'); args=parser.parse_args()
    result=verify(args.stage,read(args.input)); save(args.output,result)
    if not result['verified']: raise SystemExit('Independent verifier rejected evidence')
