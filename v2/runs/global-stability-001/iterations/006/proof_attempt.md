## C3 / R-branch — local does not determine global (refuted)

Take anchors (-2,0),(0,0),(2,0),(1,3), w=1, q=1. Let c±=(3/10,±1) and
D be the union of closed squares of halfside 1/10000 centered at c±.
At c± every two surviving Jacobian rows are independent: the three horizontal
anchors have distinct bearings; vectors to the fourth are not parallel to them
(check their rational determinants). Exact centre Gram det/trace bounds, minus
the uniform derivative perturbation over each square, certify inf_D γ>0.
Yet the first three ranges agree at c+,c−, so at least m=2 agree and d_1=0.
Thus μ_1(D)=0<inf_D γ. This disproves C3 over compact full-dimensional domains,
including domains that are closures of their interiors. D here is disconnected;
this witness does not settle an additional connected/convex-domain conjecture.

**refuted R-unbounded:** with any fixed noncollinear triple, q=0, D=R²,
x_R=(R,0), z_R=(R,1) have unit separation. Their ith range difference is
(1-2p_iy)/(h_i(x_R)+h_i(z_R))→0. Thus μ_0(R²)=0 despite exact global injectivity.


Written deduction authored in the Codex development session; not a runtime formal proof.
