# v2 Phase 2：全局鲁棒稳定性

**known**：定义 μ_q(D)=inf_{x≠z∈D} d_q(x,z)/||x-z||，d_q 由最小的 n−2q
个加权平方距离差求和得到。名称是项目术语；不声称 lower-Lipschitz 或
set-membership 是新概念。

先读 [定向文献审计](LITERATURE_AUDIT.md)、[书面证明与反例](THEORY.md)。
实际结果位于 [global-stability-001 报告](../runs/global-stability-001/report.md)。

**proved-in-project**：T2 全局误差界；T3 修正后的局部极限和域方向条件；
T4 compact 近远区论证；T5 bounded-domain 加权散布矩阵下界（允许 anchors
在 D 中）；有理数向外舍入、完整近远区覆盖及独立证书复算。

**refuted**：C3 local/global 相等、任意 compact D 下的 ambient 必要局部条件、
unbounded D 的 injectivity⇒uniform stability。C3 witness 的 D 不连通。

**numerically-supported**：固定种子的排序、局部极限和双解释误差界压力验证。
**conjectured**：潜在文献 gap、tight bounds、可扩展计算、更强 connected/convex
结论及 decoder 完整性。所有 novelty 字段为 not established。

仓库根目录，沿用已配置的 Python 环境（`..\.venv\Scripts\python.exe`）：

```powershell
python -m pytest tests v2/tests v2/global_stability/tests -q
python -m v2.global_stability.agent --run v2/runs/global-stability-reproduce --steps 8
python -m v2.global_stability.audit_run
python -m v2.audit_run
```

支持 `--steps 1`、同源恢复；源文件变化后开新 run。证书下界来自 exact
declared rational data；random pairs 只提供上界。运行日志 hash-linked，逐轮
proposal/proof_attempt/evidence/verification 可查。Python 是有限研究任务控制器，
不是自动定理证明器。独立 verifier 不导入证书 producer，但共享有理数原语。
Phase 1 源文件与 run-001 均保持原样；本阶段不扩 FFRG accuracy benchmark。
