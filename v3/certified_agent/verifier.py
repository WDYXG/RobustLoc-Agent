"""Safety consumer: no imports of the policy, planner, decoder or simulator."""
from fractions import Fraction as F
from itertools import combinations
import numpy as np
from v2.global_stability.exact import point,sqrt_interval,distance2
from v2.global_stability.verifier import verify_certificate,verify_upper

def require(condition,message):
    if not condition: raise ValueError('Phase 3 verification rejected: '+message)

def residual_check(obs,x,q):
    x=point(x); d=list(map(F,obs['domain']))
    require(d[0]<=x[0]<=d[1] and d[2]<=x[1]<=d[3],'candidate outside D')
    vals=[]
    for i,(p,w,y) in enumerate(zip(obs['anchors'],obs['weights'],obs['measurements'])):
        lo,hi=sqrt_interval(distance2(x,point(p))); y=F(y)
        vals.append((F(w)*max((lo-y)**2,(hi-y)**2),i))
    selected=sorted(vals)[:len(vals)-q]; upper2=sum(v for v,i in selected)
    return upper2,[i for v,i in selected]

def verify_record(row,pool,cfg):
    initial=row['initial_observation']; final=row['final_observation']; trace=row['trace']
    require(trace and trace[0]['observation']==initial and trace[-1]['observation']==final,'trace endpoints')
    require(all(set(t['observation']).isdisjoint({'truth','private','actual_q','bad_indices','scenario'}) for t in trace),'private leakage')
    require(initial['epsilon']==cfg['epsilon'] and initial['error_tolerance']==cfg['error_tolerance'],'fixed budgets')
    verified_outputs=0
    for i,turn in enumerate(trace):
        obs,dec=turn['observation'],turn['decision']
        require(obs['weights']==['1']*len(obs['anchors']) and len(obs['measurements'])==len(obs['anchors']),'weight contract/length')
        require(obs['q_budget']==initial['q_budget'] and obs['domain']==initial['domain']
                and obs['epsilon']==initial['epsilon'],'assumptions changed across episode')
        q=obs['q_budget']; tau=2*F(obs['epsilon'])/F(obs['error_tolerance'])
        if 'geometry' in dec:
            g=dec['geometry']; cert=pool[g['certificate_id']]
            require(cert['data']==dict(anchors=obs['anchors'],weights=obs['weights'],domain=obs['domain']) and cert['q']==q,'geometry binding')
            result=verify_certificate(cert)
            require(result['certified_lower']==g['lower'],'lower match')
            require(verify_upper(cert['data'],q,g['upper_witness'])==g['upper'],'upper match')
        if dec['action']=='acquire-more-data':
            require(i+1<len(trace) and obs['acquisitions_remaining']>0,'terminal/over-budget request')
            p=dec['acquisition']['anchor']; new=trace[i+1]['observation']
            require(p in obs['available_anchors'] and p not in obs['anchors'],'invalid reporter offer')
            require(new['anchors']==obs['anchors']+[p] and new['measurements'][:-1]==obs['measurements'],'observation history changed')
            require(new['acquisitions_remaining']==obs['acquisitions_remaining']-1,'budget decrement')
        elif dec['action']=='recover' and dec.get('certified'):
            require(q is not None and 'geometry' in dec,'recover without q or certificate')
            b=F(dec['geometry']['lower']); require(b>=tau,'recover below required margin')
            upper2,indices=residual_check(obs,dec['candidate']['position'],q)
            require(upper2<=F(obs['epsilon'])**2,'infeasible certified output')
            claimed=dec['candidate']['feasibility']
            require(claimed['feasible'] and claimed['clean_indices']==indices and F(claimed['norm2_upper'])==upper2,'residual arithmetic')
            require(F(dec['error_bound'])==2*F(obs['epsilon'])/b,'T2 error certificate')
            verified_outputs+=1
        else: require(dec['action'] in ('recover','abstain'),'invalid action')
    private=row['private_final']; truth=point(private['truth']); q=final['q_budget']
    bad_positions=[point(p) for p in private['bad_positions']]
    if private['new_bad_position']: bad_positions.append(point(private['new_bad_position']))
    bad=[i for i,p in enumerate(final['anchors']) if point(p) in bad_positions]
    noise2=F(0)
    for i,(p,y,w) in enumerate(zip(final['anchors'],final['measurements'],final['weights'])):
        if i in bad: continue
        lo,hi=sqrt_interval(distance2(truth,point(p))); y=F(y)
        noise2+=F(w)*max(abs(lo-y),abs(hi-y))**2
    d=list(map(F,final['domain'])); inside=d[0]<=truth[0]<=d[1] and d[2]<=truth[1]<=d[3]
    q_ok=q is not None and len(bad)<=q; noise_ok=noise2<=F(final['epsilon'])**2
    c=row['final_contract']
    require(c['valid']==bool(inside and q_ok and noise_ok) and c['bad_indices']==bad
            and F(c['true_clean_norm2_upper'])==noise2,'private contract accounting')
    out=row['outcome']; terminal=trace[-1]['decision']
    require(out['output']==(terminal['action']=='recover') and out['action']==terminal['action'],'terminal outcome')
    error=None
    if out['output']:
        x=np.array([float(F(v)) for v in terminal['candidate']['position']]); t=np.array([float(v) for v in truth])
        error=float(np.linalg.norm(x-t))
        require(abs(error-out['error'])<1e-10,'error recomputation')
        require(out['wrong_output']==bool(error>float(F(final['error_tolerance']))),'wrong output accounting')
    require(out['acquisitions']==len(final['anchors'])-len(initial['anchors']),'acquisition count')
    if out['certified']:
        require(verified_outputs==1 and F(out['error_bound'])==F(terminal['error_bound']),'certified outcome mismatch')
        violated=error>float(F(out['error_bound']))+1e-9
        require(out['bound_violation']==violated,'bound violation accounting')
        if c['valid']: require(not violated,'conditional theorem violation')
    else: require(verified_outputs==0,'certified output omitted from metrics')
    return dict(verified=True,certified_outputs=verified_outputs,in_contract=c['valid'])

