# refinement.md — django__django-13089

The operation-by-operation correspondence between `model.py`'s implementation
(the `boundary_for_prune` impl region) and `patch.diff` (the gold patch). Each
step is tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed** / **A-reference**), or **I** (identical concrete operation). The
claim: *any implementation that verifies against this frozen spec, refined per
the map below, is behaviourally equal to the gold patch on the tested inputs,
so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The prune-boundary site — `DatabaseCache._cull` (`django/core/cache/backends/db.py:270-272`)

Gold hunk:
```
-                cursor.execute("DELETE FROM %s "
-                               "WHERE cache_key < %%s" % table,
-                               [cursor.fetchone()[0]])
+                last_cache_key = cursor.fetchone()
+                if last_cache_key:
+                    cursor.execute(
+                        'DELETE FROM %s WHERE cache_key < %%s' % table,
+                        [last_cache_key[0]],
+                    )
```

| # | model.py impl op (`boundary_for_prune`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `row: Optional[List[int]]` | `cursor.fetchone()` result | R | the DB-API `fetchone()` returns `None` on an empty result set, else a non-empty row sequence; `Optional[List[int]]` is that carrier (mapping.md §2). The model receives the value the patch binds to `last_cache_key`. |
| A2 | `if row is not None:` | `if last_cache_key:` | R | a single-column `fetchone()` result is `None` or a non-empty row; its truthiness ↔ `is not None` (mapping.md §2). This is the GUARD the patch introduces — the heart of the fix. |
| A3 | `last = row[0]` (inside the guard) | `last_cache_key[0]` (inside the guard) | I + R | reading the row's first column — the boundary `cache_key`. Identical subscript operation; `int` column value ↔ `str` `cache_key` is the R carrier refinement (mapping.md §2). The subscript is reachable only under the presence guard (A2), so it is well defined. |
| A4 | `return last` (a present `int`) | `cursor.execute('DELETE ... WHERE cache_key < %s', [last_cache_key[0]])` | R | issuing the prune bound to the boundary key is modeled as producing that key as the present `Result()`. The model's observable is "which key the prune ran with"; the patch's observable is the executed DELETE with that key in its parameter list. |
| A5 | `return None` (the `else`/fall-through) | (no `cursor.execute` — the guard is false) | R | when no row is present the patch issues **no** DELETE; the model produces `Result() is None` (no prune issued). This is the post-fix behaviour the F2P test observes: with the store empty relative to culling, `_cull` completes without error and without deleting the just-set record. |

The discriminating content of the change — the prune subscript is consulted
ONLY when a row is present — lives in the guard (A2/A5). The pre-patch code
subscripts `cursor.fetchone()[0]` unconditionally; `model_prepatch.py`
reproduces that (`last = row[0]` with no guard) and **fails** verification on
the obligation that `row[0]`'s precondition (`len(row) > 0`, which holds only
when `row is not None`) might not hold — exactly the spec sensing the
`'NoneType' object is not subscriptable` defect (G-DIFF). The post-patch model
discharges it because the subscript sits under `row is not None`.

## B. No consumed axiom; no A-reference

The `axioms` region is empty. The changed behaviour is modeled **deeply** as
optional-row logic over the input `row`; no `@ContractOnly` contract is
consumed by the proof, and there is no deep model standing in for a real callee
that G-AX must validate. `cursor.fetchone()` is the *producer* of the modeled
`Optional[List[int]]` value (A1), not a callee whose contract the proof relies
on. The single fact the refinement relies on — DB-API `fetchone()` returns
`None` on an empty result set and otherwise a non-empty row whose `[0]` is the
selected column — is the standard, documented PEP 249 contract (mapping.md §3);
it is recorded for completeness in `axiom_check.py`, which exercises that
contract shape, but the proof consumes no axiom.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, I, or R-of-I. The one operation that genuinely changed —
guarding the row subscript on the row's presence — is modeled directly with
`Optional[List[int]]` + an `is not None` guard (A2/A5), not hidden behind an
axiom. There is no kind-3 step.

## D. verify(model) ⇒ resolved

`boundary_for_prune` verifies only if (1) it produces `Result() is None`
exactly when `row is None` — i.e. it issues no prune when the boundary row is
absent (clause `(Result() is None) == (row is None)`), and (2) it never reads a
column from an absent row (the unguarded subscript fails verification, as
`model_prepatch.py` shows), and (3) when a row is present the produced key is
exactly `row[0]` (clause `Implies(row is not None, Result() == row[0])`). By the
R-refinements (mapping.md §2: `fetchone()`↔`Optional[List[int]]`,
truthiness↔`is not None`, `cache_key`↔`int` column) a verified implementation is
exactly the guarded subscript-and-DELETE of the gold patch on the tested inputs.
The F2P tests (`test_cull_delete_when_store_empty`, both DB variants) force
`_cull` to reach the boundary fetch with an empty culling result (`_max_entries
= -1`) and assert the just-set record survives — which holds iff no DELETE is
issued for the absent row (A5). Therefore a model satisfying this spec, refined
by the map above, is the gold patch up to type refinement — and the gold patch
resolves (G-RESOLVE).
