from collections import Counter
from fractions import Fraction as F
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from v3b.assumption_agent.storage import read,save,hydrate


def summary(rows):
    cost=sum(F(r['information_cost']) for r in rows); n=sum(r['new_certified'] for r in rows)
    out=sum(r['output'] for r in rows)
    return dict(episodes=len(rows),outputs=out,new_certified=n,information_cost=str(cost),
       new_per_cost=float(F(n)/cost) if cost else None,wrong_outputs=sum(r['wrong_output'] for r in rows),
       bound_violations=sum(r['bound_violation'] for r in rows),coverage=out/len(rows) if rows else None,
       action_mix=dict(Counter(a['kind'] for r in rows for a in r['actions'])),
       final_diagnoses=dict(Counter(r['final_diagnosis'] for r in rows)),
       failures=dict(Counter(r['reason'] for r in rows if not r['output'])))


def report(path):
    cfg=read(path/'manifest.json')['config']; rows=read(path/'results.json'); tasks=hydrate(path,read(path/'research_tasks.json'))
    good={m:summary([r for r in rows if r['method']==m and r['intended_in_contract']]) for m in cfg['methods']}
    scenarios={s:{m:summary([r for r in rows if r['scenario']==s and r['method']==m]) for m in cfg['methods']} for s in cfg['scenarios']}
    bad={m:summary([r for r in rows if r['method']==m and not r['intended_in_contract']]) for m in cfg['methods']}
    save(path/'metrics.json',dict(in_contract=good,out_of_contract=bad,scenarios=scenarios))
    H=tasks['analytic_hierarchy']; fig,ax=plt.subplots(figsize=(8,4))
    ax.plot(range(4),[float(F(r['diameter_upper'])) for r in H],marker='o')
    ax.set_xticks(range(4),['no reference','one measured reference','two measured references','three noncollinear'])
    ax.set_ylabel('Exact noiseless star feasible-target diameter'); ax.set_title('Fixed frame and target observability are distinct'); ax.grid(alpha=.2)
    fig.tight_layout(); fig.savefig(path/'trust_hierarchy.png',dpi=160); plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(10,4)); labels=['range only','random info','trust directed']
    for ax,key,title in zip(axes,['new_per_cost','outputs'],['New certificates / paid information cost','Certified outputs in honest contract episodes']):
        ax.bar(labels,[good[m][key] or 0 for m in cfg['methods']],color=['#718096','#c28b35','#3f8f96']); ax.set_title(title,fontsize=10); ax.grid(axis='y',alpha=.2)
    fig.tight_layout(); fig.savefig(path/'trust_costs.png',dpi=160); plt.close(fig)
    support=(good['trust-directed']['new_per_cost'] or 0)>(good['range-only']['new_per_cost'] or 0)
    ledger=tasks['ledger']
    for row in ledger:
        if row['id']=='H1': row.update(status='numerically-supported' if support else 'conjectured',evidence='metrics.json; finite menu only')
    save(path/'CLAIM_LEDGER.json',ledger)
    save(path/'research_cycles.json',[
      dict(stage='literature',status='known',claim='gauge, rigidity, sparse observability, Byzantine models'),
      dict(stage='counterexample',status='refuted',claim='unanchored receipts verify themselves / star is rigid / frame fixes unconnected target'),
      dict(stage='proof',status='proved-in-project',claim='T1–T6 scoped proofs and continuous covers'),
      dict(stage='experiment',status='numerically-supported',claim='fixed trust menu, retained impossible and premise-budget failures')])
    lines=['# Phase 3B.2 — Joint Nuisance Identifiability & Minimal Trust','',
      'All files tracked at1ed4e01 remain byte-frozen. New scope is v3c/trust_agent. One range-localization case study, finite decision agent, human-written proofs and exact consumers; no autonomous theorem discovery, second inverse problem or novelty claim.',
      '', '## Mathematical findings','',
      '**known:** observation equivalence, Euclidean gauge, graph rigidity, sparse secure observability, set membership and Byzantine redundancy have direct prior art.',
      '', '**proved-in-project:** T1 observation-only validation impossibility and two-point error lower bound; T2 rigid stabilizers; T3 star-map sparse identifiability; T4 bounded-reference recovery; T5 all-source-branch covers; T6 finite sufficient trust frontier. Proof status is not proof-assistant formalization or priority.',
      '', '**refuted:** ordinary ranges validate unanchored calibration; star joint map is identifiable modulo rigidity; three unmeasured frame references locate the target; two measured references eliminate reflection; four exact general-position range coordinates suffice atq=1. Exact witnesses are in research_tasks.json.',
      '', 'Three noncollinear references fix a planar O(2) frame, but target-range connectivity is separate. On unrestricted D, every k−2q range-survivor subset needs three noncollinear trusted positions. k counts range coordinates: repetitions of three locations can provide coordinate-corruption redundancy; they do not automatically handle persistent reporter faults.',
      '', '100 ordinary range responses and the same alleged calibration receipt remain identical in an exact translated pair; target separation=.8 gives minimax error lower=.4. This proves impossibility for informative observation-only validation in both worlds, not that every agent must falsely certify. Abstaining remains possible.',
      '', 'One-reference and two-reference residual gauges must be feasible inside D. The displayed analytic q=0 hierarchy is a separate exact star example on D=[-3,3]^2, with a full circle at one reference and a reflected pair at two; it is not the diameter of a sampled hypothesis cloud.',
      '', '| measured references | exact feasible-target diameter |','|---|---:|']
    for h in H: lines.append(f"| {h['label']} | {float(F(h['diameter_upper'])):.6f} |")
    lines+=['','Trusted intrinsic baselines preserve global rigid gauge. Full relative graph rigidity does not itself supply absolute coordinates. Under source budgetr, three identical aliases of one failure domain count as one source, not a majority.',
      '', 'Source deletion probes (complete exact layout reports, independent groups):','', '| r | groups | continuous cover certified |','|---:|---:|---|']
    for r in tasks['source_redundancy']: lines.append(f"| {r['r']} | {r['groups']} | {r['certified']} |")
    lines+=['','The2r+1 majority statement applies only to independent whole-layout reports with identical exact honest outputs. It is not a general3r+1 Byzantine consensus or arbitrary calibration result. r and group identities remain external premises.',
      '', '## Fixed held-out experiments [numerically-supported]','',
      '| method | outputs / honest cases | new outputs | total cost | new/cost | wrong |','|---|---:|---:|---:|---:|---:|']
    for m,v in good.items(): lines.append(f"| {m} | {v['outputs']}/{v['episodes']} | {v['new_certified']} | {float(F(v['information_cost'])):.3f} | {v['new_per_cost']:.4f} | {v['wrong_outputs']} |")
    lines+=['','| scenario | range-only outputs/cost | random outputs/cost | trust-directed outputs/cost |','|---|---|---|---|']
    for s,v in scenarios.items(): lines.append('| '+s+' | '+' | '.join(f"{v[m]['outputs']}/{v[m]['episodes']}; cost={float(F(v[m]['information_cost'])):.3f}" for m in cfg['methods'])+' |')
    lines+=['','Planner optimality is restricted: enumerate affordable bundles and choose cheapest passing a sufficient common-branch geometry pre-gate for every declared finite forecast. Proved-empty forecast source branches are excluded; unresolved ones are retained. Delivered continuous certificates, not the forecast catalog, authorize output. Minimum cost of a sufficient certificate is not universal minimum physical trust or an optimal nonlinear algorithm.',
      '', 'The agent emits structural ambiguity only with checked continuous-world witnesses. Positive exact-reference margin but insufficient noise bound is called precision/certificate gap. Other failures remain unresolved; no lower=0 impossibility shortcut. All failed/exhausted actions and source branches are retained.',
      '', '## External trust and negative results','',
      'A deliberately violated premise-budget fixture has two false groups while declaringr=1. The agreed false layout passes the conditional mathematics and shifts the target by.8. This is outside the admissible-world set; it demonstrates that agreement and a schema cannot validate their own fault budget or physical source independence.',
      '', '| method | out-of-model outputs | wrong outputs | bound violations |','|---|---:|---:|---:|']
    for m,v in bad.items(): lines.append(f"| {m} | {v['outputs']} | {v['wrong_outputs']} | {v['bound_violations']} |")
    lines+=['','The evaluated setup has11 in-contract geometry/service templates with4 target/noise instances each, not a broad geometry distribution. q corruption is one fixed initial coordinate; future repeats are clean and their aggregate norm is below the declared globalE. r refers to full layout-source groups. The forecast menu is finite, service outcomes deterministic, and planning CPU is not counted as information cost.',
      '', 'Calibration roots are simulated external point instruments, not real GNSS/signature/provenance verification. Bounded references and source branches can retain ambiguity below the required resolution. Pairwise disjoint-ball tests are sufficient infeasibility proofs, not complete intersections; numerical candidate search is incomplete. Baselines are checked in witnesses but deliberately ignored by positive outer covers, hence may be conservative.',
      '', '## Reproduce','',
      '`../.venv/Scripts/python.exe -m pytest tests v2 v3/certified_agent/tests v3b/assumption_agent/tests v3c/trust_agent/tests -q`',
      '', '`../.venv/Scripts/python.exe -m v3c.trust_agent.run --run v3c/runs/trust-identifiability-reproduce`',
      '', '`../.venv/Scripts/python.exe -m v3c.trust_agent.audit --run <new run>`',
      '', 'manifest.json freezes sources/config before evaluation; history.jsonl is hash-linked; continuous certificates are independently consumed; exact witnesses and complete finite cost enumeration are checked. Existing runs cannot be overwritten. Claims in CLAIM_LEDGER.json; source audit and proofs in ../../trust_agent/.']
    (path/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
