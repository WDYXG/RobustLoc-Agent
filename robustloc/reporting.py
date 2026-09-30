"""Evidence-bound Markdown and PDF report builder."""
from pathlib import Path
from xml.sax.saxutils import escape
import numpy as np
from .storage import read, history, save
from .figures import final_figures

def bootstrap(base,final,samples):
    """Paired, scenario-stratified bootstrap of aggregate tail and failure differences."""
    rng=np.random.default_rng(77123); groups=list(base['by_scenario']); deltas=[]
    arrays={s:(np.array([r['error'] for r in base['rows'] if r['scenario']==s]),np.array([r['error'] for r in final['rows'] if r['scenario']==s])) for s in groups}
    for _ in range(samples):
        a,b=[],[]
        for s,(x,y) in arrays.items():
            idx=rng.integers(0,len(x),len(x)); a.extend(x[idx]); b.extend(y[idx])
        a,b=np.array(a),np.array(b)
        deltas.append([np.quantile(b,.9)-np.quantile(a,.9),np.mean(b>10)-np.mean(a>10)])
    ci=np.quantile(deltas,[.025,.975],axis=0)
    return dict(samples=samples,seed=77123,method='paired scenario-stratified percentile bootstrap, conditional on frozen selected method',cep90_difference_95ci=ci[:,0].tolist(),failure_rate_difference_95ci=ci[:,1].tolist())