def verify_learning(evidence,cfg):
    require(evidence['model']['train_seed']!=evidence['model']['test_seed'],'model split')
    model=evidence['model']; threshold=cfg['learning_threshold']; false_positive=0; usable=0
    tau=2*F(cfg['epsilon'])/F(cfg['error_tolerance'])
    from v2.global_stability.verifier import verify_certificate
    # Labels are also recomputed independently through scatter pairwise variance
    # rather than trusting the producer label; fixture data fully retained.
    for rows in [evidence['train_rows'],evidence['test_rows']]:
        for row in rows:
            data=row['data']; a=[point(p) for p in data['anchors']]; d=list(map(F,data['domain']))
            nu=[]
            for p,w in zip(a,data['weights']):
                R2=max(distance2(p,(x,y)) for x in d[:2] for y in d[2:])
                nu.append(F(w)/R2)
            vals=[]
            for s in combinations(range(len(a)),max(0,len(a)-2*row['q_budget'])):
                total=sum(nu[i] for i in s); A=B=C=F(0)
                if total:
                    for i,j in combinations(s,2):
                        u,v=a[i][0]-a[j][0],a[i][1]-a[j][1]; k=nu[i]*nu[j]/total
                        A+=k*u*u; B+=k*u*v; C+=k*v*v
                vals.append((A*C-B*B)/(A+C) if A+C else F(0))
            b=sqrt_interval(min(vals))[0]
            # Producer uses the max of scatter and single-box near/far. The root
            # far interval includes overlapping identical boxes, so its raw=0.
            require(str(b)==row['lower'],'learning lower label')
            pts=[(d[0],d[2]),(d[0],d[3]),(d[1],d[2]),(d[1],d[3]),((d[0]+d[1])/2,d[2]),((d[0]+d[1])/2,d[3])]
            from v2.global_stability.exact import point_upper
            upper=min(point_upper(a,list(map(F,data['weights'])),x,z,row['q_budget'])[0] for x,z in combinations(pts,2))
            require(str(upper)==row['upper'],'learning upper label')
            label=1 if b>=tau else (0 if upper<tau else None)
            require(row['label']==label,'unknown labels fabricated')
    for row in evidence['test_rows']:
        x=(np.array(row['features'])-np.array(model['mean']))/np.array(model['scale'])
        t=float(x@np.array(model['coef'])+model['intercept']); p=float(1/(1+np.exp(-np.clip(t,-60,60))))
        require(abs(p-row['probability'])<1e-12 and row['predicted']==int(p>=threshold),'surrogate predictions')
        if row['label'] is not None:
            usable+=1; false_positive+=int(row['predicted']==1 and row['label']==0)
    require(evidence['summary']['test_labeled']==usable and evidence['summary']['false_positive']==false_positive,'learning metrics')
    return dict(verified=True,separated_test_labels=usable,false_positive=false_positive,status='numerically-supported')
