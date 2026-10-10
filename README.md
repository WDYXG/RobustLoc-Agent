# RobustLoc-Agent
### Verifier-Governed Mathematical Research Agent

一个 AI for Math 课程研究项目：以距离定位（Range Localization）和相位恢复（Phase Retrieval, PR）为实验场，研究智能体如何依据数学证书判断可恢复性、选择行动，并自主提出下一条可验证的研究问题。

**当前完成阶段：Phase 5 — Verifier-Governed Codex Researcher。**

> **Codex proposes; deterministic verifier disposes.**
>
> 模型提出问题、猜想与证据，确定性验证器决定形式命题是否获准进入结论账本。

[Phase 5 完整报告](v5/runs/PHASE5_REVIEW.md) · [实现与复现说明](v5/README.md) · [最终对照数据](v5/runs/comparison-v3-001/comparison.json) · [跨问题迁移报告](v4/runs/PHASE4_REVIEW.md)

## 核心研究闭环

项目从鲁棒定位的经验失败出发，逐步形成“数学结构 → 恢复证书 → 主动决策 → 跨问题共享结构 → 自主研究选题”的闭环。Phase 5 的 proposer 是真实 Codex；早期规则型研究循环保留为历史实现，不混称为 LLM 自主研究。

```mermaid
flowchart LR
  S["Research State<br/>已有结论、未解问题与失败记录"] --> P["Codex proposer<br/>每轮一个结构化 claim"]
  P --> T["受预算约束的数学工具<br/>精确代数、枚举与反例搜索"]
  T --> V["Deterministic verifier<br/>独立检查形式化证据"]
  V --> L["Claim ledger<br/>证明、证否、有限支持或未解决"]
  L --> S
```

模型根据当前状态选择下一研究动作，没有接收预排的轮次任务表。提案自身的“证明完成”声明不能授予状态；被拒绝的证书、失败的猜想修复和执行中断都保留在记录中。形式语言、工具与初始 frontier 由人提供。

## Phase 5：真实运行结果

两种策略使用相同初始研究状态、数学工具预算与验证规则。Scripted baseline 按预定任务策略执行；Codex 根据反馈自主选题。

| 指标 | Scripted baseline | Codex researcher |
|---|---:|---:|
| 计划研究槽位 | 12 | 12 |
| 完成的正式提案 | 12 | 11 |
| `proved-in-project` | 6 | 7 |
| `refuted` / 精确反例 | 1 | 2 |
| `numerically-supported` | 1 | 0 |
| 未解决（含执行失败） | 4 | 3 |
| 被拒绝的证明证书 | 0 | 2 |
| **有效形式账本推进** | **8** | **8** |

**本轮未证明 Codex 优于固定 workflow。** “有效推进”是预定的非重复、非空泛形式账本指标，不是原创定理数。Codex 的一项已验收证明因未提交非空域见证而不计推进；第七槽位中断，保留为失败，没有补造第十二份模型提案。

模型自行沿着“lifting 稳定性 → 测量扰动界 → 扩大适用范围 → 精确反例”的路线研究。两次证书被拒后，后续修正获得验收；最后一次缩小参数范围的猜想修复仍被证否。该轨迹支持受约束的自主选题与反馈迭代可执行，尚不支持普适自主数学发现或反馈作用的因果结论。

![Scripted 与 Codex 的实际研究轨迹](v5/runs/figures/phase5_trajectory.png)

- [逐轮提案、模型回执与验证证据](v5/runs/paired-v2-codex-001/scientific/iterations/)
- [统一重放审计](v5/runs/comparison-v3-001/replay_audits.json)与[修复计数审计](v5/runs/comparison-v3-001/repair_audit.json)
- [实际调用成本](v5/runs/provider_costs.csv)：中断槽位用量未知，已捕获合计只是成本下界。
- 原运行验收记录：[220 项回归测试](v5/runs/final_test_verification.json)，另有 [1 项续跑测试](v5/runs/operations-resume-tests.xml)和 [3 项统计测试](v5/runs/metric-v3-tests.xml)。这些是已保存的执行结果，不表示本次首页更新重跑了测试。

## 按研究问题阅读

