# Theory-driven v2：问题、定义与证据协议

研究对象是 exact anchors p_i∈R²、静态未知位置 x、range map
h_i(x)=||x-p_i||，x 不与 anchor 重合。观测 y=h(x*)+a+η，||a||_0≤q。
不假设污染幅度/方向分布；q 是已知上界。anchor error 与 RSSI calibration
不在当前定理内，不借用 v1 的方差近似作为严格 likelihood。

固定可信 w_i>0，A(x)=diag(√w_i)J(x)。定义

α_k(x)=min_{|S|=n-k} λ_min(A_S(x)^T A_S(x)),
γ_k(x)=√α_k(x)。k≥n-1 时二维 α_k=0；k=2q 用于未知污染。
权重改变 units/scale，不能通过任意放大 w 宣称稳定性提高；必须同时标明
whitened noise ε 和权重规则。当前实验主用 w_i=1/sigma_i²。

目标：二维解析表达；线性化辨识与误差界；带曲率/anchor separation 的局部
非线性界；局部与全局反例；联合 residual feasibility 与 geometry 的候选估计器。

每项主张有 claim ID 与 primary status：known / proved-in-project /
conjectured / numerically-supported / refuted。已知结论即使本项目重证仍标 known，
另加 project_derivation=true。proved-in-project 不表示 novelty 或形式化证明。
数值测试不能证明全称命题，失败的猜想保留原文和 witness。

新实验关注 margin、noise-bound ratio、分支歧义、abstention、候选池覆盖与
geometry constraint failure；不选择最低 CEP90，不读取 v1 held-out cases。
默认运行固定 6 个有依赖的研究回合；预算结束保留 unresolved conjectures。
