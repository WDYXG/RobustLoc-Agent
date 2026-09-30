# 首阶段研究审查与假设补充

## known：污染预算的退化边界

几何余量 α_k 的非平凡定义采用整数 0≤k≤n；讨论 α_{2q} 时要求
0≤2q≤n。若 2q≥n，任意两个输出向量的差异支持都≤2q，可分裂成两个
q-sparse 解释，因而不可能在含两个以上状态的域上做到全称唯一纠错。
THEORY.md P3 的“n-2q anchor 子集”判据在 2q<n 的域内表述；
若剩余≤2点，在全平面同样不满足唯一纠错。K3 的正 margin 自动要求
n≥2q+2；P3 的全平面判据进一步要求 n≥2q+3。不要对负的 subset cardinality
解释命题。当前全部实验使用 n=8,q=1；精确反例使用 n=4,q=1 或 q=0。

## known：噪声预算的量纲与可靠来源

ε 是 Σ w_i η_i² 的平方根上界；权重若整体乘 b，γ、ε 同时乘 √b，
位置误差界不能因任意缩放权重而人为改善。固定 w、exact anchors、可信 q
和真实 inlier noise budget 是定理前提。实验 sigma 与 epsilon 均作为输入提供，
不是 Agent 从任意污染数据中已证明恢复的量。残差可靠性是“与当前模型
一致”，不等于观测确实未被污染。

## numerically-supported：本次实验真正显示的内容

- balanced 与 overspecified_budget 各30个实例：三种选择规则几乎总选同一
  拟合点；没有证据支持 FFRG 的精度优势。FFRG 共60个适用条件证书，0个
  observed bound violation；这不是全称证明，证明来自 P2。
- near_line 与 leverage_attack 各30个实例：FFRG 全部 abstain。
  表示有限搜索结果没有取得保守正 β 证书，不证明所有恢复方法都不可能成功。
- wrong_prior 30个实例：所有规则都 abstain。当前有限候选池为空，不能把
  这个结果解释成模型可靠地检测了错误 prior。真实 prior coverage 仍是外部假设。
- 比值选择反例 seed65171/trial79 是两个具体候选中的 ordering inversion。
  q=0，真实 noise norm0.4088低于 gate1.0224；ratio-selected residual 超过
  gate且位置误差更大。它证否相应普遍有限池选择主张，不证明连续目标所有
  global minimizers 在所有数据下都会失败。

## proved-in-project：书面证明的审查范围

P1/P2 使用整个球内的 Jacobian perturbation 上界，并对固定基点的线性项
减去扰动；没有错误地把“每点 singular value 正”直接积分成输出差下界。
球凸且不含 anchors 是必要技术假设。P3 使用垂直平分线条件处理远处反射，
不把 local differential rank 替代 global injectivity。证明由本次 Codex 会话
完成逐步推导；独立 Python 进程验证数值见证，未作 proof-assistant 认证。
这些是已知工具的直接特化或本项目显式推导；不声称第一次发现。

## conjectured：尚未得到的结果

FFRG 对实际误差的改进、geometry ranking 的普遍优势、有限搜索 completeness、
未知 q、不可信 prior、anchor uncertainty、新颖性都未解决。
如继续研究，应先建立 set-valued ambiguity 与 prior-validation 的问题定义，
并审计 geometry-aware trimming / certified nonlinear robust estimation 邻近工作。
不能通过重新优化 v1 的 CEP90 来替代这些问题。
