"""Consumer reconstructs all bounds, subset completeness and binary coverage.

Does not import producer. Shares rational sqrt/geometry primitives, so this is
independent recomputation, not a diverse formal verification implementation.
"""
from fractions import Fraction as F
from itertools import combinations
from .exact import (dataset,survivors,sqrt_interval,squared_range_box,centre,
                    grid, pair_max2,split_pair,point_upper,point,box)

def require(condition,message):
    if not condition: raise ValueError('Certificate rejected: '+message)

def verify_certificate(cert):
    anchors,weights,domain=dataset(cert['data']); q=cert['q']; m=survivors(len(anchors),q)
    require(cert['schema']=='rational-global-stability-v1','schema')
    indices=list(combinations(range(len(anchors)),m))
    nu=[w/squared_range_box(p,domain)[1] for p,w in zip(anchors,weights)]
    scatter=[]
    # Pairwise variance identity, different from producer centroid calculation.
    for s in indices:
        total=sum(nu[i] for i in s); a=b=c=F(0)
        if total:
            for i,j in combinations(s,2):
                dx=anchors[i][0]-anchors[j][0]; dy=anchors[i][1]-anchors[j][1]
                v=nu[i]*nu[j]/total
                a+=v*dx*dx; b+=v*dx*dy; c+=v*dy*dy
        det=a*c-b*b; trace=a+c
        require(det>=0,'scatter PSD')
        scatter.append(det/trace if trace else F(0))
    require([r['indices'] for r in cert['scatter']['subsets']]==[list(s) for s in indices],'subset completeness')
    require([F(r['eigen_lower2']) for r in cert['scatter']['subsets']]==scatter,'scatter entries')
    scatter_lower=sqrt_interval(min(scatter))[0]
    require(F(cert['scatter']['lower2'])==min(scatter),'scatter square')
    require(F(cert['scatter']['lower'])==scatter_lower,'scatter sqrt')
    settings=cert['settings']; cells=grid(domain,settings['divisions']); local=[]
    require(len(cells)==len(cert['local']['cells']),'local grid completeness')
    for cell,row in zip(cells,cert['local']['cells']):
        require(tuple(map(F,row['cell']))==cell,'cell geometry')
        sep=[sqrt_interval(squared_range_box(p,cell)[0])[0] for p in anchors]
        if min(sep)==0:
            value=F(0)
        else:
            x=centre(cell); ev=[]
            for s in indices:
                g=[[F(0),F(0)],[F(0),F(0)]]
                for i in s:
                    u=[x[k]-anchors[i][k] for k in (0,1)]
                    denom=sum(v*v for v in u)
                    for j in (0,1):
                        for k in (0,1): g[j][k]+=weights[i]*u[j]*u[k]/denom
                trace=g[0][0]+g[1][1]; det=g[0][0]*g[1][1]-g[0][1]*g[1][0]
                require(det>=0,'local PSD'); ev.append(det/trace if trace else F(0))
            gamma=sqrt_interval(min(ev))[0]
            rho=sqrt_interval(sum(((cell[k+1]-cell[k])/2)**2 for k in (0,2)))[1]
            L=sqrt_interval(sum(weights[i]/sep[i]**2 for i in range(len(anchors))))[1]
            require(F(row['centre_lower'])==gamma and F(row['radius_upper'])==rho
                    and F(row['derivative_upper'])==L,'local derivation')
            value=max(F(0),gamma-L*rho)
        require(F(row['lower'])==value,'local cell lower'); local.append(value)
    gamma_D=min(local)
    sep=[sqrt_interval(squared_range_box(p,domain)[0])[0] for p in anchors]
    L=sqrt_interval(sum(w/r**2 for w,r in zip(weights,sep)))[1] if min(sep)>0 else None
    require(F(cert['local']['lower'])==gamma_D,'local minimum')
    require(cert['local']['hessian_upper']==(str(L) if L is not None else None),'Hessian')
    delta=F(settings['delta']); require(delta>0,'delta')
    near=max(F(0),gamma_D-L*delta/2) if L is not None else F(0)
    require(F(cert['near_lower'])==near,'near bound')
    rows={r['path']:r for r in cert['leaves']}
    require(len(rows)==len(cert['leaves']) and len(rows)<=settings['max_leaves'],'leaf duplicates/budget')
    prefixes={r[:j] for r in rows for j in range(len(r)+1)}
    for p in prefixes:
        require(all(k in '01' for k in p),'path encoding')
        if p in rows:
            require(not any(p+k in prefixes for k in '01'),'leaf has descendants')
        else: require(p+'0' in prefixes and p+'1' in prefixes,'missing coverage child')
    require('' in prefixes,'empty coverage')
    stack=[('',domain,domain)]; computed=[]
    while stack:
        path,bx,bz=stack.pop()
        if path not in rows:
            require(len(path)<40,'excessive depth'); children=split_pair(bx,bz)
            stack.extend([(path+str(k),*children[k]) for k in (0,1)]); continue
        row=rows[path]; M2=pair_max2(bx,bz)
        if M2<=delta*delta:
            require(row['kind']=='near','near classification'); value=near
        else:
            vals=[]
            for i,p in enumerate(anchors):
                xl,xu=squared_range_box(p,bx); zl,zu=squared_range_box(p,bz)
                xl=sqrt_interval(xl)[0]; xu=sqrt_interval(xu)[1]
                zl=sqrt_interval(zl)[0]; zu=sqrt_interval(zu)[1]
                gap=max(F(0),xl-zu,zl-xu); vals.append(weights[i]*gap*gap)
            value=sqrt_interval(sum(sorted(vals)[:m])/M2)[0]
            require(row['kind'] in ('far-resolved','far-budget'),'far classification')
            if row['kind']=='far-resolved': require(value>=F(settings['target']),'resolved threshold')
        require(F(row['raw_lower'])==value,'far/near arithmetic'); computed.append(value)
    raw=min(computed); combined=max(scatter_lower,raw)
    require(F(cert['raw_cover_lower'])==raw and F(cert['certified_lower'])==combined,'global lower')
    return dict(verified=True,certified_lower=str(combined),raw_cover_lower=str(raw),
        scatter_lower=str(scatter_lower),local_lower=str(gamma_D),near_lower=str(near),
        leaves=len(rows),unresolved_far_leaves=sum(r['kind']=='far-budget' for r in rows.values()),
        status='proved-in-project',scope='exact arithmetic certificate checked; mathematical derivation requires review')

def verify_upper(data,q,witness):
    anchors,weights,domain=dataset(data); x=point(witness['x']); z=point(witness['z'])
    for p in (x,z):
        require(domain[0]<=p[0]<=domain[1] and domain[2]<=p[1]<=domain[3],'witness outside D')
    ub,equal=point_upper(anchors,weights,x,z,q)
    require(str(ub)==witness['upper'] and equal==witness['equal_coordinates'],'upper witness')
    return str(ub)
