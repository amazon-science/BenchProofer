# refinement.md — django__django-14559

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`totalRowsMatched` `do` block + the deep `totalMatched` model) and `patch.diff` (the gold
patch). Each step is tagged **R** (type refinement), **A** (axiomatized callee —
**A-consumed** where the proof uses the axiom's `ensures`, **A-reference** where a
deep model is validated == the real callee by G-AX), or **I** (identical concrete
op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The aggregate-count site — `bulk_update()` (`django/db/models/query.py`)

Gold hunks:
```
@@ -541 (empty-objs fast path)
-            return
+            return 0
@@ -563..570 (accumulate per-batch update() returns)
+        rows_updated = 0
         with transaction.atomic(using=self.db, savepoint=False):
             for pks, update_kwargs in updates:
-                self.filter(pk__in=pks).update(**update_kwargs)
+                rows_updated += self.filter(pk__in=pks).update(**update_kwargs)
+        return rows_updated
```

| # | Solution.lean impl op (`totalRowsMatched`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `matched : List Nat` | the sequence of `self.filter(pk__in=pks).update(**update_kwargs)` return values, one per batch in `updates` | A-reference + R | each element is one **unchanged** `QuerySet.update()` call's matched-row count, a non-negative `int` modeled as `Nat` (mapping.md §2, §3.1). The list itself is the deep-model reference G-AX validates (`update() ≥ 0`); `list[int] ↔ List Nat` is the R bijection. The patch does not change *how* each count is produced — only that they are summed. |
| A2 | `result : Nat := 0`, accumulated by the backward `while` fold to `totalMatched matched` | `rows_updated = 0` then `rows_updated += <update()>` per batch (`query.py:566-569`) | I | concrete accumulation: Python `int` `+=` over batches ↔ the `Nat` `+` fold. `totalMatched`/the loop ARE the summation; G-CONF transliterates it to `sum(...)`. |
| A3 | `return result` (`Nat`) | `return rows_updated` (`int`) | R | `int` total ↔ `Nat` (mapping.md §2); the harness compares the returned integer. |
| A4 | empty input: `matched = []` ⇒ loop body never runs ⇒ `result = 0 = totalMatched []` | `if not objs: return 0` fast path (`query.py:544`) | I | empty-batch-sequence total is `0` on both sides; `totalMatched_nil`. |

Discriminating content of the change — the per-batch counts are **summed and
returned** rather than discarded with a `None` return — lives in
`out = totalMatched matched` (model) ⇔ `rows_updated += …; return rows_updated` (real).
The pre-patch discarded each count and returned `None`;
`Solution_prepatch.lean` reproduces that (the loop body throws away
`matched[i-1]!` and never accumulates) and **fails** `out = totalMatched matched`
whenever any batch matched a positive number of rows (G-DIFF; the unsolved goal
reduces to `matched[i-1]?.getD 0 = 0`).

## B. No consumed axioms

There is no `axiom` the proof consumes. The only callee touched by the modeled
region, `QuerySet.update()`, is **unchanged**, and the single property relied
upon (its return is a non-negative count) is carried by the `Nat` carrier type
itself and validated against the real callee by G-AX (A-reference, mapping.md
§3.1). The summation — the operation the patch actually introduces — is modeled
**deeply** by `totalMatched`, not axiomatized.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The one operation that genuinely *changed* —
aggregating the per-batch counts and returning the total — is modeled **deeply**
(the spelled-out front-recursive fold `totalMatched` + the verified backward loop,
steps A2/A4, I), not hidden behind an axiom about the function under change.

## D. verify(Solution) ⇒ resolved

`totalRowsMatched` verifies only if its output equals the exact running total of
the per-batch counts (`out = totalMatched matched`), with the empty sequence totalling
`0` (A4). By R (`int ↔ Nat`, `list[int] ↔ List Nat`) the verified aggregate
equals `rows_updated` after `rows_updated += <each update()>`; by G-AX the
deep-model reference `matched` matches the real `QuerySet.update()` returns
(A-reference, each `≥ 0`); by G-CONF the R/I transliteration of the fold
(`sum`) agrees with the real patched `bulk_update`'s return value on ≥10⁵ fuzzed
object-list × batch-size inputs (incl. the duplicate-in-one-batch `1` vs
duplicate-across-batches `2` F2P cases). Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement and the audited
callee reference — and the gold patch resolves (G-RESOLVE). The one trust point
is the A-reference (`update()` return is the matched-row count, G-AX); refinement
fidelity is this doc + G-EQ + G-CONF.
