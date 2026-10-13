# refinement.md — scikit-learn__scikit-learn-10844

The operation-by-operation correspondence between `model.py`'s implementation
(the `pair_similarity_index` impl region) and `patch.diff` (the gold patch).
Each step is tagged **R** (type refinement), **A** (axiomatized callee — split
into **A-consumed**, where the proof uses the axiom's `Ensures`, and
**A-reference**, where a deep model is validated == the real callee by G-AX),
or **I** (identical concrete operation). The claim: *any implementation that
verifies against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## The change — `fowlkes_mallows_score` (`sklearn/metrics/cluster/supervised.py:855-859`)

Gold hunk:
```
- c = contingency_matrix(labels_true, labels_pred, sparse=True)
+ c = contingency_matrix(labels_true, labels_pred,
+                        sparse=True).astype(np.int64)
  tk = np.dot(c.data, c.data) - n_samples
  pk = np.sum(np.asarray(c.sum(axis=0)).ravel() ** 2) - n_samples
  qk = np.sum(np.asarray(c.sum(axis=1)).ravel() ** 2) - n_samples
- return tk / np.sqrt(pk * qk) if tk != 0. else 0.
+ return np.sqrt(tk / pk) * np.sqrt(tk / qk) if tk != 0. else 0.
```

The fix has two parts, which TOGETHER make the result finite on the
large-count regime:
- **widen** the contingency matrix to `np.int64` (`.astype(np.int64)`), so the
  marginals `tk`/`pk`/`qk` are each representable in a 64-bit integer domain;
- **reorder** the evaluation from `tk / sqrt(pk * qk)` to
  `sqrt(tk/pk) * sqrt(tk/qk)`, so the cross product `pk * qk` — which can exceed
  even the 64-bit domain (≈ 1.7e19 > 9.2e18 on the failing test) — is never
  formed; the two unit-interval ratios `tk/pk`, `tk/qk` are formed first.

Both parts are about staying within the finite numeric domain `m`: the widening
sets `m` (each marginal ≤ m), the reorder ensures no formed quantity exceeds m.

| # | model.py impl op (`pair_similarity_index`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | params `tk, pk, qk: float` | the numpy integer scalars `tk`/`pk`/`qk` (`:856-858`) | R | integer count ↔ interpreted real; the modeled behaviour (finiteness + floating value) is real-valued (mapping.md §2). |
| 2 | param `m: float`, `Requires(pk <= m, qk <= m)` (and `m >= 1`) | the `.astype(np.int64)` widening (`:855`): each marginal lives in the int64 domain, so each marginal ≤ `INT64_MAX = m` | R | the widening's observable effect is exactly "each marginal is representable in the domain `m`"; modeled as the per-marginal representability precondition (mapping.md §2, §3). The cross product is deliberately NOT given `<= m` — that is the overflow the reorder avoids. |
| 3 | `Requires(0 <= tk <= pk, tk <= qk)` | structural facts of the contingency counting (`:856-858`) | I | `tk = Σc²−n ≥ 0`; a concordant pair is counted by each marginal so `tk ≤ pk`, `tk ≤ qk` (mapping.md §2 provenance). Same concrete inequalities in both worlds. |
| 4 | `if tk != 0.0: … else: result = 0.0` | `… if tk != 0. else 0.` (`:859`) | I | identical guard and identical zero branch. |
| 5 | `r_p = ratio(tk, pk, m)` ; `r_q = ratio(tk, qk, m)` | `tk / pk` ; `tk / qk` (`:859`, post-patch) | A-consumed | real division axiom (mapping.md §3.1): `0 <= tk <= pk <= m` ⇒ `tk/pk ∈ [0,1]` and `== tk/pk`. The proof consumes the unit-interval bound (it keeps the operands representable). G-AX checks it on the real `/`. |
| 6 | `root(r_p, m)` ; `root(r_q, m)` | `np.sqrt(tk / pk)` ; `np.sqrt(tk / qk)` (`:859`, post-patch) | A-consumed | square-root axiom (mapping.md §3.2): `np.sqrt` of a representable unit-interval value is in `[0,1]`. The proof consumes both the non-negativity/unit bound AND the `Requires(x <= m)` representability gate — the gate is what makes the **pre-patch** order (which feeds the over-`m` cross product to the root) unverifiable (G-DIFF). G-AX checks it on the real `np.sqrt`. |
| 7 | `mul(root(r_p,m), root(r_q,m))` | `np.sqrt(tk/pk) * np.sqrt(tk/qk)` (`:859`, post-patch) | A-consumed | multiplication axiom (mapping.md §3.3): product of two unit-interval reals is in `[0,1]` and `== x*y`. The proof consumes the unit-interval bound (the index is a similarity in `[0,1]`, i.e. finite — exactly what the F2P `assert_all_finite` demands). G-AX checks it on the real `*`. |
| 8 | `return result` | `return …` | I | identical. |

