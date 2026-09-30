"""Assumption-oriented experiments; no access to v1 simulator or held-out."""
from itertools import combinations
import time
import numpy as np
from .geometry import margin,point_margin,directions,curvature_bound
from .estimator import Problem,candidate_pool,select
from .verifier import independent_margin,check_estimate

def algebra_checks(seed=7411,count=300):
    rng=np.random.default_rng(seed); discrepancies=[]; bound_ratios=[]
    for _ in range(count):
        angles=rng.uniform(-np.pi,np.pi,8); u=np.column_stack([np.cos(angles),np.sin(angles)])
        w=np.exp(rng.uniform(-1,1,8)); p=-u*rng.uniform(5,15,(8,1)); x=np.zeros(2)
        for k in [0,1,2,3]:
            discrepancies.append(abs(margin(u,w,k)['alpha']-independent_margin(x,p,w,k)))
        A=u*np.sqrt(w)[:,None]; epsilon=.01; delta=rng.normal(size=2)
        noise=rng.normal(size=8); noise*=epsilon/np.linalg.norm(noise)
        corrupt=np.zeros(8); corrupt[rng.integers(8)]=rng.choice([-1,1])*rng.uniform(1,100)
        y=A@delta+noise+corrupt
        fits=[]
        for ids in combinations(range(8),7):
            ix=list(ids); fit=np.linalg.lstsq(A[ix],y[ix],rcond=None)[0]
            score=np.sqrt(np.sort((A@fit-y)**2)[:7].sum()); fits.append((score,fit))
        residual,fit=min(fits,key=lambda t:t[0])
        bound=2*epsilon/np.sqrt(margin(u,w,2)['alpha'])
        bound_ratios.append(float(np.linalg.norm(fit-delta)/bound))
    return dict(status='numerically-supported',random_seed=seed,matrices=count,max_eigenvalue_discrepancy=max(discrepancies),max_linear_bound_ratio=max(bound_ratios),meaning='finite checks of known algebra and written linear bound; not proof')

def erasure_witness():
    u=np.array([[1.,0],[1,0],[0,1],[0,1]]); w=np.ones(4)
    p=-u; y=np.array([1.,0,0,0]); v=np.array([1.,0])
    a0=y; a1=y-u@v
    verified=np.array_equal(u@v+a1,a0) and np.count_nonzero(a0)==np.count_nonzero(a1)==1
    return dict(status='refuted',claim='alpha_q>0 suffices for q unknown corruptions',rows=u.tolist(),alpha_q=margin(u,w,1)['alpha'],alpha_2q=margin(u,w,2)['alpha'],y=y.tolist(),delta0=[0,0],delta1=v.tolist(),attack0=a0.tolist(),attack1=a1.tolist(),verified=bool(verified),proof='THEORY.md R1 exact algebra')

def nonlinear_witnesses():
    p=np.array([[-2.,0],[0,0],[2,0],[1,3]]); x=np.array([.3,1.]); z=np.array([.3,-1.])
    hx=np.linalg.norm(x-p,axis=1); hz=np.linalg.norm(z-p,axis=1); difference=hz-hx
    alpha=independent_margin(x,p,np.ones(4),2)
    eps=.01; rows=np.array([[1.,0],[eps,1],[-eps,1],[2*eps,1]])
    rows/=np.linalg.norm(rows,axis=1)[:,None]; y=np.array([1.,0,0,0]); v=np.array([1.,0])
    return dict(status='refuted',global_reflection=dict(anchors=p.tolist(),position0=x.tolist(),position1=z.tolist(),ranges0=hx.tolist(),ranges1=hz.tolist(),difference_support=int(np.count_nonzero(np.abs(difference)>1e-12)),alpha_2q=alpha,verified=bool(alpha>0 and np.count_nonzero(np.abs(difference)>1e-12)<=2),proof='THEORY.md R2'),
                l1_failure=dict(rows=rows.tolist(),alpha_2q=margin(rows,np.ones(4),2)['alpha'],cost_at_truth=float(np.abs(y).sum()),cost_at_wrong=float(np.abs(y-rows@v).sum()),verified=bool(np.abs(y-rows@v).sum()<np.abs(y).sum()),proof='THEORY.md R3'),
                tangent_unique=dict(anchors=[[-1,0],[1,0]],truth=[0,0],ranges=[1,1],alpha=0.,proof='THEORY.md R4, circle tangency gives unique exact point without a Lipschitz inverse'))

