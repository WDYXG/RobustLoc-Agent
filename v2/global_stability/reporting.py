"""Evidence-bound report/plots; outputs belong to this run only."""
from fractions import Fraction as F
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from robustloc.storage import read,history

def number(s): return float(F(s))

def report(folder):
    records=history(folder/'research_log.jsonl'); profile=read(folder/'iterations/007/evidence.json')
    recovery=read(folder/'iterations/008/evidence.json'); branch=read(folder/'iterations/004/evidence.json')
    figdir=folder/'figures'; figdir.mkdir(exist_ok=True)
    qs=[r['q'] for r in profile['rows']]
    lower=[number(r['certificate']['certified_lower']) for r in profile['rows']]
    upper=[number(r['upper_witness']['upper']) for r in profile['rows']]
    raw=[number(r['certificate']['raw_cover_lower']) for r in profile['rows']]
    fig,ax=plt.subplots(figsize=(7,4))
    ax.fill_between(qs,lower,upper,color='#dce5ef',label='Unknown true margin inside certified interval')
    ax.plot(qs,lower,'o-',label='Exact rational lower certificate')
    ax.plot(qs,upper,'s--',label='Feasible-pair upper bound')
    ax.plot(qs,raw,'x:',label='Near/far cover alone')
    ax.axhline(number(profile['kappa']),color='gray',linestyle=':',label='Required kappa')
    ax.set(xlabel='Assumed maximum corruption count q',ylabel='Global stability margin',xticks=qs)
    ax.legend(fontsize=8); fig.tight_layout(); fig.savefig(figdir/'conditional_profile.png',dpi=160); plt.close(fig)
    fig,ax=plt.subplots(figsize=(7,3.5))
    for q in range(3):
        vals=[r['ratio'] for r in recovery['rows'] if r['q']==q]
        ax.scatter([q]*len(vals),vals,s=12,alpha=.6)
    ax.axhline(1,color='gray',linestyle=':'); ax.set(xlabel='Assumed q',ylabel='Error / certified T2 bound',xticks=[0,1,2])
    fig.tight_layout(); fig.savefig(figdir/'global_bound_stress.png',dpi=160); plt.close(fig)
    lines=['# Phase 2 实际运行报告','',read(folder/'manifest.json')['title'],'',
        '**proved-in-project**：T2 全局 residual-feasible 误差界、修正域条件后的 T3、T4 近远区证明、T5 可计算散布矩阵下界已写出。T5 进一步允许 bounded D 包含 anchors。证明见 ../../global_stability/THEORY.md；不是形式化机器证明，新颖性未确立。','',
        '**known**：排序式、支持并集 2q、lower-Lipschitz 定义、加权散布恒等式及 q 单调性；文献中的 set-membership、q-relaxed intersection、几何一致性不能作为本项目新贡献。','',
        f'**refuted**：C3 的精确点对给出 μ₁=0；两个完整小方形上的 γ 均≥{number(branch["local_lower"]):.8f}>0。D 是两个不连通的二维方形，不能声称已解决 connected/convex 附加条件。另保留 thin-domain T3 和 unbounded-domain 稳定性反例。','',
        '## 条件 corruption–stability profile','',
        '输入：8 个 radius-5 有理圆周 anchors，固定 w=1，D=[-1,1]²；κ=0.2。证书作用于整个矩形，非 Monte Carlo 下界。','',
        '| assumed q | certified lower b ≤ μ | feasible-pair upper μ ≤ U | raw near/far lower | unresolved far leaves |','|---:|---:|---:|---:|---:|']
    for r in profile['rows']:
        c=r['certificate']; unresolved=sum(l['kind']=='far-budget' for l in c['leaves'])
        lines.append(f'| {r["q"]} | {number(c["certified_lower"]):.8f} | {number(r["upper_witness"]["upper"]):.8f} | {number(c["raw_cover_lower"]):.8f} | {unresolved} |')
    q0=profile['rows'][0]['certificate']
    lines+=['',f'**proved-in-project**：κ={profile["kappa"]} 时 q_cert 的认证下限={profile["q_cert_lower"]}，可行上限={profile["q_cert_possible_upper"]}。两者相同才在这个 κ 下确定最大预算；未计算各 μ 的精确真值。q=3 的反射点对保留两个相等坐标，严格给出 μ₃=0；q≥4 按空 survivor 约定为 0。这些结果不估计实际数据中 q。','',
        f'q=0 的 near/far-only 下界={number(q0["raw_cover_lower"]):.8f}>0，覆盖使用 {len(q0["leaves"])} 个叶盒。其余 raw 值/预算耗尽数见表；combined 下界使用独立 T5 兜底。raw=0 表示该覆盖预算未认证正性，不能解释成 μ=0。','',
        f'**numerically-supported**：{len(recovery["rows"])} 个合成双解释案例满足 T2；max(error/bound)={max(r["ratio"] for r in recovery["rows"]):.8f}。每个 case 均记录两套 residual budgets 和 bad supports。这不是 estimator accuracy 实验，未产生 FFRG 性能结论。','',
        '![Conditional profile](figures/conditional_profile.png)','',
        '![Global error bound stress](figures/global_bound_stress.png)','',
        '## Agent 循环与证据限制','',
        'Codex 会话写出证明，有限 Python 控制器执行 8 个实际任务，按已验证反例决定是否进入域条件修复、bounded-domain 证书和 q profile。runtime 不自动发明任意定理，也不把固定任务表包装成 LLM 自主发现。独立进程重算有理数证书、完整 subset、完整二叉覆盖、点对上界和数值 residual。共享最小算术原语，因此不声称实现多样性或形式化可信内核。','',
        '| iteration | claim | actual verified label |','|---:|---|---|']
    lines += [f'| {r["iteration"]} | {r["proposal"]["claim_id"]} | {r["verdict"]} |' for r in records]
    lines+=['','**conjectured / unresolved**：原创性；Calafiore 全文 theorem-level 对照；更紧 μ 值、可扩展 subset 下界；connected/convex 域上的更强 local/global 关系；真实工作域和噪声预算可靠性；uncertain anchors；具体 decoder 的可行性和搜索完整性。','',
        '复现：仓库根目录 `python -m v2.global_stability.agent --run v2/runs/global-stability-reproduce --steps 8`。历史审计：`python -m v2.global_stability.audit_run`。source/配置变化会拒绝续跑；新研究应开新 run。v1 94 个冻结文件和 phase 1 source hashes 均由每轮检查保留。']
    (folder/'report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    summary=dict(profile=[dict(q=q,certified_lower=b,upper_bound=u,raw_cover_lower=r) for q,b,u,r in zip(qs,lower,upper,raw)],
        q_cert_lower=profile['q_cert_lower'],q_cert_possible_upper=profile['q_cert_possible_upper'],
        recovery_trials=len(recovery['rows']),max_error_to_bound=max(r['ratio'] for r in recovery['rows']),
        c3_uniform_local_lower=number(branch['local_lower']),c3_mu=0,
        status='proved-in-project',novelty='not established',exact_values='iterations/007/evidence.json')
    from robustloc.storage import save
    save(folder/'final_summary.json',summary)
