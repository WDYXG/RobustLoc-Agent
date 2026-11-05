# 2024 BLE 原始发布数据与许可

发布者：Yuri Assayag。数据集：*Indoor Environment Dataset Based on RSSI Collected with Bluetooth Devices*，Version 1，2024-04-17。

- 数据 DOI：https://doi.org/10.17632/3v9mcsvcd2.1
- 发布页：https://data.mendeley.com/datasets/3v9mcsvcd2/1
- 论文：Assayag et al. (2024)，https://doi.org/10.1016/j.dib.2024.110692
- 全文：https://pmc.ncbi.nlm.nih.gov/articles/PMC11283029/
- 全文 XML：https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11283029/fullTextXML
- 许可：CC BY 4.0，https://creativecommons.org/licenses/by/4.0/ 。数据页与文章权限段均标示该许可。

2026-11-05 访问。11份 CSV 和 APS_Positions.txt 均保持原始字节，SHA-256 与发布方 API 中的 content_details.sha256_hash 一一核对。`source-index.json` 是下载元数据快照；`article.xml` 是公开全文的本地审查副本。`audit.py` 与所有分析结果属于本项目新增工作，未修改原始数据。保留此来源与许可说明。

下载接口：`https://data.mendeley.com/public-api/datasets/3v9mcsvcd2/files?folder_id=root&version=1`。可运行 `python -m ble_calibration.download NEW_DIRECTORY` 重新下载并校验；不得覆盖原目录。

文件与概述存在差异，不能擅自“修正”原数据：论文称150点，实际文件有160个一致的位置标签；文章称ANCHORS.csv，实际提供APS_Positions.txt；11个DEVICE标识对应同型号发射硬件，不代表11种异构手机。

2024数据论文未明确定义本次CSV中的-105编码。首次审查按缺测/左删失候选值保守排除；随后取得下述作者学位论文的无信号说明作为支持证据。不转换-105为精确距离。其他数据集的-100/-200约定不得套用到本数据集。

补充核验：作者学位论文 *Strategic Cost Reduction in Indoor Positioning Systems Using Signal Propagation Modeling Techniques*（2025年4月），第3.3.2节印刷第47页明确以-105表示无信号。已下载并视觉核对PDF第63页，来源 https://tede.ufam.edu.br/bitstream/tede/10855/5/TESE_YuriAssayag_PPGI.pdf 。参见 sentinel-source.json。PDF及截图只在本地审查使用，不随仓库再分发。上述“2024数据论文未明确编码”与这条后续补充证据需区分；采用作者说明支持-105排除规则。
