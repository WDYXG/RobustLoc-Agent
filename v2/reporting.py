"""Status-labelled theory-loop report generated from actual stored results."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from robustloc.storage import read,history,save
from .geometry import point_margin

def report(run):
    folder=Path(__file__).resolve().parent/'report'; folder.mkdir(exist_ok=True)
    figures=run/'figures'; figures.mkdir(exist_ok=True)
    records=history(run/'research_log.jsonl'); results=read(run/'iterations/006/evidence.json')
    registry=read(run/'claims.json'); algebra=read(run/'iterations/002/evidence.json'); local=read(run/'iterations/004/evidence.json'); ratio=read(run/'iterations/005/evidence.json')
    lines=['# Theory-driven v2：阶段研究报告','',
           '**known**：旧 run-001 永久冻结；本次不运行其 solver、不优化 CEP90。v1 文件哈希检查是完整性操作，不使用旧案例进行设计。','',
           '## 文献审计与贡献边界','',
           '**known**：FIM/GDOP、weighted frame operator、worst surviving frame bound、2q sparse correction、L1 balance、IRLS 与 trimming 都有既有理论或方法。详见 [LITERATURE_AUDIT.md](../LITERATURE_AUDIT.md) 和 references.json；全文与摘要阅读范围已区分。','',
           '**proved-in-project**：P1/P2 的局部曲率证书与 P3 的 range-specific 非共线判据有书面证明。这个标签只说明本项目完成推导，不宣称文献创新，也不表示 proof assistant 认证。','',
           '## 研究循环实际运行','',
           '本次 Codex 会话审计文献并写出证明/反例；Python 控制器按持久状态执行依赖式研究任务，独立 verifier 子进程复算证据。控制器不是自动形式化证明器，也不是开放式 LLM conjecture engine。预定义任务顺序与方法库是当前能力边界。','',
           '| 回合 | 主张 | 证据状态 | 后续 |','|---|---|---|---|']
    for r in records:
        lines.append(f'| {r["iteration"]} | {r["proposal"]["claim_id"]} | {r["verdict"]} | {r["next_step"]} |')
    lines.extend(['','## 主张账本','', '| ID | Status | Claim | Novelty |','|---|---|---|---|'])
    lines.extend(f'| {r["id"]} | {r["status"]} | {r["claim"]} | {r["novelty"]} |' for r in registry)
    lines.extend(['','## 可执行验证','',
                  f'**numerically-supported**：{algebra["matrices"]} 个随机矩阵上，解析 margin 与独立 eigvalsh 的最大差为 {algebra["max_eigenvalue_discrepancy"]:.3e}；线性界最大 observed error/bound 为 {algebra["max_linear_bound_ratio"]:.6f}。',
                  f'**numerically-supported**：{local["count"]} 个局部区域上遍历保留子集并抽样位置对，最小 observed output-separation / proved lower-bound 为 {local["minimum_observed_lower_lipschitz_ratio"]:.6f}。这些不是全称证明。','',
                  '**refuted**：R1 区分 q-erasure 与 q-corruption；R2 反射构造区分局部 margin 与全局分支；R3 区分 sparse identifiability 与 L1 decoder 条件；R4 区分 exact pointwise uniqueness 与 Lipschitz stability。精确论证见 THEORY.md。',''])
    if ratio['status']=='refuted':
        a=ratio['scores'][ratio['residual_choice']]; b=ratio['scores'][ratio['ratio_choice']]
        lines.extend([f'**refuted**：C2 在 seed={ratio["seed"]}、trial={ratio["trial"]} 找到实际 range-map 两候选反例：residual-only T={a["T"]:.6f}，ratio-selected T={b["T"]:.6f}；后者超出 noise feasibility gate，并且位置误差更大。反例仅证否有限候选池的普遍优势/fit-reliability 主张，不声称证明任意连续优化目标都失败。',''])
    lines.extend(['## 联合估计策略：FFRG','',
                  '**conjectured**：Feasibility-First Residual–Geometry (FFRG) 是本项目候选组合策略，新颖性尚未确立。Residual reliability 由 q-trimmed weighted residual norm 定义；先筛选 ≤epsilon+tau，再最大化候选的 beta 信息证书。不会为了恢复几何强行增加可疑 residual 的权重。','',
                  '**proved-in-project**：若 truth 与 estimate 均属于可信 prior ball、exact anchors、≤q 任意污染、fixed positive weights 且真实 whitened inlier norm≤epsilon，则任何 gated、beta>0 的 candidate 都满足 (2epsilon+tau)/beta 的条件误差界。','',
                  '**conjectured**：找到 feasible solution 的 completeness、实际误差比 residual-only 更小、不可信 prior 与未知 q 情形的稳定性均未解决。选择最大 beta 只最大化这个保守条件证书，不等于最小化真实误差。','',
                  '## 固定假设压力实验','',
                  '**numerically-supported**：共享有限候选池，三种选择规则作机制对照；seed 和场景在运行前固定。Median error 只描述结果，不用于选参数或验收。No estimates 时不会把 abstention 当作0误差。','',
                  '| Scenario | Selector | Estimates / cases | Abstain | Median error (m) | Applicable bounds | Violations |','|---|---|---:|---:|---:|---:|---:|'])
    for s,modes in results['summary'].items():
        for mode,m in modes.items():
            median='N/A' if m['median_error'] is None else f'{m["median_error"]:.5f}'
            lines.append(f'| {s} | {mode} | {m["estimates"]}/{m["cases"]} | {m["abstentions"]} | {median} | {m["applicable_certificates"]} | {m["bound_violations"]} |')
    invalid=sum(m['invalid_prior_certificates'] for modes in results['summary'].values() for m in modes.values())
    lines.extend(['',f'**numerically-supported**：wrong_prior 场景出现 {invalid} 个数学形式为正、但 truth 不在 prior 内的条件输出（跨三种规则计数），这些都不纳入有效 bound 检查。Prior coverage 无法由污染观测自动认证；模型假设错误可能导致 abstention，也可能产生不适用的条件保证。','',
                  '## 未解决与下一步','',
                  '**conjectured**：需要审计更接近的 geometry-aware trimming / robust design / certified nonlinear estimation 文献后才谈新颖性；改进 search completeness（而非 CEP90）；研究未知 q 与不可信 prior 的 set-valued ambiguity 输出；引入 anchor uncertainty 时重推 Hessian/noise 模型。','',
                  '## 复现与冻结','',
                  '从仓库根目录：`python -m pytest v2/tests -q`；`python -m v2.agent --run v2/runs/reproduce --steps 6`。单回合使用 `--steps 1`，同一 run 恢复日志。源代码/理论修改后必须新建 run，不能覆盖历史。`python -m v2.audit_run` 只检查保存结果。','',
                  '## 图表（numerically-supported）','',
                  '![Erasure margin](../runs/theory-001/figures/margin_vs_erasure.png)','',
                  '![Abstention](../runs/theory-001/figures/abstention_by_scenario.png)','',
                  '![Bound ratios](../runs/theory-001/figures/conditional_bound_ratios.png)'])
    # Figures describe assumptions/geometry, rather than optimize a tail-error benchmark.
    angles=np.arange(8)*np.pi/4; c=np.zeros(2); layouts={'balanced':10*np.column_stack([np.cos(angles),np.sin(angles)]),'near line':np.column_stack([np.linspace(-12,12,8),np.linspace(-.02,.02,8)**2])}
    plt.figure(figsize=(7,4))
    for name,p in layouts.items(): plt.plot(range(7),[point_margin(c,p,np.ones(8),k)['alpha'] for k in range(7)],'o-',label=name)
    plt.xlabel('Number of erased rows k (unknown q attacks require k=2q)'); plt.ylabel('Worst surviving lower frame bound'); plt.legend(); plt.tight_layout(); plt.savefig(figures/'margin_vs_erasure.png',dpi=170); plt.close()
    scenarios=list(results['summary']); plt.figure(figsize=(9,4)); ix=np.arange(len(scenarios))
    for i,mode in enumerate(['residual_only','unguarded_ratio','feasible_geometry']):
        plt.bar(ix+i*.25,[results['summary'][s][mode]['abstentions']/results['summary'][s][mode]['cases'] for s in scenarios],.25,label=mode)
    plt.xticks(ix+.25,scenarios,rotation=15); plt.ylabel('Abstention fraction (not zero error)'); plt.legend(); plt.tight_layout(); plt.savefig(figures/'abstention_by_scenario.png',dpi=170); plt.close()
    plt.figure(figsize=(7,4))
    for mode in ['residual_only','unguarded_ratio','feasible_geometry']:
        values=[r['bound_ratio'] for r in results['rows'] if r['mode']==mode and r['bound_applicable']]
        if values: plt.hist(values,bins=15,alpha=.5,label=mode)
    plt.axvline(1,color='red',linestyle='--',label='proved upper-bound threshold'); plt.xlabel('Observed error / conditional bound (only valid prior cases)'); plt.ylabel('Count'); plt.legend(); plt.tight_layout(); plt.savefig(figures/'conditional_bound_ratios.png',dpi=170); plt.close()
    (folder/'report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    save(run/'final_summary.json',dict(status='numerically-supported',experiment_summary=results['summary'],v1_mutations=0,iterations=len(records),unresolved=read(run/'state.json')['unresolved'],proof_status='written deductions, not formal verification',novelty='not established'))
