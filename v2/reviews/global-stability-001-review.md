# Phase 2 完成后审查，2026-10-01

这份文档是历史 run/source 冻结后的补充审查，不改写其 manifest 或证据。

**proved-in-project**：独立审计重算全部 8 轮，有理数 certificate、完整 survivor
subsets、完整二叉覆盖及可行点对上界通过。Phase 1 的 source hashes 与 6 轮
历史证据通过；v1 的 94 个冻结文件 SHA256 不变。数学推导仍需人的数学审查。

**numerically-supported**：38 项测试通过，包括证书伪造、缺失覆盖叶盒、缺失
subset、预算耗尽、anchor-containing domain、精确反射和几何尺度不变性。
100 个双 feasible explanation 案例满足全局误差界，max(error/bound)=0.60601743。
这不是 decoder 的 accuracy 或完整性验证。

**proved-in-project**：q=0,1,2 的 μ 下界分别 ≥1.123723765129169、
0.821368901095061、0.369868427089418。q=3 的 exact reflection pair 给 μ=0。
κ=0.2 时 q_cert=2 已由下界和零上界夹定；实际数据污染数量未被推断。

**known / scope correction**：profile 的 raw near/far 值 q=2 为 0，但该项没有
far-budget leaves。这是固定 δ=2 的 near curvature bound 为零，而不是远区
覆盖失败；combined T5 下界仍为正。q=0,1 的 raw near/far 均为正。若未来要
加强单独 interval-cover 结果，可按这一反馈减小 δ 并增加远区分割预算，在新
run 中实施，不修改此次输出。q=3,4 的 raw 预算耗尽已显式保留；这两项的
μ=0 依据 exact witness/empty-survivor convention，与盒子预算无关。

**refuted**：C3 witness 给全域 γ≥0.03178664026214805，而 μ=0。这个 D 是
两个二维小方形的并，避免 anchors，且是 int(D) 的闭包。不能推广为对 convex
D 的反例。薄域反例表明任意 compact D 下 ambient γ 不是必要条件。无界域
反例表明全局 injectivity 不蕴含统一 lower-Lipschitz 常数。

**known / audit boundary**：2011 Jaulin 全文的 q-relaxed intersection 和
Gordian 技术报告全文的反例生成已核验；2026 Calafiore 的正式出版信息、摘要
和参考文献已核验。尝试下载作者 arXiv PDF 在普通及批准的网络执行中均只收到
3,145,728 / 16,639,082 字节；Range 请求返回 HTTP 406，未获得可解析全文。
因此全文 theorem-level 原创性比较仍未完成。这是资料获取限制，不能用“未
找到相同结论”支持原创性。T5 的平方距离和加权散布代数仍明确归于已知基础。

**conjectured / unresolved**：potential narrow gap、tight μ、connected/convex
域的更强关系、可扩展子集证书、具体 decoder 完整性、真实 prior 和 residual
预算可靠性、uncertain anchors。当前只有固定输入的稳定性研究，没有性能或
工业应用声明，也没有自动生成/形式化验证任意定理的声明。

主报告：[global-stability-001/report.md](../runs/global-stability-001/report.md)。
数学与源码：[global_stability](../global_stability/README.md)。
