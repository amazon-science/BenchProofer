# refinement.md — django__django-14122

The operation-by-operation correspondence between `model.py`'s implementation
(the `assemble_grouping_key` impl region and the deep `order_contrib` fold) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — **A-consumed** where the proof uses the axiom's
`Ensures`, **A-reference** where a deep model is validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The grouping-key site — `get_group_by()` (`django/db/models/sql/compiler.py:63`)

Gold hunk (`compiler.py:128-132`):
```
-        for expr, (sql, params, is_ref) in order_by:
-            # Skip References to the select clause, as all expressions in the
-            # select clause are already part of the group by.
-            if not is_ref:
-                expressions.extend(expr.get_group_by_cols())
+        if not self._meta_ordering:
+            for expr, (sql, params, is_ref) in order_by:
+                # Skip references to the SELECT clause, as all expressions in
+                # the SELECT clause are already part of the GROUP BY.
+                if not is_ref:
+                    expressions.extend(expr.get_group_by_cols())
```
The change wraps the existing ordering loop in `if not self._meta_ordering:`.

| # | model.py impl op (`assemble_grouping_key`) | patch.diff / surrounding op | tag | justification |
|---|---|---|---|---|
| A1 | the SELECT loop `while s < len(select_cols): result.append(select_cols[s])` | `for expr, _, _ in select: expressions.extend(expr.get_group_by_cols())` (+ the ref-source skip and `having` are folded into `select_cols`/`trailing_cols`) | R + I | unconditional append of the SELECT source's tokens; column objects ↔ `int` tokens (mapping.md §2). Outside the changed hunk; faithfully reproduced. |
| A2 | guard `if ordering_was_requested:` around the ordering loop | the inserted `if not self._meta_ordering:` | R | `ordering_was_requested` ↔ `not self._meta_ordering` (mapping.md §1, §3.2): `_meta_ordering` is truthy iff the ordering is the model default. This is the single changed control-flow node. |
| A3 | inner `while k < len(order_cols): if order_is_backref[k] == 0: result.append(order_cols[k])` | `for expr, (sql, params, is_ref) in order_by: if not is_ref: expressions.extend(expr.get_group_by_cols())` | R + I | per-entry back-reference skip; `is_ref` bool ↔ `order_is_backref[k] != 0`; `extend(get_group_by_cols())` ↔ append one token (mapping.md §2). The accumulated result equals the deep model `order_contrib(order_cols, order_is_backref)` (step A5). |
| A4 | the trailing loop `while t < len(trailing_cols): result.append(trailing_cols[t])` | `for expr in having_group_by: expressions.append(expr)` (`compiler.py:133-135`) | R + I | unconditional append of the trailing (HAVING) source; outside the changed hunk; reproduced. |
| A5 | the value of `order_contrib(ToSeq(order_cols), ToSeq(order_is_backref))` and the conditional assembly in the two postcondition clauses | the whole patched `get_group_by` token algorithm (the SELECT loop, the *guarded* ordering loop with its ref skip, the HAVING loop) | A-reference | the changed operation is modeled **deeply**: `order_contrib` (the spelled-out non-back-reference fold) + the `ordering_was_requested` guard ARE the patched assembly. There is **no consumed axiom**. The deep model is validated **== the real patched logic** out-of-band: G-AX (axiom_check.py) transcribes the patched `get_group_by` at the token level and asserts equality on 14 boundary + 50 000 fuzz inputs, plus the F2P default-ordering witness (mapping.md §3.1). |

The discriminating content of the change — that a DEFAULT ordering must NOT add
its columns to the grouping key — lives in the postcondition clause
`Implies(not ordering_was_requested, ToSeq(Result()) == ToSeq(select_cols) + ToSeq(trailing_cols))`
(no ordering tokens). The pre-patch code folds the ordering source in
unconditionally; `model_prepatch.py` reproduces that (the ordering loop is run
with no guard) and **fails** exactly this clause (G-DIFF) — see §B.

## B. The pre-patch differential (G-DIFF)

`model_prepatch.py` keeps the spec byte-identical and reverts the impl to the
pre-patch skeleton: the ordering loop runs **unconditionally** (no
`if ordering_was_requested:` guard). It then always produces
`select_cols + order_contrib(order_cols, order_is_backref) + trailing_cols`, which
satisfies the `ordering_was_requested` postcondition clause but **violates** the
`not ordering_was_requested` clause whenever the ordering contributes a
non-back-reference token. Nagini reports exactly:

```
Postcondition of assemble_grouping_key might not hold. Assertion
Implies((not ordering_was_requested),
        (ToSeq(Result()) == (ToSeq(select_cols) + ToSeq(trailing_cols))))
might not hold.
```

This is the spec sensing the bug: a default ordering's column leaking into the
grouping key — precisely the wrong-aggregation defect the issue reports
(`values('author').annotate(Count('author'))` on a model with
`Meta.ordering = ['-pub_date']` would erroneously group by `pub_date` too).

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the conditional folding of the ordering source — is modeled
**deeply** (the `order_contrib` fold + the `ordering_was_requested` guard,
step A5, an **A-reference**), not hidden behind an axiom about the function
under change. There is **no consumed `@ContractOnly` axiom** (the `axioms`
region is empty), so there is no A-consumed row and no dead axiom.

## D. verify(model) ⇒ resolved

`assemble_grouping_key` verifies only if its result drops the ordering source's tokens
when `ordering_was_requested` is false (A2, A5) and includes the non-back-ref
ordering tokens when it is true (A3, A5). By R (`int` tokens ↔ grouping columns,
`_meta_ordering` ↔ `not ordering_was_requested`) the verified assembly equals the
patched `get_group_by`'s token-level behaviour; by G-AX the deep model
`order_contrib`/`assemble_grouping_key` equals the real patched `get_group_by`
algorithm (A-reference) over boundary + 50 000 fuzz inputs incl. the F2P
witness. Therefore a model satisfying this spec, refined by the map above, is the
gold patch up to type refinement — and the gold patch resolves (G-RESOLVE). The
single trust point is refinement fidelity (this document, G-EQ) plus the
A-reference soundness check (G-AX); there is no axiom-soundness trust point
because there is no consumed axiom.
