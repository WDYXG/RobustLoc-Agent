## T2 — global feasible recovery (proved-in-project)

Let a common observation y have two explanations at x*, xhat∈D. There are bad sets
B*, Bhat of size at most q such that the weighted residual norms on their clean
complements are ≤ε1 and ≤ε2. The complement of their union contains at least m
indices. Choose any m of these as S. Triangle inequality on S gives
d_q(x*,xhat)≤||W_S^(1/2)(h_S(x*)-h_S(xhat))||≤ε1+ε2.
If μ_q(D)>0, its defining lower bound implies

\[
\|\hat x-x^*\|\le(\varepsilon_1+\varepsilon_2)/\mu_q(D).
\]

Using an independently certified b≤μ with b>0 gives the conservative bound
(ε1+ε2)/b. This applies to every feasible candidate in D, with no smallball prior
or finite-pool completeness assumption. It does not assert a specific decoder
finds such a candidate, nor certify truth∈D or the noise/corruption assumptions.


Written deduction authored in the Codex development session; not a runtime formal proof.
