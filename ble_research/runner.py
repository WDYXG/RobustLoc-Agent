"""One research proposal per call; final test requires locked validation choice."""
import argparse,hashlib,json,time
from pathlib import Path
import numpy as np
from concurrent.futures import ProcessPoolExecutor
from .core import read,fit,field_model,estimate,FIXED

ROOT=Path(__file__).resolve().parents[1]
def save(p,o):Path(p).write_text(json.dumps(o,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def load(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sources():
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'ble_research').glob('*.py'))}
def summary(rows):
    labels=sorted({r['label'] for r in rows}); groups=[[r for r in rows if r['label']==k] for k in labels]
    errors=[];weights=[]
    for g in groups:
        for r in g:
            if r['error'] is not None:errors.append(r['error']);weights.append(1/len(g))
    if errors:
        order=np.argsort(errors);v=np.array(errors)[order];w=np.array(weights)[order];cdf=np.cumsum(w)/sum(w)
        q=lambda t:float(v[min(len(v)-1,np.searchsorted(cdf,t))])
    else:q=lambda t:None
    rates={str(t):float(np.mean([np.mean([r['error'] is not None and r['error']<=t for r in g]) for g in groups])) for t in (5,10,30)} if groups else {}
    return dict(rows=len(rows),positions=len(labels),outputs=sum(r['error'] is not None for r in rows),
         coverage=float(np.mean([np.mean([r['error'] is not None for r in g]) for g in groups])) if groups else None,
         cep50=q(.5),cep90=q(.9),success_rates=rates,failure_rate=1-rates['30'] if rates else None,
         optimization_failures=sum(not r['success'] and r['n']>=3 for r in rows))
def init_worker(p,model,method):
    global PARAMS
    PARAMS=(p,model,method)
def work(r):
    p,model,method=PARAMS;t=time.perf_counter();a=estimate(r['public'],p,model,method)
    err=float(np.linalg.norm(np.array(a['position'])-r['truth'])) if a['position'] is not None else None
    return dict(key=r['key'],label=r['label'],device=r['public']['device'],room=r['room'],**a,error=err,seconds=time.perf_counter()-t)
def evaluate(rows,p,model,method):
    with ProcessPoolExecutor(max_workers=4,initializer=init_worker,initargs=(p,model,method)) as pool:
        out=list(pool.map(work,rows,chunksize=16))
    return dict(overall=summary(out),n_ge_11=summary([r for r in out if r['n']>=11]) if any(r['n']>=11 for r in out) else None,
        by_device={d:summary([r for r in out if r['device']==d]) for d in sorted({r['device'] for r in out})},rows=out)
def start(out):
    out.mkdir(parents=True,exist_ok=False);p,g,s=read();save(out/'split.json',g)
    model=fit(s['calibration'],p,'global');save(out/'model-global.json',model)
    save(out/'manifest.json',dict(sources=sources(),protocol_sha256=hashlib.sha256((ROOT/'ble_research/PROTOCOL.md').read_bytes()).hexdigest(),
       counts={k:len(v) for k,v in s.items()},data_sha256={x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in (ROOT/'ble_calibration/data').glob('*.csv')}))
    for name,m,method in [('fixed-wls',FIXED,'wls'),('fixed-cauchy',FIXED,'cauchy'),('global-wls',model,'wls'),('global-cauchy',model,'cauchy')]:
        res=evaluate(s['validation'],p,m,method);save(out/f'validation-{name}.json',res);print(name,res['overall'],flush=True)
    save(out/'incumbent.json',dict(name='global-cauchy',model='model-global.json',method='cauchy'))
def gate(candidate,incumbent):
    c,b=candidate['overall'],incumbent['overall'];gain=(b['cep90']-c['cep90'])/max(b['cep90'],1e-8)
    return dict(accepted=bool(gain>=.01 and c['coverage']>=b['coverage']-1e-12),relative_gain=gain,
       device_regressions=[d for d in c_by(candidate) if candidate['by_device'][d]['cep90']>incumbent['by_device'][d]['cep90']*1.2],
       evidence='numerically-supported validation only; selection bias remains')
def c_by(r):return r['by_device']
def step(out,name,kind,method,parent=None,bandwidth=4.):
    p,g,s=read();folder=out/name;folder.mkdir(exist_ok=False)
    model=field_model(s['calibration'],p,load(out/parent),bandwidth) if kind=='field' else fit(s['calibration'],p,kind)
    save(folder/'model.json',model);res=evaluate(s['validation'],p,model,method);save(folder/'validation.json',res)
    inc=load(out/'incumbent.json');old=load(out/f'validation-{inc["name"]}.json') if not (out/inc['name']).is_dir() else load(out/inc['name']/'validation.json')
    verdict=gate(res,old);save(folder/'verdict.json',verdict)
    if verdict['accepted']:save(out/'incumbent.json',dict(name=name,model=f'{name}/model.json',method=method))
    print(name,res['overall'],verdict,flush=True)
def final(out):
    lock=out/'FINAL_LOCK.json'
    if lock.exists():raise FileExistsError('Final test may only execute once per run')
    inc=load(out/'incumbent.json');save(lock,dict(selected=inc,sources=sources(),timestamp=time.time(),model_sha256=hashlib.sha256((out/inc['model']).read_bytes()).hexdigest()))
    p,g,s=read();assert g==load(out/'split.json');results={}
    specs=[('centre',FIXED,'centre'),('fixed-wls',FIXED,'wls'),('fixed-cauchy',FIXED,'cauchy'),
           ('global-wls',load(out/'model-global.json'),'wls'),('global-cauchy',load(out/'model-global.json'),'cauchy'),('final',load(out/inc['model']),inc['method'])]
    for name,m,method in specs:
        res=evaluate(s['test'],p,m,method);save(out/f'test-{name}.json',res);results[name]=res['overall'];print(name,res['overall'],flush=True)
    save(out/'test-summary.json',results)
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('action');a.add_argument('output',type=Path);a.add_argument('--name');a.add_argument('--kind');a.add_argument('--method',default='db');a.add_argument('--parent');a.add_argument('--bandwidth',type=float,default=4.)
    x=a.parse_args()
    if x.action=='start':start(x.output)
    elif x.action=='step':step(x.output,x.name,x.kind,x.method,x.parent,x.bandwidth)
    elif x.action=='final':final(x.output)
