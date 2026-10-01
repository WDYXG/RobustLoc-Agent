## T1 — sorted separation (known; derivation checked in project)

Let a_(1)≤…≤a_(n). For any subset of size m, its ordered selected values are at
least the first m order statistics coordinatewise. Choosing their indices attains
the bound, including ties. Thus d_q²=Σ_{j=1}^m a_(j). For a fixed pair (x,z),
evaluate all ranges in O(n), sort in O(n log n). This does **not** turn the local
minimization over directions, the global four-dimensional infimum, or all subset
scatter certificates into O(n log n). Linear-time selection is also possible.


Written deduction authored in the Codex development session; not a runtime formal proof.
