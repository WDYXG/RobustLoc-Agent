# 众包离线定位：原题闭环验收

这是 v1–v5 之后的有限验收补充，不是 v6，也不重新优化旧 benchmark。
题目归属按用户提供的 HarmonyOS 第七期说明记录；原始教师文件及数值标准
尚未独立核对。实验使用距离代理观测，不是实际 BLE/RSSI 或 HarmonyOS 部署。

入口：[预注册协议](PROTOCOL.md)、[最终报告](runs/final-001/REPORT.md)、
[逐场景数据](runs/final-001/summary.csv)、[单个闭环示例](runs/final-001/DEMO.md)、
[最终审计](runs/final-001/audit.json)。文件存在并通过审计后才视为完成。

系统输入包括 nominal anchors、ranges、weights、位置域、anchor error balls、
全局异常数上界 Q、clean noise norm E，以及有限候选 reporter 位置。
策略只看公开信息，输出 recover/abstain，或者选择下一 reporter 并取得其
预先固定的仿真响应后重新认证。真实位置、异常标记与未来响应只在私有仿真端。

两种信息策略（随机、一步几何证书质量）在相同新增数量 k=0..3 下比较。
每份已观测数据分别用于 WLS、冻结 Cauchy、冻结 v3b certified recovery。
认证可能拒绝；不给未输出的案例记零误差。全局污染身份在策略开始前固定，
新增观测也可能被污染。该流程是确定性定位决策系统，不冒充运行时 LLM agent。

从仓库根目录使用现有环境，无新增依赖：

```powershell
..\.venv\Scripts\python.exe -m pytest final_acceptance/tests -q -p no:cacheprovider
..\.venv\Scripts\python.exe -m final_acceptance.audit final_acceptance/runs/final-001 --output final_acceptance/runs/replay-new.json --replay-solvers
```

审计输出必须是新路径。新实验用新目录：

```powershell
..\.venv\Scripts\python.exe -m final_acceptance.study run --output final_acceptance/runs/reproduce-new
..\.venv\Scripts\python.exe -m final_acceptance.audit final_acceptance/runs/reproduce-new --output final_acceptance/runs/reproduce-new/audit.json --replay-solvers
..\.venv\Scripts\python.exe -m final_acceptance.report final_acceptance/runs/reproduce-new
```

`PREVIOUS_FREEZE.json` 绑定首页更新后 `0c78d9f` 时的全部 4,483 个既有文件。
任何后续修改旧文件都会使本验收的严格审计拒绝；复现应选择保留该字节集的
提交/工作树。旧 v5 审计仍应按根 README 的说明选择它自己的冻结提交。
开发种子与最终种子分开；脚本拒绝覆盖已有运行。缺少 Q 的输入不得通过预测值
获得认证。证书不负责证明物理契约真实，也不保证不完整解码器一定找到可行解。

旧 v3/v3b 功能回归共 44 项，其中两项检查旧首页哈希，必须在 `c734a70`
冻结 checkout 中运行。当前主页下的首次组合测试保留了这两项预期失败，
见 runs/acceptance-tests.xml；不要把它计为全部通过。本验收的历史完整性使用
新的 4,483 文件清单，未删除或放松任何旧冻结检查。
