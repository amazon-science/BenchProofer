# refinement.md — django__django-14559

The operation-by-operation correspondence between `model.py`'s implementation
(the `bulk_apply_count` impl region, the deep `batched_total` fold, and the live
`matched_rows` axiom) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A** (axiomatized callee — split into **A-consumed**,
where the proof uses the axiom's `Ensures`, and **A-reference**, where a deep
model is validated == the real callee by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The two gold hunks

```
@@ bulk_update @@
-        if not objs:
-            return                      # (hunk 1) pre-patch: returns None
+        if not objs:
+            return 0                    # (hunk 1) post-patch: returns 0
 ...
+        rows_updated = 0                # (hunk 2)
         with transaction.atomic(using=self.db, savepoint=False):
             for pks, update_kwargs in updates:
-                self.filter(pk__in=pks).update(**update_kwargs)   # report discarded
+                rows_updated += self.filter(pk__in=pks).update(**update_kwargs)
+        return rows_updated             # (hunk 2)
```

## B. Operation correspondence

| # | model.py impl op (`bulk_apply_count`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | parameter `keys: List[int]` | `objs` (tuple of instances), each reduced to `obj.pk` | R | object ↔ its primary-key value; the affected-row count depends only on the pks (mapping.md §2). Order and multiplicity preserved. |
| B2 | parameter `group_size: int`, `Requires(group_size >= 1)` | the effective `batch_size` (`min(batch_size, max_batch_size)` or `max_batch_size`, always `>= 1`) | R | the effective batch size is a positive int; positional chunking `objs[i:i+batch_size]` ↔ `keys` split into groups of `group_size` (mapping.md §2). |
| B3 | `if len(keys) == 0: return 0` | hunk 1: `if not objs: return 0` | I | the empty-collection early exit returning a zero count. Concrete-identical control flow; `len(keys) == 0` ↔ `not objs` under R (empty collection). |
| B4 | the forward loop over groups: `total = total + matched_rows(rem.take(group_size))`, `off += step` | hunk 2: `for pks, update_kwargs in updates: rows_updated += self.filter(pk__in=pks).update(**update_kwargs)` | A-consumed + I | the accumulation is identical (`+=` of the per-group report into a running total, initialised `0`); each per-group call `matched_rows(group)` ↔ `self.filter(pk__in=pks).update(...)`, the unchanged callee (axiom, mapping.md §3.1). The grouping `rem.take(group_size)` over the suffix ↔ the precomputed `updates` list of per-`batch_objs` pk groups (`query.py:550,565`). |
| B5 | `return total` | hunk 2: `return rows_updated` | I | return the accumulated total. Under R, `total : int` (non-`None`) ↔ `rows_updated : int`; `Result() is not None` ↔ "returns the int count, not None". |

The discriminating content of the change — *report a count instead of `None`,
that count being the per-group sum* — lives in the postconditions
`Result() is not None` and `Result() == batched_total(ToSeq(keys), group_size)`.
Because Nagini proves partial correctness by default, the value clauses alone
would be dischargeable vacuously by an implementation that never returns
(a frozen loop or unbounded self-recursion). The precondition therefore also
carries the termination obligation `Requires(MustTerminate(2))`, consumed by
the impl loop's strictly decreasing, bounded-below measure
`Invariant(MustTerminate(len(keys) - off))`: the count must actually be
delivered in finite time, which the real operation does (it walks a finite
tuple of groups and returns). Non-terminating same-spec implementations now
fail the obligation-leak check instead of verifying.
Pre-patch, both the empty path (bare `return`, hunk 1) and the non-empty path
(implicit fall-through, hunk 2) yield `None`; the two `model_prepatch*` files
reproduce each and **fail** the `Result() is not None` clause (G-DIFF).

## C. The duplicate subtlety (the ticket's non-triviality)

The hints/ticket flag that summing per-group `update()` returns is NOT the same
as a global distinct count: duplicates split between batches are counted twice
(Django ticket #32388). This is captured **structurally** by the deep model
`batched_total`, which sums `matched_rows` *per group*:
`batched_total(s, bs) = matched_rows(s.take(bs)) + batched_total(s.drop(bs), bs)`.
Because the sum is taken group-by-group, a key appearing in two distinct groups
is reported by each group's `matched_rows` and therefore summed twice, whereas
two appearances in one group share that group's single `matched_rows` report
(which collapses `pk__in` duplicates). The per-group collapse vs. across-group
summation is exactly the F2P `test_updated_rows_when_passing_duplicates`
(`[note, note]` one group → 1; `batch_size=1` two groups → 2). The per-group
value (the collapse) is the unchanged `update()` callee (A-consumed,
G-AX-checked, mapping.md §3.1); the *summation over groups* is the changed
logic, modelled deeply by `batched_total` + the verified accumulating loop.

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A, or I. The operation that genuinely *changed* — turning
a discarded per-group result into an accumulated, returned total — is modelled
**deeply** (the `batched_total` fold and the verified accumulating loop, B4/B5),
not hidden behind an axiom about the function under change. The only consumed
axiom, `matched_rows` (**A-consumed**, B4), covers the **unchanged** callee
`QuerySet.update` the batched loop invokes per group. There is no `A-reference`
deep-model-of-a-callee here (the changed logic is summation/return structure,
not a re-implementation of a stdlib callee), so `deep_model_references` is empty.

## E. verify(model) ⇒ resolved

`bulk_apply_count` verifies only if it terminates (the `MustTerminate`
obligation, consumed by the loop measure `len(keys) - off`) and returns a
non-`None`, non-negative count (B3, B5) equal to the per-group sum
`batched_total` (B4). By R (object ↔ pk,
effective `batch_size >= 1`, positional grouping) the verified function equals
the post-patch `bulk_update` on the tested inputs: empty → `0`
(`test_empty_objects`), 2000 distinct objects in one effective batch → 2000
(`test_large_batch`), and `[note, note]` → 1 (one group) / 2 (`batch_size=1`,
two groups) (`test_updated_rows_when_passing_duplicates`). By G-AX the per-group
axiom `matched_rows` over-approximates the real `QuerySet.update` (A-consumed).
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the one audited callee — and the gold patch
resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1: axiom
soundness (G-AX) and refinement fidelity (this document, G-EQ).
