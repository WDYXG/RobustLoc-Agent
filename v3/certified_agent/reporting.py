"""Research report: safety, usefulness and sensing cost are reported together."""
from fractions import Fraction as F
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from robustloc.storage import save

def report(folder,summary,learning,results,audit,cfg):
    figs=folder/'figures'; figs.mkdir(exist_ok=True)
    names=cfg['methods']; shortened=['always','passive','random','greedy','active','learned']
    fig,axes=plt.subplots(1,3,figsize=(13,4))
    for ax,key,label in zip(axes,['coverage','wrong_output_rate','mean_acquisitions'],['Output coverage','Wrong outputs / all cases','Mean added ranges']):
        values=[summary['in_contract'][n][key] or 0 for n in names]
        ax.bar(shortened,values,color=['#a6a6a6','#8cafd0','#a0c28e','#d5b46b','#437ba6','#bb91ad'])
        ax.set_title(label); ax.tick_params(axis='x',rotation=30)
    fig.suptitle('In-contract paired synthetic episodes; no unconditional real-world guarantee')
    fig.tight_layout(); fig.savefig(figs/'decisions_risk_cost.png',dpi=150); plt.close(fig)
    certified=[r for r in results if r['method']=='active-certified' and r['final_contract']['valid']
               and r['outcome']['lower_before'] is not None]
    fig,ax=plt.subplots(figsize=(7,4))
    ax.scatter([float(F(r['outcome']['lower_before'])) for r in certified],
               [float(F(r['outcome']['lower_after'])) for r in certified],s=22,alpha=.55)
    upper=max(float(F(r['outcome']['lower_after'])) for r in certified)
    ax.plot([0,upper],[0,upper],':',color='gray')
    ax.set(xlabel='Initial certified lower margin',ylabel='Final certified lower margin',
        title='Active acquisition changes the guaranteed lower bound')
    fig.tight_layout(); fig.savefig(figs/'active_certificate_gain.png',dpi=150); plt.close(fig)
    scenarios=cfg['scenarios'][:8]
    values=np.array([[summary['by_scenario'][method][s]['coverage'] for s in scenarios] for method in names])
    fig,ax=plt.subplots(figsize=(11,4))
    im=ax.imshow(values,vmin=0,vmax=1,cmap='Blues',aspect='auto')
    ax.set(xticks=range(len(scenarios)),xticklabels=scenarios,yticks=range(len(names)),yticklabels=shortened)
    ax.tick_params(axis='x',rotation=30); fig.colorbar(im,ax=ax,label='Output coverage')
    for i in range(len(names)):
        for j in range(len(scenarios)): ax.text(j,i,f'{values[i,j]:.2f}',ha='center',va='center',fontsize=8)
    fig.tight_layout(); fig.savefig(figs/'scenario_coverage.png',dpi=150); plt.close(fig)
    active=summary['in_contract']['active-certified']; always=summary['in_contract']['always-cauchy']
    passive=summary['in_contract']['passive-certified']; learned=learning['summary']
    lines=['# Phase 3A：从 certificate 到 adaptive decision 的实际运行','',cfg['title'],'',
        '**numerically-supported**：已执行 observation → certificate → decision → acquire → reverify 闭环。每个请求在仿真环境中取得一个真实生成的新 range，累计预算保持原样，然后重新认证。有限规则/前瞻控制器不等于 LLM 自主定理发现。','',
        f'共 {len(results)} 个 method–episode 结果，{len(cfg["scenarios"])*cfg["heldout_cases_per_scenario"]} 个 paired episodes；训练 {cfg["training_layouts"]}、模型测试 {cfg["model_test_layouts"]} 个独立几何布局。历史 {audit["frozen_files"]} 个 v1/v2 文件逐字节不变。','',
        '## 条件有效场景：风险、覆盖率与成本','',
        '| method | outputs / cases | coverage | wrong outputs | selective risk | mean acquisitions | bound violations |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for name in names:
        m=summary['in_contract'][name]; risk='undefined' if m['selective_risk'] is None else f'{m["selective_risk"]:.3f}'
        lines.append(f'| {name} | {m["outputs"]}/{m["cases"]} | {m["coverage"]:.3f} | {m["wrong_outputs"]} | {risk} | {m["mean_acquisitions"]:.3f} | {m["certified_bound_violations"]} |')
    lines+=['',f'**numerically-supported**：always-Cauchy 错误输出 {always["wrong_outputs"]}/{always["cases"]}；active-certified 为 {active["wrong_outputs"]}/{active["cases"]}，同时输出 {active["outputs"]}/{active["cases"]}，平均新增 {active["mean_acquisitions"]:.3f} 次观测。passive-certified 输出 {passive["outputs"]}/{passive["cases"]}，用以检查 active 是否只靠拒绝获得安全。','',
        f'严格 μ 提升案例 {active["strict_mu_improvement_cases"]}：只在 post-lower > pre-upper 时计数。其他变化仅称 certified lower gain，不能解释为测得 μ 真值。单步与随机方法在相同预算及环境规则下比较；缓存影响 wall runtime，本阶段不主张运行速度优势。','',
        '![Decision risk and cost](figures/decisions_risk_cost.png)','',
        '![Certificate gain](figures/active_certificate_gain.png)','',
        '![Scenario coverage](figures/scenario_coverage.png)','',
        '## 反例与前瞻','',
        '**refuted**：q=1、4 个共线旧 anchors 时，加一个新 anchor 仍可保留 3 个旧共线坐标，reflection 给 μ=0；“加一个必然恢复”失败。前三步中 immediate lower 可以保持零，而 3 个新 reporters 的组合能够越过阈值。单步 positive-gain greedy 会停止；horizon agent 执行获取后逐步重新认证。budget-limited 场景拒绝输出并保留原因，不强制做无效采集。','',
        '## 学习型诊断的证据边界','',
        f'**numerically-supported**：独立模型测试中 {learned["test_labeled"]} 个可区分标签、{learned["test_unknown"]} 个 unknown；accuracy={learned["accuracy"]:.3f}，false-positive={learned["false_positive"]}，false-negative={learned["false_negative"]}，Brier={learned["brier"]:.4f}。这些是 certificate-separated synthetic labels，未学习到精确 μ，也未得到概率安全保证。unknown 没有被标为 0。','',
        '预测器对 certified policy 只作建议；learned-gate 是无证书对照。估计 q 不参与恢复授权；missing-q-budget 场景输出 conditional capacity profile 后拒绝。capacity_lower 只覆盖已计算 q≤profile_max_q，不能称为实际 q 或完整最大容量。','',
        '## 假设失效场景','',
        '| method | outputs / cases | wrong outputs | bound violations |', '|---|---:|---:|---:|']
    for name in names:
        m=summary['outside_contract'][name]
        lines.append(f'| {name} | {m["outputs"]}/{m["cases"]} | {m["wrong_outputs"]} | {m["certified_bound_violations"]} |')
    lines+=['','真位置不在 D、clean noise 超预算、实际 bad support 超 q 或 q_budget 缺失均单列；数学证书不能证明这些假设在真实系统成立。新观测污染 stress 使用“首个新 reporter 被污染”的一致响应规则；各政策的坏 reporter 位置可能不同。','',
        '## 已实现与未完成','',
        '**known**：reject option、active sensing、sensor placement、Cauchy/trimmed LS 和 logistic regression 是已有方法。**proved-in-project**：输出门控复用 Phase 2 T2/T5，独立消费者重算精确几何与 residual，并检查传感器预算和轨迹一致性；不声称正式形式化验证或新数学定理。','',
        '**conjectured / unresolved**：真实环境 q/domain/noise contract 的可靠来源、uncertain anchors、动态目标、全局 decoder 完整性、跨 inverse problems 的通用性、硬件观测成本与人机请求执行。无真实 BLE/众包部署，无新颖性或工业适用性声明。','',
        '代码入口：`python -m v3.certified_agent.run --run v3/runs/certified-agent-reproduce`；只读审计：`python -m v3.certified_agent.audit`。数据/动作/证书/模型/失败都保存在此 run。源文件/配置变化后必须开新 run，不改历史。']
    (folder/'report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    save(folder/'summary.json',summary)
