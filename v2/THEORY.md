# 理论账本：worst-case geometric information margin

所有符号遵循 PROBLEM_SPEC.md。证据标签是性质与来源，不代表新颖性。
以下为逐步书面证明，尚无 proof assistant 形式化认证。

## K1 / known：frame 与 FIM 的对应

J_i(x)=u_i(x)^T，u_i=(x-p_i)/||x-p_i||。A=diag(√w)J。
G_S=A_S^T A_S=Σ_{i∈S} w_i u_i u_i^T 是 weighted frame operator。
在独立 Gaussian、固定已知 covariance 的 range 模型下等于相应 FIM；
一般 residual-adaptive W 不满足这个解释。来源见 LITERATURE_AUDIT.md S1/S2。

## K2 / known；project_derivation=true：二维解析表达

设 u_i=(cos θ_i,sin θ_i)，t_S=Σ_S w_i，
c_S=Σ_S w_i cos(2θ_i)，s_S=Σ_S w_i sin(2θ_i)。

G_S = 1/2 [[t_S+c_S,s_S],[s_S,t_S-c_S]],

λ_min(G_S) = (t_S-√(c_S²+s_S²))/2，
λ_max(G_S) = (t_S+√(c_S²+s_S²))/2，

**α_k(x)=1/2 min_{|S|=n-k}(t_S-|Σ_S w_i exp(2iθ_i)|)。**

证明：cos²θ=(1+cos2θ)/2，sin²θ=(1-cos2θ)/2，
sinθ cosθ=sin2θ/2；再解 2×2 characteristic polynomial 即得。
这只是已知二维谱代数的显式重写，不是新定理。

同样 det G_S=Σ_{i<j∈S} w_i w_j sin²(θ_i-θ_j)（Cauchy–Binet 展开）。
记该和为 D_S。数值实现采用 2D_S/(t_S+√(t_S²-4D_S))，避免近退化时
直接相减；t_S=0 定义为0。数值舍入保护不得当作严格 positivity 证明。

**known**：由 Rayleigh quotient 与有限集合 min 交换，
α_k=min_{||v||=1} Σ 最小的(n-k)个 {w_i(u_i^Tv)²}。
证明：对于固定 v，删去最大的 k 项；之后再对 v 最小化。
α_{k+1}≤α_k；旋转/平移同时作用于 x,p 不改变它；单位正权重固定时
α_k>0 当且仅当每个保留子集含至少两个不平行的 unoriented bearings。
这里 opposite bearings 仍是同一直线；它们的外积相同。

## K3 / known；project_derivation=true：2q 条件，非 q 条件

线性化观测 z=Aδ+a+η，whitened a 仍至多 q-sparse。假定 η=0。

下列等价：

1. 对所有 δ 和所有 ≤q 支持污染，δ 可唯一恢复；
2. 每个非零 v 满足 ||Av||_0>2q；
3. 删除任意 ≤2q 行后 A 仍满列秩；
4. α_{2q}>0。

证明 1→2：若 Av 只在≤2q 分量非零，分成 K1,K2，|Kj|≤q。
令 a0=(Av)_{K1}，a1=-(Av)_{K2}。则 A0+a0=Av+a1，两个不同 δ
解释同一观测。2→1：若 Aδ+a=Aδ'+a'，Av=a'-a，其支持≤2q，
故 δ=δ'。2↔3 来自行删除后的 nullspace；3↔4 来自有限 PSD 矩阵
最小谱值。权重正则不改变 support/rank。二维至少需要 n≥2q+2。
这正是 Fawzi et al. Prop.2 的静态特例和经典 sparse error-correction 事实。

## K4 / known；project_derivation=true：线性化稳定界

若 α_{2q}>0，真实与候选解释各有≤q 支持污染，且各自 whitened residual
norm≤ε，则

**||δ_hat-δ*||≤2ε/√α_{2q}。**

