# 原题静态定位：求解与验证

本目录回到 HarmonyOS 第七期静态目标：**n>10 时 CEP90≤30米**。复用既有定位器、研究策略和精确证书，不另开版本研究。所有旧跟踪文件保持冻结。

**先看[一页结果与缺口](RESULTS.md)**：n>10距离代理CEP90为24.09米；合成RSSI混合场景为86.06米，未整体达标。真实BLE指标仍未验证，三项Agent候选均被拒绝。

先读：[现状审查](AUDIT.md)、[预注册协议](PROTOCOL.md)、[实际结果](runs/static-003/REPORT.md)、[完整分组结果](runs/static-003/study/strata.csv)、[审计](runs/static-003/audit.json)。首次运行的保存缺陷及修复见 [EVALUATOR_ISSUE](runs/static-001/EVALUATOR_ISSUE.md)，未删除失败记录。

## 当前流程

`观测输入 → 距离/RSSI适配 → 冻结鲁棒定位器 → 数值估计`

如果提供了有依据的硬契约，再执行：

`几何预检 → 残差检查 / 既有有界恢复后备 → 独立 verifier → recover`

不能认证时，可靠位置出口为 `abstain`；信息来源可用时为 `acquire-more-data`。原数值估计单独保留，主实验对全部数值估计计算 CEP90，不能用拒绝输出来美化指标。有请求不代表已获得测量；实际闭环示例在 `runs/static-003/reliability/acquisition.json`，明确保存执行回执。

研究 Agent 与运行时模块是两件事：本轮复用规则型 proposer，在新开发/验证集上检查三个迁移机制，由旧 verifier 子进程决定接受或拒绝；没有新的 v5 Codex 开放式研究调用。不要把本轮说成通用自主发现。

## 实际使用

以米为单位提供局部平面位置。输入 JSON：

```json
{
  "units": "metres",
  "reports": [
    {"id":"a","position":[0,0],"position_sigma":2,"distance":20,"distance_sigma":4},
    {"id":"b","position":[40,0],"position_sigma":2,"distance":25,"distance_sigma":4},
    {"id":"c","position":[0,40],"position_sigma":3,"distance":30,"distance_sigma":5}
  ],
  "information_available": false
}
```

这是格式示例，不是 n>10 性能证据。至少三个不同 reporter；重复扫描须先按设备身份聚合。输入不得包含 truth、异常身份或评价字段。RSSI 可替换 distance/distance_sigma 为 `rssi_dbm` 和 `calibration`（`a_at_1m_dbm`、`path_loss_exponent`、`sigma_db`），参数须来自外部校准；-200/null 是缺测。不支持直接输入经纬度。

在仓库根目录运行，输出路径必须不存在：

```powershell
..\.venv\Scripts\python.exe -m static_localization.service input.json output-new.json --method static_localization/runs/static-003/study/selected-method.json
```

硬契约格式与可运行实例见 `reliability/case-*.json` 中的 observation；`epsilon_max` 是正常距离噪声向量二范数上界，`radii` 是 reporter 误差球半径，`q_max` 是全局异常数量上界，`domain` 必须包含真实目标，`error_tolerance` 是位置误差要求。标准差不能替代这些界。

## 复现（新输出目录）

依赖沿用仓库 requirements/environment lock；本轮实际 Python/NumPy/SciPy 版本和源码哈希见 manifest。

```powershell
..\.venv\Scripts\python.exe -m pytest static_localization/tests -q -p no:cacheprovider
..\.venv\Scripts\python.exe -m static_localization.study static_localization/runs/reproduce-new/study --workers 4
..\.venv\Scripts\python.exe -m static_localization.reliability static_localization/runs/reproduce-new/reliability --method static_localization/runs/reproduce-new/study/selected-method.json
..\.venv\Scripts\python.exe -m static_localization.real_data static_localization/runs/reproduce-new/real-data
..\.venv\Scripts\python.exe -m static_localization.review static_localization/runs/reproduce-new/study --audit static_localization/runs/reproduce-new/audit.json --reliability static_localization/runs/reproduce-new/reliability --real static_localization/runs/reproduce-new/real-data --report static_localization/runs/reproduce-new/REPORT.md
```

主实验保存每一例各方法输出，并分别存放公共观测与私有真值。审计重生成全部案例、重算全部最终误差与汇总、重放三轮 verifier，并对每单元首例的四种方法重跑（528次）；不是全量求解器重跑。可靠性实验保存逐例精确证书，可由原消费者逐条复核。

## 边界

本轮数据主实验是合成距离代理及明确标注的合成RSSI，不能冒充真实 BLE。公开 UCI BLE 已取得，但可见信标最多5个、米制尺度未验证，仅完成数据适用性审查。真实设备达标、移动检测、设备端扫描集成均未完成。本目录报告数值支持与失败，不提出新定理或原创性主张。

纠正运行说明：static-001 因保存类型错误中止；static-002 的主数值实验完成，但主动轨迹说明字段有可变引用问题，见 [REPLAY_ISSUE](runs/static-002/REPLAY_ISSUE.md)。static-003 仅修正记录快照，使用相同配置、种子与选定方法重复核验，不能把重复样本计为新增独立证据。

额外复放全部有界恢复案例与主动轨迹：

```powershell
..\.venv\Scripts\python.exe -m static_localization.validation.replay_reliability static_localization/runs/reproduce-new/reliability static_localization/runs/reproduce-new/study/selected-method.json static_localization/runs/reproduce-new/reliability-audit.json
```
