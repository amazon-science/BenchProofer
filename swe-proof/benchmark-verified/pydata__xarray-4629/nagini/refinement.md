# refinement.md — pydata__xarray-4629

The operation-by-operation correspondence between `model.py`'s implementation
(the `combine_attrs` impl region — the drop branch and the per-entry copy loop)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed**, where the proof uses an
axiom's `Ensures`, and **A-reference**, where a deep model is validated == the
real callee by axiom_check.py / G-AX), or **I** (identical concrete operation).
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The override site — `merge_attrs` (`xarray/core/merge.py:503-504`)

Gold hunk:
```
 elif combine_attrs == "override":
-    return variable_attrs[0]
+    return dict(variable_attrs[0])
```

| # | model.py impl op (`combine_attrs`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `variable_attrs: List[List[int]]` | `variable_attrs` (a `list` of attr `dict`s) | R | each mapping ↔ its content `List[int]`; the collection ↔ `List[List[int]]` (mapping.md §2). |
| A2 | parameter `mode: int` (`OVERRIDE=1`) compared `mode == OVERRIDE` | `combine_attrs == "override"` | R | mode string ↔ `int` token; equality compare ↔ equality compare (mapping.md §2). |
| A3 | `src = variable_attrs[0]` | `variable_attrs[0]` | R/I | the leading-source selection; index `0` is identical, carrier refined per A1. |
| A4 | the per-entry copy loop building a fresh `result` with `ToSeq(result) == ToSeq(src)` and `result is not src`, returned with full permission | `dict(variable_attrs[0])` | A-reference | the changed operation is modelled **deeply**: the spelled-out loop IS the copy. There is no consumed copy axiom — the proof never depends on one. The deep model is validated **== the real callee** out-of-band: G-AX (axiom_check.py) runs `dict(variable_attrs[0])` and asserts it returns a distinct (`is not`), content-equal object whose mutation leaves the source unchanged — exactly what the loop's postconditions (`Result() is not variable_attrs[0]`, `ToSeq(Result()) == ToSeq(variable_attrs[0])`, full `Acc(list_pred(Result()))` with the source's `1/2` retained) encode. `dict(d)` is precisely a fresh content-equal copy (mapping.md §3.1). |

The discriminating content of the change — the result is an INDEPENDENT object,
not a shared reference to `variable_attrs[0]` — lives in the postcondition pair
`Result() is not variable_attrs[0]` + `Acc(list_pred(Result()))` while
`Acc(list_pred(variable_attrs[0]), 1/2)` is retained. A result that aliased the
source would need full + half permission on the same object (`3/2 > 1`),
impossible. The pre-patch `return variable_attrs[0]` reproduces exactly that
alias; `model_prepatch.py` returns the alias and **fails** the postcondition
`Acc(list_pred(Result()))` (insufficient permission), which is precisely the
spec sensing the change (G-DIFF).

## B. The drop site — `merge_attrs` (`xarray/core/merge.py:501-502`)

| # | model.py impl op (`combine_attrs`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `mode == DROP` → return a fresh empty `List[int]` (`len(Result()) == 0`, full permission) | `if combine_attrs == "drop": return {}` | R/I | unchanged sibling branch, modeled to situate the override change; `{}` (fresh empty dict) ↔ a fresh empty list. Identical control flow under the carrier refinement. Not in the gold diff (no hunk), so no separate prepatch witness. |

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — wrapping the leading source in `dict(...)` to make an independent
copy — is modelled **deeply** (the spelled-out per-entry copy loop in
`combine_attrs`, step A4, an **A-reference**), not hidden behind an axiom about
the function under change: there is **no consumed copy axiom**. There are no
A-consumed axioms in this bundle (the model imports no `@ContractOnly`). The
deep model's equality to the real `dict(...)` copy (distinct object, equal
content) is the only trust point on the axiom side, and it is audited by G-AX
(axiom_check.py).

## D. verify(model) ⇒ resolved

`combine_attrs` verifies only if, under `OVERRIDE`, the result is a DISTINCT
object from `variable_attrs[0]` carrying full permission while the source keeps
its read permission (A4), with content equal to `variable_attrs[0]`. By R
(mapping ↔ `List[int]` content, mode ↔ token, identity ↔ Nagini reference
identity) the verified branch equals `dict(variable_attrs[0])` on the tested
inputs; by G-AX the deep copy model equals the real `dict(...)` copy
(A-reference). Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement and the audited copy reference — and the
gold patch resolves (G-RESOLVE: the F2P `test_merge_attrs_override_copy` mutates
the merged attrs and asserts the source is unchanged). The trust points are
exactly the two of PLAN §1.1: deep-model/axiom soundness (G-AX) and refinement
fidelity (this document, G-EQ).