证明：删除两支持的并集 E，|E|≤2q；在 S=E^c，
A_S(δ_hat-δ*)=η*_S-η_hat_S，右侧 norm≤2ε。用最小 singular value
γ_{2q}。若 |S|>n-2q，取任意 n-2q 子集仍可应用同一界。
若两 residual 上界为 ε1,ε2，则分子改为 ε1+ε2。

**known**：理想 q-trimmed least squares 的全局最优解可写为同时对
δ 和删除≤q项求最小 residual norm，因此其 residual≤真实解释的 ε。
这使上界适用于该理想解；不证明任意局部 nonlinear solver 的返回点有此性质。
该界是一般线性代数推论，不能冒充项目原创。

## P1 / proved-in-project：显式局部非线性区域与稳定界

选定中心 c 与闭球 B(c,R)，R<min_i||c-p_i||。固定 w_i>0。
令 r_i=||c-p_i||，
L_R = √(Σ_i w_i/(r_i-R)²)，γ=√α_{2q}(c)。
假定 **γ-L_R R>0**。

对任意 x,z∈B(c,R)、任何 |S|≥n-2q，

**||diag(√w_S)(h_S(x)-h_S(z))|| ≥ (γ-L_R R)||x-z||。**

证明：range Hessian H_i=(I-u_i u_i^T)/||x-p_i||，operator norm
≤1/(r_i-R) 于球内成立。球凸且不含任何 anchor，故
||A_S(t)-A_S(c)||_op≤||A(t)-A(c)||_F≤L_R||t-c||≤L_R R。
线段积分 h(x)-h(z)=J(c)(x-z)+∫[J(z+t(x-z))-J(c)](x-z)dt。
注意用三角不等式先保留 A_S(c)(x-z)，再减整个扰动，不能对积分中
每一点的 norm 求下界后直接交换 norm/integral。因而得上述式。

如真实与候选位置均在该球中、各至多 q 个任意污染、两个 residual norm≤ε，
删除支持并集并应用上式，得到

**||x_hat-x*||≤2ε/(γ-L_R R)。**

零噪声下得到该球内 q-corruption uniqueness。这里 c,R 是可信的先验区域，
不是从污染观测自动证明真值已在其中；不能把 simulator truth 偷作 c。

**proved-in-project**：若 γ>0，总存在这样的正 R。例如令 r_min=min r_i，
W=Σ w_i，取 R=γ r_min/(4√W)。γ≤√W，故 R≤r_min/4，
L_R≤2√W/r_min，L_R R≤γ/2。于是区域内逆 Lipschitz 常数≤2/γ。
这是标准 Taylor/perturbation 论证的本项目显式量化；新颖性未声称。

**proved-in-project**：固定某点 c，如果要求每个保留子集都存在一个统一
正的局部 lower-Lipschitz 常数，那么 α_{2q}(c)>0 是必要的：
沿 z=c+tv，t→0，若某 A_S(c)v=0，输出/位移比趋于0。
仅“这个目标位置在 noiseless data 下是唯一解”不要求这样的 Lipschitz 条件。

## P2 / proved-in-project：候选中心的条件证书

对任意 x_hat∈B(c,R)，令

β(x_hat)=γ_{2q}(x_hat)-L_R(R+||x_hat-c||)。

在真值也属于 B(c,R) 的前提下，使用 A(x_hat) 作积分基点，同样证明
输出差≥β(x_hat)||x_hat-x*||。所以当 β>0，候选解释删除≤q项后
residual≤ε+τ（τ≥0 是显式数值容差），真实 residual≤ε 时，

**||x_hat-x*||≤(2ε+τ)/β(x_hat)。**

证书依赖 q、可信权重、noise budget、prior coverage；不依赖污染幅度。
β≤0 应报告缺乏这个证书，不可凭图形漂亮宣称稳定。β 是保守下界，
β≤0 不证明方法不能恢复。该结论不保证候选池找到 feasible point。

## P3 / proved-in-project：非线性全局 exact-anchor 特化

**known foundation**：任意 map h 在域 D 上能唯一纠正 q 个任意污染 iff
任意 x≠z∈D 满足 ||h(x)-h(z)||_0>2q；证明同 K3 的支持分裂，不用线性。