def report(run,cfg):
    final_figures(run)
    results={m:read(run/f'heldout_{m}.json') for m in ['unweighted','weighted','final']}
    ci=bootstrap(results['weighted'],results['final'],cfg['experiment']['bootstrap_samples']); save(run/'bootstrap.json',ci)
    records=history(run/'research_log.jsonl'); frozen=read(run/'frozen_method.json')
    base,final=results['weighted']['overall'],results['final']['overall']
    gain=100*(1-final['cep90']/base['cep90'])
    sections=[]
    def add(title,text): sections.append((title,text))
    add('Abstract',f'A persistent bounded research agent tested {len(records)} hypotheses on synthetic crowd-localization observations. The frozen method is {frozen["method"]["name"]}. On {final["n"]} held-out cases, weighted baseline CEP90 was {base["cep90"]:.3f} m and final CEP90 was {final["cep90"]:.3f} m ({gain:.1f}% relative reduction). Failure rates were {base["failure_rate"]:.3%} and {final["failure_rate"]:.3%}. These are simulation observations, not a proof or an industrial claim.')
    add('1 Introduction','Question: can a persistent agent improve tail localization performance under fixed heterogeneous and corrupted synthetic observations? This course project studies a finite family of robust estimators. It does not claim a newly invented robust loss or a solution to an established open mathematical problem.')
    add('2 Problem Formulation','For target x in R^2, reporter positions p_i and distance proxies d_i, residual r_i(x)=||x-p_i||-d_i. Unweighted NLS minimizes sum r_i^2. WLS minimizes sum c_i r_i^2/s_i^2, with s_i^2=distance_sigma_i^2+position_sigma_i^2. The variance approximation uses a first-order radial projection of isotropic position error. It is not an exact errors-in-variables likelihood. Robust candidates minimize sum rho(c_i r_i^2/(s_i^2 t^2))*t^2 using SciPy loss conventions. Nonconvex range residuals mean convergence is not a certificate of global optimality.')
    add('3 Why This Is a Mathematical Research Agent','The controller reads persistent incumbent metrics and research history, identifies a worst scenario, selects one untested hypothesis, modifies a solver configuration, executes tests and experiments, searches counterexamples, and submits results to an independent verifier process. Accepted and rejected hypotheses change subsequent parents and ordering. The proposer is an authored rule policy, not an LLM, and creativity is bounded by its method library. Skills guide human/Codex extension; the Python controller does not execute Markdown Skills or call Codex CLI.')
    add('4 Agent Architecture','Simulator -> immutable baselines/evaluator -> observation-only solver -> saved measurements -> verifier subprocess -> append-only history and atomic state -> proposer. Protected source hashes and historical baseline hashes are checked each round. This is an auditable integrity guard, not a security sandbox against arbitrary malicious Python. The verifier independently applies acceptance rules but shares simulator assumptions; it is not an independent scientific replication.')
    add('5 Synthetic Experimental Environment',f'Eight equally sampled scenarios: clean, Gaussian, heteroscedastic, 10/20/30% outliers, poor geometry, sparse reporters. Development: {cfg["experiment"]["development_cases"]} cases/scenario; validation: {cfg["experiment"]["validation_cases"]}; final held-out: {cfg["experiment"]["heldout_cases"]}. Split roots 110000, 220000, 930000; each scenario uses root+10000*scenario_index+case_index. RSSI error is approximated with additive Gaussian distance noise, clipped at 0.1 m; outliers add signed 15-45 m offsets. Reporter position error is isotropic. Confidence is independent uniform [0.65,1], not an oracle. Outlier counts are rounded (2,3,5 of 16); sparse has 1 of 4. Poor geometry uses a narrow angular arc. Freshness is preserved but unused. Moving targets are outside this phase.')
    add('6 Baselines','Both baselines use analytic Jacobians, a weighted centroid initialization, and a 150-function-evaluation budget per start. Optimization failure returns a finite centroid fallback with success=False, and both its error and failure are retained. Baseline development/validation results and tests were completed before any research round.')
    add('7 Autonomous Research Protocol','Only one mechanism changes relative to the incumbent each round. Independent acceptance requires at least 2% lower aggregate validation CEP90, at most 0.5 percentage points failure-rate increase, no scenario CEP90 exceeding max(0.25 m, 1.25*incumbent), and no increase in optimization failures or nonfinite cases. Supported means these empirical rules passed; rejected means regression/invalidity; otherwise inconclusive and retained as a branch. These thresholds were fixed before research. Repeated validation selection can overfit; the held-out split was evaluated only after freeze.')
    add('8 Iteration History','\n'.join(f'Iteration {r["iteration"]}: {r["proposal"]["mechanism"]}; parent {r["proposal"]["parent"]}; {r["verdict"]}; CEP90 {r["metrics"]["validation"]["overall"]["cep90"]:.3f} m; failure {r["metrics"]["validation"]["overall"]["failure_rate"]:.3%}. Hypothesis: {r["hypothesis"]} Motivation: {r["proposal"]["motivation"]}' for r in records))
    add('9 Final Method',str(frozen['method'])+'\nThe method and source hash were saved before accessing held-out results. No post-held-out tuning is allowed in this run. Huber and soft-L1 have bounded influence; Cauchy has redescending influence and a nonconvex robust objective. Multi-start compares the same robust objective across deterministic starts. MAD is a residual-based scale heuristic, not an unbiased scale estimate with fitted corrupted residuals.')
    add('10 Experimental Results','\n'.join(f'{m}: mean {v["overall"]["mean"]:.3f} m; median/CEP50 {v["overall"]["median"]:.3f} m; CEP90 {v["overall"]["cep90"]:.3f} m; failures {v["overall"]["failure_rate"]:.3%}; mean runtime {1000*v["overall"]["runtime_mean_s"]:.3f} ms; optimizer failures {v["overall"]["optimization_failures"]}; nonfinite {v["overall"]["nonfinite_cases"]}.' for m,v in results.items())+f'\nPaired stratified bootstrap 95% CI, final minus WLS: CEP90 {ci["cep90_difference_95ci"]} m; failure rate {ci["failure_rate_difference_95ci"]}. Timing is hardware/load dependent. Bootstrap conditions on the selected estimator; it does not capture research selection uncertainty.')
    scenario_table='| Scenario | WLS CEP90 | Final CEP90 | WLS failure | Final failure |\n|---|---:|---:|---:|---:|\n'
    for s in results['final']['by_scenario']:
        b=results['weighted']['by_scenario'][s]; f=results['final']['by_scenario'][s]
        scenario_table+=f'| {s} | {b["cep90"]:.3f} | {f["cep90"]:.3f} | {b["failure_rate"]:.3%} | {f["failure_rate"]:.3%} |\n'
    add('10.1 Scenario Results',scenario_table)
    negatives=[r for r in records if r['verdict']!='supported']
    worst=max(results['final']['rows'],key=lambda r:r['error'])
    add('11 Failure Cases and Negative Results',f'{len(negatives)} proposals were not accepted. Full positive-excess candidate-versus-incumbent cases are saved in every verification.json. Worst held-out final case: {worst["scenario"]}, seed {worst["seed"]}, error {worst["error"]:.3f} m, optimizer success {worst["success"]}. An optimizer can converge and still give an inaccurate estimate. Sparse measurements and near-collinear geometry remain fundamental difficulties. Final failure-case visualization was produced for analysis only, after freeze.')
    add('12 Limitations','Only synthetic, static 2D data; no real BLE calibration, map constraints, correlated/malicious errors, temporal tracking, or external replication. No Tukey estimator is implemented. The simulator, candidate library, and fixed selection rule were authored together; no novelty or independent invention is established. Equal scenario mixtures determine aggregate CEP90. Reused validation seeds induce selection bias. Confidence is intentionally uninformative. Integrity checks are policy enforcement, not process isolation. Paired bootstrap does not correct all multiple comparisons. Finite budgets and centroid baselines may disadvantage NLS; fairer stronger baselines are future work.')
    add('13 Conclusion',f'Under this project\'s synthetic benchmark, the frozen method achieved {gain:.1f}% aggregate CEP90 reduction relative to the defined WLS baseline. Per-scenario regressions, residual failures and runtime must be considered alongside this aggregate. Mathematical facts: metric definitions and specified objectives. Empirical evidence: saved experiments. Hypotheses: each proposal. Conjecture/unresolved: robustness under other noise distributions and real BLE measurements; no mechanism or global-optimality proof.')
    add('Appendix: Reproducibility','Use Python 3.10+ and requirements.txt. Run python -m pytest -q; python agent.py baseline --run runs/reproduce; python agent.py research --run runs/reproduce; python agent.py finalize --run runs/reproduce. Do not overwrite run-001. Exact metrics reproduce under the saved numerical stack; runtimes vary. Files: manifest.json, environment.lock.txt, per-case JSON outputs, candidate snapshots, verifier requests/results, tests, state.json, hash-linked research_log.jsonl and frozen_method.json. Interrupted between log append and state commit: controller blocks on mismatch for explicit recovery, rather than inventing a round. GitHub publication requires an authenticated account and target repository.')
    add('References','Conceptual inspiration: DeepMathLLM/Creative-Intelligence, https://github.com/DeepMathLLM/Creative-Intelligence (accessed 2026-09-30). SciPy least_squares documentation: https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html. No source code was copied from the reference project.')
    root=Path(__file__).resolve().parents[1]; folder=root/'report'; folder.mkdir(exist_ok=True)
    markdown='# RobustLoc-Agent\n\nAn Agent for Discovery and Verification of Robust Nonlinear Crowd-Localization Methods\n\n'+'\n\n'.join('## '+h+'\n\n'+t for h,t in sections)
    images=['iteration_cep90','iteration_failure_rate','final_error_distribution','final_cep90_by_scenario','final_failure_rate_by_scenario','outlier_ratio','typical_case','failure_case']
    markdown+='\n\n## Figures\n\n'+'\n\n'.join(f'![{name}](../{run.relative_to(root).as_posix()}/figures/{name}.png)' for name in images)
    (folder/'report.md').write_text(markdown,encoding='utf-8')
    make_pdf(folder/'report.pdf',sections,run,images)
    (root/'RESULTS.md').write_text(sections[0][1]+'\n\n'+scenario_table,encoding='utf-8')