def local_bound_checks(seed=9417,count=150):
    rng=np.random.default_rng(seed); ratios=[]; outputs=[]
    for _ in range(count):
        angles=np.arange(8)*2*np.pi/8+rng.uniform(-.05,.05,8); p=np.column_stack([np.cos(angles),np.sin(angles)])*10
        w=np.ones(8); c=np.zeros(2); gamma=np.sqrt(point_margin(c,p,w,2)['alpha']); R=gamma*10/(4*np.sqrt(8)); L=curvature_bound(c,R,p,w)
        x=rng.normal(size=2); x*=rng.uniform(0,R)/np.linalg.norm(x)
        z=rng.normal(size=2); z*=rng.uniform(0,R)/np.linalg.norm(z)
        d=np.linalg.norm(x-z)
        for ids in combinations(range(8),6):
            difference=np.linalg.norm(x-p[list(ids)],axis=1)-np.linalg.norm(z-p[list(ids)],axis=1)
            ratios.append(float(np.linalg.norm(difference)/((gamma-L*R)*d)))
        outputs.append(gamma-L*R)
    return dict(status='numerically-supported',seed=seed,count=count,minimum_observed_lower_lipschitz_ratio=min(ratios),minimum_denominator=min(outputs),meaning='random pairs in certified ball; proof is P1, not this test')

def ratio_counterexample(seed=65171,max_trials=2000):
    """Actively search a real range-map finite-pool residual/geometry ordering inversion."""
    rng=np.random.default_rng(seed)
    for trial in range(max_trials):
        p=rng.uniform(-5,5,(6,2)); truth=np.zeros(2); noise=rng.normal(0,.2,6)
        d=np.linalg.norm(p,axis=1)+noise; x0=truth+rng.normal(0,.5,2); x1=truth+rng.normal(0,.5,2)
        score=[]
        for x in [x0,x1]:
            T=float(np.sum((np.linalg.norm(x-p,axis=1)-d)**2)); alpha=independent_margin(x,p,np.ones(6),0)
            score.append((T,alpha))
        residual_index=int(np.argmin([r[0] for r in score])); ratio_index=int(np.argmin([r[0]/r[1] for r in score]))
        if residual_index!=ratio_index and np.linalg.norm([x0,x1][ratio_index])>np.linalg.norm([x0,x1][residual_index]):
            epsilon=float(np.sqrt(score[residual_index][0]))
            if np.linalg.norm(noise)>epsilon: continue
            return dict(status='refuted',claim='unguarded residual/geometry ratio universally respects fit reliability or improves finite-pool position error',trial=trial,seed=seed,q=0,anchors=p.tolist(),truth=truth.tolist(),observations=d.tolist(),positions=[x0.tolist(),x1.tolist()],scores=[dict(T=T,alpha=alpha,ratio=T/alpha) for T,alpha in score],residual_choice=residual_index,ratio_choice=ratio_index,epsilon_gate=epsilon,true_whitened_noise_norm=float(np.linalg.norm(noise)),verified=bool(score[ratio_index][0]>epsilon**2+1e-10),scope='finite two-candidate pool selector, not a proof about every continuous global optimizer',next_step='Use an explicit residual feasibility gate before geometry ranking')
    return dict(status='conjectured',seed=seed,search_budget=max_trials,result='no witness found; not evidence of a universal guarantee')