| 问题 | 内容与入口 |
|---|---|
| 经验失败能否形成研究问题？ | v1：固定 synthetic BLE benchmark 与规则型循环。[历史结果](RESULTS.md)、[历史报告](report/report.md) |
| 任意污染下，何时可辨识、可稳定恢复？ | v2：文献审计、几何信息裕度、局部/全局区别与反例。[理论路线](v2/README.md)、[全局稳定性](v2/global_stability/README.md) |
| 证书能否指导估计、拒绝与获取信息？ | v3：[certificate-driven decision agent](v3/README.md) |
| 证书依赖的假设、信任与行动成本如何处理？ | [v3b：assumption](v3b/README.md)、[v3c：trust](v3c/README.md)、[v3d：minimal trust / optimality](v3d/README.md) |
| 哪些结构可以跨逆问题复用？ | v4：共享数学核心 + Range / PR adapters，同时保留不成立的迁移。[实现](v4/README.md)、[迁移报告](v4/runs/PHASE4_REVIEW.md) |
| 下一步研究什么，能否由模型决定？ | v5：Research State、真实 Codex proposer、hard verifier gate 与 scripted 对照。[实现](v5/README.md)、[报告](v5/runs/PHASE5_REVIEW.md) |

v4 的共享核心支持有限范围的结构迁移；PR 原点附近的 intensity 稳定裕度退化、sign quotient 下欧氏三点 witness 的直接迁移失败也保留在报告中。本轮 Codex 没有自主调用 Range/PR 共用 minimax 工具，不能把先前实现的跨问题能力归为此次自主运行的成果。

## 复现：先选择冻结快照

**首页是展示入口，严格实验审计请使用完成 Phase 5 时的提交 `c734a7011c055cedd1d24a91be3e750962ad8f4c`。**

2026-10-10 的首页同步是实验完成后的文档更新。旧冻结清单包含根目录 `README.md`，因此在更新后的 `main` 直接运行旧字节审计会报告首页哈希变化。我们保留原清单和验证器，用独立 checkout 复现原实验，不重新签署或绕过历史哈希。

从已有仓库创建一个新的复现目录：

```powershell
git worktree add --detach ../RobustLoc-Agent-phase5-frozen c734a7011c055cedd1d24a91be3e750962ad8f4c
cd ../RobustLoc-Agent-phase5-frozen
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m v5.runs.evaluator_v2.run replay v5/runs/paired-v2-scripted-001
.\.venv\Scripts\python.exe -m v5.runs.evaluator_v2.run replay v5/runs/paired-v2-codex-001
```

Python 3.10+；Linux/macOS 将解释器路径替换为 `.venv/bin/python`。复现目录需尚不存在；依赖范围见 [requirements.txt](requirements.txt)，记录的版本见 [environment.lock.txt](environment.lock.txt)。

以上重放使用已记录的真实模型提案，重新执行确定性检查，**不调用模型**。完整测试、统计重评分及新的模型运行入口见 [v5/README](v5/README.md)，在上述冻结 checkout 中执行；其中的解释器路径应替换为你实际的虚拟环境路径。新实验使用新输出目录，模型重新生成不保证得到相同轨迹。

## 证据边界与冻结约定

- 数学结论区分 `known / proved-in-project / conjectured / numerically-supported / refuted`；验证失败或尚未完成的提案保留为 `unresolved`。
- 文献状态独立使用 `known / novelty-uncertain`。证明一个形式命题不等于确认原创；冻结文献查询表也不是穷尽式文献搜索。
- 验证器只验收声明的形式命题与假设；自然语言解释、物理模型对应关系、真实传感器可信性不会自动获得证明。
- 有限枚举不能代替连续空间完备性；单条合成研究轨迹不能证明总体科研优势或工业适用性。
- `runs/run-001` 永久冻结，不再优化 CEP90。历史代码、实验、账本和报告保留；首页改版前的全部字节可在[冻结提交](https://github.com/WDYXG/RobustLoc-Agent/tree/c734a7011c055cedd1d24a91be3e750962ad8f4c)核验，[旧首页](https://github.com/WDYXG/RobustLoc-Agent/blob/c734a7011c055cedd1d24a91be3e750962ad8f4c/README.md)也完整保留。

项目核心研发在 Phase 5 收束。当前结论与未解问题以[最终阶段报告](v5/runs/PHASE5_REVIEW.md)为准，后续面向课程研究报告与答辩材料整理。

早期循环设计参考 [Creative-Intelligence](https://github.com/DeepMathLLM/Creative-Intelligence) 的思想，未复制其代码。各阶段数学文献与已知结果边界见对应目录的 literature audit。