在全平面域（可删掉有限个 anchors）中，对 exact 2D ranges：

**每个 n-2q anchor 子集都含至少三个非共线位置**
当且仅当该 map 满足上述全局纠错条件。

证明：两个不同 x,z 到同一个 p 距离相等 iff p 在 xz 的垂直平分线上。
若距离向量至多2q个分量不同，则至少 n-2q anchors 位于该线。
反之，若某保留子集在一条线上，选其两侧一对反射点，避开有限 anchors，
这些观测全部相等，差异支持≤2q，因此两个 q-sparse 解释可相同。
若子集≤2点，总可找到包含它们的线；因此 n≥2q+3 是全平面必要数目。
同位置重复 anchors 按观测数计数，不能算三个非共线点。

这是已知 error-correction criterion 在 range geometry 的直接特化及初等
垂直平分线论证。标签表示本项目写出并检查了证明，不宣称原创文献贡献。

## R1 / refuted：α_q>0 就可纠正 q 个未知污染

n=4,q=1，A 的行为 (1,0),(1,0),(0,1),(0,1)。α_1=1，α_2=0。
v=(1,0) 使 Av=(1,1,0,0)。观测 y=(1,0,0,0)，既可由 δ=0、
a=(1,0,0,0) 产生，也可由 δ=v、a=(0,-1,0,0) 产生。
这是代数精确反例，不只是 Monte Carlo 失败。

## R2 / refuted：α_{2q}(x*)>0 就保证非线性全局唯一性

q=1，p=(-2,0),(0,0),(2,0),(1,3)，x+=(0.3,1)，x-=(0.3,-1)。
前3个 range 相同，只有第4个不同。任意两个 bearings 在 x+ 均不平行：
前三个非共线方向，第4向量(-0.7,-2)与前三者逐对 determinant 非零。
故 α_2(x+)>0，但用≤1污染就可使 x+ 解释 h(x-)；x- 以零污染也能解释。
第4个 anchor 去掉后只剩共线 subset，违反 P3。局部唯一性和全局分支
识别不矛盾，反射另一分支在局部球外。

## R3 / refuted：α_{2q}>0 足以保证 L1 decoder

q=1，单位行 A=(1,0)、(.01,1)/√1.0001、(-.01,1)/√1.0001、
(.02,1)/√1.0004。任意两行不平行，故 α_2>0。
δ*=0，y=(1,0,0,0)，仅第1项被污染。在0处 L1 residual=1；
在 v=(1,0) 处 residual sum=2*.01/√1.0001+.02/√1.0004<.04<1。
因此真值不是 L1 minimizer。小而正的 lower frame bound 并未满足 L1 balance。
已知依据是 Fawzi et al. Prop.6，不把这个机制称为新发现。

## R4 / refuted：α=0 必然意味着该点 exact noiseless 解不唯一

q=0，p=(-1,0),(1,0)，x*=0。两个 range=1 的圆相切，唯一解为0，
但所有 bearings 共线，α_0=0。沿 x=(0,t)，range 变化为
√(1+t²)-1=O(t²)，不存在这个点的 Lipschitz 稳定逆。
“exact pointwise uniqueness”与“regular local stable recoverability”不能混写。

## C1 / conjectured：联合 residual 与 geometry 的实际效用

从有限 solver candidate pool 中，先以 q-trimmed residual norm≤ε+τ 筛选
feasible candidates，再在有可信 prior 的情形最大化 β(x)。P2 对任何通过
检查的候选都成立；但搜索 completeness、相对于 residual-only 方法的误差
优势、在不可信 prior/unknown q 下的恢复能力均未证明。
P2 是 conditional guarantee，不是 C1 的性能或创新证明。

## C2 / conjectured（待检验）：无门控的 T_q/α_{2q} 有普遍优势

此目标把 residual reliability 与 geometry 信息直接相除。它可能偏好
residual 更差而 margin 更大的点；甚至噪声为0时仍不能辨识反射分支。
Agent 应搜索一个实际有限候选池 witness，随后决定 refuted / unresolved。