def estimator_experiment(seed=88191,cases_per_scenario=30):
    rng=np.random.default_rng(seed); rows=[]
    scenarios=['balanced','near_line','leverage_attack','wrong_prior','overspecified_budget']
    for scenario in scenarios:
        for case_id in range(cases_per_scenario):
            n=8; q=1; truth=rng.uniform(-.03,.03,2); c=np.zeros(2); R=.25
            if scenario=='near_line': p=np.column_stack([np.linspace(-12,12,n),rng.uniform(-.02,.02,n)])
            else:
                angles=np.arange(n)*2*np.pi/n+rng.uniform(-.15,.15,n)
                p=10*np.column_stack([np.cos(angles),np.sin(angles)])
            if scenario=='wrong_prior': truth+=np.array([1.,0.])
            sigma=rng.uniform(.01,.025,n); weights=1/sigma**2
            if scenario=='leverage_attack':
                # Suppress most geometric y-information; corrupt the sole vertical anchor.
                p=np.column_stack([np.linspace(-12,12,n),rng.uniform(-.05,.05,n)]); p[0]=[0,10]
            eta=rng.normal(size=n); eta*=.6/np.linalg.norm(eta)
            clean=np.linalg.norm(truth-p,axis=1); distances=clean+eta*sigma
            attack=0 if scenario=='leverage_attack' else int(rng.integers(n))
            amplitude=rng.choice([-1,1])*rng.uniform(1,10)
            distances[attack]+=amplitude
            epsilon=2. if scenario=='overspecified_budget' else 1.
            problem=Problem(p,distances,weights,q,epsilon,c,R)
            start=time.perf_counter(); pool,failures=candidate_pool(problem); runtime=time.perf_counter()-start
            for mode in ['residual_only','unguarded_ratio','feasible_geometry']:
                result=select(problem,pool,mode); verification=check_estimate(problem,result)
                if not verification['verified']: raise RuntimeError('Independent estimate verification failed')
                error=float(np.linalg.norm(np.array(result['position'])-truth)) if result['status']=='estimate' else None
                bound=result.get('conditional_error_bound'); coverage=bool(np.linalg.norm(truth-c)<=R)
                rows.append(dict(scenario=scenario,case=case_id,mode=mode,status=result['status'],error=error,conditional_bound=bound,prior_contains_truth=coverage,bound_applicable=coverage and bound is not None,bound_ratio=error/bound if bound is not None and error is not None else None,pool_size=len(pool),optimizer_failures=failures,pool_runtime_s=runtime,trimmed_norm=result.get('trimmed_norm'),beta=result.get('beta'),estimated_position=result.get('position'),truth=truth.tolist(),anchors=p.tolist(),observations=distances.tolist(),weights=weights.tolist(),epsilon=epsilon,q=q,prior_center=c.tolist(),prior_radius=R,verification=verification))
    summary={}
    for s in scenarios:
        summary[s]={}
        for mode in ['residual_only','unguarded_ratio','feasible_geometry']:
            group=[r for r in rows if r['scenario']==s and r['mode']==mode]; estimated=[r for r in group if r['error'] is not None]
            applicable=[r for r in group if r['bound_applicable']]
            summary[s][mode]=dict(cases=len(group),estimates=len(estimated),abstentions=len(group)-len(estimated),median_error=float(np.median([r['error'] for r in estimated])) if estimated else None,applicable_certificates=len(applicable),bound_violations=sum(r['bound_ratio']>1+1e-7 for r in applicable),maximum_applicable_bound_ratio=max([r['bound_ratio'] for r in applicable],default=None),invalid_prior_certificates=sum(not r['prior_contains_truth'] and r['conditional_bound'] is not None for r in group))
    return dict(status='numerically-supported',seed=seed,cases_per_scenario=cases_per_scenario,summary=summary,rows=rows,objective='assumption stress, feasibility, local stability and abstention; no CEP90 tuning',warning='Wrong-prior conditional outputs have no valid guarantee. Empirical median is descriptive, never an acceptance target.')
