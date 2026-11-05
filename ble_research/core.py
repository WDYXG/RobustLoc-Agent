"""Calibrators train with labels; public-only estimators never receive labels."""
import ast,csv,hashlib,json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from robustloc.simulator import Observation
from robustloc.baseline import solve_weighted
from robustloc.candidate import solve as cauchy
from static_localization.service import INCUMBENT

DATA=Path(__file__).resolve().parents[1]/'ble_calibration/data'

def read():
    anchors=ast.literal_eval((DATA/'APS_Positions.txt').read_text().split('=',1)[1])
    ids=list(anchors); p=np.array([anchors[k] for k in ids]); rows=[]
    for path in sorted(DATA.glob('*.csv')):
        for i,r in enumerate(csv.DictReader(path.open())):
            rows.append(dict(key=f'{path.stem}:{i}',label=r['LABEL'],truth=[float(r['X']),float(r['Y'])],
                 room=r['ROOM_ID'],public=dict(device=r['DEVICE'],rssi=[float(r[k]) for k in ids])))
    labels=sorted({r['label'] for r in rows},key=lambda k:hashlib.sha256(('ble-real-stage-20261105/'+k).encode()).hexdigest())
    groups={'calibration':labels[:96],'validation':labels[96:128],'test':labels[128:]}
    return p,groups,{s:[r for r in rows if r['label'] in ls] for s,ls in groups.items()}

def aggregate(rows):
    groups={}
    for r in rows: groups.setdefault((r['label'],r['public']['device']),[]).append(r)
    out=[]
    for rs in groups.values():
        a=np.array([r['public']['rssi'] for r in rs]); a=np.where(a==-105,np.nan,a)
        sums=np.nansum(a,axis=0); count=np.sum(np.isfinite(a),axis=0)
        v=np.divide(sums,count,out=np.full(a.shape[1],-105.),where=count>0)
        out.append(dict(truth=rs[0]['truth'],public=dict(device=rs[0]['public']['device'],rssi=v.tolist())))
    return out

def fit(rows,p,kind):
    rs=aggregate(rows); devs=sorted({r['public']['device'] for r in rs}); X=[]; y=[]
    m=len(p); base=1 if kind=='global' else m
    width=base+1+(len(devs)-1 if kind=='device' else 0)+(1 if kind=='dual' else 0)
    for r in rs:
        dist=np.maximum(.5,np.linalg.norm(p-r['truth'],axis=1)); logs=np.log10(dist)
        for j,s in enumerate(r['public']['rssi']):
            if s==-105:continue
            row=np.zeros(width);row[0 if kind=='global' else j]=1;row[base]=logs[j]
            if kind=='device' and r['public']['device']!=devs[0]:row[base+devs.index(r['public']['device'])]=1
            if kind=='dual':row[-1]=max(0,logs[j]-1)
            X.append(row);y.append(s)
    X=np.array(X);y=np.array(y); penalty=np.eye(width)*np.sqrt(.1);penalty[base,base]=0
    coef=np.linalg.lstsq(np.vstack([X,penalty]),np.r_[y,np.zeros(width)],rcond=None)[0]
    if coef[base]>=0 or (kind=='dual' and coef[base]+coef[-1]>=0):raise ValueError('Non-decreasing fitted path loss')
    model=dict(kind=kind,intercepts=([float(coef[0])]*m if kind=='global' else coef[:m].tolist()),
         slope=float(coef[base]),device_offsets={d:(float(coef[base+i]) if kind=='device' and i else 0.) for i,d in enumerate(devs)},
         hinge=float(coef[-1]) if kind=='dual' else 0.,sigma=5.)
    model['sigma']=max(2.,float(np.sqrt(np.mean((X@coef-y)**2))))
    return model

def predict(x,p,device,model):
    logs=np.log10(np.maximum(.5,np.linalg.norm(x-p,axis=1)))
    result=np.array(model['intercepts'])+model['slope']*logs+model.get('hinge',0)*np.maximum(0,logs-1)+model['device_offsets'].get(device,0.)
    if 'field' in model:
        f=model['field']; coords=np.array(f['positions']); val=np.array(f['residuals']); valid=np.array(f['valid'])
        w=np.exp(-np.sum((coords-x)**2,axis=1)/(2*f['bandwidth']**2))[:,None]*valid
        result+=np.sum(w*val,axis=0)/np.maximum(np.sum(w,axis=0),1e-8)
    return result

def field_model(rows,p,base,bandwidth):
    model=json.loads(json.dumps(base));coords=[];values=[];valid=[]
    grouped={}
    for r in aggregate(rows):
        rss=np.array(r['public']['rssi']); mask=rss!=-105
        res=rss-predict(np.array(r['truth']),p,r['public']['device'],base)
        grouped.setdefault(tuple(r['truth']),[]).append((res,mask))
    for xy,rs in grouped.items():
        counts=np.sum([mask for _,mask in rs],axis=0)
        summed=np.sum([np.where(mask,res,0) for res,mask in rs],axis=0)
        coords.append(list(xy));values.append((summed/np.maximum(counts,1)).tolist());valid.append((counts>0).astype(int).tolist())
    model['field']=dict(positions=coords,residuals=values,valid=valid,bandwidth=bandwidth)
    return model

def estimate(public,p,model,method):
    if set(public)!={'device','rssi'}:raise ValueError('Only device and RSSI may enter estimator')
    rss=np.array(public['rssi'],float)
    if rss.shape!=(len(p),) or not np.isfinite(rss).all() or np.any(rss>=0):raise ValueError('Invalid RSSI vector')
    mask=rss!=-105;n=int(sum(mask))
    if method=='centre':return dict(position=p.mean(axis=0).tolist(),success=True,n=n)
    if n<3:return dict(position=None,success=False,n=n,reason='fewer-than-three-receivers')
    if method in ('wls','cauchy'):
        a=np.array(model['intercepts'])+model['device_offsets'].get(public['device'],0.)
        d=10**((rss[mask]-a[mask])/model['slope']);sd=np.maximum(.05,d*np.log(10)*model['sigma']/abs(model['slope']))
        obs=Observation(p[mask],d,np.zeros(n),sd,np.ones(n),np.ones(n))
        sol=solve_weighted(obs) if method=='wls' else cauchy(obs,INCUMBENT)
        return dict(position=sol.position.tolist(),success=bool(sol.success),n=n)
    lo=p.min(axis=0)-10;hi=p.max(axis=0)+10;c=(lo+hi)/2;span=(hi-lo)/4
    starts=[c]+[c+span*np.array(v) for v in [(-1,-1),(-1,1),(1,-1),(1,1)]]
    best=None
    for start in starts:
        sol=least_squares(lambda x:(predict(x,p,public['device'],model)[mask]-rss[mask])/model['sigma'],
             start,bounds=(lo,hi),loss='huber',f_scale=1.,max_nfev=100)
        if sol.success and (best is None or sol.cost<best.cost):best=sol
    return dict(position=best.x.tolist() if best is not None else None,success=best is not None,n=n)

FIXED=dict(kind='fixed',intercepts=[-59.]*15,slope=-20.,hinge=0.,device_offsets={},sigma=4.)
