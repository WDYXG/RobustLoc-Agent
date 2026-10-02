# Phase 3B.1 核验与研究判断

本轮只实现 uncertain-contract frontier、bounded anchor uncertainty 和四类信息采购；未扩展第二 inverse problem 或接入 Codex Researcher。旧版本 1,417 个文件永久保留原字节。

数学结果：T1 shared-map 导数扰动界、T2 robust scatter 下界、T3 anchor 模型误差膨胀恢复界、T4 sufficient frontier 均标为 proved-in-project。支撑它们的 scatter、singular-value perturbation、support union、set membership 标为 known；不据此声称首创。C1 同步平移反例和 C2 不确定球内共线化反例标为 refuted。项目术语 Certified Assumption Frontier 没有数学原创性声明。

重要修正：用户最初提出的 2epsilon / robust-margin 不能直接授权未知-anchor 恢复。uniform shared-map 的每个 secant 固定同一真实 p；两个未知 p 解释可以整体平移。实际门槛使用 2(E+zeta_Q)/b_Q，最终候选还必须通过 nominal trimmed residual <= E+zeta_Q；Q 是可信上界集合，不是污染预测。正 margin 不等于 nuisance 参数可辨识。

实际执行：82项测试通过；216个方法回合、648条决策、312份精确证书、2个反例核验；诚实且满足合同的输出无错误和 bound violation。15个 radius/q 网格、1,800次 secant 数值检查无下界冲突。这些样本不是下界证明。

诚实服务结果：仅新增 range 的新增证书/成本=0.0625，随机信息=0.2388，单步=0.3571，多步=0.3571。单步与多步同样输出36/42、同样消耗84成本单位、同样平均原始假设体积缩减0.5708。不得说多步规划显著优于单步；本轮没有这项证据。预算受限场景保留拒绝结果。多类型信息优于 range-only 仅有此固定 simulation 的 numerically-supported 证据。

边界压力：不可信回执被拒绝，但假装合法来源的虚假校准可获授权并违反物理前提：随机4次、单步6次、多步6次错误输出及 bound violation，共16次。系统不能从来源字符串/嵌套一致性验证物理真实性；条件证明仍需真实独立服务。这个失败是结果，不能隐去或合并入诚实服务安全性。

实验规模与限制：诚实部分是7个固定几何/服务模板，每模板6个目标/测量实例，不是42个独立几何分布。坏观测在固定首个 reporter 上，污染幅度固定；新的 range 服务均干净。校准服务在同一中心缩球，真实诚实 offsets 很小；独立 domain 服务预告了可提供的缩域结果。服务效果是确定性公告，尚无随机可靠性、置信度分配、真实 GNSS/BLE 校准或 belief updating。采购成本不含规划CPU成本。候选 solver 不完整，几何下界可能很保守，subset 枚举组合增长。

体积指标：q可选整数个数、噪声区间长度、domain面积及原始anchor球面积的归一化乘积。新anchors改变维度而不进入该体积乘积，故仅购买range可能有有效定位增益但该体积缩减仍为0。多anchor缩球会使乘积大幅下降，不能解读为后验定位体积、熵、概率或真实位置置信度。

复现：独立新进程重跑 assumption-frontier-reproduce-001；除运行耗时 completion.json 及包含该耗时哈希的 output_hashes.json 外，701个输出文件逐字节一致（包含所有证书、私有evaluation状态、决策history、报告、指标和图片）。两个run都通过审计。verification-001.json记录环境与核验；原run及重跑都保留，不覆盖、不调参。

下一阶段仍需由研究目标决定；当前工作不构成跨问题框架泛化、自主数学发现或无条件物理安全的证据。
