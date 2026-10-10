# 单个定位闭环示例

事后按“有效契约、初始拒绝、主动采集后认证输出”选择首个案例；若无匹配则取首个案例。
它仅用于解释流程，不能替代全部配对结果。真值仅由私有评估器在报告中揭示。

案例：`e02-000`；场景：`collinear`。

| 策略 | 已新增 reporter | 决策 | 位置误差 m | 条件误差上界 m |
|---|---:|---|---:|---:|
| active | 0 | abstain | 未输出 | 未获认证 |
| active | 1 | abstain | 未输出 | 未获认证 |
| active | 2 | abstain | 未输出 | 未获认证 |
| active | 3 | recover | 0.0050 | 0.2076 |
| random | 0 | abstain | 未输出 | 未获认证 |
| random | 1 | abstain | 未输出 | 未获认证 |
| random | 2 | abstain | 未输出 | 未获认证 |
| random | 3 | recover | 0.0031 | 0.2151 |

完整输入、固定未来响应、动作评分与证书：[案例 JSON](cases/e02-000.json)。
