# refinement.md — django__django-16819

The operation-by-operation correspondence between `model.py`'s implementation
(the `reduce_add_index` impl region plus the deep `base_combine` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (the proof uses an axiom's `Ensures`), **A-reference** (a deep
model is validated == the real callee by `axiom_check.py` / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The new combination rule — `AddIndex.reduce`

Gold hunk (`django/db/migrations/operations/models.py`, new method on `AddIndex`):
```python
def reduce(self, operation, app_label):
    if isinstance(operation, RemoveIndex) and self.index.name == operation.name:
        return []
    return super().reduce(operation, app_label)
```

| # | model.py impl op (`reduce_add_index`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `index_name: List[int]` | `self.index.name` (a `str`) | R | `str` ↔ `List[int]` of code points (mapping.md §2). Read-only, at `Acc(list_pred(index_name), 1/2)`. |
| A2 | `operation: Operand` with fields `is_remove_index`, `name`, `elidable` | the `operation` argument (an `Operation`) | R | minimal class carrying only the touched facets (mapping.md §2). |
| A3 | `operation.is_remove_index` | `isinstance(operation, RemoveIndex)` | R | the runtime type test ↔ a boolean tag. The optimizer only ever passes another migration `Operation`; the tag is True exactly for `RemoveIndex` instances (mapping.md §2). |
| A4 | `names_equal(index_name, operation.name)` ≡ `ToSeq(index_name) == ToSeq(operation.name)` | `self.index.name == operation.name` | R | sequence equality of code points ↔ `str.__eq__` (mapping.md §2). Evaluated under the `is_remove_index` guard — the `and` short-circuit is preserved: `operation.name` is consulted only when the operation is a removal (where the real `operation.name` exists). |
| A5 | `if operation.is_remove_index and names_equal(...): return 1` | `if isinstance(...) and ... == ...: return []` | R + I | identical control flow (a guarded early return); `return 1` ↔ `return []` is the R outcome encoding (tag 1 = empty list, mapping.md §2). |
| A6 | `return base_combine(self_elidable, operation.elidable)`, spelled out as `if self_elidable: return 2 / if operation.elidable: return 3 / return 0` | `return super().reduce(operation, app_label)` = `Operation.reduce`: `if self.elidable: return [operation] / elif operation.elidable: return [self] / return False` | R (deep model) | the unchanged base-class generic combination rule is the function-under-spec's OWN superclass logic, fully expressible, so it is modelled **deeply** (`base_combine`, 1:1 with the three base-reduce branches), NOT axiomatized. `return 2` ↔ `[operation]`, `return 3` ↔ `[self]`, `return 0` ↔ `False` (tag encoding, mapping.md §2). `app_label` is unused by `Operation.reduce` and dropped (mapping.md §3). |

## B. No axioms; no kind-3 steps

Every step is R or I. There is **no `@ContractOnly` axiom** in this bundle: the
only callee, `super().reduce`, is the base class `Operation.reduce`, expressible
as three boolean branches and modelled deeply as `base_combine` (a *deep model*,
not even an A-reference — there is no opaque external callee to validate
`base_combine` against; its faithfulness is a direct line-for-line transcription
audited in this table, step A6). Consequently `axiom_check.py` carries **no
axiom-soundness obligation**; it exists only to document that there is no axiom
and to re-assert the tag↔value encoding, and exits 0 trivially.

The one operation that genuinely *changed* — the new cancellation rule
(`isinstance(operation, RemoveIndex) and names equal ⇒ []`) — is modelled
**deeply and directly** (steps A3–A5), never hidden behind an axiom about the
function under change.

## C. The discriminating clause and G-DIFF

`reduce_add_index` verifies only if, when `operation.is_remove_index and
names_equal(index_name, operation.name)`, the result is the empty-list tag `1`
(postcondition clause 1), and otherwise the result is exactly
`base_combine(self_elidable, operation.elidable)` (clause 2). `model_prepatch.py`
reproduces the pre-patch state — `AddIndex` has **no** `reduce` override, so the
operation always defers to the generic base rule (no cancellation branch) — and
**fails** verification precisely on
`Implies(operation.is_remove_index and names_equal(index_name, operation.name),
Result() == 1)` (it returns `0`/`False` for a matching `RemoveIndex` with both
operations non-elidable). That is exactly the bug the F2P test
`test_add_remove_index` exposes: `[AddIndex("Pony", idx), RemoveIndex("Pony",
idx.name)]` must optimise to `[]`, which requires `reduce` to return the empty
list for the matching removal (G-DIFF).

## D. verify(model) ⇒ resolved

By R (str ↔ List[int]; `str.__eq__` ↔ `ToSeq` equality; `isinstance` ↔ tag;
list/`False` ↔ the four-tag encoding) the verified `reduce_add_index` computes,
for every (index_name, self_elidable, operation) input, exactly the value the
gold `AddIndex.reduce` returns: the empty list when the counterpart removes an
index of the same name, and `super().reduce(...)` otherwise. The optimizer
(`optimizer.py:48`) treats the returned empty list as a list-result that drops
both operations — the cancellation the F2P test asserts. The gold patch is this
function verbatim and resolves (G-RESOLVE). The single trust point is refinement
fidelity (this document, G-EQ); there is no axiom-soundness trust point because
there is no axiom.