## Why no separate `model_prepatch_<k>`: a single fixed behaviour

The fix is a single observable behavioural change — *the index is finite/in-range
on the large-count regime instead of non-finite* — produced by the
widening+reorder pair acting together to keep every formed quantity inside the
domain `m`. There is one `model_prepatch.py`: it keeps the spec byte-identical
and transcribes the pre-patch evaluation order (form `prod = pk * qk`, then
`root(prod, m)`, then divide). It **fails** verification at the `root(prod, m)`
precondition `prod <= m` — i.e. `pk * qk <= m` is not derivable from the
per-marginal representability (`pk <= m`, `qk <= m`) — which is precisely the
int-overflow the issue reports (the cross product leaves the representable
range, so the square root receives a non-representable value and the result is
non-finite). That is the spec sensing the bug (G-DIFF).

The widening (`.astype(np.int64)`) alone is insufficient — `pk * qk` overflows
even int64 (≈ 1.7e19 > 9.2e18; confirmed in axiom_check.py on the actual failing
labels) — so the prepatch correctly fails even though it could "have widened":
the model gives `pk <= m`, `qk <= m` (the widening's effect) yet still cannot
discharge `pk * qk <= m`. Only the reorder (model.py impl: divide first) keeps
every intermediate `<= m`. The discriminating clause is therefore the
representability gate on the square-root argument, shared by both the
"didn't widen" and "widened but didn't reorder" failure modes.

## No kind-3 (unexpressible-changed-op) steps

Every step above is R, A, or I. The operations that genuinely *changed* —
division, square root, multiplication on numeric scalars — are **unchanged
numeric callees** (invoked both before and after the fix); only their
*evaluation order* and integer *width* changed. They are modeled as
**A-consumed** axioms (`ratio`/`root`/`mul`) over interpreted reals, each the
weakest sufficient contract, each validated against the real operation by
axiom_check.py (G-AX). The changed *order* (divide-first vs. product-first) and
*width* (`m` bound) are modeled deeply and concretely in the impl + preconditions
(steps 2, 5–7), not hidden behind an axiom. There is no axiom about the function
under change itself.

## verify(model) ⇒ resolved

`pair_similarity_index` verifies only if it forms the two unit-interval ratios
first and never feeds an over-`m` quantity to the square root (steps 5–7,
enforced by the `root` representability precondition), and only if the result is
in `[0,1]` (finite) on every admissible input including the large-count regime
(post-conditions). By R (integer ↔ real; the `.astype(np.int64)` widening ↔ the
`m` bound) and the A-consumed axioms (validated == the real `/`, `np.sqrt`, `*`
by G-AX), the verified computation equals the gold patch's
`np.sqrt(tk/pk) * np.sqrt(tk/qk)` on the tested inputs; the gold patch resolves
(G-RESOLVE). The trust points are exactly the two of PLAN §1.1: axiom soundness
(G-AX) and refinement fidelity (this document, G-EQ).
