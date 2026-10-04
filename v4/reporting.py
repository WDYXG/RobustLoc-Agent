from collections import Counter
from fractions import Fraction as F
from .storage import read,save
from .core.claim_ledger import entry
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def report(path):
    rows=read(path/'results.json'); regression=read(path/'range_regression.json')
    recovery=[r for r in rows if r['kind']=='recovery']; active=[r for r in rows if r['kind']=='active-finite']; continuous=[r for r in rows if r['kind']=='active-continuous']
    metrics=dict(range_regressions=regression['cases'],noisy_q1_recovery_cases=len(recovery),
        noisy_recoveries=sum(r['action']=='recover' for r in recovery),shared_research_cycles=len(active),
        continuous_q1_acquisition_cases=len(continuous),continuous_states=dict(Counter(r['interval']['state'] for r in continuous)),
        continuous_gap_closed=sum(r['interval']['gap']=='0' for r in continuous),
        actual_q1_acquisition_recoveries=sum(r['actual_recovery'] for r in continuous),
        retained_refutations=4,scope='synthetic exact transfer checks; finite candidate grid, fixed designs, no learned transfer rate')
    save(path/'metrics.json',metrics)
    matrix=[
      dict(component='support union q -> 2q',classification='shared unchanged',evidence='core/corruption.py; THEORY T1,T3'),
      dict(component='abstract stable recovery inequality',classification='shared unchanged',evidence='core/certificate.py; THEORY T1'),
      dict(component='candidate verification and abstention',classification='shared unchanged',evidence='core/certificate.py; both noisy q=1 families'),
      dict(component='finite minimax / incident cost LB',classification='shared unchanged',evidence='core/decision.py,core/verify.py; 43 legacy intervals'),
      dict(component='budget decision / optimality gaps',classification='shared unchanged',evidence='core/decision.py; both active families and PR q=1 continuous'),
      dict(component='research and reply-only action loop',classification='shared unchanged',evidence='core/research.py; identical five-stage sequence'),
      dict(component='symmetry validity and state metric',classification='adapter structure required',evidence='finite supplied transform family; exact adapter algebra; fixed range identity, PR sign'),
      dict(component='global positive margin',classification='adapter structure required',evidence='frozen range margin versus PR lifted Gram on annulus'),
      dict(component='radius oracle',classification='adapter structure required',evidence='core/geometry.py; all sign lifts for quotient'),
      dict(component='physical world / action binding',classification='adapter structure required',evidence='frozen range contracts; PR intensity and joint q budget'),
      dict(component='response-uniform acquisition UB',classification='adapter structure required',evidence='reference geometry versus sensing-vector design'),
      dict(component='Euclidean three-world witness limit',classification='failed transfer',evidence='exact quotient four-world obstruction'),
      dict(component='injectivity implies positive intensity margin under d_pm',classification='failed transfer',evidence='origin scaling; annulus restriction explicit'),
      dict(component='joint nuisance gauge / unknown PR sensing system',classification='not implemented',evidence='PR adapter rejects nuisance; no new gauge solver'),
      dict(component='LLM-generated hypotheses',classification='not implemented',evidence='human-declared sequence; phase5 deferred')]
    save(path/'transfer_matrix.json',matrix)
    ledger=[entry('K1','known','Real PR sign quotient, complement property and metric-dependent stability','LITERATURE_AUDIT.md','existing literature, no novelty'),
      *[entry('T'+str(i),'proved-in-project','Scoped proof '+str(i),'THEORY.md T'+str(i),'manual mathematical proof plus exact consumer checks; not a formal proof assistant') for i in (1,3,4,5,6,7)],
      *[entry('H'+str(i),'refuted',claim,'counterexamples.json','exact declared real planar model') for i,claim in enumerate([
        'equal intensity implies literal state equality','q deletions suffice for q unknown corruptions',
        'injectivity gives positive d_pm intensity margin near zero','three-point Helly witnesses transfer to sign quotient'],1)],
      entry('E1','numerically-supported','The same core executes two adapter research/action cycles and q=1 stable recovery','results.json;range_regression.json','predeclared finite synthetic families, not broad inverse-problem generality'),
      entry('H5','conjectured','Further inverse problems may use the same separation/cost core','THEORY.md H5','requires new domain certificates and independent transfer evaluation')]
    save(path/'CLAIM_LEDGER.json',ledger)
    counts=Counter(r['classification'] for r in matrix)
    fig,ax=plt.subplots(figsize=(9,4)); ax.barh(list(counts),list(counts.values()),color=['#368d82','#658cae','#c78942','#8b8b8b'])
    ax.invert_yaxis(); ax.set_xlabel('Declared components (audit categories, not a generalization percentage)'); ax.set_title('What transferred, what required structure, and what failed'); ax.set_xlim(0,7)
    fig.tight_layout(); fig.savefig(path/'transfer_components.png',dpi=160); plt.close(fig)
    fig,ax=plt.subplots(figsize=(8,3.8))
    for i,r in enumerate(continuous):
        d=r['interval']; lo=float(F(d['cost_lower'])); hi=float(F(d['cost_upper']))
        ax.plot([lo,hi],[i,i],linewidth=5,color='#368d82'); ax.scatter([lo,hi],[i,i],marker='|',s=150,color='#24455f')
    ax.set_yticks(range(len(continuous)),[r['case'] for r in continuous]); ax.invert_yaxis(); ax.set_xlabel('Continuous PR information-cost interval, global q=1'); ax.grid(axis='x',alpha=.2)
    fig.tight_layout(); fig.savefig(path/'pr_cost_intervals.png',dpi=160); plt.close(fig)
    lines=['# Phase 4 — Cross-Problem Generalization','',
      'One common core executes range and real phase retrieval. Prior artifacts remain frozen. This is a deterministic, human-directed transfer experiment; no LLM proposer or new phase-retrieval theory is claimed.','',
      f"Range compatibility: **{regression['cases']}/43** frozen Phase3C intervals reproduced by the new core. Four actual delivered subset outputs are identical. Frozen range proofs are wrapped in the adapter, not copied into a new application.",'',
      '## Transfer audit','', '| component | outcome | evidence |','|---|---|---|']
    lines += [f"| {r['component']} | {r['classification']} | {r['evidence']} |" for r in matrix]
    lines += ['', 'The component list is a declared engineering/proof audit, not an independent random sample of research skills. No aggregate transfer percentage is claimed.',
      '', '## Retained counterexamples [refuted]','',
      '1. x and -x have equal PR intensity; quotient distance makes their separation zero. The eight-candidate symmetry search checks universal algebra, not only sampled observations.',
      '2. Four generic planar sensing vectors survive any one deletion, but a two-world transcript is compatible with one arbitrary corrupted coordinate in each world. The common support-union core needs2q survivors.',
      '3. Squared intensity degenerates as t^2 near zero while d_pm scales as t. A phase-retrievable frame can therefore have zero requested margin. Positive certificates explicitly assume ||x||>=1/2.',
      '4. Four rational quotient points have squared enclosing radius4/5 while every triple has squared radius<=1/2. With tolerance4/5, a three-world witness limit misses the obstruction. Generic witness search now permits larger subsets.',
      '', '## Recovery and active measurement [numerically-supported]','',
      f"Noisy q=1 recovery: {metrics['noisy_recoveries']}/{len(recovery)} certified outputs across the two adapters, all checked against continuous domain margins. Candidates come from a fixed public 80-state grid; this is not a complete continuous reconstruction algorithm.",
      '', f"The SAME five-stage research function ran {len(active)} finite active cases across range and PR. Every finite policy is executed in every declared possible world. Finite prior completeness is explicit, and no finite tree upper is silently transferred to continuous worlds.",
      '', f"Continuous PR acquisitions: {len(continuous)} cases, states {metrics['continuous_states']}; actual certified post-acquisition outputs {metrics['actual_q1_acquisition_recoveries']}. Future observations retain one total q=1 budget, not a new budget per measurement and not an assumption that new observations are trusted.",
      '', '| case | lower | upper | gap | budget diagnosis |', '|---|---:|---:|---:|---|']
    for r in continuous:
        d=r['interval']; lines.append(f"| {r['case']} | {d['cost_lower']} | {d['cost_upper']} | {d['gap']} | {d['state']} |")
    lines += ['', 'The lower is an optimum of a physically checked restriction including every action. The upper is a continuous, all-replies sufficient design bound from the annulus margin. Gaps are retained; the finite optimum is not promoted to the continuous optimum.',
      '', '## What is actually general','',
      'Support-union, metric stability reduction, verified candidate gating, reply partitions, path-based cost lower bounds, Bellman decisions, budget states and the research loop do not contain a range/PR name branch. Observation algebra, valid symmetries, radius computations, positive global margins and action physics require problem structure.',
      '', 'The PR coefficient checker and annulus proof are adapter supplied. The program searches a supplied transform family, generates checked finite witnesses, and runs a human-declared task sequence. It has not autonomously invented the research questions or proved new literature-level theorems.',
      '', '## Reproducibility and limits','',
      'manifest.json freezes source/config before evaluation; output_hashes.json and audit.json verify stored artifacts. Runtime is measured before plots/final audit. history.jsonl binds every executed query reply. All prior tracked files are checked by PREVIOUS_FREEZE.json.',
      '', 'Real two-dimensional fixed designs only. No complex phase, unknown PR sensing vectors, general continuous minimax solver, unrestricted symmetry discovery or LLM proposer. Finite-catalog exact cost relies on declared completeness. Continuous certificates and budgets remain conditional on the specified domain/noise/corruption assumptions. Consumers use different computations but have the same author; they are not a formal proof assistant or external peer review.',
      '', 'See ../../THEORY.md, ../../LITERATURE_AUDIT.md and ../../README.md. Reproduce in a fresh path with `python -m v4.run --run v4/runs/reproduce-new`.']
    (path/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
