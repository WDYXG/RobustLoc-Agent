# 静态定位实际结果

结论范围：本轮是米制合成实验与公开真实数据适用性审查。原题静态目标已核对；没有获得原题验证数据，不宣称 HarmonyOS 实测达标。

最终配置由验证集选择：`frozen-cauchy`，`{"loss": "cauchy", "threshold": 1.0, "uncertainty": true, "confidence": false, "multistart": false, "adaptive": true}`。最终测试前已冻结。

## n>10 的主要结果

以下覆盖所有数值输出，包括未获可靠性证书的估计；失败指误差>30米。不同生成模型分开汇总。

|模型|方法|样本数|CEP90 米|失败率|优化未成功|
|---|---|---:|---:|---:|---:|
|distance-proxy|unweighted-ls|3240|39.64|21.6%|0|
|distance-proxy|weighted-ls|3240|40.53|21.6%|0|
|distance-proxy|frozen-cauchy|3240|24.09|6.0%|0|
|distance-proxy|final|3240|24.09|6.0%|0|
|synthetic-rssi|unweighted-ls|720|361.32|85.8%|0|
|synthetic-rssi|weighted-ls|720|62.28|36.7%|0|
|synthetic-rssi|frozen-cauchy|720|86.06|42.8%|0|
|synthetic-rssi|final|720|86.06|42.8%|0|

## 最终方案按场景分组

下表每行汇总 n=11/16/32；完整 n×几何×噪声×异常比例表见 `study/strata.csv`。不能用总平均代替特定场景达标。

|场景|案例|CEP90 米|30米点估计达标|失败率|
|---|---:|---:|---|---:|
|line/high/outliers-0.0|120|22.17|是|3.3%|
|line/high/outliers-0.1|120|26.67|是|8.3%|
|line/high/outliers-0.3|120|41.10|否|26.7%|
|line/low/outliers-0.0|120|5.80|是|0.0%|
|line/low/outliers-0.1|120|5.71|是|0.0%|
|line/low/outliers-0.3|120|8.11|是|0.0%|
|line/medium/outliers-0.0|120|13.81|是|0.0%|
|line/medium/outliers-0.1|120|12.11|是|0.0%|
|line/medium/outliers-0.3|120|20.26|是|1.7%|
|rssi/line/mismatch-False|120|12.25|是|0.0%|
|rssi/line/mismatch-True|120|105.28|否|91.7%|
|rssi/sector/mismatch-False|120|26.98|是|7.5%|
|rssi/sector/mismatch-True|120|87.07|否|72.5%|
|rssi/surround/mismatch-False|120|11.93|是|0.8%|
|rssi/surround/mismatch-True|120|119.44|否|84.2%|
|sector/high/outliers-0.0|120|36.26|否|15.8%|
|sector/high/outliers-0.1|120|42.72|否|25.8%|
|sector/high/outliers-0.3|120|57.27|否|37.5%|
|sector/low/outliers-0.0|120|6.72|是|0.0%|
|sector/low/outliers-0.1|120|8.43|是|0.0%|
|sector/low/outliers-0.3|120|12.88|是|3.3%|
|sector/medium/outliers-0.0|120|21.45|是|2.5%|
|sector/medium/outliers-0.1|120|20.49|是|2.5%|
|sector/medium/outliers-0.3|120|29.91|是|9.2%|
|surround/high/outliers-0.0|120|23.36|是|5.0%|
|surround/high/outliers-0.1|120|24.44|是|2.5%|
|surround/high/outliers-0.3|120|34.30|否|15.8%|
|surround/low/outliers-0.0|120|2.25|是|0.0%|
|surround/low/outliers-0.1|120|2.27|是|0.0%|
|surround/low/outliers-0.3|120|2.41|是|0.0%|
|surround/medium/outliers-0.0|120|10.23|是|0.0%|
|surround/medium/outliers-0.1|120|9.07|是|0.8%|
|surround/medium/outliers-0.3|120|11.94|是|0.0%|

n>10 共 99 个最终单元，其中 73 个 CEP90 点估计≤30米。每单元40例，尾部估计不精确；区间保存在 strata.json/csv，不作真实环境保证。

## Agent 实际做了什么

- threshold：rejected；验证 CEP90 相对改善 -6.79%，场景退化数 5。保存了 proposal、开发/验证误差和独立 verifier 裁决。
- uncertainty：rejected；验证 CEP90 相对改善 -43.13%，场景退化数 4。保存了 proposal、开发/验证误差和独立 verifier 裁决。
- multistart：rejected；验证 CEP90 相对改善 -1.16%，场景退化数 2。保存了 proposal、开发/验证误差和独立 verifier 裁决。

这是既有规则型研究 Agent 的三轮迁移检查；运行时是数值求解器和条件决策模块。本轮没有新的 Codex 自主研究调用，不能把有限策略列表说成开放式发现。

## 可靠性与实际信息获取

主实验的 Gaussian 不确定性没有硬上界，所有最终估计均未冒充 certified 输出：证书覆盖率为0，可靠性出口拒绝输出；数值位置仍保留并全部评价。这是系统限制，不计作精度成功。

|独立受控契约组|案例|获得条件认证|误差>30米的认证输出|
|---|---:|---:|---:|
|understated-common-position-bias|36|12|12|
|valid-contract|36|12|0|
- 信息获取 step 0：n=11，acquire-more-data，q=1 几何下界=0.0，评价误差=16.346米。
- 信息获取 step 1：n=12，acquire-more-data，q=1 几何下界=0.0，评价误差=0.013米。
- 信息获取 step 2：n=13，acquire-more-data，q=1 几何下界=0.0，评价误差=0.011米。
- 信息获取 step 3：n=14，recover，q=1 几何下界=0.231584513819395，评价误差=0.011米。

该轨迹真的调用了仿真信息提供端并重新认证；未执行现实设备扫描。该有限例子不证明主动选择一般优于随机。失配组展示共同坐标偏差会使错误的外部契约产生错误安全感，几何内核不能自行鉴别。

## 真实数据与尚未解决问题

UCI 原始 BLE 数据已下载：1,420 条标签记录只有1–5个可见信标，0条满足 n>10；地图米制比例未验证。未用重复包凑人数，未伪造米制定位准确率。详见 real-data/audit.json 和 data/SOURCES.md。

仍需：原题指定的米制真实验证集、设备间 RSSI 校准、可信 reporter 误差/异常数量上界、复杂几何下稳定解算与证书计算规模控制。当前 API 接收局部米制坐标，没有完成 GNSS 地理坐标投影、移动检测或设备端部署。

## 失败场景与证据边界

近共线/单侧几何、较大正常定位误差、异常污染和 RSSI 传播系数失配均在预先固定网格中保留。观察到的关联不等于分离出的因果机制。下面列出最终误差最大的5例，完整记录包含所有成功与失败。

- seed=33507006，n=11，rssi/surround/mismatch-True：误差242.35米，优化成功标志=True。
- seed=33501002，n=8，rssi/surround/mismatch-True：误差218.77米，优化成功标志=True。
- seed=33505024，n=8，rssi/line/mismatch-True：误差208.17米，优化成功标志=True。
- seed=33501000，n=8，rssi/surround/mismatch-True：误差195.53米，优化成功标志=True。
- seed=33501004，n=8，rssi/surround/mismatch-True：误差184.40米，优化成功标志=True。

本轮新增结论均为 **numerically-supported**；沿用的已证明界见 v2/v3b 原账本。没有新增原创定理，没有把有限仿真当作真实 BLE 性能证明。
