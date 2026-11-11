# 静态 BLE 跨环境验证

结果见 [完整报告](runs/transfer-001/REPORT.md)、[指标](runs/transfer-001/test-summary.json)、[独立审计](runs/transfer-001/audit.json)、[固定协议](PROTOCOL.md)。原始数据按 [源文件清单](source-manifest.json) 核验。

第二场地来自 [Position-Annotated-BLE-RSSI-Dataset](https://github.com/philotuxo/Position-Annotated-BLE-RSSI-Dataset) 的静态 set_1。发布者为 Daniş、Naskali、Cemgil 和 Ersoy，数据仓库许可为 CC0-1.0。固定版本为 `77474b69dc7d73fc5b07b74d7b4b65f3235a663e`。论文说明 8 个外接适配器和 4 个板载接收端由 4 台 Raspberry Pi 承载。坐标采用发布的米制地图，目标坐标来自静态日志文件名。原始日志保存在本地 raw 目录。仓库包含所有固定窗口、文件哈希及获取脚本。 [数据论文](https://doi.org/10.1016/j.pmcj.2022.101554) · [设备配置说明](https://arxiv.org/html/2209.02270#S3.SS1)

21 网关 [原发布](https://github.com/XPengZhao/Wireless-Localization-Dataset) 的 SharePoint 数据链接本轮返回 404，[NeRF2 再发布](https://github.com/XPengZhao/NeRF2) 的 OneDrive 链接返回 403。[GSRF](https://github.com/nesl/GSRF) 指向同一 NeRF2 发布。Daniş 数据通过公开、固定版本的 tar 流下载。整仓库 zip 传输中断后，改为只读静态子目录的 tar 流，成功取得所需全部文件。另核查过 UJALoc 的公开记录，其观测方向是手机接收 8 个固定信标的广播，优先采用本项目所需的固定接收端数据。 [UJALoc 发布页](https://zenodo.org/records/19076975)

在仓库根目录使用既有 Python 环境。前两条用于重新获取和生成窗口，仓库已附本次生成的窗口。输出目录须使用新路径。输入数据保留所有预定窗口，包括其中的无信号观测。

```powershell
..\.venv\Scripts\python.exe -m ble_transfer.prepare fetch ble_transfer/raw
..\.venv\Scripts\python.exe -m ble_transfer.prepare windows ble_transfer/raw ble_transfer/observations-replay
..\.venv\Scripts\python.exe -m pytest ble_transfer/tests -q -p no:cacheprovider
..\.venv\Scripts\python.exe -m ble_transfer.study start ble_transfer/runs/reproduce-new
..\.venv\Scripts\python.exe -m ble_transfer.study step ble_transfer/runs/reproduce-new --mechanism position_sigma
..\.venv\Scripts\python.exe -m ble_transfer.study step ble_transfer/runs/reproduce-new --mechanism existing
..\.venv\Scripts\python.exe -m ble_transfer.study final ble_transfer/runs/reproduce-new
..\.venv\Scripts\python.exe -m ble_transfer.audit ble_transfer/runs/reproduce-new
```

审计检查原始文件、分区、重新拟合、候选裁决、误差和分层求解复放。定位求解器接收测绘坐标或半合成报告坐标以及 RSSI，目标真值仅进入校准器与误差计算。未收包用 JSON null 表示，原始记录中的 -105 dBm 保持为实际观测值。

第一场地每个接收设备的截距没有跨场地对应身份。本轮迁移对照包含冻结的统一参数和逐接收端模型的截距均值投影。8 点校准保持源场地斜率，估计新截距和残差尺度。优化返回失败时，本轮评价把该窗记录为无输出，避免把有限的回退坐标误记为成功定位。
