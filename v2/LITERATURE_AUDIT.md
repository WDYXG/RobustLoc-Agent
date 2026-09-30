# 文献审计：已知结果与 v2 的研究边界

状态：**known**（文献事实）；审计日期 2026-09-30。下述为定向审计，不是穷尽式
综述，也不是新颖性证明。只使用作者论文/原始期刊，读过全文的结果标明定位。

| 类别 | 原始来源与定位 | 已知内容 | 不能推出什么 |
|---|---|---|---|
| Range FIM / GDOP | Moreno-Salinas, Pascoal, Aranda (2013), [Sensors](https://doi.org/10.3390/s130810674), §2 Eqs. 8–10; §3.2 Eq.24（全文对应段落） | 独立同方差 Gaussian range 模型下，FIM 为单位径向向量外积之和除以方差；GDOP 与逆几何矩阵有关；均衡方向是经典设计目标 | CRB 需 likelihood 与 regularity；不保证任意污染恢复或无偏，不保证非线性全局唯一性 |
| Frame / robust frame | Fickus & Mixon, [Numerically erasure-robust frames](https://arxiv.org/html/1202.4525), Definition 1、引言（全文） | frame bounds 是分析算子的奇异值平方；full spark 的代数可逆性和数值条件不同。NERF 要求所有保留子集的条件数受控 | “robust frame”不是任何鲁棒损失函数的别名；满秩不等于良好稳定常数 |
| Worst-case erasures | Fickus & Mixon 同上；Wang, [Random Matrices and Erasure Robust Frames](https://arxiv.org/abs/1403.5969)（摘要，后者未审全部证明） | 删除任意已知位置后的最坏子矩阵稳定性已有系统研究 | 仅下 frame bound 与同时上下 bound/条件数的 NERF 定义应区分；本项目 min λ_min 不是新数学对象 |
| Unknown sparse corruptions | Fawzi, Tabuada, Diggavi, [Secure estimation and control](https://arxiv.org/html/1205.5073), §III-A Prop.2（全文） | 不同状态的输出支持必须超过 2q；两个 q-sparse 解释的支持并集产生 2q。静态线性模型是 T=1 特例 | 已知 q 个 erasure 的条件不能直接搬到未知 q 个污染；线性动态定理也不是直接的非线性全局定理 |
| L1 correction | Fawzi et al. 同上 §III-D Prop.6；Candès & Tao, [Decoding by Linear Programming](https://arxiv.org/abs/math/0502327)（后者摘要与论文导论） | L1 需要输出方向上的 L1 mass balance/nullspace 条件，而不仅仅是 sparse identifiability | positive worst-case frame margin 不足以证明任意 L1/Huber/IRLS 成功 |
| Robust localization / IRLS | Zaeemzadeh, Joneidi, Shahrasbi, Rahnavard, [Robust Target Localization Based on Squared Range IRLS](https://arxiv.org/html/1802.05235), §II–III Eq.5/权重更新（全文对应段落） | residual-based weighting 与 squared-range robust localization 已有方法 | 残差可靠性、IRLS、几何信息单独出现都不是创新 |
| Trimming / consensus | Tzoumas, Antonante, Carlone, [Outlier-Robust Spatial Perception](https://www.cl.cam.ac.uk/~asp45/icra2019/papers/Tzoumas.pdf), §II–III（全文） | robust estimation 可写成最小删除/consensus 组合问题；算法优化和统计有效性必须区分 | 本项目枚举 subset 与 trimmed residual 是已知方法思想，不可重命名为新发现 |
| Nonlinear attacked observation | Chong, Sandberg, Hespanha, [A secure state estimation algorithm for nonlinear systems](https://arxiv.org/abs/2008.12697)（摘要） | 非线性系统中的安全估计已有工作，充分条件需明确 observer/系统假设 | 本项目不是第一个讨论 nonlinear sparse attack 的工作；尚未做动态/observer 全文细节对照 |

## 三个概念的对齐

**known**：令 J 的第 i 行为 range gradient u_i^T。给定固定正权重 W，
J^T W J 是 weighted frame operator。在可信独立 Gaussian range 误差且
W=diag(1/σ_i²) 时才是该简化模型的 FIM。残差驱动权重通常只是估计器的
局部加权几何矩阵，不能自动叫 FIM。GDOP 常用 tr((J^TJ)^(-1)) 的平方根；
它衡量全部名义数据的平均方向误差放大，不枚举 adversarial deletion。

**known**：v2 的 α_k=min_{|S|=n-k} λ_min(J_S^T W_S J_S) 是所有保留子集的
最坏 lower frame bound。“worst-case geometric information margin”仅为本项目
的操作性名称。删除位置已知的 k=q 与未知污染的 k=2q 是不同用途。

**known**：α_{2q}>0 给出线性化 sparse identifiability；更强的 L1 balance
用于具体 L1 decoder。非线性 global injectivity 还取决于 distance map 的
反射/分支结构，不能用一个点的 Jacobian 代替。

## v2 可以诚实主张什么

- **proved-in-project**：在明确 exact-anchor、正固定权重、局部区域与 bounded
  whitened inlier noise 的假设下写出推导与稳定界；不声称这些推导首次出现。
- **refuted**：用精确构造证否 q-erasure→q-corruption、local margin→global
  uniqueness、positive margin→L1 recovery 等过强猜想。
- **conjectured**：feasibility-first、residual reliability 与 geometry certificate
  联合选择的估计策略，在有限候选搜索下的实际效用；其新颖性尚未确立。
- **numerically-supported**：只指固定 v2 实验上的检查；不升级为数学证明。

后续新颖性核查应扩展到 constrained robust optimal design、geometry-aware
trimming、certified robust nonlinear estimation。当前不声称原创 frame/FIM 定理，
不声称首次联合 residual 与 geometry。
