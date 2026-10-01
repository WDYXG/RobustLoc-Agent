"""Advisory logistic surrogate on certificate-separated labels only."""
from fractions import Fraction as F
import numpy as np
from scipy.optimize import minimize
from .certificates import geometry,features

def layouts(seed,count,cfg):
    rng=np.random.default_rng(seed); rows=[]
    for i in range(count):
        family=i%4; n=int(rng.choice([6,7,8])); q=int(rng.integers(0,3))
        if family==0:
            angles=np.linspace(0,2*np.pi,n,endpoint=False)+rng.uniform(-.1,.1,n)
            p=np.column_stack([5*np.cos(angles),5*np.sin(angles)])
        elif family==1:
            p=np.column_stack([np.linspace(-5,5,n)+rng.uniform(-.1,.1,n),np.zeros(n)])
        elif family==2:
            p=np.column_stack([np.linspace(-5,5,n),rng.uniform(-.03,.03,n)])
        else: p=rng.uniform(-5,5,(n,2))
        data=dict(anchors=[[format(v,'.6f') for v in x] for x in p],weights=['1']*n,domain=cfg['domain'])
        g=geometry(data,q); tau=2*F(cfg['epsilon'])/F(cfg['error_tolerance'])
        label=1 if F(g['lower'])>=tau else (0 if F(g['upper'])<tau else None)
        obs=dict(data,q_budget=q,estimated_corruption=int(rng.integers(0,3)))
        rows.append(dict(layout_id=f'{seed}-{i}',family=family,data=data,q_budget=q,
            lower=g['lower'],upper=g['upper'],label=label,features=features(obs)['values'],
            label_scope='positive sufficient lower / negative upper witness; unresolved excluded'))
    return rows

def predict(model,values):
    x=(np.array(values)-np.array(model['mean']))/np.array(model['scale'])
    logit=float(np.dot(x,np.array(model['coef']))+model['intercept'])
    return float(1/(1+np.exp(-np.clip(logit,-60,60))))

def train(cfg):
    train_rows=layouts(cfg['train_seed'],cfg['training_layouts'],cfg)
    test_rows=layouts(cfg['model_test_seed'],cfg['model_test_layouts'],cfg)
    labeled=[r for r in train_rows if r['label'] is not None]
    X=np.array([r['features'] for r in labeled]); y=np.array([r['label'] for r in labeled])
    if len(np.unique(y))<2: raise RuntimeError('Insufficient separated training labels')
    mean=X.mean(axis=0); scale=np.maximum(X.std(axis=0),1e-8); Z=(X-mean)/scale
    def objective(beta):
        t=Z@beta[:-1]+beta[-1]
        loss=np.logaddexp(0,t).sum()-np.dot(y,t)+.5*np.dot(beta[:-1],beta[:-1])
        p=1/(1+np.exp(-np.clip(t,-60,60)))
        grad=np.r_[Z.T@(p-y)+beta[:-1],np.sum(p-y)]
        return loss,grad
    result=minimize(objective,np.zeros(X.shape[1]+1),jac=True,method='L-BFGS-B',options={'maxiter':200})
    model=dict(mean=mean.tolist(),scale=scale.tolist(),coef=result.x[:-1].tolist(),intercept=float(result.x[-1]),
        optimizer_success=bool(result.success),train_seed=cfg['train_seed'],test_seed=cfg['model_test_seed'],
        threshold=cfg['learning_threshold'],status='numerically-supported',
        target='certificate-separated synthetic label, not exact mu or certified probability')
    tested=[]
    for row in test_rows:
        p=predict(model,row['features']); tested.append(dict(row,probability=p,predicted=int(p>=cfg['learning_threshold'])))
    usable=[r for r in tested if r['label'] is not None]
    summary=dict(train_labeled=len(labeled),train_unknown=len(train_rows)-len(labeled),
        test_labeled=len(usable),test_unknown=len(test_rows)-len(usable),
        accuracy=sum(r['predicted']==r['label'] for r in usable)/len(usable),
        false_positive=sum(r['predicted']==1 and r['label']==0 for r in usable),
        false_negative=sum(r['predicted']==0 and r['label']==1 for r in usable),
        brier=float(np.mean([(r['probability']-r['label'])**2 for r in usable])),
        status='numerically-supported',scope='held-out layouts; unknown labels excluded, no safety guarantee')
    return dict(model=model,train_rows=train_rows,test_rows=tested,summary=summary)
