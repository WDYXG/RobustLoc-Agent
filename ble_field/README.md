# RobustLoc 真实众包 BLE 静态实测包

**当前证据状态：实测工具已构建，实地定位尚待采集。** [研究报告](REPORT.md) · [PDF 报告](artifacts/field-report.pdf) · [实地协议及原题核对](PROTOCOL.md) · [安卓 APK](artifacts/RobustLoc-Field.apk) · [软件验证记录](artifacts/verification.json)

## 上手机

APK 适用 Android 8.0 及以上且支持 BLE 的设备。它使用本地测试签名。用同一个 APK 安装到报告手机和单独的目标手机。安装来源与 SHA-256 见验证记录。用户授权附近设备及精确定位后再次点击采集按钮。采集、广播和本机保存均在前台运行。导出使用 Android 的文件选择界面，应用没有互联网权限。 [Android 蓝牙权限](https://developer.android.com/develop/connectivity/bluetooth/bt-permissions)

1. 各报告手机填入现场实体编号，点击“复制手机登记信息”。把 JSON 对象登记到 `roster.json` 的 `phones`。现场记录每个编号对应哪台实体手机，目标不进入该名单。
2. 数据管理员登记计划、测绘点和分区，生成本次 JSON 采集票。将同一票发给参与本次试验的手机和目标。目标手机点“启动目标广播”，报告手机点“准备采集”。保持屏幕点亮、应用在前台、设备停在各自测绘标记。开始前用现场公共时钟核对设备间时间。
3. 到时确认手机已保存。采集批次完成后，各手机导出整个活动记录。成功、空包和中断状态均可以导出。导出文件包含经纬度，交给指定数据管理员存放在私有目录。

工具以 128 位 BLE 服务 UUID 识别受控目标，使用收到广播的单调时钟时间戳和同一手机的定位时间戳。现场首测须确认扫描、广播、定位和导出都正常。扫描其他类型的目标广播时，可用下述统一格式导入实际采集的记录。 [Android 包时间戳](https://developer.android.com/reference/android/bluetooth/le/ScanResult#getTimestampNanos()) · [定位精度字段](https://developer.android.com/reference/android/location/Location#getAccuracy())

## 数据文件

将 [plan 模板](templates/plan.json)、[roster 模板](templates/roster.json) 复制到 `ble_field/private/site-a/`。将 [测绘模板](templates/survey.json) 复制为 `survey/calibration.json`、`survey/development.json`、`survey/validation.json`、`survey/test.json`。模板中的空字段由现场测绘、排程和实物登记填入。试验阶段与字段含义如下。

| 文件或数组 | 内容 |
|---|---|
| `plan.json` | 活动编号、`evidence` 为 `field`、固定目标 UUID、WGS84 原点、全部预定试验 |
| `plan.trials[]` | `trial_id`、`location_id`、`site_id`、`layout_id`（可选）、`split`、`start_utc_ms`、`duration_ms`、`reporter_ids` |
| `roster.phones[]` | App 复制出来的对象，含 `reporter_id`、`installation_id`、`manufacturer`、`model`、`os_release`、`sdk_int` |
| `survey/<split>.json` 的 `targets[]` | 每个目标物理位置一条，含 `location_id`、`lat`、`lon`、`method`、`uncertainty_m` |
| `survey/<split>.json` 的 `receivers[]` | 每条已完成的手机摆位测绘，含 `trial_id`、`reporter_id`、`lat`、`lon`、`method`、`uncertainty_m` |
| `robustloc-capture-bundle-v1` | App 导出的 `{schema,reports}`。导入也接受单个 `robustloc-capture-v1` 对象 |
| 单条采集对象 | `schema,ticket,device,armed_utc_ms,scan_started_utc_ms,ended_utc_ms,clock_drift_ms,status,reason,packets,fixes` |
| `packets[]` | `t_utc_ms,rssi_dbm`，只保留所指定目标的包。空列表代表本手机在该窗无目标包 |
| `fixes[]` | `t_utc_ms,lat,lon,accuracy_m,provider,mock`。精度以米计，时间为 UTC Unix 毫秒 |

手机和试验编号使用 1–48 位英数字、下划线或短横线。试验窗为 5–120 秒。每个 `location_id` 表示一个物理标记，重复试验沿用该 ID。同一标记分配到同一分区，跨分区近重合坐标也会触发校验。可为新的受控目标生成 UUID，用 PowerShell 的 `[guid]::NewGuid().ToString()`。时间可从现场 UTC 计划用 `[DateTimeOffset]::Parse("2030-01-01T01:00:00Z").ToUnixTimeMilliseconds()` 转换，示例日期换成实际时间。

原始手机包和测绘文件留在数据管理员目录。相同记录可以重复导入，冲突记录会被拒绝。导入器按计划的分区和实体编号写入一份记录。同一手机的包数不会增加人数。无导出记录的预定窗继续参加测试。缺少手机摆位测绘的上报仍可用于定位，相应校准或坐标对照标记缺失。填表时核对坐标基准，测绘和手机上报均按 WGS84 入库。

## 从采集到评估

在仓库根目录运行，沿用项目的 Python、NumPy 和 SciPy 环境。示例试验 ID `T001` 换成活动计划里的编号。下列路径中的 `private` 已加入忽略规则。

```powershell
$python = "..\.venv\Scripts\python.exe"
$site = "ble_field/private/site-a"
$run = "ble_field/private/site-a-run-001"
& $python -m ble_field.campaign $site design
& $python -m ble_field.campaign $site ticket T001
& $python -m ble_field.campaign $site ingest path-to-export.json
& $python -m ble_field.campaign $site check development
& $python -m ble_field.study prepare $site $run
& $python -m ble_field.study step $site $run
& $python -m ble_field.study freeze $site $run
& $python -m ble_field.study final $site $run
& $python -m ble_field.audit $site $run
```

`design` 供独立数据管理员在布点后核对全部测绘和空间分区。研究阶段先导入校准、开发和验证文件。实际需要验证算法变更时运行一次 `step`，检查候选、裁决与失效案例。可在保留冻结算法的情况下直接 `freeze`。最终锁生成后才交付、导入测试采集与测绘数据。开发阶段的代码、数据或模型改变需使用新运行目录。

输出 `test-summary.json` 包含预定窗、有效手机数、≥10 和 ≥11 的输出条件 CEP90、覆盖率、总体成功率、实测手机位置误差及型号残差。测绘手机坐标对照仅用于离线诊断。研究日志保存在 `round-*`，独立审计会重新拟合、复算裁决与全部预测。实测的设备级独立性、目标静止、测绘质量和跨设备时钟同步由现场记录支持。

## 软件复现

```powershell
..\.venv\Scripts\python.exe -m ble_field.fixture ble_field/fixture-output/local-check --verify
..\.venv\Scripts\python.exe -m pytest ble_field/tests -q -p no:cacheprovider
& .\ble_field\android\build.ps1 -Sdk "C:/path/to/Android/Sdk" -Output "ble_field/private/rebuilt.apk"
```

Android 重构建需要 JDK 17、Android SDK API 35 和 Build Tools 35.0.0。构建脚本生成本地测试签名，私钥留在本地构建目录。重新生成签名时 APK 文件哈希会改变。合成夹具只检查软件与分母口径，完整流程标注 `synthetic_fixture`。
