# 2024 公开 BLE 数据：先审查，再校准

**本轮只完成下载与适用性审查，未拟合参数、未运行定位器、未生成 CEP90。** 不修改旧算法与既有运行。2022补充数据暂不下载处理。

结论：可以用于真实、米制、固定基础设施下的 RSSI 校准和静态定位部分验证；**不足以直接代表 HarmonyOS 原题的 n>10 众包验收**。关键原因是有效接收锚点稀疏，而非名义部署数不足。

入口：[适用性报告](DATA_REVIEW.md)、[机器可读审查](runs/data-audit-002/audit.json)、[接入前协议](CALIBRATION_HANDOFF.md)、[来源与许可](data/SOURCES.md)。

从仓库根目录运行，无新依赖：

```powershell
..\.venv\Scripts\python.exe -m pytest ble_calibration/tests -q -p no:cacheprovider
..\.venv\Scripts\python.exe -m ble_calibration.audit ble_calibration/data ble_calibration/runs/audit-new
```

输出目录必须不存在。审查器只读数据，不导入拟合器或定位器，验证发布方全部12个数据文件的哈希、设备/位置一致性、有效接收数和重复记录。`PREVIOUS_FREEZE.json` 绑定提交4d5a73f的4,972个既有文件。

重新下载到新目录：

```powershell
..\.venv\Scripts\python.exe -m ble_calibration.download ble_calibration/data-redownload
```

-105排除规则已由作者相关系统的学位论文提供无信号说明支持，见 data/sentinel-source.json。不得将其当成精确测距，也不能补齐成15个真实观测。首次假设与后续来源确认的过程见 runs/data-audit-001/SOURCE_UPDATE.md。
