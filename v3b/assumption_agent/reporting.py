"""Generate metrics and figures from a frozen run, without tuning."""
from collections import Counter
from fractions import Fraction as F
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .storage import read,save,hydrate


def summarize(rows):
    cost=sum(F(r['information_cost']) for r in rows); new=sum(r['new_certified'] for r in rows)
    out=sum(r['evaluation']['output'] for r in rows); wrong=sum(r['evaluation']['wrong_output'] for r in rows)
    return dict(episodes=len(rows),outputs=out,newly_certified=new,wrong_outputs=wrong,
        risk=wrong/out if out else None,coverage=out/len(rows) if rows else None,information_cost=str(cost),
        new_certificates_per_cost=float(F(new)/cost) if cost else None,
        mean_information_cost=float(cost)/len(rows) if rows else None,
        mean_volume_reduction=sum(float(F(r['volume_reduction'])) for r in rows)/len(rows) if rows else None,
        mean_log_volume_ratio=sum(math.log(float(F(r['volume_ratio']))) for r in rows)/len(rows) if rows else None,
        rejections=sum(len(r['rejected']) for r in rows),
        actions=dict(Counter(a['kind'] for r in rows for a in r['acquisitions'])),
        failures=dict(Counter(r['failure_reason'] for r in rows if r['final_action']=='abstain')))


