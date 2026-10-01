"""Producer: complete near/far coverage plus independent analytic fallback."""
from fractions import Fraction as F
from itertools import combinations
from .exact import (dataset, survivors, sqrt_interval, squared_range_box, centre,
                    gram_at, det_trace_lower, grid, range_box, pair_max2, split_pair,
                    rational, encode)

def scatter_bound(anchors,weights,domain,q):
    m=survivors(len(anchors),q)
    nu=[w/squared_range_box(p,domain)[1] for p,w in zip(anchors,weights)]
    rows=[]
    for indices in combinations(range(len(anchors)),m):
        total=sum(nu[i] for i in indices)
        if not total:
            rows.append(dict(indices=list(indices),eigen_lower2=F(0))); continue
        pc=[sum(nu[i]*anchors[i][k] for i in indices)/total for k in (0,1)]
        a=sum(nu[i]*(anchors[i][0]-pc[0])**2 for i in indices)
        b=sum(nu[i]*(anchors[i][0]-pc[0])*(anchors[i][1]-pc[1]) for i in indices)
        c=sum(nu[i]*(anchors[i][1]-pc[1])**2 for i in indices)
        rows.append(dict(indices=list(indices),eigen_lower2=det_trace_lower((a,b,c))))
    lower2=min(row['eigen_lower2'] for row in rows)
    return dict(lower=sqrt_interval(lower2)[0],lower2=lower2,subsets=rows)

def local_bound(anchors,weights,domain,q,divisions):
    m=survivors(len(anchors),q); rows=[]
    indices=list(combinations(range(len(anchors)),m))
    for cell in grid(domain,divisions):
        separations=[sqrt_interval(squared_range_box(p,cell)[0])[0] for p in anchors]
        if min(separations)==0:
            rows.append(dict(cell=cell,lower=F(0),reason='anchor-containing-cell')); continue
        c=centre(cell)
        gamma=sqrt_interval(min(det_trace_lower(gram_at(anchors,weights,c,s)) for s in indices))[0]
        rho=sqrt_interval(((cell[1]-cell[0])/2)**2+((cell[3]-cell[2])/2)**2)[1]
        lipschitz=sqrt_interval(sum(w/r**2 for w,r in zip(weights,separations)))[1]
        rows.append(dict(cell=cell,lower=max(F(0),gamma-lipschitz*rho),
                         centre_lower=gamma,radius_upper=rho,derivative_upper=lipschitz))
    sep=[sqrt_interval(squared_range_box(p,domain)[0])[0] for p in anchors]
    L=sqrt_interval(sum(w/r**2 for w,r in zip(weights,sep)))[1] if min(sep)>0 else None
    return dict(lower=min(row['lower'] for row in rows),hessian_upper=L,cells=rows)

def raw_far_bound(anchors,weights,bx,bz,q):
    values=[]
    for p,w in zip(anchors,weights):
        lx,ux=range_box(p,bx); lz,uz=range_box(p,bz)
        gap=max(F(0),lx-uz,lz-ux); values.append(w*gap*gap)
    numerator=sum(sorted(values)[:survivors(len(anchors),q)])
    denominator=pair_max2(bx,bz)
    return sqrt_interval(numerator/denominator)[0] if denominator else F(0)

def build(data,q,divisions=4,delta='1',max_leaves=1024,target='1/20'):
    anchors,weights,domain=dataset(data); delta=rational(delta); target=rational(target)
    if delta<=0 or max_leaves<1 or target<0: raise ValueError('Invalid certificate settings')
    scatter=scatter_bound(anchors,weights,domain,q)
    local=local_bound(anchors,weights,domain,q,divisions)
    near=max(F(0),local['lower']-local['hessian_upper']*delta/2) if local['hessian_upper'] is not None else F(0)
    leaves=[]; pending=[('',domain,domain)]
    # Every split replaces one box with both children. No uncovered/pruned region.
    while pending:
        path,bx,bz=pending.pop()
        if pair_max2(bx,bz)<=delta*delta:
            leaves.append(dict(path=path,kind='near',raw_lower=near)); continue
        raw=raw_far_bound(anchors,weights,bx,bz,q)
        if raw>=target:
            leaves.append(dict(path=path,kind='far-resolved',raw_lower=raw)); continue
        if len(leaves)+len(pending)+1>=max_leaves or len(path)>=32:
            leaves.append(dict(path=path,kind='far-budget',raw_lower=raw)); continue
        children=split_pair(bx,bz)
        pending.extend([(path+str(k),*children[k]) for k in (1,0)])
    raw_global=min(F(row['raw_lower']) for row in leaves)
    combined=max(scatter['lower'],raw_global)
    return encode(dict(schema='rational-global-stability-v1',data=data,q=q,
        settings=dict(divisions=divisions,delta=delta,max_leaves=max_leaves,target=target),
        scatter=scatter,local=local,near_lower=near,leaves=leaves,
        raw_cover_lower=raw_global,certified_lower=combined,
        proof='THEORY.md T5 and Computed near/far certificate',
        scope='exact declared rational inputs; analytic fallback reported separately'))
