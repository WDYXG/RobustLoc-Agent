"""Explicit exact counterexamples, analytic hierarchy and source-budget probes."""
from copy import deepcopy
from fractions import Fraction as F
from v3b.assumption_agent.verifier import root
from .verifier import verify_witness
from .core import basis,recover
from .simulator import make


def basic(p,values,q=0,refs=()):
    return dict(episode_id='theory',nominal=p,measurements=[dict(anchor=i,value=v,weight='1') for i,v in zip(p,values)],
       hard_refs=[dict(anchor=i,centre=p[i],radius='0',root='external') for i in refs],reports=[],failure_groups={},external_roots=['external'],
       q=q,r=0,epsilon='1/1000000',tolerance='1/10',domain=['-2','2','-2','2'],budget='0',offers=[],receipts=[],baselines=[],
       forecast_frames=[dict(R=[['1','0'],['0','1']],t=['0','0'])])


def witness(obs,A,B):
    d2=sum((F(a)-F(b))**2 for a,b in zip(A['target'],B['target'])); lo=root(d2)[0]
    c=dict(worlds=[A,B],diameter_lower=str(lo),minimax_radius_lower=str(lo/2),scope='exact continuous-world witness')
    verify_witness(obs,c); return c


def execute(cfg):
    counter=[]
    p={'a0':['5','0'],'a1':['3','4'],'a2':['0','5']}; obs=basic(p,['5']*3)
    obs['measurements']*=34; obs['measurements']=obs['measurements'][:100]
    obs.update(r=1,failure_groups={'receipt':'one-group'},reports=[dict(issuer='receipt',points=[dict(anchor=i,centre=a,radius='0') for i,a in p.items()])])
    A=dict(target=['0','0'],positions=p); pp={i:[str(F(a[0])+F('4/5')),a[1]] for i,a in p.items()}; B=dict(target=['4/5','0'],positions=pp)
    counter.append(dict(id='C0',status='refuted',claim='observation-only receipt validation separates translated worlds',
       observation=obs,witness=witness(obs,A,B),identical_ordinary_ranges=100,
       calibration_predicate=dict(A=True,B=False),known_mechanism='indistinguishability / translation gauge'))
    p={'a0':['1','0'],'a1':['0','1']}; obs=basic(p,['1','1'])
    A=dict(target=['0','0'],positions=p); B=dict(target=['1/2','0'],positions={'a0':['3/2','0'],'a1':['-1/2','0']})
    counter.append(dict(id='C1',status='refuted',claim='star map identifiable modulo rigid transformations',
       observation=obs,witness=witness(obs,A,B),anchor_baseline2_A='2',anchor_baseline2_B='4'))
    p={'a0':['2','0'],'a1':['0','2'],'a2':['-2','0']}; obs=basic(p,['2']*3)
    fixed={'u0':['0','0'],'u1':['1','0'],'u2':['0','1']}; obs['nominal'].update(fixed)
    obs['hard_refs']=[dict(anchor=i,centre=a,radius='0',root='external') for i,a in fixed.items()]
    A=dict(target=['0','0'],positions=deepcopy(obs['nominal'])); pp=deepcopy(obs['nominal'])
    for i in ('a0','a1','a2'): pp[i]=[str(F(pp[i][0])+F('1/2')),pp[i][1]]
    B=dict(target=['1/2','0'],positions=pp)
    counter.append(dict(id='C2',status='refuted',claim='three fixed frame points suffice without measured connectivity',observation=obs,witness=witness(obs,A,B)))
    p={'a0':['-3/4','0'],'a1':['3/4','0']}; obs=basic(p,['5/4']*2,refs=p)
    A=dict(target=['0','1'],positions=p); B=dict(target=['0','-1'],positions=p)
    counter.append(dict(id='C3',status='refuted',claim='two exact measured references remove reflection',observation=obs,witness=witness(obs,A,B)))
    p=dict(p,a2=['0','4'],a3=['0','-4']); obs=basic(p,['5/4','5/4','3','3'],q=1,refs=p)
    A=dict(target=['0','1'],positions=p); B=dict(target=['0','-1'],positions=p)
    counter.append(dict(id='C4',status='refuted',claim='four general-position exact range coordinates suffice at q=1',observation=obs,witness=witness(obs,A,B),bad_support_A=[3],bad_support_B=[2]))
    # With only two points on any line, all three-survivor subsets are noncollinear.
    stable=deepcopy(obs); stable['nominal']['a4']=['4','3']; stable['hard_refs'].append(dict(anchor='a4',centre=['4','3'],radius='0',root='external'))
    stable['measurements'].append(dict(anchor='a4',value=format(20**.5,'.17f'),weight='1'))
    certificate=recover(stable,cfg)
    if not certificate.get('certified'): raise AssertionError('five-reference q1 development target not certified')
    # Exact noiseless hierarchy is analytic, not a finite sampled cloud.
    hierarchy=[dict(label='no reference',refs=0,diameter2='72',diameter_lower=str(root(F(72))[0]),diameter_upper=str(root(F(72))[1]),
                    model='D=[-3,3]^2; all star anchors free'),
        dict(label='one measured point',refs=1,diameter2='8',diameter_lower=str(root(F(8))[0]),diameter_upper=str(root(F(8))[1]),model='circle centred(0,0), radius sqrt2 wholly in D'),
        dict(label='two measured points',refs=2,diameter2='4',diameter_lower='2',diameter_upper='2',model='refs(0,0),(4,0); target(1,+/-1)'),
        dict(label='three noncollinear points',refs=3,diameter2='0',diameter_lower='0',diameter_upper='0',model='third ref(0,4); target(1,1) unique')]
    source_probes=[]
    obs,private=make('three-source-majority',0,cfg,cfg['development_seed'])
    good=obs['reports'][0]['points']; bad=obs['reports'][1]['points']
    for r in (1,2):
        for M in (2*r,2*r+1):
            s=deepcopy(obs); s['r']=r; s['reports']=[]; s['failure_groups']={}
            for i in range(M):
                issuer='probe-'+str(i); s['failure_groups'][issuer]=issuer
                s['reports'].append(dict(issuer=issuer,points=deepcopy(bad if i<r else good)))
            c=recover(s,cfg); source_probes.append(dict(r=r,groups=M,certificate=c,
                certified=bool(c.get('certified')),labels='known redundancy instantiated; positive continuous cover verified'))
    uncertainty=[]
    for delta in ('0','1/1000','1/100','1/20'):
        s=deepcopy(obs); s['reports']=[]; s['hard_refs']=[dict(a,root='external-position-instrument',radius=delta) for a in good]
        b=basis(s); uncertainty.append(dict(radius=delta,pre_bound=b['pre_bound'],certificate=b))
    ledger=[dict(id='K1',status='known',claim='indistinguishability, Euclidean gauge, rigidity, sparse observability and group redundancy'),
       *[dict(id='T'+str(i),status='proved-in-project',proof='THEORY.md T'+str(i),novelty='unestablished') for i in range(1,7)],
       *[dict(id=r['id'],status=r['status'],claim=r['claim']) for r in counter],
       dict(id='H1',status='conjectured',claim='trust-directed finite purchases can avoid structurally useless ranges')]
    return dict(counterexamples=counter,ledger=ledger,analytic_hierarchy=hierarchy,
        five_reference_q1=dict(observation=stable,certificate=certificate),source_redundancy=source_probes,
        bounded_reference_profile=uncertainty,scope='scripted research cycles; human proofs plus exact consumers, not autonomous LLM discovery')
