# MathResearch-Agent / Phase 3A

Certified Adaptive Localization Agent 是 range localization 的有限决策实验。
MathResearch-Agent 是项目路线的总称；跨非线性 inverse problems 的能力尚未验证。
v1、v2 和全部旧文件已冻结，新工作仅在 v3/。

核心闭环：observations → conditional certificate → recover / abstain /
acquire-more-data → simulated new observation → independent re-certification。

阅读 [输入与证据契约](certified_agent/SPEC.md)、[文献边界](certified_agent/LITERATURE.md)、
[实际运行报告](runs/certified-agent-001/report.md)。

在仓库根目录运行，沿用 `..\.venv\Scripts\python.exe`，无需安装新依赖：

```powershell
python -m pytest v3/certified_agent/tests -q
python -m v3.certified_agent.run --run v3/runs/certified-agent-reproduce
python -m v3.certified_agent.audit
python -m v2.global_stability.audit_run
python -m v2.audit_run
```

单次实际输入：`python -m v3.certified_agent.cli --input observation.json --output decision.json`。
输入格式见 run 的 observations/；epsilon、error_tolerance、domain 必须显式提供。
省略 q_budget 会拒绝，estimated_corruption 不填补这个缺失。acquire-more-data 只
返回下一次请求的位置与计划，不直接联络设备。仿真 run 才会执行观测获取。

估计污染数和 learned probability 只作诊断；恢复需要声明的条件 q budget、固定
weights、valid D/noise contract、正几何下界及精确 residual feasibility。
Certificate lower=0 不等于 μ=0。Planner 最大化有限候选中的认证下界，支持最多
3 步前瞻。容量报告是 computed q 内的 conditional lower capacity，不估计实际 q。

报告同时给风险、coverage、abstention 和 acquisition cost；包含 always-Cauchy、
passive、random、greedy、active、learned-gate 对照和独立的 assumption-violation
场景。学习标签保留 unknown，训练/模型测试/最终 episode 使用不同种子。
所有来源、动作日志、观测、private evaluator evidence、证书、模型和拒绝原因持久化。

**known**：拒绝选项、主动观测和布局设计均有 prior art。
**proved-in-project**：输出条件沿用 v2 T2/T5，有限精确证书可复算。
**numerically-supported**：仿真结果和学习诊断。
**refuted**：单个新增 anchor 普遍充分的假设（q=1 共线反例）。
**conjectured**：真实环境适用性、跨问题通用性、解码完整性和原创性。