def make_pdf(path,sections,run,images):
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,Table,TableStyle,PageBreak,KeepTogether
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    styles=getSampleStyleSheet(); styles['BodyText'].fontSize=9; styles['BodyText'].leading=12
    styles['BodyText'].spaceAfter=7
    story=[Paragraph('RobustLoc-Agent',styles['Title']),Paragraph('Synthetic mathematical research agent | Reproducible course experiment',styles['BodyText']),Spacer(1,12)]
    for title,text in sections:
        story.append(Paragraph(escape(title),styles['Heading2']))
        if text.startswith('| Scenario'):
            rows=[line.strip('|').split('|') for line in text.strip().splitlines() if not line.startswith('|---')]
            rows=[[v.strip() for v in row] for row in rows]
            table=Table(rows,colWidths=[120,85,85,85,85],repeatRows=1)
            table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#183c56')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTSIZE',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),('GRID',(0,0),(-1,-1),.3,colors.lightgrey)]))
            heading=story.pop(); story.append(KeepTogether([heading,table]))
        else:
            for p in text.split('\n'): story.append(Paragraph(escape(p),styles['BodyText']))
    for index,name in enumerate(images):
        if index % 2 == 0 or name in ['typical_case','failure_case']:
            story.append(PageBreak())
        story.append(Paragraph(name.replace('_',' ').title(),styles['Heading2']))
        from PIL import Image as PILImage
        with PILImage.open(run/'figures'/(name+'.png')) as im: w,h=im.size
        scale=min(465/w,(540 if name in ['typical_case','failure_case'] else 280)/h)
        story.extend([Image(str(run/'figures'/(name+'.png')),width=w*scale,height=h*scale),Spacer(1,12)])
    def footer(canvas,doc):
        canvas.setFont('Helvetica',8); canvas.drawString(42,25,'RobustLoc-Agent | Synthetic evidence only'); canvas.drawRightString(550,25,str(doc.page))
    SimpleDocTemplate(str(path),pagesize=(595,842),rightMargin=42,leftMargin=42,topMargin=40,bottomMargin=42).build(story,onFirstPage=footer,onLaterPages=footer)
