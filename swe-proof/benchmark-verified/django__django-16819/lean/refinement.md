# refinement.md — django__django-16819

Maps every operation in `implementation_reduceAddIndex` to its `patch.diff`
counterpart (the `AddIndex.reduce` method added in
`django/db/migrations/operations/models.py`). Tags: **R** type-refinement,
**A-consumed** proof uses a callee axiom, **A-reference** deep-modeled / opaque
unchanged callee validated == real callee by G-AX, **I** identical concrete op.

## Patch (the added method)
```python
def reduce(self, operation, app_label):
    if isinstance(operation, RemoveIndex) and self.index.name == operation.name:
        return []
    return super().reduce(operation, app_label)
```

## Operation correspondence
| # | Lean op (`implementation_reduceAddIndex`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `if op.isRemoveIndex && selfName == op.name then` | `if isinstance(operation, RemoveIndex) and self.index.name == operation.name:` | R | the added guard. `op.isRemoveIndex : Bool` ↔ `isinstance(operation, RemoveIndex)`; `selfName == op.name` ↔ `self.index.name == operation.name` (string equality). Conjunction `&&` ↔ `and` (both short-circuit; equivalent here as both sides are pure). |
| 2 | `return ReduceResult.replace []` | `return []` | R | the annihilation: the add/remove pair is replaced by NO operations. `ReduceResult.replace []` ↔ the empty `list` (distinct from the `False` "cannot optimize" sentinel — see op 4 bijection). |
| 3 | `return baseReduce selfName op appLabel` | `return super().reduce(operation, app_label)` | A-reference | fallback to the UNCHANGED generic reducer `Operation.reduce` (`base.py:128-138`). Modeled opaquely as `baseReduce`; the spec frames the else-branch to its value (not left free). The proof consumes NO property of it (closes by case split + `rfl`), so it is an A-reference validated == real `Operation.reduce` by G-AX, not a consumed axiom. |
| (type) | `ReduceResult.cannot` vs `ReduceResult.replace _` | `False` vs `list[Operation]` | R | the result-type bijection (mapping.md): `False` ↔ `.cannot`, any returned list ↔ `.replace`. |

Op 1 + 2 are R (the only behavior the patch adds); op 3 is A-reference. The impl
region is therefore NOT all-A-tagged → `conf_skip = false`: G-CONF
differential-tests the R guard leg (with `baseReduce` left as the real
`Operation.reduce` callee, per the A-reference rule).

## A-reference (no consumed axiom)
`super().reduce` is referenced, not axiomatized: the proof does not use any
`baseReduce_prop`. `meta.json axioms = []`; `deep_model_references = ["baseReduce"]`.
G-AX validates that the model treats the fallback as the real `Operation.reduce`
(it is invoked unchanged on the same `(operation, app_label)`), by exercising the
real `Operation.reduce` on boundary + fuzzed operations and confirming the
else-branch result equals it.

## R/I legs ⇒ G-CONF
The guard leg (ops 1–2) is R, so `conformance_check.py` mechanically
differential-tests the impl shadow against the patched `AddIndex.reduce` behavior
over ≥10⁵ fuzzed `(self.index.name, operation, app_label)` inputs, using the REAL
`Operation.reduce` for the else-branch (the A-reference left as the real callee).
`conf_skip = false`.

## Prepatch = the real bug
Pre-patch, `AddIndex` has NO `reduce` override, so its reduction ALWAYS resolves
to `Operation.reduce` (the inherited generic fallback) — even when the following
operation is a `RemoveIndex` of the same index name. The add/remove pair that
should annihilate is never cancelled. The prepatch impl
(`return baseReduce selfName op appLabel`, unconditionally) is exactly this: it
omits the guard and always defers to the base reducer. It cannot satisfy
`problem_spec_reduceAddIndex` on the same-name remove-index branch, where the
spec demands `ReduceResult.replace []` but the impl yields the opaque
`baseReduce` (which is `.cannot`/`False` here, since neither operation is
elidable) — precisely the case the FAIL_TO_PASS test `test_add_remove_index`
exercises (an `AddIndex` then a matching-name `RemoveIndex` must optimize to
`[]`). The carried gold proof fails to typecheck against the buggy impl (its
`split <;> rfl` cannot close the annihilation branch), the G-DIFF signal.
