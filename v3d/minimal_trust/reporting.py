from collections import Counter
from fractions import Fraction as F
from v3b.assumption_agent.storage import read,save,hydrate
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def report(path):
    rows=read(path/'results.json'); finite=[r for r in rows if r['mode']=='finite-complete']; continuous=[r for r in rows if r['mode']=='continuous']
    analytic=[r for r in rows if r['mode']=='continuous-exact-reduction']
    regression=read(path/'compulsory_regression.json')
    metrics=dict(finite_cases=len(finite),finite_exact_finite_optima=sum(not r['interval']['lower_infinite'] for r in finite),
        finite_proved_infinite=sum(r['interval']['lower_infinite'] for r in finite),continuous_cases=len(continuous),
        continuous_exact_reduction_cases=len(analytic),continuous_nonzero_closed_gaps=sum(r['interval']['gap']=='0' and F(r['interval']['cost_upper'])>0 for r in analytic),
        continuous_closed_gaps=sum(r['interval']['gap']=='0' for r in continuous),
        continuous_states=dict(Counter(r['interval']['state'] for r in continuous)),
        finite_states=dict(Counter(r['interval']['state'] for r in finite)),
        automatic_old_miss_repairs=sum(r['automatic_old_miss_repaired'] for r in continuous),
        compulsory_development_repaired=regression['automatic_old_miss_repaired'],
        subset_nodes=sum(r['subset_nodes'] for r in continuous),uniform_certificate_nodes=sum(r['uniform_nodes'] for r in continuous),
        finite_adaptive_states=sum(r['adaptive_states'] for r in finite),finite_cover_nodes=sum(r['cover_nodes'] for r in finite),
        witness_count=sum(r['witness_count'] for r in rows),
        incomplete_uniform_searches=sum(not r['uniform_search_complete'] for r in continuous),
        full_results='results.json',runtime='runtime.json')
    save(path/'metrics.json',metrics)
    ledger=[dict(id='K1',status='known',claim='Helly/enclosing disks, test-cost decision trees, set cover and restriction monotonicity'),
      *[dict(id='P'+str(i),status='proved-in-project',proof='THEORY.md P'+str(i),novelty='unestablished') for i in range(1,9)],
      dict(id='C1',status='refuted',claim='pair diameter alone characterizes planar enclosing radius'),
      dict(id='C2',status='refuted',claim='global batch hitting set is always an adaptive cost lower bound'),
      dict(id='R1',status='numerically-supported',claim='automatic recovery of the fixed old cost3.6 miss and declared held-out variants'),
      dict(id='F1',status='proved-in-project',claim='checked exact optima for explicitly complete finite catalogs; not continuous upper bounds'),
      dict(id='H1',status='conjectured',claim='stronger continuous witness/certificate families may close remaining physical gaps')]
    save(path/'CLAIM_LEDGER.json',ledger)
    save(path/'research_cycles.json',[
       dict(status='known',step='audit enclosing disks, decision trees and adaptive cover'),
       dict(status='refuted',step='test pair-only radius and batch-to-adaptive lower-bound transfer'),
       dict(status='proved-in-project',step='derive incident-hyperedge lower bound, exact finite DP, uniform subset-policy upper'),
       dict(status='proved-in-project',step='check exact zero-noise tangency reduction before transferring finite equality to continuous cost'),
       dict(status='numerically-supported',step='automatically repair old miss and run frozen gap experiment'),
       dict(status='conjectured',step='retain nonzero continuous gap rather than claim physical optimality')])
    # Clear distinction between a missing UB and a proved infinite lower bound.
    representative=[next(r for r in continuous if r['case']==k+'-0') for k in ('regression','positive-gap','insufficient-budget','search-limited','family-limited')]
    fig,ax=plt.subplots(figsize=(9,4.6))
    for i,r in enumerate(representative):
        v=r['interval']; lo=float(F(v['cost_lower'])); hi=float(F(v['cost_upper'])) if v['cost_upper'] is not None else None
        ax.scatter([lo],[i],color='#254d75',marker='|',s=220)
        if hi is not None:
            ax.plot([lo,hi],[i,i],color='#3b918b',linewidth=5); ax.scatter([hi],[i],color='#254d75',marker='|',s=220)
        else: ax.annotate('upper not established',xy=(lo+.12,i),va='center',fontsize=10,color='#8a5b24')
    ax.set_yticks(range(len(representative)),[r['case'][:-2] for r in representative]); ax.invert_yaxis()
    ax.set_xlabel('Certified interval for continuous adaptive information cost'); ax.set_xlim(-.12,4.1); ax.grid(axis='x',alpha=.2)
    ax.set_title('A finite witness restriction supplies a lower bound, not an upper bound')
    fig.tight_layout(); fig.savefig(path/'continuous_cost_intervals.png',dpi=160); plt.close(fig)
    a=next(r for r in finite if r['case']=='adaptive-four-0'); t=next(r for r in finite if r['case']=='acute-triple-0')
    fig,axes=plt.subplots(1,2,figsize=(9,4))
    axes[0].bar(['Fixed batch','Adaptive tree'],[float(F(a['batch_cost'])),float(F(a['interval']['cost_upper']))],color=['#bc8b43','#3b918b'])
    axes[0].set_title('Batch cost can exceed adaptive optimum'); axes[0].set_ylabel('Information cost')
    axes[1].bar(['Pairs only','Pairs + triples'],[float(F(t['pair_batch_cost'])),float(F(t['batch_cost']))],color=['#bc8b43','#3b918b'])
    axes[1].set_title('Pair witnesses can miss a radius obstruction')
    fig.tight_layout(); fig.savefig(path/'exact_counterexamples.png',dpi=160); plt.close(fig)
    lines=['# Phase 3C — Minimal Trust Optimality Gap','',
      'Frozen source/config/seeds; 3,686 previous tracked files preserved. This phase implements cost bounds and subset search for one localization case study. It does not claim general minimal trust is solved.',
      '', '## Main distinctions','',
      '- **known:** enclosing-radius/Helly witnesses, set cover, decision trees and restriction monotonicity have direct prior art.',
      '- **proved-in-project:** scoped P1–P8 proofs and exact consumers. Project proofs are not novelty claims or proof-assistant formalizations.',
      '- **refuted:** a global nonadaptive witness cover need not lower-bound adaptive cost; three unit-cost tests give batch3 versus adaptive2 in the fixed development counterexample.',
      '- **refuted:** pair distances<=2rho do not imply enclosing radius<=rho; the rational acute triangle has radius13/12>21/20, while every pair fits.',
      '- **numerically-supported:** subset search automatically repairs the old3.6 example; original frozen results are not overwritten.',
      '', '## Exact finite models','',
      f"{metrics['finite_cases']} finite instances: {metrics['finite_exact_finite_optima']} exact finite cost optima, {metrics['finite_proved_infinite']} proved impossible under their complete menus. Positive equality assumes the finite catalog is the complete prior. The infinite cases also give continuous impossibility lower witnesses because every physical query reply preserves their dangerous pair.",
      '', '| case | pair batch | hypergraph batch | incident LB | exact adaptive cost | state at budget2 |',
      '|---|---:|---:|---:|---:|---|']
    for r in finite:
        if r['case'].endswith('-0'):
            show=lambda x:'infinite' if x is None else x
            lines.append(f"| {r['case']} | {show(r['pair_batch_cost'])} | {show(r['batch_cost'])} | {show(r['incident_lower'])} | {show(r['interval']['cost_upper'])} | {r['interval']['state']} |")
    lines+=['','The finite variants change declared prices on six fixed templates; this is controlled exact-instance validation, not held-out geometry generalization. All finite-policy trees are executed in every catalog world, including counterfactual policy checks for underfunded decision budgets. The budget decision itself rejects an underfunded plan. The actual world id is used only by the simulator; the policy input is the public possible-world catalog.',
       '', '## Exactly closed continuous special cases [proved-in-project]','',
       'A separately checked algebraic completeness certificate reduces an initially continuous physical problem to exactly two reflection worlds. Two exact fixed-reference ranges force x=(0,+/-h); an unknown anchor with ||p||<=2h and range3h must satisfy p=-2x by equality in the triangle inequality. This is an exact, zero-noise q=r=0 boundary case, not sampled completeness.',
       '', '| instance | continuous lower | continuous upper | gap | weaker uniform-ball family UB |',
       '|---|---:|---:|---:|---|']
    for r in analytic:
        v=r['interval']; lines.append(f"| {r['case']} | {v['cost_lower']} | {v['cost_upper']} | {v['gap']} | {'not found' if r['uniform_ball_family_upper'] is None else r['uniform_ball_family_upper']} |")
    lines+=['','These nonzero continuous optima are authorized by proof of the exact physical reduction. The weaker uniform-ball family misses them because it includes anchor geometries excluded by the observed range equations. This provides explicit evidence of certificate conservatism. It does not solve general positive-noise continuous optimality.',
       '', '## Continuous physical cost bounds','',
       'The lower bound solves a checked finite restriction using EVERY available action. The upper bound quantifies ALL replies consistent with initial hard balls, by uniform geometry and post-purchase nuisance radii. It is stronger in scope than a finite forecast pre-gate.',
       '', '| case | lower | upper | absolute gap | relative gap | budget diagnosis |',
       '|---|---:|---:|---:|---:|---|']
    for r in representative:
        v=r['interval']; show=lambda x:'unknown' if x is None else x
        lines.append(f"| {r['case']} | {v['cost_lower']} | {show(v['cost_upper'])} | {show(v['gap'])} | {show(v['relative_gap'])} | {v['state']} |")
    lines+=['',f"Continuous held-out instances: {len(continuous)}; closed physical gaps: {metrics['continuous_closed_gaps']}; states: {metrics['continuous_states']}.",
       '', 'Unknown upper is not infinity. Search-limited cases stop enumeration after one node; family-limited cases exhaust the declared uniform family without a certificate. Neither establishes physical impossibility. Insufficient-budget cases use lower>budget, not a failed upper search.',
       '', 'Each search-limited input matches its positive-gap counterpart up to episode id; unlimited search supplies upper3.6 on that same physical input. This is concrete evidence of search incompleteness, separate from the analytic certificate-conservatism examples and unseparable-reflection impossibility examples.',
       '', '## Compulsory old miss','',
       f"Development regression repaired: {regression['automatic_old_miss_repaired']}. Held-out old-generator misses repaired automatically: {metrics['automatic_old_miss_repairs']}/{sum(r['case'].startswith('regression-') for r in continuous)}.",
       '', 'Bundle and measurement subset are selected by enumeration, not by a hardcoded a0/a1/a2 rule. The development bundle costs18/5=3.6 and yields a post-delivery radius near0.0113. Its continuous lower is0, so physical cost3.6 is not claimed optimal. Finite-menu exhaustive optimality applies only to the chosen sufficient uniform family.',
       '', '## Search and audit evidence','',
       f"Held-out subset nodes={metrics['subset_nodes']}; uniform certificate nodes={metrics['uniform_certificate_nodes']}; finite adaptive states={metrics['finite_adaptive_states']}; witness count={metrics['witness_count']}. Per-case counts are in results.json; measured execution times are in runtime.json.",
       '', 'The independent finite consumer uses acute-triangle/Helly threshold tests and a bottom-up minimax recurrence. Continuous consumers bind every selected coordinate, retained source assertion, geometry certificate, residual and union bound to the original observation. Physical witness verification checks all query replies and the combined future clean-noise budget. Hash-linked histories and immutable source/output manifests are audited.',
       '', '## Remaining limitations','',
       'Finite models are tiny synthetic catalogs with deterministic replies and externally declared completeness. The continuous witness search uses a few feasible translated worlds; it is not complete. The uniform upper family uses exact reference purchases and initial hard balls, and does not yet handle soft-source reply games. It may ignore useful baseline/range information. Nonlinear candidate search and ball-union centering are incomplete. Costs are declared information prices; CPU is reported separately.',
       '', 'Root honesty, q/r, domain/noise coverage and source identities remain external. No autonomous LLM discovery or second inverse problem was added. Scientific source/config changes after evaluation are forbidden. All conclusions retain known / proved-in-project / conjectured / numerically-supported / refuted labels.',
       '', 'Reproduce: `../.venv/Scripts/python.exe -m v3d.minimal_trust.run --run v3d/runs/minimal-trust-reproduce-new`.',
       'Audit: `../.venv/Scripts/python.exe -m v3d.minimal_trust.audit --run <run>`.',
       'Theory and primary-source audit are in ../../minimal_trust/.']
    (path/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
