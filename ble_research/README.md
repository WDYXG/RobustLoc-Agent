# 真实BLE静态定位完整研究阶段

正式运行：`runs/real-001`。这是同一研究阶段的一次位置隔离实验，复用2024真实数据，不增加v6等版本分支。历史全部5,007个跟踪文件保护于PREVIOUS_FREEZE.json。

入口：[最终报告](runs/real-001/REPORT.md)、[含位置聚类区间的指标](runs/real-001/review/metrics.json)、[校准误差](runs/real-001/review/calibration-errors.json)、[独立审计](runs/real-001/review/audit.json)、[预注册](PROTOCOL.md)、[补充数据追踪](SUPPLEMENTARY_DATA.md)。

研究过程：当前Codex会话读取验证反馈，依次提出接收节点校准、dB域Huber、设备偏移、分段传播、4米空间残差修正、8米平滑修正。每次运行前保存proposal-01..06.json；各候选模型、全部验证输出和裁决保留。用户授权的改进范围覆盖旧审查阶段的只读限制，但旧目录本身未修改。模型在校准位置拟合，验证位置用于门槛判断；最终32位置仅在FINAL_LOCK生成之后评价。

本阶段没有声称新增原创定理或证明更复杂模型普遍优越。当前Codex参与研究决策；仓库的runner执行确定性实验与gate。复现既有步骤并不等于再次进行开放式自主研究。独立audit重算决策与全部误差，并对每种方法每个测试位置首例重跑。

## 使用最终方法

输入JSON只有`device`（发射设备标识）与`rssi`数组。数组顺序必须对应final-bundle.json中的receiver_order，-105表示缺测。坐标由bundle提供，单位米。不接受truth、LABEL、ROOM_ID。少于3有效接收点返回abstain，不虚构位置。输出是经验估计，没有确定性数学可靠保证。

```powershell
..\.venv\Scripts\python.exe -m ble_research.localize ble_research/runs/real-001/final-bundle.json ble_research/runs/real-001/example-observation.json output-new.json
```

现成示例结果见runs/real-001/example-output.json。

## 复现实验

沿用父目录Python环境，无新依赖。所有输出路径必须是新路径，不能覆盖既有最终记录。

```powershell
..\.venv\Scripts\python.exe -m pytest ble_research/tests -q -p no:cacheprovider
..\.venv\Scripts\python.exe -m ble_research.runner start ble_research/runs/reproduce-new
..\.venv\Scripts\python.exe -m ble_research.runner step ble_research/runs/reproduce-new --name r1-receiver --kind receiver --method cauchy
..\.venv\Scripts\python.exe -m ble_research.runner step ble_research/runs/reproduce-new --name r2-db --kind receiver --method db
..\.venv\Scripts\python.exe -m ble_research.runner step ble_research/runs/reproduce-new --name r3-device --kind device --method cauchy
..\.venv\Scripts\python.exe -m ble_research.runner step ble_research/runs/reproduce-new --name r4-dual --kind dual --method db
..\.venv\Scripts\python.exe -m ble_research.runner step ble_research/runs/reproduce-new --name r5-field4 --kind field --method db --parent r1-receiver/model.json --bandwidth 4
..\.venv\Scripts\python.exe -m ble_research.runner step ble_research/runs/reproduce-new --name r6-field8 --kind field --method db --parent r1-receiver/model.json --bandwidth 8
..\.venv\Scripts\python.exe -m ble_research.runner final ble_research/runs/reproduce-new
..\.venv\Scripts\python.exe -m ble_research.validation.review ble_research/runs/reproduce-new
```

注意：start时的manifest记录开发初始源码，开发过程中新增空间模型与输入校验；最终源码以FINAL_LOCK为准，审计核验最终锁与当前源码。初始化后只改变新候选代码，没有改变分区、数据处理规则、门槛或既有候选的数值行为。校准模型冻结在JSON中。所有原始数据、说明和CC BY4.0归属沿用ble_calibration/data/SOURCES.md。

最终结论必须同时看覆盖率与输出条件CEP90；不能仅以5.92米宣称所有病例达标。此场地的公开锚点中心也低于30米，说明30米门槛缺乏辨识力。n≥11独立位置非常少，21网关补充数据未实际取得，众包位置误差和跨环境部署仍未验证。
