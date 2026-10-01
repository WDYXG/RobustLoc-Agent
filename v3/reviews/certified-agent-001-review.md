# Phase 3A 完成后研究审查

不修改 frozen 源文件、manifest 或原始输出；以下是对既有证据的审查。

**numerically-supported**：132 个配对 episode ×6 方法，792 个结果、1179 个
实际动作，66 个复用证书对象。独立消费者复核 216 个 certified outputs 的
全域几何下界、精确 residual feasibility、预算和轨迹；没有 in-contract bound
violation。56 项测试通过，v1/v2 共 248 个已跟踪文件逐字节不变。

**numerically-supported**：84 个 in-contract episodes，always-Cauchy 48 次错误；
passive-certified 24 次输出、0 错误；active-certified 72 次输出、0 错误。阈值
是预先固定的 0.4 个坐标单位，不是 v1 的 10 m 指标。不能将单位混用或把
这批刻意包含 reflection/near-line 的仿真比例解释成真实部署失败率。

**numerically-supported**：active 与 random 都恢复 72 个场景，平均新增观测
分别 1.286 与 1.464，差约 12.2%。这仅为配对仿真的观察，没有显著性或
总体最优结论。greedy 48 次输出；多步前瞻解决部分 immediate-gain 平台。
48 个 active cases 满足 post-lower > pre-upper，严格证明这些实例的 μ 提升。
其中 collinear-q0 单次采集即可提升；q=1 共线案例可能需要多次新增。

**refuted**：一个新 anchor 普遍足够，已被 exact reflection 反例否定。
高 surrogate probability 普遍提供证书，也有独立测试假阳性反例。其 label=0
依据的是可行点对上界 <tau，不是“lower=0”。模型 113 个可分测试布局中
1 个假阳性、7 个布局保留 unknown。最终 learned-gate 在 episode 中没有
错误，但 coverage 与 passive 相同；这不能支持以预测取代证书。

具体假阳性为 model_test layout 310020-91：p=0.57277443，几何点对上界
U=0.16543418<tau=0.2。这里反驳的是预先固定的 0.5 概率门，不声称已找到
p≥0.95 的误判，也不以该单例估计分布外错误概率。

**known / limitation**：invalid-contract 场景中的 certified policy 全部 abstain；
这是这批输入的实际行为，不证明 Agent 能检测所有 assumption violations。
尤其 missing q_budget 的拒绝只是授权信息缺失。Noise 和真位置的有效性只有
private evaluator 在仿真中可验证；实际系统仍需要外部可靠契约。

**known / implementation scope**：q hint 随机生成（或 wrong-hint 专门给 0），
没有从 private actual_q 复制到 policy；声明预算是实验条件。对新的污染观测
使用同一 reactive adversary rule，未来 range 不被 planner 读取。固定 w=1，
没有通过改变权重单位使 μ 任意膨胀。Decoder 不完备，失败日志和拒绝原因保留。
所有选择都是有限规则与候选集合上的 3 步前瞻，没有开放式科研自主性声明。

**proved-in-project**：完整 conditional capacity 可用 ../capacity.py 单独计算。
它检查全部整数 q 的上下界，属于完成后诊断，保留 input/source hashes。
历史 episode 的快速 profile 只到 q≤2，不能据此声称完整最大容量。

**conjectured / unresolved**：真实 BLE/众包环境、成本函数与观测相关性、移动
reporter 布局、uncertain anchors、未知污染上限的可靠来源、其他 inverse problems
上的通用性和原创性。MathResearch-Agent 是路线名称，RobustLoc 是首个 case study。

报告：[certified-agent-001](../runs/certified-agent-001/report.md)。
