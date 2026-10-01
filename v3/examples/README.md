# 三种真实运行的 JSON 决策示例

这些观测取自 frozen certified-agent-001，均没有 truth/bad labels。

```powershell
python -m v3.certified_agent.cli --input v3/examples/healthy-input.json --output decision.json
python -m v3.certified_agent.cli --input v3/examples/acquire-input.json --output decision.json
python -m v3.certified_agent.cli --input v3/examples/missing-budget-input.json --output decision.json
```

分别得到 recover / acquire-more-data / abstain。第三例即使 geometry capacity
为正，也不会把 estimated_corruption 当作真实污染上限。所有 recover bound
都条件依赖所声明的 domain/q/noise contract。acquire 示例会显示三步计划，
而不是直接发送设备消息。

运行中的快速 profile 计算 q≤2（或已声明的更大 q），字段明确为 capacity_lower。
完整 conditional profile 使用独立的完成后诊断：

```powershell
python -m v3.capacity --input v3/examples/healthy-input.json --output capacity.json
```

它比较全体 q 的下/上界，只有 capacity_lower=possible_capacity_upper 才标为
capacity_determined。该诊断不改变已冻结 run 的决策，不推断实际 q。