def report(path):
    cfg=read(path/'manifest.json')['config']; rows=read(path/'results.json')
    metrics={m:summarize([r for r in rows if r['method']==m and r['service_model_valid']]) for m in cfg['methods']}
    scenario={s:{m:summarize([r for r in rows if r['method']==m and r['scenario']==s]) for m in cfg['methods']} for s in cfg['scenarios']}
    stressed={m:summarize([r for r in rows if r['method']==m and not r['service_model_valid']]) for m in cfg['methods']}
    save(path/'metrics.json',dict(honest_service=metrics,service_integrity_stress=stressed,scenarios=scenario))
    fig,axes=plt.subplots(1,3,figsize=(13,4))
    labels=['range only','random info','one step','multi step']; xs=list(range(4))
    for ax,key,title in zip(axes,['new_certificates_per_cost','mean_information_cost','mean_volume_reduction'],
            ['New certified outputs / information cost','Mean information cost','Mean prior assumption-volume reduction']):
        ax.bar(xs,[metrics[m][key] or 0 for m in cfg['methods']],color=['#718096','#c28b35','#3f8f96','#5a67c9'])
        ax.set_xticks(xs,labels,rotation=20); ax.set_title(title,fontsize=10); ax.grid(axis='y',alpha=.2)
    fig.tight_layout(); fig.savefig(path/'information_tradeoffs.png',dpi=160); plt.close(fig)
    tasks=hydrate(path,read(path/'research_tasks.json')); fig,ax=plt.subplots(figsize=(6,4))
    for q in range(3):
        points=[r for r in tasks['perturbation'] if r['q']==q]
        ax.plot([float(F(r['radius'])) for r in points],[float(F(r['lower'])) for r in points],marker='o',label=f'q={q} lower certificate')
        ax.plot([float(F(r['radius'])) for r in points],[float(F(r['sampled_secant_upper_min'])) for r in points],linestyle=':',alpha=.6,label=f'q={q} sampled upper witness')
    ax.set_xlabel('Anchor ball radius'); ax.set_ylabel('Shared-map margin'); ax.legend(fontsize=7); ax.grid(alpha=.2)
    fig.tight_layout(); fig.savefig(path/'margin_perturbation.png',dpi=160); plt.close(fig)
    c1=tasks['counterexamples'][0]; nominal_front=next(r for r in tasks['frontiers'] if r['radius']=='1/100' and r['domain']==cfg['default_domain'])['frontier']
    lines=['# Phase 3B.1 actual run','',
      'This is a finite range-localization decision/planning agent under uncertain premises. Prior 1,417 tracked files remain frozen. No phase retrieval, LLM scientist or novelty claim.',
      '', '## Mathematical result and correction','',
      '**proved-in-project:** shared-map derivative perturbation, robust weighted-scatter certificate, nominal model-error recovery bound and a sufficient conditional frontier. Conventional scatter/perturbation/set-membership foundations are **known**.',
      '',f"**refuted:** naive unknown-anchor error <=2epsilon/mu_rob. Exact simultaneous translation by 0.1 changes the target but preserves every range, with epsilon=0 and positive uniform lower {float(F(c1['positive_uniform_lower'])):.6f}. This leaves the shared-map definition valid; it defeats its misuse across two anchor explanations.",
      '', 'Correct conservative gate: B_q=2(E+zeta_q)/b_q, zeta_q^2 is the sum of the n-q largest weighted ball-radius squares. Final nominal residual must be <=E+zeta_Q; error <=(E+rhat+zeta_Q)/b_Q for every actual q<=Q. No q prediction or learned output grants safety.',
      '', 'Example frontier (circle, D=[-1,1]^2, all radii=0.01, rmax=0.4):','',
      '| q | uniform lower | epsilon ceiling | error bound at E=.04 | pre-gate |','|---|---:|---:|---:|---|']
    for r in nominal_front['rows']:
        num=lambda v:f'{float(F(v)):.6f}' if v is not None else 'uncertified'
        lines.append(f"| {r['q']} | {num(r['lower'])} | {num(r['epsilon_ceiling'])} | {num(r['error_bound'])} | {r['certified']} |")
    lines+=['','This is a sufficient frontier, not exact mu or an impossibility test. Smaller hypothetical domains/radii are conditional until receipts are accepted.',
       '', '## Fixed held-out simulation [numerically-supported]','',
       '| method | outputs / honest cases | new outputs | cost | new/cost | mean volume reduction | wrong outputs |',
       '|---|---:|---:|---:|---:|---:|---:|']
    for m,v in metrics.items():
        lines.append(f"| {m} | {v['outputs']}/{v['episodes']} | {v['newly_certified']} | {float(F(v['information_cost'])):.2f} | {v['new_certificates_per_cost']:.4f} | {v['mean_volume_reduction']:.4f} | {v['wrong_outputs']} |")
    lines+=['','Numerator excludes already certified episodes; denominator includes all paid requests, including failed or unnecessary purchases. Report costs, abstentions and risk alongside this ratio.',
       '', '| scenario | range-only outputs/cost | random outputs/cost | one-step outputs/cost | multi-step outputs/cost |',
       '|---|---|---|---|---|']
    for s,values in scenario.items():
        lines.append('| '+s+' | '+' | '.join(f"{values[m]['outputs']}/{values[m]['episodes']}; cost={float(F(values[m]['information_cost'])):.2f}" for m in cfg['methods'])+' |')
    support=metrics['multi-step']['new_certificates_per_cost']>metrics['measurement-only']['new_certificates_per_cost']
    ledger=tasks['ledger']
    for claim in ledger:
        if claim['id']=='H1':
            claim.update(status='numerically-supported' if support else 'conjectured',
                evidence='metrics.json honest_service; finite fixed simulation only',
                limitation='No universal dominance; retain per-scenario results and service integrity stress')
    save(path/'CLAIM_LEDGER.json',ledger)
    save(path/'research_cycles.json',[
       dict(stage='literature',label='known',result='scatter, anchor uncertainty and information value have prior art'),
       dict(stage='conjecture',label='conjectured',target='shared-map margin alone bounds unknown-anchor recovery'),
       dict(stage='counterexample',label='refuted',evidence='research_tasks.json C1 exact translation'),
       dict(stage='revision',label='proved-in-project',result='T3 nominal model-error inflation; human proof plus exact consumer'),
       dict(stage='experiment',label='numerically-supported',evidence='perturbation secants and fixed costed scenarios'),
       dict(stage='limitation',label='known',result='conditional safety cannot establish physical issuer honesty')])
    lines+=['',f"H1 pooled evaluation: {'numerically-supported' if support else 'not supported in this run'}. This is not a universal dominance theorem; the table retains per-scenario ties/failures and the finite horizon/budget limit.",
      '', 'Volume metric is normalized product measure over original q/noise/domain/anchor uncertainty dimensions. It is not feasible-position volume or posterior probability. Range purchases alone score zero contraction here even when they improve recovery. Shrinking eight independent radii creates a very large product reduction; mean log ratio is also recorded in metrics.json.',
      '', '## Service integrity stress and limits','',
      'Untrusted calibration receipts are rejected, with paid cost retained. A dishonest calibration using an allowed issuer can pass provenance/nesting checks while placing actual anchors outside new balls. These episodes are separated from honest-service performance; physical truth cannot be established from a receipt schema. Exact conditional bounds cease to apply there. The final failures are retained in results.json and every action in history.jsonl.',
      '', 'Planning uses advertised deterministic nested information outcomes, finite offers and horizon3; it is not expected-value optimal under stochastic service errors. Calibration shrinks same-centre balls in a synthetic service; no real calibration protocol is implemented. Solver is incomplete. Robust margin bounds may be loose and subset enumeration is combinatorial.',
      '', 'Research cycles are explicit scripted records of this project development, with written proofs and exact verification. They are not evidence of an LLM autonomously discovering or approving theorems.',
      '', f"Perturbation experiment: {len(tasks['perturbation'])} radius/q cells, {sum(r['trials'] for r in tasks['perturbation'])} sampled exact interval secants, {sum(r['violations'] for r in tasks['perturbation'])} lower-bound violations. Samples test the derivations and never create certified lower bounds.",
      '', '## Reproduce and inspect','',
      'From repository root using ../.venv/Scripts/python.exe: run `-m pytest tests v2 v3/certified_agent/tests v3b/assumption_agent/tests -q`; create a fresh run with `-m v3b.assumption_agent.run --run v3b/runs/assumption-frontier-reproduce`; audit with `-m v3b.assumption_agent.audit --run <new path>`. Existing run folders cannot be overwritten.',
      '', 'Sources/config are frozen in manifest.json before evaluation. Mathematical certificates are consumed using pairwise variance rather than producer centering arithmetic; hashes, receipt transitions, costs, original-domain volume and private evaluation are replayed independently. The audit verifies conditional math, not issuer honesty.',
      '', 'Figures: information_tradeoffs.png and margin_perturbation.png. Primary-source audit: ../../assumption_agent/LITERATURE_AUDIT.md. Human-readable proofs: ../../assumption_agent/THEORY.md.']
    lines+=['','Service-integrity stress uses a deliberately stricter rmax=.05 and E=.001 for the dishonest calibration fixture; these rows are not pooled with honest cases.',
       '', '| method | stress outputs | wrong outputs | violated reported bounds | rejected requests |',
       '|---|---:|---:|---:|---:|']
    for m,v in stressed.items():
        violations=sum(r['evaluation']['bound_violation'] for r in rows if r['method']==m and not r['service_model_valid'])
        lines.append(f"| {m} | {v['outputs']} | {v['wrong_outputs']} | {violations} | {v['rejections']} |")
    (path/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
